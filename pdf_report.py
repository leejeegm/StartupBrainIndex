"""
SBI 진단 결과 PDF 리포트 생성 (ReportLab).
통합 지수, 역량별 점수, AI 해석, 도표·그래프, 5페이지 이상 분량.
한글 출력을 위해 시스템/프로젝트 한글 폰트를 등록해 사용합니다.
"""
import os
from typing import Dict, List, Any, Optional

PDF_OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
os.makedirs(PDF_OUTPUT_DIR, exist_ok=True)

# 한글 폰트 등록 (맑은고딕 호환·통일). 한 번만 실행.
_KOREAN_FONT_NAME = None
_FONT_REGISTERED = False


def _get_font_name():
    """한글 호환 폰트(맑은고딕/나눔고딕) 통일. 없으면 fonts/에 자동 다운로드. 항상 한글 폰트명 반환."""
    global _KOREAN_FONT_NAME, _FONT_REGISTERED
    if _KOREAN_FONT_NAME is not None:
        return _KOREAN_FONT_NAME
    base = os.path.dirname(os.path.abspath(__file__))
    fonts_dir = os.path.join(base, "fonts")
    os.makedirs(fonts_dir, exist_ok=True)
    # 배포 환경(Linux): fonts/에 폰트 없으면 먼저 다운로드 시도
    _try_download_korean_font(fonts_dir)
    try:
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        candidates = [
            ("Korean", "C:/Windows/Fonts/malgun.ttf", None),
            ("Korean", os.path.join(fonts_dir, "malgun.ttf"), None),
            ("Korean", os.path.join(fonts_dir, "NanumGothic.ttf"), None),
            ("Korean", os.path.join(fonts_dir, "NanumGothic-Regular.ttf"), None),
            ("Korean", os.path.join(fonts_dir, "NotoSansKR-Regular.ttf"), None),
            ("Korean", "/usr/share/fonts/truetype/nanum/NanumGothic.ttf", None),
            ("Korean", "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc", 0),
        ]
        for name, path, subfont in candidates:
            if not os.path.isfile(path):
                continue
            try:
                if subfont is not None and path.lower().endswith(".ttc"):
                    pdfmetrics.registerFont(TTFont(name, path, subfontIndex=subfont))
                else:
                    pdfmetrics.registerFont(TTFont(name, path))
                _KOREAN_FONT_NAME = name
                _FONT_REGISTERED = True
                return name
            except Exception:
                continue
    except Exception:
        pass
    # 한글 미지원 Helvetica는 한글이 깨지므로, 재시도 없으면 예외로 알림
    import logging
    logging.getLogger(__name__).warning(
        "PDF 한글 폰트를 찾지 못했습니다. fonts/ 폴더에 NanumGothic-Regular.ttf 또는 NanumGothic.ttf를 넣어 주세요."
    )
    _KOREAN_FONT_NAME = "Helvetica"
    return "Helvetica"


def _try_download_korean_font(fonts_dir: str) -> None:
    """fonts/에 나눔고딕(맑은고딕 호환) 없으면 공개 URL에서 다운로드 (Linux/배포 환경용)."""
    if os.path.isfile(os.path.join(fonts_dir, "NanumGothic.ttf")) or os.path.isfile(os.path.join(fonts_dir, "NanumGothic-Regular.ttf")):
        return
    # (url, 저장 파일명)
    urls = [
        ("https://github.com/google/fonts/raw/refs/heads/main/ofl/nanumgothic/NanumGothic-Regular.ttf", "NanumGothic-Regular.ttf"),
        ("https://github.com/naver/nanumfont/raw/master/NanumGothic.ttf", "NanumGothic.ttf"),
        ("https://github.com/naver/nanumfont/raw/main/NanumGothic.ttf", "NanumGothic.ttf"),
    ]
    try:
        import urllib.request
        for url, filename in urls:
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; SBI-PDF/1.0)"})
                with urllib.request.urlopen(req, timeout=25) as r:
                    data = r.read()
                    if len(data) > 50000:
                        path = os.path.join(fonts_dir, filename)
                        with open(path, "wb") as f:
                            f.write(data)
                        return
            except Exception:
                continue
    except Exception:
        pass


