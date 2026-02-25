# -*- coding: utf-8 -*-
"""
DB 저장·조회·수정 기능 테스트 (3회 실행).
- 회원 가입/조회, 설문 저장/목록/조회/수정, 대화 저장/목록/조회,
  게시판 등록/목록/조회/수정, 뇌파 저장/목록/조회
- 3회 반복 실행 후 실패 건 수정 및 보고
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run_one_cycle(cycle: int, results: list):
    def ok(name, msg=""):
        results.append(("OK", cycle, name, msg or "성공"))
    def fail(name, msg):
        results.append(("FAIL", cycle, name, str(msg)))

    # 1) DB 연결 및 테이블 확인
    try:
        from db import get_conn, execute_all, DB_ENGINE
        with get_conn() as conn:
            if DB_ENGINE == "sqlite":
                tables = execute_all(conn, "SELECT name AS tbl FROM sqlite_master WHERE type='table'", ())
                table_names = [t.get("tbl") or t.get("name") for t in tables if t]
            else:
                tables = execute_all(conn, "SHOW TABLES", ())
                table_names = [list(t.values())[0] for t in tables] if tables else []
        need = ["users", "survey_saves", "chat_saves", "board", "eeg_saves"]
        missing = [t for t in need if t not in table_names]
        if missing:
            fail("DB 테이블", "누락: " + ", ".join(missing))
            return
        ok("DB 연결", "테이블 확인")
    except Exception as e:
        fail("DB 연결", e)
        return

    email = f"test_cycle{cycle}@test.com"
    pw = "test1234"

    # 2) 회원 가입·조회
    try:
        from user_storage import register, get_user_by_email, verify_password
        try:
            register(email, pw)
        except ValueError as ve:
            if "이미 등록된" not in str(ve):
                fail("회원 가입", ve)
                return
        u = get_user_by_email(email)
        if not u:
            fail("회원 조회", "조회 없음")
            return
        if not verify_password(email, pw):
            fail("비밀번호 확인", "불일치")
            return
        ok("회원 가입·조회", email)
    except Exception as e:
        fail("회원", e)
        return

    # 3) 설문 저장·목록·조회·수정·재조회
    try:
        from survey_storage import save_survey, update_survey, list_saved, get_saved
        r1 = {1: 3, 2: 4, 3: 5}
        req = [1, 2, 3]
        out = save_survey(email, r1, req, title=f"[테스트{cycle}] 설문")
        sid = out["id"]
        lst = list_saved(email)
        if not lst or not any(x["id"] == sid for x in lst):
            fail("설문 목록", "저장 후 목록에 없음")
        else:
            ok("설문 저장·목록", f"id={sid}")
        loaded = get_saved(email, sid)
        if not loaded or loaded.get("responses") != r1:
            fail("설문 조회", "내용 불일치")
        else:
            ok("설문 조회", "일치")
        r2 = {1: 4, 2: 5, 3: 4}
        update_survey(sid, email, r2, req)
        loaded2 = get_saved(email, sid)
        if not loaded2 or loaded2.get("responses") != r2:
            fail("설문 수정·재조회", loaded2)
        else:
            ok("설문 수정·재조회", "일치")
    except Exception as e:
        fail("설문 저장/조회/수정", e)

    # 4) 대화 저장·목록·조회
    try:
        from chat_storage import save_chat, list_saved, get_saved
        msgs = [{"role": "user", "text": f"테스트{cycle}"}, {"role": "assistant", "text": "답변"}]
        out = save_chat(email, msgs, summary_title=f"[테스트{cycle}] 대화")
        cid = out["id"]
        lst = list_saved(email)
        if not lst or not any(x["id"] == cid for x in lst):
            fail("대화 목록", "저장 후 목록에 없음")
        loaded = get_saved(email, cid)
        if not loaded or loaded.get("messages") != msgs:
            fail("대화 조회", "내용 불일치")
        ok("대화 저장·목록·조회", f"id={cid}")
    except Exception as e:
        fail("대화 저장/조회", e)

    # 5) 게시판 등록·목록·조회·수정·재조회
    try:
        from board_storage import create_item, update_item, get_item, list_items
        out = create_item("board", f"[테스트{cycle}] 제목", f"본문{cycle}")
        bid = out["id"]
        row = get_item(bid)
        if not row or row["title"] != out["title"]:
            fail("게시판 조회", row)
        lst = list_items(type_filter="board")
        if not lst or not any(x["id"] == bid for x in lst):
            fail("게시판 목록", "등록 후 목록에 없음")
        update_item(bid, title=f"[테스트{cycle}] 수정제목", content=f"수정본문{cycle}")
        row2 = get_item(bid)
        if not row2 or row2["title"] != f"[테스트{cycle}] 수정제목" or row2["content"] != f"수정본문{cycle}":
            fail("게시판 수정·재조회", row2)
        ok("게시판 등록·목록·조회·수정", f"id={bid}")
    except Exception as e:
        fail("게시판 저장/조회/수정", e)

    # 6) 뇌파 저장·목록·조회
    try:
        from eeg_storage import save_eeg, list_saved, get_saved
        data = {"motivation": 70 + cycle, "resilience": 60}
        out = save_eeg(email, data, title=f"[테스트{cycle}] 뇌파")
        eid = out["id"]
        lst = list_saved(email)
        if not lst or not any(x["id"] == eid for x in lst):
            fail("뇌파 목록", "저장 후 목록에 없음")
        loaded = get_saved(email, eid)
        if not loaded or loaded.get("data") != data:
            fail("뇌파 조회", "내용 불일치")
        ok("뇌파 저장·목록·조회", f"id={eid}")
    except Exception as e:
        fail("뇌파 저장/조회", e)


def main():
    results = []
    for cycle in range(1, 4):
        run_one_cycle(cycle, results)

    print("=== DB 저장·조회·수정 테스트 (3회) ===\n")
    for r in results:
        status, cycle, name, msg = r
        print("  [%s] 회차%d %s: %s" % (status, cycle, name, msg))
    failed = [r for r in results if r[0] == "FAIL"]
    print("\n총 %s 항목, 실패 %s 건" % (len(results), len(failed)))
    if failed and all("DB 연결" in r[3] or "Can't connect" in r[3] or "2003" in r[3] for r in failed):
        print("\n[안내] MySQL이 실행 중이 아니어서 연결에 실패했습니다. DB 실행 후 재실행하면 저장·조회·수정이 검증됩니다.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
