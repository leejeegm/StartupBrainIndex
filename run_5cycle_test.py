# -*- coding: utf-8 -*-
"""오류 테스트 5회 실행 스크립트. 서버 기동 후 실행."""
import urllib.request
import urllib.error
import ssl
import sys

BASE = "http://127.0.0.1:8001"
ROUTES = [
    ("GET", "/", "초기화면"),
    ("GET", "/login", "로그인"),
    ("GET", "/register", "회원가입"),
    ("GET", "/admin", "관리자"),
    ("GET", "/dashboard", "대시보드"),
    ("GET", "/static/mobile-common.css", "모바일공통CSS"),
]

def one_request(method, path):
    url = BASE + path
    req = urllib.request.Request(url, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10, context=ssl.create_default_context()) as r:
            return r.getcode(), None
    except urllib.error.HTTPError as e:
        return e.code, str(e)
    except Exception as e:
        return None, str(e)

def run_one_cycle(cycle):
    results = []
    for method, path, name in ROUTES:
        code, err = one_request(method, path)
        ok = code in (200, 302, 307) if code else False
        results.append((name, code, err, ok))
    return results

def main():
    print("=== 오류 테스트 5회 실행 (BASE=%s) ===\n" % BASE)
    all_ok = True
    for cycle in range(1, 6):
        print("--- 회차 %d ---" % cycle)
        row = run_one_cycle(cycle)
        for name, code, err, ok in row:
            status = "OK" if ok else "FAIL"
            if not ok:
                all_ok = False
            detail = "code=%s" % code if code else "error=%s" % (err or "?")
            print("  %s %s: %s" % (status, name, detail))
        print()
    print("=== 5회 완료. 전체 통과: %s ===" % ("예" if all_ok else "아니오"))
    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main())
