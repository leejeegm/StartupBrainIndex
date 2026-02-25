# Step 3-1: 지식 DB 구축 및 스크래핑 엔진 — 검증 결과

## 구현 요약

1. **블로그 수집 (blog_scraper.py)**  
   - `requests` + `BeautifulSoup`으로 장산뇌혁신데이터랩 블로그(`https://jangsanbrainlab.tistory.com/`) 수집  
   - `get_latest_post_links(limit)`: 최신 포스트 URL 목록  
   - `get_post_content(post_url)`: 단일 포스트 제목·본문 텍스트 추출 (티스토리 본문 태그 다수 시도)  
   - `fetch_latest_posts(limit)`: 최신 N건 일괄 수집  

2. **유튜브 자막 (youtube_transcript.py)**  
   - `youtube-transcript-api` 사용  
   - `get_transcript(video_id)`: 영상 ID만 넣으면 자막 전체 텍스트 반환  
   - `get_transcript_with_timestamps(video_id)`: 시작 시간·길이 포함  

3. **로컬 지식 DB (knowledge_db.py)**  
   - `sbi_knowledge.db` (SQLite)  
   - 테이블: `id`(PK), `source_type`(블로그/유튜브), `title`, `content`, `url`, `created_at`  
   - `url` UNIQUE로 중복 저장 방지  
   - `insert(source_type, title, content, url)` → (row_id, inserted)  
   - 기존 `body`/`category` 스키마가 있으면 새 스키마로 마이그레이션  

4. **키워드 검색**  
   - `search_knowledge(keyword, top_k=3)`: TfidfVectorizer로 관련성 상위 3건  
   - 실패 시 단순 키워드 매칭으로 폴백  

5. **검증 테스트 (test_knowledge_step3.py)**  
   - 블로그 1건 수집 → DB 저장  
   - 유튜브 1건 자막 수집(자막 있는 video_id 사용 시) → DB 저장  
   - 키워드('뇌', '위기극복', '심리')로 상위 3건 검색 후 출력  

## 검증 실행 결과

- **블로그 1건**: 샘플 URL `https://jangsanbrainlab.tistory.com/196` 수집·저장 **성공**  
- **유튜브 1건**: 샘플 video_id에 자막이 없으면 스킵(실제 운영 시 `@jangsanbrain` 채널 영상 ID로 교체)  
- **키워드 검색**: DB에 1건 있을 때 키워드 `심리`로 **1건 검색** 정상 동작  

## 사용 방법

```bash
# 의존성
pip install -r requirements.txt

# DB 초기화
python -c "from knowledge_db import init_db; init_db()"

# 검증 테스트 (블로그 1건 + 유튜브 시도 + 검색)
python test_knowledge_step3.py
```

유튜브 자막 테스트를 하려면 `test_knowledge_step3.py` 안의 `SAMPLE_VIDEO_ID`를 자막이 있는 `@jangsanbrain` 영상 ID로 바꾸면 됩니다.
