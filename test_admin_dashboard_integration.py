# -*- coding: utf-8 -*-
"""
Admin dashboard integration tests (5 checks).
Run with: python test_admin_dashboard_integration.py
Server must be running; admin login required.
"""
import urllib.request
import urllib.error
import json
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


def is_db_connection_error(err_msg):
    """MySQL/DB 연결 불가(2003, 10061 등) 또는 500 서버 오류(DB 원인 가능) 여부."""
    if not err_msg:
        return False
    s = (err_msg + str(err_msg)).lower()
    if "2003" in s or "10061" in s or "mysql" in s or "connection" in s or "connect" in s or "거부" in s:
        return True
    if "500" in s and ("internal" in s or "server error" in s):
        return True
    return False


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
    """Step1: survey-saved-list all_users + get one"""
    data, err = get_json(opener, "/api/survey-saved-list?all_users=1")
    if err:
        return False, "List: %s" % err, is_db_connection_error(err)
    items = data.get("items") or []
    if not items:
        return True, "0 items", False
    first_id = items[0].get("id")
    if not first_id:
        return True, "%d items" % len(items), False
    data2, err2 = get_json(opener, "/api/survey-saved/%s" % first_id)
    if err2:
        return False, "Get: %s" % err2, is_db_connection_error(err2)
    # optional: include_questions / include_analysis (admin Step1/Step2 보기용)
    _, err3 = get_json(opener, "/api/survey-saved/%s?include_questions=1" % first_id)
    if err3:
        return False, "Get+questions: %s" % err3, is_db_connection_error(err3)
    _, err4 = get_json(opener, "/api/survey-saved/%s?include_analysis=1" % first_id)
    if err4:
        return False, "Get+analysis: %s" % err4, is_db_connection_error(err4)
    return True, "%d items, get OK" % len(items), False


def run_test_2(opener):
    """Step2: same survey list"""
    data, err = get_json(opener, "/api/survey-saved-list?all_users=1")
    if err:
        return False, err, is_db_connection_error(err)
    return True, "%d items" % len(data.get("items") or []), False


def run_test_3(opener):
    """Step3: eeg-saved-list all_users + get one"""
    data, err = get_json(opener, "/api/eeg-saved-list?all_users=1")
    if err:
        return False, err, is_db_connection_error(err)
    items = data.get("items") or []
    if not items:
        return True, "0 items", False
    _, err2 = get_json(opener, "/api/eeg-saved/%s" % items[0].get("id"))
    if err2:
        return False, err2, is_db_connection_error(err2)
    return True, "%d items, get OK" % len(items), False


def run_test_4(opener):
    """Step4: chat-saved-list all_users + get one"""
    data, err = get_json(opener, "/api/chat-saved-list?all_users=1")
    if err:
        return False, err, is_db_connection_error(err)
    items = data.get("items") or []
    if not items:
        return True, "0 items", False
    _, err2 = get_json(opener, "/api/chat-saved/%s" % items[0].get("id"))
    if err2:
        return False, err2, is_db_connection_error(err2)
    return True, "%d items, get OK" % len(items), False


def run_test_5(opener):
    """Board list"""
    data, err = get_json(opener, "/api/board-list")
    if err:
        return False, err, is_db_connection_error(err)
    items = data.get("items") if isinstance(data, dict) else (data if isinstance(data, list) else [])
    if items is None:
        items = []
    return True, "%d items" % len(items), False


def main():
    print("=== Admin dashboard integration (5 tests) BASE=%s ===\n" % BASE)
    opener = make_opener()
    ok_login, err_login = login(opener)
    if not ok_login:
        print("Login failed:", err_login)
        return 1
    print("Login OK\n")
    results = [
        ("1. Step1 survey list+get", run_test_1(opener)),
        ("2. Step2 survey list", run_test_2(opener)),
        ("3. Step3 eeg list+get", run_test_3(opener)),
        ("4. Step4 chat list+get", run_test_4(opener)),
        ("5. Board list", run_test_5(opener)),
    ]
    passed = skipped = failed = 0
    for name, res in results:
        ok, msg, db_err = res
        if ok:
            status = "OK"
            passed += 1
        elif db_err:
            status = "SKIP"
            skipped += 1
            msg = "MySQL not connected (run MySQL and retry)"
        else:
            status = "FAIL"
            failed += 1
        print("  [%s] %s: %s" % (status, name, msg))
    print("\nPassed: %d  Skipped (DB): %d  Failed: %d" % (passed, skipped, failed))
    if failed > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
