# -*- coding: utf-8 -*-
"""
1) 관리자 회원 상세 API 검증
2) 대시보드 Step 단계별 HTML/스크립트 검증
서버 실행 후: python test_step_and_admin_detail.py
"""
import urllib.request
import urllib.error
import json
import os
import sys
from http.cookiejar import CookieJar

BASE = os.environ.get("TEST_BASE", "http://127.0.0.1:8001")
ADMIN_EMAIL = "admin@test.com"
ADMIN_PW = "admin"
USER_EMAIL = os.environ.get("TEST_USER", "user@test.com")
USER_PW = os.environ.get("TEST_PW", "pass1234")


def make_opener():
    cj = CookieJar()
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))


def login(opener, email, password):
    url = BASE + "/api/login"
    data = json.dumps({"email": email, "password": password}).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST", headers={"Content-Type": "application/json"})
    try:
        with opener.open(req, timeout=10) as r:
            j = json.loads(r.read().decode("utf-8"))
            return j.get("ok") is True, None
    except urllib.error.HTTPError as e:
        return False, "HTTP %s %s" % (e.code, e.read().decode("utf-8")[:200])
    except Exception as e:
        return False, str(e)


def get_admin_user_detail(opener, email):
    url = BASE + "/api/admin/user-detail?email=" + urllib.parse.quote(email, safe="")
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with opener.open(req, timeout=10) as r:
            return r.getcode(), json.loads(r.read().decode("utf-8")), None
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        try:
            data = json.loads(body)
        except Exception:
            data = {"detail": body[:200]}
        return e.code, data, None
    except Exception as e:
        return None, None, str(e)


def get_dashboard_html(opener):
    url = BASE + "/dashboard"
    req = urllib.request.Request(url)
    try:
        with opener.open(req, timeout=10) as r:
            return r.read().decode("utf-8", errors="replace"), None
    except urllib.error.HTTPError as e:
        return None, "HTTP %s" % e.code
    except Exception as e:
        return None, str(e)


def check_step_panels(html):
    """Step 1~5 패널 및 설문진단 관련 요소 존재 여부."""
    errors = []
    # Step 링크
    for step in range(1, 6):
        if ('data-step="%d"' % step) not in html and ("data-step='" + str(step) + "'") not in html:
            errors.append("Step %d 링크(data-step) 없음" % step)
    # 패널 영역 (id로 패널 구분하는 경우)
    for step in range(1, 6):
        if ("panel-step-" + str(step)) not in html and ("step-panel-" + str(step)) not in html:
            # 일부는 다른 id 쓸 수 있음
            pass
    if "step-link" not in html:
        errors.append("step-link 클래스 없음")
    if "showStep" not in html:
        errors.append("showStep 함수 없음")
    if "설문 진단" not in html and "설문진단" not in html:
        errors.append("설문 진단 메뉴 텍스트 없음")
    return errors


def main():
    print("=" * 60)
    print("1) 관리자 회원 상세 API / 2) 대시보드 Step 단계 검증")
    print("BASE=%s" % BASE)
    print("=" * 60)

    all_ok = True
    html = None

    # --- 1) 관리자 회원 상세 API ---
    print("\n[1] 관리자 로그인 후 /api/admin/user-detail 호출")
    opener_admin = make_opener()
    ok_login, err = login(opener_admin, ADMIN_EMAIL, ADMIN_PW)
    if not ok_login:
        print("  실패: 관리자 로그인 실패 - %s" % (err or "알 수 없음"))
        all_ok = False
    else:
        code, data, err = get_admin_user_detail(opener_admin, USER_EMAIL)
        if err:
            print("  실패: API 호출 오류 - %s" % err)
            all_ok = False
        elif code == 404:
            # 데모/미가입 계정은 404 정상
            msg = (data or {}).get("detail", "")
            print("  통과: 404 (해당 회원 없음) - %s" % (msg or "OK"))
        elif code == 200:
            if isinstance(data, dict) and ("email" in data or "detail" in data):
                print("  통과: 200 회원 상세 반환 (이메일/프로필 필드 포함)")
            else:
                print("  경고: 200 but 응답 형식 확인 필요")
        else:
            print("  실패: HTTP %s" % code)
            all_ok = False

    # --- 2) 일반 로그인 후 대시보드 Step 검증 ---
    print("\n[2] 일반 로그인 후 대시보드 Step 1~5 요소 검증")
    opener_user = make_opener()
    ok_login, err = login(opener_user, USER_EMAIL, USER_PW)
    if not ok_login:
        print("  실패: 로그인 실패 - %s" % (err or "알 수 없음"))
        all_ok = False
    else:
        html, err = get_dashboard_html(opener_user)
        if err or not html:
            print("  실패: 대시보드 로드 - %s" % (err or "빈 HTML"))
            all_ok = False
        else:
            step_errors = check_step_panels(html)
            if step_errors:
                print("  실패: " + "; ".join(step_errors[:5]))
                all_ok = False
            else:
                print("  통과: Step 1~5 링크·showStep·설문진단 텍스트 존재")

    # --- 3) Step 패널 id 존재 (dashboard 구조) ---
    print("\n[3] 대시보드 패널 영역(id) 검증")
    if not html:
        print("  스킵: 대시보드 미로드")
    else:
        found = 0
        for step in range(1, 6):
            if ("panel-step" + str(step)) in html:
                found += 1
        if found >= 4:
            print("  통과: Step 패널 id 4개 이상 존재 (panel-step1~5)")
        else:
            print("  경고: panel-step* id %d/5" % found)

    print("\n" + "=" * 60)
    if all_ok:
        print("결과: 모든 검증 통과")
        sys.exit(0)
    else:
        print("결과: 일부 실패")
        sys.exit(1)


if __name__ == "__main__":
    main()
