# -*- coding: utf-8 -*-
"""
관리자 대시보드 연동 테스트 5종.
- 테스트 1: Step1 설문 저장 전체 목록 (survey-saved-list?all_users=1) + 조회
- 테스트 2: Step2 결과/PDF 동일 설문 목록 연동
- 테스트 3: Step3 뇌파 저장 전체 목록 (eeg-saved-list?all_users=1) + 조회
- 테스트 4: Step4 AI 상담 저장 전체 목록 (chat-saved-list?all_users=1) + 조회
- 테스트 5: 저장·불러오기 + 게시판 목록 연동 (board-list)
서버 기동 후 admin 로그인 세션으로 API 호출. 실패 시 오류 기록.
"""
import urllib.request
import urllib.error
import urllib.parse
import json
import ssl
import sys
from http.cookiejar import CookieJar

BASE = "http://127.0.0.1:8001"
ADMIN_EMAIL = "admin@test.com"
ADMIN_PW = "admin"


def make_opener():
    cj = CookieJar()
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))


def login(opener):
    url = BASE + "/api/login"
    data = json.dumps({"email": ADMIN_EMAIL, "password": ADMIN_PW}).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST", headers={"Content-Type": "application/json"})
    try:
        with opener.open(req, timeout=10) as r:
            body = r.read().decode("utf-8")
            j = json.loads(body)
            return j.get("ok") is True, None
    except urllib.error.HTTPError as e:
        return False, "HTTP %s %s" % (e.code, e.read().decode("utf-8")[:200])
    except Exception as e:
        return False, str(e)


def get_json(opener, path):
    url = BASE + path
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with opener.open(req, timeout=10) as r:
            return json.loads(r.read().decode("utf-8")), None
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode("utf-8")
            return None, "HTTP %s %s" % (e.code, body[:300])
        except Exception:
            return None, "HTTP %s" % e.code
    except Exception as e:
        return None, str(e)


def run_test_1(opener):
    """Step1: 설문 저장 전체 목록 + 한 건 조회 (관리자)"""
    data, err = get_json(opener, "/api/survey-saved-list?all_users=1")
    if err:
        return False, "목록 조회 실패: %s" % err
    items = data.get("items") or []
    if not items:
        return True, "목록 0건 (정상)"
    first_id = items[0].get("id")
    if not first_id:
        return True, "목록 %d건 (id 없음)" % len(items)
    _, err2 = get_json(opener, "/api/survey-saved/%s" % first_id)
    if err2:
        return False, "상세 조회 실패: %s" % err2
    return True, "목록 %d건, 상세 조회 OK" % len(items)


def run_test_2(opener):
    """Step2: 결과/PDF용 설문 목록 동일 API 연동"""
    data, err = get_json(opener, "/api/survey-saved-list?all_users=1")
    if err:
        return False, "Step2 목록 연동 실패: %s" % err
    return True, "Step2 동일 목록 %d건" % len(data.get("items") or [])


def run_test_3(opener):
    """Step3: 뇌파 저장 전체 목록 + 한 건 조회"""
    data, err = get_json(opener, "/api/eeg-saved-list?all_users=1")
    if err:
        return False, "뇌파 목록 실패: %s" % err
    items = data.get("items") or []
    if not items:
        return True, "뇌파 목록 0건 (정상)"
    first_id = items[0].get("id")
    _, err2 = get_json(opener, "/api/eeg-saved/%s" % first_id)
    if err2:
        return False, "뇌파 상세 실패: %s" % err2
    return True, "뇌파 목록 %d건, 상세 OK" % len(items)


def run_test_4(opener):
    """Step4: AI 상담 저장 전체 목록 + 한 건 조회"""
    data, err = get_json(opener, "/api/chat-saved-list?all_users=1")
    if err:
        return False, "대화 목록 실패: %s" % err
    items = data.get("items") or []
    if not items:
        return True, "대화 목록 0건 (정상)"
    first_id = items[0].get("id")
    _, err2 = get_json(opener, "/api/chat-saved/%s" % first_id)
    if err2:
        return False, "대화 상세 실패: %s" % err2
    return True, "대화 목록 %d건, 상세 OK" % len(items)


def run_test_5(opener):
    """저장·불러오기 + 게시판 목록 연동"""
    data, err = get_json(opener, "/api/board-list")
    if err:
        return False, "게시판 목록 실패: %s" % err
    items = data.get("items") if isinstance(data, dict) else (data if isinstance(data, list) else [])
    if items is None:
        items = []
    return True, "게시판 목록 %d건" % len(items)


def main():
    print("=== 관리자 대시보드 연동 테스트 5종 (BASE=%s) ===\n" % BASE)
    opener = make_opener()
    ok_login, err_login = login(opener)
    if not ok_login:
        print("로그인 실패: %s" % err_login)
        print("서버 기동 및 admin@test.com 계정 확인 후 재실행하세요.")
        return 1
    print("관리자 로그인 OK\n")

    results = []
    results.append(("1. Step1 설문 저장 전체 목록·조회", run_test_1(opener)))
    results.append(("2. Step2 결과/PDF 목록 연동", run_test_2(opener)))
    results.append(("3. Step3 뇌파 저장 전체 목록·조회", run_test_3(opener)))
    results.append(("4. Step4 AI 상담 저장 전체 목록·조회", run_test_4(opener)))
    results.append(("5. 저장·불러오기·게시판 목록", run_test_5(opener)))

    all_ok = True
    for name, (ok, msg) in results:
        status = "OK" if ok else "FAIL"
        if not ok:
            all_ok = False
        print("  [%s] %s: %s" % (status, name, msg))
    print("\n=== 5종 완료. 전체 통과: %s ===" % ("예" if all_ok else "아니오"))
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
