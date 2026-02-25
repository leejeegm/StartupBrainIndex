"""
Step 3-1 검증 테스트: 블로그 1건 + 유튜브 1건 수집 → DB 저장 → 키워드 검색 결과 확인
"""
import sys

# @jangsanbrain 채널 영상 ID (자막 있는 영상으로 교체 가능)
SAMPLE_VIDEO_ID = "R2d0R6VQ0zU"  # 샘플; 실제 운영 시 @jangsanbrain 채널 영상 ID로 교체


def run():
    from blog_scraper import get_latest_post_links, get_post_content
    from youtube_transcript import get_transcript
    from knowledge_db import (
        init_db,
        insert,
        count,
        search_knowledge,
        SOURCE_BLOG,
        SOURCE_YOUTUBE,
    )

    print("=" * 60)
    print("Step 3-1: 지식 DB 구축 및 검색 검증")
    print("=" * 60)

    init_db()
    before_count = count()
    print(f"[1] DB 초기화 완료. 기존 행 수: {before_count}")

    # 블로그 1건 수집 (목록에서 링크 추출, 실패 시 샘플 URL로 1건 직접 요청)
    print("\n[2] 블로그 1건 수집 (jangsanbrainlab.tistory.com)")
    links = get_latest_post_links(limit=1)
    if not links:
        links = ["https://jangsanbrainlab.tistory.com/196"]
        print("    목록 조회 실패 → 샘플 URL 1건으로 시도")
    blog_saved = False
    if links:
        post = get_post_content(links[0])
        if post and (post.title or post.content):
            rid, ok = insert(SOURCE_BLOG, post.title, post.content, post.url)
            blog_saved = ok
            print(f"    URL: {post.url}")
            print(f"    제목: {post.title[:60]}..." if len(post.title) > 60 else f"    제목: {post.title}")
            print(f"    저장: {'성공' if ok else '중복으로 스킵'}")
        else:
            print("    본문 추출 실패 또는 빈 포스트")
    else:
        print("    수집할 URL 없음")

    # 유튜브 1건 자막 수집
    print("\n[3] 유튜브 자막 1건 수집 (video_id=%s)" % SAMPLE_VIDEO_ID)
    transcript = get_transcript(SAMPLE_VIDEO_ID)
    youtube_saved = False
    if transcript:
        title = "유튜브 자막 " + SAMPLE_VIDEO_ID
        url = "https://www.youtube.com/watch?v=" + SAMPLE_VIDEO_ID
        rid, ok = insert(SOURCE_YOUTUBE, title, transcript, url)
        youtube_saved = ok
        print(f"    자막 길이: {len(transcript)} 자")
        print(f"    저장: {'성공' if ok else '중복으로 스킵'}")
    else:
        print("    자막 없음 또는 API 오류 (video_id를 자막 있는 영상으로 바꿔보세요)")

    after_count = count()
    print(f"\n[4] DB 행 수: {before_count} -> {after_count} (추가: {after_count - before_count})")

    # 키워드 검색 (상위 3건)
    print("\n[5] 키워드 검색 (상위 3건)")
    for kw in ["뇌", "위기극복", "심리"]:
        rows = search_knowledge(kw, top_k=3)
        print(f"    키워드 '{kw}': {len(rows)}건")
        for i, r in enumerate(rows, 1):
            print(f"      {i}. [{r.source_type}] {r.title[:50]}... | {r.url[:50]}...")

    print("\n" + "=" * 60)
    print("검증 요약")
    print("=" * 60)
    print("  블로그 1건 수집 및 저장: %s" % ("OK" if blog_saved or (after_count > before_count and links) else "SKIP/FAIL"))
    print("  유튜브 1건 자막 및 저장: %s" % ("OK" if youtube_saved else "SKIP(자막 없거나 중복)"))
    print("  키워드 검색(상위 3건): 실행됨")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(run())
