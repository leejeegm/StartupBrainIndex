# -*- coding: utf-8 -*-
"""
DB 데모 데이터 저장·불러오기 테스트.
연결: localhost, DB leejee5, 사용자 leejee5, 비밀번호 sunkim5do#
테이블은 create_tables_mysql.sql 로 미리 생성되어 있어야 함.
"""
import sys
import os

# 프로젝트 루트를 path에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run():
    results = []
    def ok(name, msg=""):
        results.append(("OK", name, msg or "성공"))
    def fail(name, msg):
        results.append(("FAIL", name, str(msg)))

    # 1) DB 연결 및 테이블 존재 확인
    try:
        from db import get_conn, execute_all, DB_ENGINE
        with get_conn() as conn:
            if DB_ENGINE == "sqlite":
                tables = execute_all(conn, "SELECT name AS tbl FROM sqlite_master WHERE type='table'", ())
                table_names = [t.get("tbl") or t.get("name") for t in tables if t]
            else:
                tables = execute_all(conn, "SHOW TABLES", ())
                table_names = [list(t.values())[0] for t in tables] if tables else []
        need = ["users", "survey_saves", "chat_saves", "board", "eeg_saves", "indicator_formulas"]
        missing = [t for t in need if t not in table_names]
        if missing:
            fail("DB 테이블", "누락: " + ", ".join(missing) + ". create_tables_mysql.sql 실행 필요.")
        else:
            ok("DB 연결 및 테이블", "테이블 6개 확인")
    except Exception as e:
        fail("DB 연결", e)
        for r in results:
            print("[%s] %s: %s" % (r[0], r[1], r[2]))
        return 1

    # 2) 회원 데모 저장·불러오기
    try:
        from user_storage import register, get_user_by_email, verify_password
        demo_email = "demo_test@test.com"
        demo_pw = "demo1234"
        try:
            out = register(demo_email, demo_pw)
            ok("회원 가입(데모)", "id=%s" % out.get("id"))
        except ValueError as ve:
            if "이미 등록된" in str(ve):
                ok("회원 가입(데모)", "이미 존재하여 스킵")
            else:
                fail("회원 가입", ve)
        u = get_user_by_email(demo_email)
        if not u:
            fail("회원 조회", "가입 후 조회 없음")
        else:
            ok("회원 조회", u["email"])
        if not verify_password(demo_email, demo_pw):
            fail("비밀번호 확인", "불일치")
        else:
            ok("비밀번호 확인", "일치")
    except Exception as e:
        fail("회원 저장/불러오기", e)

    # 3) 설문 데모 저장·불러오기
    try:
        from survey_storage import save_survey, list_saved, get_saved
        demo_responses = {1: 3, 2: 4, 3: 5, 4: 3, 5: 4}
        required = [1, 2, 3, 4, 5]
        out = save_survey("demo_test@test.com", demo_responses, required, title="[데모테스트] 설문 저장")
        ok("설문 저장", "id=%s" % out.get("id"))
        lst = list_saved("demo_test@test.com")
        if not lst:
            fail("설문 목록", "0건")
        else:
            ok("설문 목록", "%s건" % len(lst))
        loaded = get_saved("demo_test@test.com", out["id"])
        if not loaded or loaded.get("responses") != demo_responses:
            fail("설문 불러오기", loaded)
        else:
            ok("설문 불러오기", "일치")
    except Exception as e:
        fail("설문 저장/불러오기", e)

    # 4) 대화 데모 저장·불러오기
    try:
        from chat_storage import save_chat, list_saved, get_saved
        msgs = [{"role": "user", "text": "테스트 메시지"}, {"role": "assistant", "text": "테스트 답변"}]
        out = save_chat("demo_test@test.com", msgs, summary_title="[데모] 대화 저장")
        ok("대화 저장", "id=%s" % out.get("id"))
        lst = list_saved("demo_test@test.com")
        if not lst:
            fail("대화 목록", "0건")
        else:
            ok("대화 목록", "%s건" % len(lst))
        loaded = get_saved("demo_test@test.com", out["id"])
        if not loaded or loaded.get("messages") != msgs:
            fail("대화 불러오기", "내용 불일치")
        else:
            ok("대화 불러오기", "일치")
    except Exception as e:
        fail("대화 저장/불러오기", e)

    # 5) 게시판 데모 저장·불러오기
    try:
        from board_storage import create_item, get_item, list_items
        out = create_item("board", "[데모] 게시판 제목", "데모 본문 내용")
        ok("게시판 등록", "id=%s" % out.get("id"))
        row = get_item(out["id"])
        if not row or row["title"] != "[데모] 게시판 제목":
            fail("게시판 조회", row)
        else:
            ok("게시판 조회", "일치")
        lst = list_items(type_filter="board")
        ok("게시판 목록", "%s건" % len(lst))
    except Exception as e:
        fail("게시판 저장/불러오기", e)

    # 6) 뇌파 데모 저장·불러오기
    try:
        from eeg_storage import save_eeg, list_saved, get_saved
        data = {"motivation": 70, "resilience": 60, "innovation": 80, "responsibility": 75}
        out = save_eeg("demo_test@test.com", data, title="[데모] 뇌파 저장")
        ok("뇌파 저장", "id=%s" % out.get("id"))
        lst = list_saved("demo_test@test.com")
        if not lst:
            fail("뇌파 목록", "0건")
        else:
            ok("뇌파 목록", "%s건" % len(lst))
        loaded = get_saved("demo_test@test.com", out["id"])
        if not loaded or loaded.get("data") != data:
            fail("뇌파 불러오기", "내용 불일치")
        else:
            ok("뇌파 불러오기", "일치")
    except Exception as e:
        fail("뇌파 저장/불러오기", e)

    # 결과 출력
    print("=== DB 데모 저장·불러오기 테스트 ===\n")
    for r in results:
        print("  [%s] %s: %s" % (r[0], r[1], r[2]))
    failed = [r for r in results if r[0] == "FAIL"]
    print("\n총 %s 항목, 실패 %s 건" % (len(results), len(failed)))
    return 1 if failed else 0

if __name__ == "__main__":
    sys.exit(run())
