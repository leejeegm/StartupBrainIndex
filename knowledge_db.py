"""
Step 3-1: 로컬 지식 DB (SQLite) — 블로그/유튜브 수집 데이터 저장 및 키워드·TF-IDF 검색
테이블: id(PK), source_type(블로그/유튜브), title, content, url, created_at
중복: url 기준으로 중복 저장 방지.
"""
import os
import sqlite3
from typing import List, Tuple, Optional
from dataclasses import dataclass

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sbi_knowledge.db")
SOURCE_BLOG = "블로그"
SOURCE_YOUTUBE = "유튜브"
# 하위 호환용
DEFAULT_CATEGORY_BLOG = SOURCE_BLOG
DEFAULT_CATEGORY_YOUTUBE = SOURCE_YOUTUBE


@dataclass
class KnowledgeRow:
    source_type: str
    title: str
    content: str
    url: str
    row_id: Optional[int] = None
    created_at: Optional[str] = None

    @property
    def category(self) -> str:
        return self.source_type


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    """sbi_knowledge.db 및 테이블 생성. url 유니크로 중복 저장 방지."""
    conn = get_connection()
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='knowledge'")
    if cur.fetchone():
        cur = conn.execute("PRAGMA table_info(knowledge)")
        cols = [c[1] for c in cur.fetchall()]
        if "body" in cols and "content" not in cols:
            conn.execute("""
                CREATE TABLE knowledge_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT,
                    url TEXT NOT NULL UNIQUE,
                    created_at TEXT DEFAULT (datetime('now','localtime'))
                )
            """)
            conn.execute("""
                INSERT OR IGNORE INTO knowledge_new (id, source_type, title, content, url, created_at)
                SELECT id, COALESCE(category,'블로그'), title, body, url, created_at FROM knowledge
            """)
            conn.execute("DROP TABLE knowledge")
            conn.execute("ALTER TABLE knowledge_new RENAME TO knowledge")
    else:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS knowledge (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_type TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT,
                url TEXT NOT NULL UNIQUE,
                created_at TEXT DEFAULT (datetime('now','localtime'))
            )
        """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_source_type ON knowledge(source_type)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_url ON knowledge(url)")
    conn.commit()
    conn.close()


def insert(source_type: str, title: str, content: str, url: str) -> Tuple[int, bool]:
    """
    한 건 삽입. url이 이미 있으면 중복 저장하지 않음.
    반환: (last_row_id, inserted여부). 중복 시 (0, False).
    """
    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO knowledge (source_type, title, content, url) VALUES (?, ?, ?, ?)",
            (source_type, title, (content or "")[:500000], url),
        )
        conn.commit()
        rid = cur.lastrowid or 0
        return (rid, True)
    except sqlite3.IntegrityError:
        conn.rollback()
        return (0, False)
    finally:
        conn.close()


def insert_many(rows: List[Tuple[str, str, str, str]]) -> int:
    """(source_type, title, content, url) 리스트 일괄 삽입. 중복 url은 건너뜀. 반환: 삽입된 행 수."""
    conn = get_connection()
    inserted = 0
    for r in rows:
        try:
            conn.execute(
                "INSERT INTO knowledge (source_type, title, content, url) VALUES (?, ?, ?, ?)",
                (r[0], r[1], (r[2] or "")[:500000], r[3]),
            )
            inserted += 1
        except sqlite3.IntegrityError:
            pass
    conn.commit()
    conn.close()
    return inserted


def count() -> int:
    """전체 행 수"""
    conn = get_connection()
    n = conn.execute("SELECT COUNT(*) FROM knowledge").fetchone()[0]
    conn.close()
    return n


def search_keyword(keyword: str, limit: int = 10) -> List[KnowledgeRow]:
    """단순 키워드 매칭: 제목/본문에 keyword 포함된 행 반환"""
    conn = get_connection()
    q = "%" + keyword.replace("%", "%%") + "%"
    cur = conn.execute(
        "SELECT id, source_type, title, content, url, created_at FROM knowledge WHERE title LIKE ? OR content LIKE ? ORDER BY id DESC LIMIT ?",
        (q, q, limit),
    )
    rows = [_row_from_tuple(r) for r in cur.fetchall()]
    conn.close()
    return rows


def _row_from_tuple(r: tuple) -> KnowledgeRow:
    return KnowledgeRow(
        source_type=r[1],
        title=r[2],
        content=r[3] or "",
        url=r[4],
        row_id=r[0],
        created_at=r[5] if len(r) > 5 else None,
    )


def search_tfidf(query: str, limit: int = 10) -> List[KnowledgeRow]:
    """TfidfVectorizer로 유사 문서 검색. DB가 비어있으면 빈 리스트."""
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
    except ImportError:
        return search_keyword(query, limit=limit)

    conn = get_connection()
    cur = conn.execute("SELECT id, source_type, title, content, url, created_at FROM knowledge")
    all_rows = cur.fetchall()
    conn.close()

    if not all_rows:
        return []

    documents = [(r[2] or "") + " " + (r[3] or "") for r in all_rows]
    vectorizer = TfidfVectorizer(max_features=5000, token_pattern=r"(?u)\b\w+\b")
    try:
        X = vectorizer.fit_transform(documents)
    except Exception:
        return search_keyword(query, limit=limit)

    q_vec = vectorizer.transform([query])
    sims = cosine_similarity(q_vec, X).flatten()
    top_indices = sims.argsort()[::-1][:limit]

    return [
        _row_from_tuple(all_rows[i])
        for i in top_indices
        if sims[i] > 0
    ]


def search_knowledge(keyword: str, top_k: int = 3) -> List[KnowledgeRow]:
    """
    역량 키워드(예: '뇌 유연화', '위기극복')로 DB 검색해 관련성 높은 상위 top_k개 반환.
    TfidfVectorizer 사용, 실패 시 단순 키워드 매칭.
    """
    return search_tfidf(keyword, limit=top_k)


def search_for_report(keywords: List[str], limit_per_source: int = 3) -> dict:
    """
    리포트용: 키워드 리스트로 검색해 블로그/유튜브 구분해 반환.
    반환: { "blog": [KnowledgeRow,...], "youtube": [KnowledgeRow,...] }
    """
    blog, youtube = [], []
    for kw in keywords:
        for row in search_tfidf(kw, limit=limit_per_source * 2):
            if row.source_type == SOURCE_YOUTUBE and len(youtube) < limit_per_source:
                if not any(r.url == row.url for r in youtube):
                    youtube.append(row)
            elif row.source_type == SOURCE_BLOG and len(blog) < limit_per_source:
                if not any(r.url == row.url for r in blog):
                    blog.append(row)
        if len(blog) >= limit_per_source and len(youtube) >= limit_per_source:
            break
    return {"blog": blog[:limit_per_source], "youtube": youtube[:limit_per_source]}


if __name__ == "__main__":
    init_db()
    print("DB initialized at", DB_PATH)
    print("Count:", count())
