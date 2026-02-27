"""
Step 1~3 통합 파이프라인: 설문 응답 -> 가상 뇌파 -> 통합 지수 -> DB 검색 -> PDF 생성.
실제 사용자 시나리오 한 번 실행 및 구간별 소요 시간·에러 반환.
"""
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field


@dataclass
class PipelineResult:
    success: bool
    error: Optional[str] = None
    pdf_path: Optional[str] = None
    timings_ms: Dict[str, float] = field(default_factory=dict)
    combined_result: Optional[Dict] = None
    report_dict: Optional[Dict] = None
    knowledge_blog: List[Dict] = field(default_factory=list)
    knowledge_youtube: List[Dict] = field(default_factory=list)


def run_full_pipeline(
    responses: Dict[int, int],
    customer_name: str = "고객",
    exclude_sequences: Optional[List[int]] = None,
    output_pdf_name: Optional[str] = None,
    ai_consultation_notes: Optional[List[str]] = None,
    user_profile: Optional[Dict[str, Any]] = None,
) -> PipelineResult:
    """
    설문 응답 -> 채점 -> 가상 뇌파 -> 통합 SBI -> 리포트 생성 -> DB 검색 -> PDF 생성.
    각 구간별 소요 시간(ms)과 에러를 기록해 반환.
    """
    out = PipelineResult(success=False, timings_ms={})
    t0 = time.perf_counter()

    try:
        from data_loader import SurveyDataLoader
        from scoring import ScoringEngine
        from eeg_provider import MockEEGProvider
        from analysis_engine import calculate_combined_sbi
        from report_generator import generate_report, report_to_dict, _domain_to_key, augment_report_with_knowledge
        from email_coupon import DOMAIN_SEARCH_KEYWORDS
        from knowledge_db import init_db, search_for_report, count
        from pdf_report import generate_sbi_pdf
    except ImportError as e:
        out.error = f"Import error: {e}"
        return out

    exclude_sequences = exclude_sequences or []

    # --- 1. 설문 채점 ---
    t1 = time.perf_counter()
    try:
        loader = SurveyDataLoader()
        scoring = ScoringEngine(loader)
        survey_result = scoring.calculate_score(responses, excluded_sequences=exclude_sequences)
    except Exception as e:
        out.error = f"Step 1 (설문 채점) 실패: {e}"
        out.timings_ms["1_survey_scoring"] = (time.perf_counter() - t1) * 1000
        return out
    out.timings_ms["1_survey_scoring"] = (time.perf_counter() - t1) * 1000

    # --- 2. 가상 뇌파 생성 ---
    t2 = time.perf_counter()
    try:
        eeg_metrics = MockEEGProvider().get_metrics()
    except Exception as e:
        out.error = f"Step 2 (가상 뇌파) 실패: {e}"
        out.timings_ms["2_mock_eeg"] = (time.perf_counter() - t2) * 1000
        return out
    out.timings_ms["2_mock_eeg"] = (time.perf_counter() - t2) * 1000

    # --- 3. 통합 SBI + 리포트 ---
    t3 = time.perf_counter()
    try:
        combined = calculate_combined_sbi(survey_result, eeg_metrics)
        report = generate_report(combined.영역별_통합점수, combined.inconsistency_flag, user_profile=user_profile)
        report_dict = report_to_dict(report)
    except Exception as e:
        out.error = f"Step 3 (통합 SBI/리포트) 실패: {e}"
        out.timings_ms["3_combined_sbi"] = (time.perf_counter() - t3) * 1000
        return out
    out.timings_ms["3_combined_sbi"] = (time.perf_counter() - t3) * 1000

    eeg_dict = {}
    try:
        eeg_dict = {
            "motivation": getattr(combined.eeg_영역별, "motivation", None),
            "resilience": getattr(combined.eeg_영역별, "resilience", None),
            "innovation": getattr(combined.eeg_영역별, "innovation", None),
            "responsibility": getattr(combined.eeg_영역별, "responsibility", None),
        }
    except Exception:
        pass
    combined_result = {
        "통합지수_0_100": combined.통합지수_0_100,
        "사용된_문항수": combined.사용된_문항수,
        "영역별_통합점수": [
            {
                "영역명": d.영역명,
                "combined_score": d.combined_score,
            }
            for d in combined.영역별_통합점수
        ],
        "eeg_영역별": eeg_dict,
    }
    out.combined_result = combined_result
    out.report_dict = report_dict

    # 설문 응답 목록 (순번, 문항 요약, 점수) — PDF 설문 응답 표 반영용
    survey_response_rows: List[tuple] = []
    try:
        for seq in sorted(responses.keys()):
            item = loader.get_item_by_sequence(seq)
            text = ""
            if item and getattr(item, "문항보정", None):
                raw = (item.문항보정 or "").strip().replace("\n", " ")
                text = (raw[:72] + "…") if len(raw) > 72 else raw
            if not text:
                text = "문항 " + str(seq)
            survey_response_rows.append((seq, text, responses.get(seq, 0)))
    except Exception:
        pass

    # --- 4. DB 검색 (리포트 키워드 / 낮은 역량 키워드) ---
    t4 = time.perf_counter()
    keywords = []
    for d in combined.영역별_통합점수:
        if getattr(d, "combined_score", 100) < 50:
            key = _domain_to_key(getattr(d, "영역명", ""))
            if key:
                keywords.extend(DOMAIN_SEARCH_KEYWORDS.get(key, ["뇌교육", "창업"]))
    if not keywords:
        keywords = ["뇌교육", "창업", "동기부여"]
    search_result_blog: List[Any] = []
    search_result_youtube: List[Any] = []
    try:
        init_db()
        if count() > 0:
            search_result = search_for_report(keywords, limit_per_source=3)
            search_result_blog = search_result.get("blog") or []
            search_result_youtube = search_result.get("youtube") or []
            out.knowledge_blog = [{"title": r.title, "url": r.url} for r in search_result_blog]
            out.knowledge_youtube = [{"title": r.title, "url": r.url} for r in search_result_youtube]
            # AI 검색 결과를 근거로 역량별 해석에 참고 문장 추가
            report_dict = augment_report_with_knowledge(
                report_dict, search_result_blog, search_result_youtube
            )
            out.report_dict = report_dict
    except Exception:
        # DB 검색 실패해도 PDF는 생성 (추천은 빈 목록 또는 기본 링크만)
        pass
    out.timings_ms["4_db_search"] = (time.perf_counter() - t4) * 1000

    # --- 5. PDF 생성 ---
    t5 = time.perf_counter()
    try:
        pdf_path = generate_sbi_pdf(
            combined_result=combined_result,
            report_dict=report_dict,
            knowledge_blog=out.knowledge_blog,
            knowledge_youtube=out.knowledge_youtube,
            output_filename=output_pdf_name,
            ai_consultation_notes=ai_consultation_notes,
            user_profile=user_profile,
            survey_response_rows=survey_response_rows,
        )
        out.pdf_path = pdf_path
    except Exception as e:
        out.error = f"Step 5 (PDF 생성) 실패: {e}"
        out.timings_ms["5_pdf_generate"] = (time.perf_counter() - t5) * 1000
        return out
    out.timings_ms["5_pdf_generate"] = (time.perf_counter() - t5) * 1000

    out.success = True
    out.timings_ms["total"] = (time.perf_counter() - t0) * 1000
    return out
