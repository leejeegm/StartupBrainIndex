"""
진단 결과가 특정 점수 이하인 고객에게
박사님 블로그/유튜브 추천 + 1:1 상담 할인권 발송용 이메일 템플릿 생성.

- 기준: 통합지수_0_100 <= COUPON_EMAIL_THRESHOLD 이면 추천·할인권 메일 대상
- 추천: 낮은 역량 키워드로 지식 DB 검색 후 블로그/유튜브 중 랜덤 1건 (DB 없으면 채널/블로그 링크)
"""
import random
import uuid
from typing import List, Any, Optional, Dict
from dataclasses import dataclass

# 진단 점수 이하이면 할인권 이메일 발송 대상 (0~100)
COUPON_EMAIL_THRESHOLD = 55

BLOG_URL = "https://jangsanbrainlab.tistory.com/"
YOUTUBE_CHANNEL_URL = "https://www.youtube.com/@jangsanbrain"

# 역량 키워드(한글) → 검색용 키워드 리스트 (낮은 점수 역량별 추천 검색)
DOMAIN_SEARCH_KEYWORDS = {
    "창업공감": ["창업 동기부여", "공감", "자아성찰", "창업생태계"],
    "위기감수": ["위기극복", "회복탄력성", "스트레스", "재도전"],
    "두뇌활용": ["뇌 유연화", "창의성", "뇌교육", "혁신"],
    "주체적": ["주체적 협업", "사회적 책임", "창업의식"],
}


def _domain_to_key(영역명: str) -> Optional[str]:
    n = (영역명 or "").strip()
    if "창업공감" in n or "동기부여" in n:
        return "창업공감"
    if "위기감수" in n or "극복" in n:
        return "위기감수"
    if "두뇌활용" in n or "계발" in n:
        return "두뇌활용"
    if "주체적" in n or "창업의식" in n:
        return "주체적"
    return None


def get_low_score_domains(영역별_통합점수: List[Any], threshold: float = 45) -> List[str]:
    """점수가 threshold 미만인 역량의 concept 키 리스트 반환 (키워드 검색용)."""
    keys = []
    for d in 영역별_통합점수:
        score = getattr(d, "combined_score", None)
        if score is None:
            continue
        if score < threshold:
            key = _domain_to_key(getattr(d, "영역명", ""))
            if key and key not in keys:
                keys.append(key)
    return keys


def get_recommendations_for_low_score(
    영역별_통합점수: List[Any],
    통합지수_0_100: float,
    threshold: float = COUPON_EMAIL_THRESHOLD,
) -> Dict[str, Any]:
    """
    진단 점수 이하일 때 진단 결과에 맞는 블로그/유튜브 콘텐츠를 랜덤 추천.
    반환: {
      "대상": True/False,
      "추천_블로그": { "title", "url" } 또는 None,
      "추천_유튜브": { "title", "url" } 또는 None,
      "강조_역량": ["창업공감", ...],
    }
    """
    대상 = 통합지수_0_100 <= threshold
    추천_블로그 = None
    추천_유튜브 = None
    강조_역량 = []

    if not 대상:
        return {"대상": False, "추천_블로그": None, "추천_유튜브": None, "강조_역량": []}

    강조_역량 = get_low_score_domains(영역별_통합점수, threshold=45)
    keywords = []
    for k in 강조_역량:
        keywords.extend(DOMAIN_SEARCH_KEYWORDS.get(k, []))

    if not keywords:
        keywords = ["뇌교육", "창업", "동기부여", "위기극복"]

    try:
        from knowledge_db import search_for_report, count
        if count() > 0:
            result = search_for_report(keywords, limit_per_source=5)
            blog_list = result.get("blog") or []
            youtube_list = result.get("youtube") or []
            if blog_list or youtube_list:
                # 블로그/유튜브 중 각 0~1건 랜덤 선택 (한 쪽만 추천하거나 둘 다)
                if blog_list and (not youtube_list or random.random() > 0.5):
                    b = random.choice(blog_list)
                    추천_블로그 = {"title": (b.title or "블로그 글")[:80], "url": b.url or BLOG_URL}
                if youtube_list and (not blog_list or random.random() > 0.5):
                    y = random.choice(youtube_list)
                    추천_유튜브 = {"title": (y.title or "유튜브 영상")[:80], "url": y.url or YOUTUBE_CHANNEL_URL}
        if not 추천_블로그 and not 추천_유튜브:
            # DB 없거나 검색 무결과: 채널/블로그 링크로 기본 추천
            if random.random() > 0.5:
                추천_블로그 = {"title": "장산뇌혁신데이터랩 블로그", "url": BLOG_URL}
            else:
                추천_유튜브 = {"title": "장산뇌혁신데이터랩 유튜브 (@jangsanbrain)", "url": YOUTUBE_CHANNEL_URL}
    except Exception:
        추천_블로그 = {"title": "장산뇌혁신데이터랩 블로그", "url": BLOG_URL}
        추천_유튜브 = {"title": "장산뇌혁신데이터랩 유튜브 (@jangsanbrain)", "url": YOUTUBE_CHANNEL_URL}

    return {
        "대상": True,
        "추천_블로그": 추천_블로그,
        "추천_유튜브": 추천_유튜브,
        "강조_역량": 강조_역량,
    }


