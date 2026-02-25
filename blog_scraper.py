"""
Step 3-1: 장산뇌혁신데이터랩 블로그 수집 (requests + BeautifulSoup)
https://jangsanbrainlab.tistory.com/
"""
import re
import time
import requests
from bs4 import BeautifulSoup
from typing import List, Optional
from dataclasses import dataclass

BLOG_BASE = "https://jangsanbrainlab.tistory.com"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


@dataclass
class BlogPost:
    title: str
    content: str
    url: str


def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": USER_AGENT, "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8"})
    return s


def _get_html(url: str) -> Optional[str]:
    try:
        r = _session().get(url, timeout=15)
        r.raise_for_status()
        return r.text
    except Exception:
        return None


def _clean_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def get_latest_post_links(limit: int = 10) -> List[str]:
    """
    블로그 메인/목록에서 최신 포스트 URL 목록을 가져옵니다.
    """
    html = _get_html(BLOG_BASE)
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    links: List[str] = []
    seen = set()

    for a in soup.find_all("a", href=True):
        href = (a.get("href") or "").strip()
        if not href:
            continue
        if not href.startswith("http"):
            href = BLOG_BASE + ("/" + href.lstrip("/"))
        if "jangsanbrainlab.tistory.com" not in href:
            continue
        m = re.match(r"https?://jangsanbrainlab\.tistory\.com/(\d+)(?:\?.*)?$", href.split("#")[0])
        if m:
            canonical = m.group(0).split("?")[0]
            if canonical not in seen:
                seen.add(canonical)
                links.append(canonical)

    if not links:
        for s in re.finditer(r'href=["\']([^"\']*jangsanbrainlab\.tistory\.com/(\d+))["\']', html):
            url = s.group(1).split("?")[0].split("#")[0]
            if url not in seen:
                seen.add(url)
                links.append(url)

    return links[:limit]


def get_post_content(post_url: str) -> Optional[BlogPost]:
    """
    단일 포스트 URL에서 제목과 본문 텍스트를 추출합니다.
    티스토리 본문 태그: .article_view, #content, .post-view, .post_content, [class*='article'] 등 시도.
    """
    html = _get_html(post_url)
    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")

    # 제목: title 태그 또는 h1, .title 등
    title = ""
    t = soup.find("title")
    if t and t.get_text(strip=True):
        title = _clean_text(t.get_text())
    if not title:
        h1 = soup.find("h1") or soup.find("p", class_=re.compile("tit", re.I))
        if h1:
            title = _clean_text(h1.get_text())

    # 본문: 티스토리 본문 컨테이너 (순서대로 시도)
    content = ""
    for sel in [
        "div.article_view",
        "div.post-view",
        "div.post_content",
        "#content",
        "div.contents_style",
        "article .content",
        "div[class*='article']",
        "div[class*='post-view']",
    ]:
        el = soup.select_one(sel)
        if el:
            raw = el.get_text(separator=" ", strip=True)
            content = _clean_text(raw)
            if len(content) > 100:
                break
    if not content:
        div_content = soup.find("div", id="content")
        if div_content:
            content = _clean_text(div_content.get_text(separator=" ", strip=True))
    if not content:
        for div in soup.find_all("div", class_=True):
            c = " ".join(div.get("class", []))
            if "article" in c or "post" in c:
                content = _clean_text(div.get_text(separator=" ", strip=True))
                if len(content) > 100:
                    break
    if not content:
        content = _clean_text(soup.get_text(separator=" ", strip=True))
        if len(content) > 5000:
            content = content[:5000]

    if not title:
        title = post_url.split("/")[-1].split("?")[0] or "제목 없음"

    return BlogPost(title=title, content=content, url=post_url)


def fetch_latest_posts(limit: int = 5) -> List[BlogPost]:
    """
    최신 포스트 링크를 가져온 뒤 각 포스트 제목·본문을 수집합니다.
    """
    links = get_latest_post_links(limit=limit)
    results: List[BlogPost] = []
    for url in links:
        post = get_post_content(url)
        if post and post.content:
            results.append(post)
        time.sleep(0.5)
    return results
