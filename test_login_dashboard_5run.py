# -*- coding: utf-8 -*-
"""
로그인 및 대시보드 접근 5회 검증.
서버 실행 후: python test_login_dashboard_5run.py
"""
import urllib.request
import urllib.error
import json
import os
import sys
from http.cookiejar import CookieJar

BASE = os.environ.get("TEST_BASE", "http://127.0.0.1:8001")
# 데모 계정 (main.py USERS_DEMO)
USER_EMAIL = os.environ.get("TEST_USER", "user@test.com")
USER_PW = os.environ.get("TEST_PW", "pass1234")


def make_opener():
    cj = CookieJar()
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))


def login(opener):
    url = BASE + "/api/login"
    data = json.dumps({"email": USER_EMAIL, "password": USER_PW}).encode("utf-8")
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


def get_me(opener):
    url = BASE + "/api/me"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with opener.open(req, timeout=10) as r:
            return json.loads(r.read().decode("utf-8")), None
    except urllib.error.HTTPError as e:
        return None, "HTTP %s" % e.code
    except Exception as e:
        return None, str(e)


def get_dashboard_html(opener):
    url = BASE + "/dashboard"
    req = urllib.request.Request(url)
    try:
        with opener.open(req, timeout=10) as r:
            html = r.read().decode("utf-8", errors="replace")
            return html, None
    except urllib.error.HTTPError as e:
        return None, "HTTP %s" % e.code
    except Exception as e:
        return None, str(e)


def check_dashboard_script(html):
    """대시보드에 Step/버튼 동작에 필요한 코드가 포함되어 있는지 확인."""
    errors = []
    required = [
        ("showStep", "showStep 함수"),
        ("attachNavDelegation", "attachNavDelegation"),
        ("id=\"btn-save\"", "저장·불러오기 버튼"),
        ("id=\"btn-short-survey\"", "간편 설문 버튼"),
        ("id=\"btn-survey-load\"", "불러오기 버튼"),
        ("id=\"btn-retry-random\"", "다시하기 버튼"),
        ("data-step=\"1\"", "Step1 링크"),
        ("step-link", "step-link 클래스"),
    ]
    for token, name in required:
        if token not in html:
            errors.append("누락: %s" % name)
    return errors


def run_one_cycle(opener, cycle):
    ok_login, err_login = login(opener)
    if not ok_login:
        return False, "로그인 실패: %s" % (err_login or "알 수 없음")

    me, err_me = get_me(opener)
    if err_me:
        return False, "api/me 실패: %s" % err_me
    if not me or not me.get("email"):
        return False, "api/me 응답 이상"

    html, err_dash = get_dashboard_html(opener)
    if err_dash:
        return False, "대시보드 페이지 실패: %s" % err_dash
    if not html or "Startup Brain Index" not in html:
        return False, "대시보드 HTML 이상"

    script_errors = check_dashboard_script(html)
    if script_errors:
        return False, "스크립트 검증: " + "; ".join(script_errors[:3])

    return True, "OK (로그인·api/me·대시보드·스크립트 검증 통과)"


def main():
    print("=" * 60)
    print("로그인 및 대시보드 입력 테스트 5회")
    print("BASE=%s  USER=%s" % (BASE, USER_EMAIL))
    print("=" * 60)

    results = []
    for i in range(1, 6):
        opener = make_opener()
        ok, msg = run_one_cycle(opener, i)
        results.append((i, ok, msg))
        status = "통과" if ok else "실패"
        print("[%d/5] %s - %s" % (i, status, msg))
        if not ok:
            print("       (서버 실행 여부, 로그인 계정 확인)")

    print("=" * 60)
    passed = sum(1 for _, ok, _ in results if ok)
    print("결과: %d/5 회 통과" % passed)
    if passed < 5:
        print("실패한 항목:")
        for i, ok, msg in results:
            if not ok:
                print("  %d: %s" % (i, msg))
        sys.exit(1)
    print("모든 검증 통과.")
    sys.exit(0)


if __name__ == "__main__":
    main()