def generate_coupon_code(prefix: str = "SBI") -> str:
    """상담 할인권 코드 생성 (예: SBI-1A2B-3C4D)."""
    u = uuid.uuid4().hex[:8].upper()
    return f"{prefix}-{u[:4]}-{u[4:8]}"


def render_consultation_coupon_email(
    customer_name: str,
    통합지수_0_100: float,
    추천_블로그: Optional[Dict[str, str]] = None,
    추천_유튜브: Optional[Dict[str, str]] = None,
    coupon_code: Optional[str] = None,
    coupon_expiry_days: int = 30,
) -> str:
    """
    1:1 상담 할인권 발송용 HTML 이메일 본문 생성.
    customer_name: 수신자 이름 (또는 '고객' 등)
    """
    coupon_code = coupon_code or generate_coupon_code()
    score_text = f"{통합지수_0_100:.0f}점" if isinstance(통합지수_0_100, (int, float)) else str(통합지수_0_100)

    blog_block = ""
    if 추천_블로그:
        blog_block = f"""
        <tr><td style="padding:12px 0 8px 0; font-weight:bold; color:#1e3a8a;">추천 블로그</td></tr>
        <tr><td style="padding:4px 0 16px 0;">
          <a href="{추천_블로그.get('url', BLOG_URL)}" style="color:#2563eb; text-decoration:underline;">{추천_블로그.get('title', '장산뇌혁신데이터랩 블로그')}</a>
          <br><span style="color:#64748b; font-size:12px;">{BLOG_URL}</span>
        </td></tr>"""
    youtube_block = ""
    if 추천_유튜브:
        youtube_block = f"""
        <tr><td style="padding:12px 0 8px 0; font-weight:bold; color:#1e3a8a;">추천 영상 (유튜브)</td></tr>
        <tr><td style="padding:4px 0 16px 0;">
          <a href="{추천_유튜브.get('url', YOUTUBE_CHANNEL_URL)}" style="color:#2563eb; text-decoration:underline;">{추천_유튜브.get('title', '장산뇌혁신데이터랩 유튜브')}</a>
          <br><span style="color:#64748b; font-size:12px;">{YOUTUBE_CHANNEL_URL}</span>
        </td></tr>"""

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>SBI 진단 결과 및 1:1 상담 할인 안내</title>
</head>
<body style="margin:0; padding:0; font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif; background:#f1f5f9;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f1f5f9;">
    <tr>
      <td align="center" style="padding:24px 16px;">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:560px; background:#ffffff; border-radius:12px; box-shadow:0 4px 6px rgba(0,0,0,0.06);">
          <tr>
            <td style="padding:32px 28px;">
              <h1 style="margin:0 0 8px 0; font-size:20px; color:#0f172a;">SBI 창업가 뇌지수 진단 결과 안내</h1>
              <p style="margin:0; font-size:13px; color:#64748b;">뇌교육학 박사 이중환 · 장산뇌혁신데이터랩</p>
            </td>
          </tr>
          <tr>
            <td style="padding:0 28px 20px 28px;">
              <p style="margin:0; font-size:15px; color:#334155; line-height:1.6;">안녕하세요, <strong>{customer_name}</strong>님.</p>
              <p style="margin:14px 0 0 0; font-size:15px; color:#334155; line-height:1.6;">SBI(Startup Brain Index) 진단에 참여해 주셔서 감사합니다. 진단 결과를 바탕으로 도움이 될 만한 콘텐츠와 1:1 상담 할인 혜택을 안내드립니다.</p>
            </td>
          </tr>
          <tr>
            <td style="padding:0 28px 8px 28px;">
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f8fafc; border-radius:8px; border:1px solid #e2e8f0;">
                <tr><td style="padding:14px 16px; font-size:14px; color:#475569;">진단 통합 지수: <strong style="color:#1e40af;">{score_text}</strong> / 100</td></tr>
              </table>
            </td>
          </tr>
          <tr>
            <td style="padding:8px 28px 20px 28px;">
              <p style="margin:0; font-size:14px; font-weight:bold; color:#1e3a8a;">진단 결과에 맞춘 추천 콘텐츠</p>
              <p style="margin:6px 0 0 0; font-size:13px; color:#64748b;">아래 블로그 또는 유튜브 콘텐츠를 시청하시면, 진단에서 보강이 필요한 역량을 뇌교육·BOS 관점에서 다듬는 데 도움이 됩니다.</p>
            </td>
          </tr>
          <tr>
            <td style="padding:0 28px 24px 28px;">
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="border:1px solid #e2e8f0; border-radius:8px;">
                {blog_block}
                {youtube_block}
              </table>
            </td>
          </tr>
          <tr>
            <td style="padding:20px 28px 12px 28px; border-top:1px solid #e2e8f0;">
              <p style="margin:0; font-size:14px; font-weight:bold; color:#1e3a8a;">1:1 상담 할인권</p>
              <p style="margin:6px 0 12px 0; font-size:13px; color:#475569;">박사님과의 1:1 상담 시 아래 할인 코드를 사용하실 수 있습니다.</p>
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#eff6ff; border:1px dashed #3b82f6; border-radius:8px;">
                <tr>
                  <td style="padding:16px; text-align:center;">
                    <span style="font-size:18px; font-weight:bold; letter-spacing:2px; color:#1d4ed8;">{coupon_code}</span>
                  </td>
                </tr>
              </table>
              <p style="margin:10px 0 0 0; font-size:12px; color:#64748b;">* 유효기간: 발송일로부터 {coupon_expiry_days}일 이내 사용 가능 (상담 예약 시 안내에 따라 적용)</p>
            </td>
          </tr>
          <tr>
            <td style="padding:16px 28px 28px 28px; font-size:13px; color:#64748b; border-top:1px solid #e2e8f0;">
              <p style="margin:0;">· 블로그: <a href="{BLOG_URL}" style="color:#2563eb;">{BLOG_URL}</a></p>
              <p style="margin:6px 0 0 0;">· 유튜브: <a href="{YOUTUBE_CHANNEL_URL}" style="color:#2563eb;">{YOUTUBE_CHANNEL_URL}</a></p>
              <p style="margin:16px 0 0 0; font-size:12px;">본 메일은 SBI 진단 결과에 따른 자동 발송 메일입니다.</p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""
    return html