# 보라색 기반 전문 보고서 컬러 (자신을 깨우는 시간)
_PURPLE_DARK = "#4C1D95"   # 진보라 (제목·헤더)
_PURPLE_MID = "#6d28d9"    # 메인
_PURPLE_ACCENT = "#7c3aed" # 강조·그래프
_PURPLE_LIGHT = "#a78bfa"  # 연보라
_PURPLE_BG = "#f5f3ff"     # 배경 톤

# 표 가독성: 셀 패딩(좌우상하), 헤더/본문 폰트 크기 — 맑은고딕 호환 가독
_TABLE_PADDING = 6
_TABLE_HEADER_FONTSIZE = 11
_TABLE_BODY_FONTSIZE = 10
_CHART_LABEL_FONTSIZE = 10


def generate_sbi_pdf(
    combined_result: Dict[str, Any],
    report_dict: Dict[str, Any],
    knowledge_blog: Optional[List[Dict]] = None,
    knowledge_youtube: Optional[List[Dict]] = None,
    output_filename: Optional[str] = None,
    ai_consultation_notes: Optional[List[str]] = None,
    user_profile: Optional[Dict[str, Any]] = None,
    survey_response_rows: Optional[List[tuple]] = None,
) -> str:
    """
    설문+뇌파 통합 결과, 리포트 해석, DB 검색 결과, AI 상담 요약을 담은 PDF 생성.
    user_profile 있으면 대상자 정보 섹션 추가. survey_response_rows 있으면 설문 응답 내역 표 추가.
    보라색 기반 전문 보고서 스타일. 반환: 생성된 PDF 파일 경로.
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib import colors
    from reportlab.graphics.shapes import Drawing
    from reportlab.graphics.charts.barcharts import VerticalBarChart
    try:
        from report_generator import BRAIN_STAGES, BOS_LAWS
    except Exception:
        BRAIN_STAGES = []
        BOS_LAWS = []

    knowledge_blog = knowledge_blog or []
    knowledge_youtube = knowledge_youtube or []

    font_name = _get_font_name()

    if not output_filename:
        import time
        output_filename = f"sbi_report_{int(time.time())}.pdf"
    path = os.path.join(PDF_OUTPUT_DIR, output_filename)

    doc = SimpleDocTemplate(path, pagesize=A4, rightMargin=20*mm, leftMargin=20*mm, topMargin=20*mm, bottomMargin=26*mm)
    story = []
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        name="Title", fontName=font_name, fontSize=20, spaceAfter=10,
        textColor=colors.HexColor(_PURPLE_DARK), alignment=1, spaceBefore=6
    )
    subtitle_style = ParagraphStyle(
        name="Subtitle", fontName=font_name, fontSize=13, spaceAfter=16,
        textColor=colors.HexColor(_PURPLE_MID), alignment=1
    )
    heading_style = ParagraphStyle(
        name="Heading", fontName=font_name, fontSize=12, spaceAfter=6, spaceBefore=4,
        textColor=colors.HexColor(_PURPLE_DARK)
    )
    body_style = ParagraphStyle(name="Body", fontName=font_name, fontSize=10, leading=17)

    DOMAIN_ORDER = [
        "창업공감 및 동기부여 역량",
        "창업위기감수 및 극복 역량",
        "창업두뇌활용 및 계발 역량",
        "주체적책임 및 창업의식 역량",
    ]

    def _norm(s: str) -> str:
        return " ".join((s or "").strip().split())

    def _score_from(d: Any) -> float:
        if not d or not isinstance(d, dict):
            return 0.0
        sc = d.get("combined_score")
        if sc is not None and isinstance(sc, (int, float)):
            return max(0.0, min(100.0, float(sc)))
        avg = d.get("평균점수")
        if avg is not None and isinstance(avg, (int, float)) and 1 <= avg <= 5:
            return round((float(avg) - 1) / 4.0 * 100.0, 1)
        return 0.0

    domains = combined_result.get("영역별_통합점수") or combined_result.get("영역별점수") or []
    domain_scores = []
    for name in DOMAIN_ORDER:
        d = next(
            (x for x in domains if x and (_norm(name) in _norm(x.get("영역명") or "") or _norm(x.get("영역명") or "") in _norm(name) or _norm(x.get("영역명") or "") == _norm(name))),
            None,
        )
        domain_scores.append((name, _score_from(d)))

    # ========== 1페이지: 표지 (보라색 전문 · 자신을 깨우는 시간) ==========
    story.append(Spacer(1, 18*mm))
    story.append(Paragraph("Startup Brain Index", title_style))
    story.append(Paragraph("SBI 창업가 뇌 지수 측정 리포트", subtitle_style))
    story.append(Paragraph("자신을 깨우는 시간의 보고서", ParagraphStyle(
        name="Tagline", fontName=font_name, fontSize=11, spaceAfter=16,
        textColor=colors.HexColor(_PURPLE_ACCENT), alignment=1
    )))
    story.append(Spacer(1, 6*mm))
    story.append(Paragraph("뇌교육학 박사 이중환 · 장산뇌혁신데이터랩", body_style))
    story.append(Spacer(1, 10*mm))

    # 대상자 정보 (회원 프로필 있을 때)
    if user_profile and isinstance(user_profile, dict):
        profile_rows = [["항목", "내용"]]
        if (user_profile.get("name") or "").strip():
            profile_rows.append(["이름", (user_profile.get("name") or "").strip()])
        if (user_profile.get("gender") or "").strip():
            profile_rows.append(["성별", (user_profile.get("gender") or "").strip()])
        if user_profile.get("age") is not None:
            profile_rows.append(["연령", str(user_profile["age"]) + "세"])
        if (user_profile.get("occupation") or "").strip():
            profile_rows.append(["직업", (user_profile.get("occupation") or "").strip()])
        if (user_profile.get("nationality") or "").strip():
            profile_rows.append(["국적", (user_profile.get("nationality") or "").strip()])
        if (user_profile.get("sleep_hours") or "").strip():
            profile_rows.append(["일 평균 수면시간", str(user_profile.get("sleep_hours", "")).strip()])
        if (user_profile.get("sleep_quality") or "").strip():
            profile_rows.append(["수면의 질", (user_profile.get("sleep_quality") or "").strip()])
        if (user_profile.get("meal_habit") or "").strip():
            profile_rows.append(["식사습관", (user_profile.get("meal_habit") or "").strip()])
        if (user_profile.get("bowel_habit") or "").strip():
            profile_rows.append(["배변습관", (user_profile.get("bowel_habit") or "").strip()])
        if (user_profile.get("exercise_habit") or "").strip():
            profile_rows.append(["운동습관", (user_profile.get("exercise_habit") or "").strip()])
        if len(profile_rows) > 1:
            pt = Table(profile_rows, colWidths=[40*mm, 115*mm])
            pt.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(_PURPLE_DARK)),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, -1), font_name),
                ("FONTSIZE", (0, 0), (-1, 0), _TABLE_HEADER_FONTSIZE),
                ("FONTSIZE", (0, 1), (-1, -1), _TABLE_BODY_FONTSIZE),
                ("LEFTPADDING", (0, 0), (-1, -1), _TABLE_PADDING),
                ("RIGHTPADDING", (0, 0), (-1, -1), _TABLE_PADDING),
                ("TOPPADDING", (0, 0), (-1, -1), _TABLE_PADDING),
                ("BOTTOMPADDING", (0, 0), (-1, -1), _TABLE_PADDING),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor(_PURPLE_LIGHT)),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (0, -1), "LEFT"),
                ("ALIGN", (1, 0), (1, -1), "LEFT"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor(_PURPLE_BG)]),
            ]))
            story.append(Paragraph("대상자 정보 (맞춤 해석 반영)", heading_style))
            story.append(Spacer(1, 3*mm))
            story.append(pt)
            story.append(Spacer(1, 8*mm))

    total = combined_result.get("통합지수_0_100")
    if total is not None:
        story.append(Paragraph(f"통합 지수: {total:.1f} / 100", heading_style))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(f"사용 문항 수: {combined_result.get('사용된_문항수', 96)}", body_style))
    story.append(Spacer(1, 14*mm))
    story.append(PageBreak())

    # ========== 설문 응답 내역 (체계적 반영) ==========
    survey_response_rows = survey_response_rows or []
    if survey_response_rows:
        story.append(Paragraph("설문 응답 내역 (전체 문항·점수)", heading_style))
        story.append(Spacer(1, 3*mm))
        # 표: 순번 | 문항(요약) | 점수 — 여러 페이지로 나누기 위해 청크 단위로
        chunk_size = 24
        for i in range(0, len(survey_response_rows), chunk_size):
            if i > 0:
                story.append(PageBreak())
                story.append(Paragraph("설문 응답 내역 (계속)", heading_style))
                story.append(Spacer(1, 3*mm))
            chunk = survey_response_rows[i:i + chunk_size]
            data = [["순번", "문항(요약)", "점수"]]
            for seq, text, score in chunk:
                data.append([str(seq), (text or "")[:60], str(score)])
            col_widths = [20*mm, 110*mm, 25*mm]
            t = Table(data, colWidths=col_widths)
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(_PURPLE_DARK)),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, -1), font_name),
                ("FONTSIZE", (0, 0), (-1, 0), _TABLE_HEADER_FONTSIZE),
                ("FONTSIZE", (0, 1), (-1, -1), _TABLE_BODY_FONTSIZE),
                ("LEFTPADDING", (0, 0), (-1, -1), _TABLE_PADDING),
                ("RIGHTPADDING", (0, 0), (-1, -1), _TABLE_PADDING),
                ("TOPPADDING", (0, 0), (-1, -1), _TABLE_PADDING),
                ("BOTTOMPADDING", (0, 0), (-1, -1), _TABLE_PADDING),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor(_PURPLE_LIGHT)),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (0, -1), "CENTER"),
                ("ALIGN", (2, 0), (2, -1), "CENTER"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor(_PURPLE_BG)]),
            ]))
            story.append(t)
            story.append(Spacer(1, 4*mm))
        story.append(PageBreak())

    # ========== 2페이지: 역량별 점수 테이블 + AI 연관 막대 그래프 ==========
    story.append(Paragraph("역량별 통합 점수 (4대 영역 정식 명칭)", heading_style))
    data = [["영역", "점수(0~100)"]]
    for name, score in domain_scores:
        data.append([name[:35], f"{score:.1f}"])
    if len(data) > 1:
        t = Table(data, colWidths=[105*mm, 40*mm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(_PURPLE_DARK)),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, -1), font_name),
            ("FONTSIZE", (0, 0), (-1, 0), _TABLE_HEADER_FONTSIZE),
            ("FONTSIZE", (0, 1), (-1, -1), _TABLE_BODY_FONTSIZE),
            ("LEFTPADDING", (0, 0), (-1, -1), _TABLE_PADDING),
            ("RIGHTPADDING", (0, 0), (-1, -1), _TABLE_PADDING),
            ("TOPPADDING", (0, 0), (-1, -1), _TABLE_PADDING),
            ("BOTTOMPADDING", (0, 0), (-1, -1), _TABLE_PADDING),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor(_PURPLE_LIGHT)),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (0, -1), "LEFT"),
            ("ALIGN", (1, 0), (1, -1), "CENTER"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor(_PURPLE_BG)]),
        ]))
        story.append(t)
    story.append(Spacer(1, 8*mm))
    story.append(Paragraph("【AI 기반 역량 점수 시각화】 역량별 점수 막대 그래프", heading_style))
    story.append(Spacer(1, 4*mm))
    try:
        if domain_scores and len(domain_scores) >= 1:
            # 그래프: 한글 폰트·막대 가시성(barWidth/barSpacing)·배치
            drawing = Drawing(170*mm, 75*mm)
            bc = VerticalBarChart()
            bc.x = 50
            bc.y = 20
            bc.height = 55*mm
            bc.width = 120*mm
            data_vals = [float(s) for _, s in domain_scores]
            bc.data = [data_vals]
            bc.barWidth = 18
            bc.barSpacing = 4
            bc.groupSpacing = 10
            bc.strokeColor = colors.HexColor(_PURPLE_ACCENT)
            bc.fillColor = colors.HexColor(_PURPLE_LIGHT)
            bc.categoryAxis.labels.boxAnchor = "ne"
            short_names = []
            for n, _ in domain_scores:
                if not n:
                    short_names.append("")
                elif "공감" in n or "동기" in n:
                    short_names.append("창업공감")
                elif "위기" in n or "극복" in n:
                    short_names.append("창업위기")
                elif "두뇌" in n or "계발" in n:
                    short_names.append("두뇌활용")
                elif "주체" in n or "의식" in n:
                    short_names.append("주체적")
                else:
                    short_names.append((n.strip()[:4]) if n else "")
            bc.categoryAxis.categoryNames = short_names
            bc.categoryAxis.labels.fontName = font_name
            bc.categoryAxis.labels.fontSize = _CHART_LABEL_FONTSIZE
            bc.valueAxis.valueMin = 0
            bc.valueAxis.valueMax = 100
            bc.valueAxis.valueStep = 20
            try:
                bc.valueAxis.labels.fontName = font_name
                bc.valueAxis.labels.fontSize = _CHART_LABEL_FONTSIZE
            except Exception:
                pass
            bc.bars[0].fillColor = colors.HexColor(_PURPLE_ACCENT)
            drawing.add(bc)
            story.append(drawing)
        else:
            story.append(Paragraph("(역량별 점수 데이터가 없습니다. 설문·뇌파 통합 결과를 먼저 생성해 주세요.)", body_style))
    except Exception:
        story.append(Paragraph("(그래프: 4대 영역 순서대로 창업공감·위기감수·두뇌활용·주체적 역량 점수 0~100)", body_style))
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph("※ 방사형 도표는 웹 대시보드 Step 2에서 확인할 수 있습니다.", body_style))
    story.append(PageBreak())

    # ========== 3페이지: AI 해석·시사점 (영역별 해석, 불일치, 시사점 분석) ==========
    story.append(Paragraph("AI 해석 및 시사점 분석", heading_style))
    if report_dict:
        요약 = report_dict.get("요약") or ""
        story.append(Paragraph(str(요약)[:2000], body_style))
        story.append(Spacer(1, 6*mm))
        story.append(Paragraph("【역량별 해석】", ParagraphStyle(name="SubHeading", fontName=font_name, fontSize=11, spaceAfter=4, textColor=colors.HexColor(_PURPLE_DARK))))
        역량별 = report_dict.get("역량별", [])
        for name in DOMAIN_ORDER:
            s = next((x for x in 역량별 if (x.get("영역명") or "") and (_norm(name) in _norm(x.get("영역명") or "") or _norm(x.get("영역명") or "") in _norm(name))), None)
            if s:
                해석텍스트 = (s.get("해석") or "").strip()
                if 해석텍스트:
                    story.append(Paragraph(f"[{name}] {해석텍스트[:800]}" + ("…" if len(해석텍스트) > 800 else ""), body_style))
                참고 = (s.get("참고_검색근거") or "").strip()
                if 참고:
                    story.append(Paragraph(f"※ 참고(검색 근거): {참고[:300]}", body_style))
                story.append(Spacer(1, 3*mm))
        if report_dict.get("불일치_해석"):
            story.append(Paragraph("【설문-뇌파 불일치 안내】 " + str(report_dict["불일치_해석"])[:600], body_style))
            story.append(Spacer(1, 4*mm))
        story.append(Paragraph("【시사점】 위 역량별 해석은 뇌교육 5단계와 BOS 5법칙에 따른 맞춤 안내입니다. 점수가 높은 역량은 강점 리더십으로, 낮은 역량은 뇌 유연화·정화·통합 단계와 BOS 실천으로 보강할 수 있으며, 설문(의식)과 뇌파(무의식) 차이가 있는 역량은 정보 정화·뇌 통합 관점의 훈련을 권장합니다.", body_style))
    else:
        story.append(Paragraph("4대 역량별 통합 지수를 뇌교육·BOS 관점에서 해석한 내용은 웹에서 확인할 수 있습니다.", body_style))
    story.append(Spacer(1, 8*mm))
    story.append(Paragraph("【역량별 개선 참고】 점수가 낮은 역량은 뇌교육 단계와 BOS 실천으로 보강할 수 있습니다.", body_style))
    story.append(PageBreak())

    # ========== 4페이지: 뇌파 시각화 요약 + 역량별 로드맵 + AI 상담 요약 ==========
    eeg_영역별 = combined_result.get("eeg_영역별") or {}
    if eeg_영역별 and isinstance(eeg_영역별, dict):
        story.append(Paragraph("뇌파 시각화 요약", heading_style))
        eeg_names = [
            ("motivation", "창업공감·동기부여(전두엽 비대칭)"),
            ("resilience", "창업위기감수·극복(알파파 회복)"),
            ("innovation", "창업두뇌·계발(SMR/Beta 코히어런스)"),
            ("responsibility", "주체적·창업의식(전전두엽 안정도)"),
        ]
        for key, label in eeg_names:
            v = eeg_영역별.get(key)
            if v is not None:
                story.append(Paragraph(f"· {label}: {float(v):.1f} (0~100)", body_style))
        story.append(Paragraph("본 수치는 설문 역량 지수와 결합해 통합 지수에 반영되었으며, 웹 대시보드 Step 2·3에서 방사형 도표 및 뇌파 그래프로 확인할 수 있습니다.", body_style))
        story.append(Spacer(1, 6*mm))
    story.append(Paragraph("역량별 개선 로드맵 (AI 추천)", heading_style))
    try:
        low_domains = [(n, s) for n, s in domain_scores if s < 55]
        if low_domains:
            roadmap_data = [["역량", "추천 뇌교육 단계", "BOS 강조"]]
            for name, score in low_domains[:4]:
                short = name.split()[0][:6] if name else ""
                roadmap_data.append([short, "뇌 유연화·정화 단계", "굿뉴스, 선택하면 이루어진다"])
            if len(roadmap_data) > 1:
                rt = Table(roadmap_data, colWidths=[48*mm, 52*mm, 55*mm])
                rt.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(_PURPLE_DARK)),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, -1), font_name),
                    ("FONTSIZE", (0, 0), (-1, 0), _TABLE_HEADER_FONTSIZE),
                    ("FONTSIZE", (0, 1), (-1, -1), _TABLE_BODY_FONTSIZE),
                    ("LEFTPADDING", (0, 0), (-1, -1), _TABLE_PADDING),
                    ("RIGHTPADDING", (0, 0), (-1, -1), _TABLE_PADDING),
                    ("TOPPADDING", (0, 0), (-1, -1), _TABLE_PADDING),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), _TABLE_PADDING),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor(_PURPLE_LIGHT)),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor(_PURPLE_BG)]),
                ]))
                story.append(rt)
        else:
            story.append(Paragraph("전 역량 균형이 양호합니다. 유지와 함께 뇌교육 5단계·BOS 실천을 꾸준히 하시면 좋습니다.", body_style))
    except Exception:
        story.append(Paragraph("역량별 개선은 뇌교육 5단계와 BOS 5법칙을 참고해 주세요.", body_style))
    story.append(Spacer(1, 8*mm))
    ai_consultation_notes = ai_consultation_notes or []
    if ai_consultation_notes:
        story.append(Paragraph("AI 상담 요약", heading_style))
        for note in ai_consultation_notes:
            if (note or "").strip():
                story.append(Paragraph((note or "").strip()[:500], body_style))
                story.append(Spacer(1, 2*mm))
    story.append(PageBreak())

    # ========== 5페이지: 뇌교육 5단계·BOS 참고 + 추천 콘텐츠 ==========
    story.append(Paragraph("뇌교육 5단계 참고", heading_style))
    try:
        for i, stage in enumerate((BRAIN_STAGES or [])[:5], 1):
            text = (stage if isinstance(stage, str) else str(stage))[:200]
            story.append(Paragraph(f"{i}. {text}", body_style))
            story.append(Spacer(1, 2*mm))
    except Exception:
        story.append(Paragraph("1~5단계: 뇌 감각 깨우기 → 유연화 → 정화 → 통합 → 주인되기", body_style))
    story.append(Spacer(1, 6*mm))
    story.append(Paragraph("BOS 5법칙 참고", heading_style))
    try:
        for i, law in enumerate((BOS_LAWS or [])[:5], 1):
            text = (law if isinstance(law, str) else str(law))[:80]
            story.append(Paragraph(f"{i}. {text}…", body_style))
            story.append(Spacer(1, 2*mm))
    except Exception:
        story.append(Paragraph("정신차려라, 굿뉴스, 선택하면 이루어진다, 시간과 공간의 주인, 모든 환경을 디자인하라", body_style))
    story.append(Spacer(1, 8*mm))
    story.append(Paragraph("추천 콘텐츠 (장산뇌혁신데이터랩)", heading_style))
    for b in knowledge_blog[:3]:
        title = (b.get("title") or b.get("제목", ""))[:60]
        url = b.get("url") or b.get("링크", "") or ""
        story.append(Paragraph(f"블로그: {title}", body_style))
        if url:
            story.append(Paragraph(f"  링크: {url}", body_style))
        story.append(Spacer(1, 2*mm))
    for y in knowledge_youtube[:3]:
        title = (y.get("title") or y.get("제목", ""))[:60]
        url = y.get("url") or y.get("링크", "") or ""
        story.append(Paragraph(f"유튜브: {title}", body_style))
        if url:
            story.append(Paragraph(f"  링크: {url}", body_style))
        story.append(Spacer(1, 2*mm))
    if not knowledge_blog and not knowledge_youtube:
        story.append(Paragraph("블로그: https://jangsanbrainlab.tistory.com/", body_style))
        story.append(Paragraph("유튜브: https://www.youtube.com/@jangsanbrain", body_style))
    story.append(Spacer(1, 6*mm))
    story.append(Paragraph("— 본 리포트는 「자신을 깨우는 시간의 보고서」 Startup Brain Index(SBI) 창업가 뇌 지수 측정 결과입니다. since 2024 장산뇌혁신데이터랩", body_style))

    def _draw_footer(canvas, doc):
        canvas.saveState()
        try:
            from reportlab.lib import colors
            canvas.setFont(font_name, 9)
            canvas.setFillColor(colors.HexColor(_PURPLE_MID))
            y = 14 * mm
            centre_x = doc.pagesize[0] / 2
            canvas.drawCentredString(centre_x, y, "↑ 위로가기")
        finally:
            canvas.restoreState()

    def _first_page(canvas, doc):
        try:
            canvas.bookmarkPage("pdf_top")
        except Exception:
            pass
        _draw_footer(canvas, doc)

    doc.build(story, onFirstPage=_first_page, onLaterPages=_draw_footer)
    return path
