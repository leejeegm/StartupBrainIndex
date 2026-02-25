"""
SBI MVP 부하 테스트: 동시 접속·RPS·에러율·지연 구간 측정.
사용법:
  1. 서버 실행 (run_server.bat 또는 python main.py)
  2. python load_test.py
     또는 python load_test.py --base http://127.0.0.1:8000 --workers 50 --duration 30
"""
import argparse
import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from urllib.parse import urljoin

try:
    import requests
except ImportError:
    print("requests 필요: pip install requests")
    raise

# 전역 수집
latencies = []  # (endpoint, latency_sec, status_code, error_msg)
latencies_lock = Lock()
BASE_URL = "http://127.0.0.1:8000"
TIMEOUT = 30


def _get(url: str, session: requests.Session, **kwargs) -> tuple:
    t0 = time.perf_counter()
    err_msg = None
    status = 0
    try:
        r = session.get(url, timeout=TIMEOUT, **kwargs)
        status = r.status_code
    except Exception as e:
        err_msg = str(e)
    elapsed = time.perf_counter() - t0
    return (url, elapsed, status, err_msg)


def _post(url: str, session: requests.Session, json=None, data=None, **kwargs) -> tuple:
    t0 = time.perf_counter()
    err_msg = None
    status = 0
    try:
        if json is not None:
            r = session.post(url, json=json, timeout=TIMEOUT, **kwargs)
        else:
            r = session.post(url, data=data, timeout=TIMEOUT, **kwargs)
        status = r.status_code
    except Exception as e:
        err_msg = str(e)
    elapsed = time.perf_counter() - t0
    return (url, elapsed, status, err_msg)


def one_user_flow_light(base: str, user_index: int) -> list:
    """경량 시나리오: GET /, GET /health 만 (세션 불필요). 최대 RPS/동시접속 한계 측정용."""
    session = requests.Session()
    session.headers.update({"User-Agent": "SBI-LoadTest/1.0"})
    results = []
    u = urljoin(base, "/")
    r = _get(u, session)
    results.append(("/", r[1], r[2], r[3]))
    u = urljoin(base, "/health")
    r = _get(u, session)
    results.append(("/health", r[1], r[2], r[3]))
    return results


def one_user_flow(base: str, user_index: int, use_light: bool = False) -> list:
    """한 명의 사용자 시나리오: 루트 → 로그인 → 대시보드 → API(경량). use_light=True면 경량만."""
    if use_light:
        return one_user_flow_light(base, user_index)
    session = requests.Session()
    session.headers.update({"User-Agent": "SBI-LoadTest/1.0"})
    results = []

    # 1) GET /
    u = urljoin(base, "/")
    r = _get(u, session)
    results.append(("/", r[1], r[2], r[3]))

    # 2) GET /login
    u = urljoin(base, "/login")
    r = _get(u, session)
    results.append(("/login", r[1], r[2], r[3]))

    # 3) POST /login (데모 계정)
    u = urljoin(base, "/login")
    r = _post(u, session, data={"email": "user@test.com", "password": "pass1234", "next": "/dashboard"})
    results.append(("/login POST", r[1], r[2], r[3]))
    if r[2] not in (200, 302, 303):
        return results  # 로그인 실패 시 여기서 종료

    # 4) GET /dashboard
    u = urljoin(base, "/dashboard")
    r = _get(u, session)
    results.append(("/dashboard", r[1], r[2], r[3]))

    # 5) GET /api/me
    u = urljoin(base, "/api/me")
    r = _get(u, session)
    results.append(("/api/me", r[1], r[2], r[3]))

    # 6) GET /health (경량)
    u = urljoin(base, "/health")
    r = _get(u, session)
    results.append(("/health", r[1], r[2], r[3]))

    return results


def run_worker(base: str, user_index: int, use_light: bool = False) -> None:
    try:
        res = one_user_flow(base, user_index, use_light=use_light)
        with latencies_lock:
            for path, elapsed, status, err in res:
                latencies.append((path, elapsed, status, err))
    except Exception as e:
        with latencies_lock:
            latencies.append(("_worker", 0, 0, str(e)))