def build_coupon_email_for_result(
    customer_name: str,
    영역별_통합점수: List[Any],
    통합지수_0_100: float,
    coupon_code: Optional[str] = None,
) -> Dict[str, Any]:
    """
    진단 결과로 할인권 메일 대상 여부를 판단하고, 대상이면 HTML 본문과 추천 콘텐츠를 반환.
    반환: {
      "발송_대상": bool,
      "이메일_HTML": str 또는 None,
      "추천_블로그": {...} 또는 None,
      "추천_유튜브": {...} 또는 None,
      "할인코드": str,
    }
    """
    rec = get_recommendations_for_low_score(영역별_통합점수, 통합지수_0_100)
    코드 = coupon_code or generate_coupon_code()

    if not rec["대상"]:
        return {
            "발송_대상": False,
            "이메일_HTML": None,
            "추천_블로그": None,
            "추천_유튜브": None,
            "할인코드": 코드,
        }

    html = render_consultation_coupon_email(
        customer_name=customer_name,
        통합지수_0_100=통합지수_0_100,
        추천_블로그=rec.get("추천_블로그"),
        추천_유튜브=rec.get("추천_유튜브"),
        coupon_code=코드,
    )
    return {
        "발송_대상": True,
        "이메일_HTML": html,
        "추천_블로그": rec.get("추천_블로그"),
        "추천_유튜브": rec.get("추천_유튜브"),
        "할인코드": 코드,
    }
