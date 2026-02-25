"""
공통 의존성: 세션 사용자, 관리자 여부, DB 오류 메시지, 데모 계정.
"""
from typing import Optional, Dict


USERS_DEMO = {"user@test.com": "pass1234", "admin@test.com": "admin"}


def get_current_user(request) -> Optional[Dict]:
    """세션에서 로그인 사용자 반환. 없으면 None."""
    return request.session.get("user")


def is_admin(user: Optional[Dict]) -> bool:
    return user and (user.get("email") or "").lower() == "admin@test.com"


def db_error_message(e: Exception) -> str:
    """DB 연결 오류 시 사용자 안내 문구."""
    s = str(e)
    msg = s.lower()
    if (
        "2003" in s or "10061" in msg or "winerror" in msg
        or "connect" in msg or "connection" in msg or "refused" in msg
        or "mysql" in msg or "operationalerror" in msg
        or "localhost" in msg or "찾을 수 없" in s or "cannot find" in msg or "could not connect" in msg
    ):
        return "데이터베이스에 연결할 수 없습니다. MySQL 서버가 실행 중인지, DB 호스트 설정(환경변수 DB_HOST)이 맞는지 확인해 주세요."
    return s[:200]