def run_load_test(base_url: str, num_workers: int, duration_sec: int, light_only: bool = False) -> dict:
    global latencies
    latencies = []
    base = base_url.rstrip("/")

    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        futures = [ex.submit(run_worker, base, i, light_only) for i in range(num_workers)]
        for f in as_completed(futures):
            if time.perf_counter() - start >= duration_sec:
                break
    elapsed_total = time.perf_counter() - start

    # 집계
    by_path = {}
    for path, lat, status, err in latencies:
        if path not in by_path:
            by_path[path] = {"latencies": [], "statuses": [], "errors": []}
        by_path[path]["latencies"].append(lat)
        by_path[path]["statuses"].append(status)
        if err:
            by_path[path]["errors"].append(err)

    total_requests = len(latencies)
    all_lat = [x[1] for x in latencies]
    ok = sum(1 for x in latencies if x[2] in (200, 302, 303))
    failed = total_requests - ok

    report = {
        "base_url": base_url,
        "num_workers": num_workers,
        "light_only": light_only,
        "duration_sec": round(elapsed_total, 2),
        "total_requests": total_requests,
        "ok_requests": ok,
        "failed_requests": failed,
        "error_rate_pct": round(100 * failed / total_requests, 2) if total_requests else 0,
        "rps": round(total_requests / elapsed_total, 2) if elapsed_total > 0 else 0,
        "latency_all_ms": {
            "min": round(min(all_lat) * 1000, 2) if all_lat else 0,
            "max": round(max(all_lat) * 1000, 2) if all_lat else 0,
            "avg": round(statistics.mean(all_lat) * 1000, 2) if all_lat else 0,
        },
        "by_path": {},
    }

    if all_lat:
        sorted_lat = sorted(all_lat)
        n = len(sorted_lat)
        report["latency_all_ms"]["p50_ms"] = round(sorted_lat[int(n * 0.50)] * 1000, 2)
        report["latency_all_ms"]["p95_ms"] = round(sorted_lat[int(n * 0.95)] * 1000, 2) if n >= 20 else report["latency_all_ms"]["max"]
        report["latency_all_ms"]["p99_ms"] = round(sorted_lat[int(n * 0.99)] * 1000, 2) if n >= 100 else report["latency_all_ms"]["max"]

    for path, data in by_path.items():
        lats = data["latencies"]
        report["by_path"][path] = {
            "count": len(lats),
            "ok": sum(1 for s in data["statuses"] if s in (200, 302, 303)),
            "avg_ms": round(statistics.mean(lats) * 1000, 2) if lats else 0,
            "p95_ms": round(sorted(lats)[int(len(lats) * 0.95)] * 1000, 2) if len(lats) >= 20 else (round(lats[0] * 1000, 2) if lats else 0),
            "error_sample": data["errors"][:3] if data["errors"] else None,
        }

    return report


def main():
    global BASE_URL
    ap = argparse.ArgumentParser(description="SBI MVP 부하 테스트")
    ap.add_argument("--base", default=BASE_URL, help="서버 주소 (예: http://127.0.0.1:8000)")
    ap.add_argument("--workers", type=int, default=20, help="동시 사용자(스레드) 수")
    ap.add_argument("--duration", type=int, default=15, help="최대 유지 시간(초)")
    ap.add_argument("--light", action="store_true", help="경량만 (/ + /health) 측정")
    args = ap.parse_args()
    BASE_URL = args.base

    print(f"[SBI 부하테스트] {args.base} / workers={args.workers} / duration={args.duration}s" + (" [경량]" if args.light else " [전체플로우]"))
    print("서버가 실행 중이어야 합니다. (run_server.bat 또는 python main.py)")
    report = run_load_test(args.base, args.workers, args.duration, light_only=args.light)

    # 콘솔 출력
    print("\n========== 요약 ==========")
    print(f"총 요청: {report['total_requests']}, 성공: {report['ok_requests']}, 실패: {report['failed_requests']}")
    print(f"에러율: {report['error_rate_pct']}%")
    print(f"RPS: {report['rps']}")
    print(f"지연(전체): min={report['latency_all_ms']['min']}ms, avg={report['latency_all_ms']['avg']}ms, p95={report['latency_all_ms'].get('p95_ms')}ms, max={report['latency_all_ms']['max']}ms")
    print("\n========== 경로별 ==========")
    for path, d in report["by_path"].items():
        print(f"  {path}: count={d['count']}, ok={d['ok']}, avg_ms={d['avg_ms']}, p95_ms={d['p95_ms']}" + (f", errors={d['error_sample']}" if d.get("error_sample") else ""))

    # 보고서 파일 저장
    report_path = "load_test_report.txt"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("SBI MVP 부하 테스트 보고\n")
        f.write(f"BASE_URL={report['base_url']}\n")
        f.write(f"workers={report['num_workers']}, duration_sec={report['duration_sec']}\n")
        f.write(f"total_requests={report['total_requests']}, ok={report['ok_requests']}, failed={report['failed_requests']}, error_rate_pct={report['error_rate_pct']}\n")
        f.write(f"rps={report['rps']}\n")
        f.write(f"latency_all_ms={report['latency_all_ms']}\n")
        for path, d in report["by_path"].items():
            f.write(f"  {path}: {d}\n")
    print(f"\n보고 저장: {report_path}")
    return report


if __name__ == "__main__":
    main()
