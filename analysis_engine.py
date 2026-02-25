"""
Step 2: 뇌파 데이터 결합 분석 엔진
설문(SBI) 점수와 뇌파(EEG) 지표를 결합하여 통합 지수를 산출합니다.
박사 논문 수식: 영역별 (S*ws + E*we), 불일치 20% 이상 시 리포트 플래그.
"""
from typing import Optional, Dict, Any, List
from models import (
    SurveyResult, BrainWaveMetrics, CombinedAnalysisResult, DomainScore,
    EEGDomainMetrics, DomainCombinedScore, CombinedSBIResult, Domain,
)


# 영역별 뇌파 지표 매핑 및 가중치 (박사 논문 수식)
DOMAIN_EEG_WEIGHTS = {
    Domain.창업공감_및_동기부여:     ("motivation",    0.7, 0.3),  # S*0.7 + E*0.3
    Domain.창업위기감수_및_극복:     ("resilience",    0.5, 0.5),  # S*0.5 + E*0.5
    Domain.창업두뇌활용_및_계발:     ("innovation",    0.6, 0.4),  # S*0.6 + E*0.4
    Domain.주체적책임_및_창업의식:   ("responsibility", 0.8, 0.2), # S*0.8 + E*0.2
}

INCONSISTENCY_THRESHOLD = 20.0  # 0~100 스케일에서 20% 차이 이상 시 불일치


def _normalize_domain_name(name: str) -> str:
    """영역명 비교용 정규화 (공백·줄바꿈 통일)"""
    if not name:
        return ""
    return " ".join(str(name).strip().replace("\n", " ").replace("\r", " ").split())


def _normalize_1_5_to_100(score_1_to_5: float) -> float:
    """설문 1~5점을 0~100 스케일로 변환 (통합 지수 수식용)"""
    if score_1_to_5 is None or score_1_to_5 < 1 or score_1_to_5 > 5:
        return 0.0
    return round((score_1_to_5 - 1) / 4.0 * 100.0, 2)


# 설문 점수 1~5를 0~100으로 정규화
def _normalize_sbi(score_1_to_5: float) -> float:
    """1~5점 리커트를 0~100 스케일로 변환"""
    if score_1_to_5 is None or score_1_to_5 < 1 or score_1_to_5 > 5:
        return 0.0
    return round((score_1_to_5 - 1) / 4.0 * 100.0, 2)


def run_combined_analysis(
    survey_result: SurveyResult,
    brainwave: Optional[BrainWaveMetrics] = None,
    survey_weight: float = 0.6,
    eeg_weight: float = 0.4,
) -> CombinedAnalysisResult:
    """
    설문 결과와 뇌파 데이터를 결합하여 통합 분석 결과를 반환합니다.

    Args:
        survey_result: Step 1에서 산출한 설문(SBI) 결과
        brainwave: 뇌파 요약 지표 (None이면 설문만 사용)
        survey_weight: 결합 시 설문 가중치 (0~1)
        eeg_weight: 결합 시 뇌파 가중치 (0~1, survey_weight + eeg_weight = 1 권장)

    Returns:
        CombinedAnalysisResult: 결합 지수 및 상세 점수
    """
    sbi_normalized = _normalize_sbi(survey_result.전체평균)

    if brainwave is None:
        combined_index = sbi_normalized
        eeg_eng = None
        eeg_foc = None
        message = "설문(SBI) 점수만 반영된 종합 지수입니다. 뇌파 데이터를 추가하면 결합 지수가 산출됩니다."
    else:
        # 뇌파 지표: engagement 또는 focus 우선, 없으면 alpha/beta 기반 추정
        eeg_eng = getattr(brainwave, "engagement", None)
        eeg_foc = getattr(brainwave, "focus", None)

        if eeg_eng is not None and 0 <= eeg_eng <= 100:
            eeg_score = eeg_eng
        elif eeg_foc is not None and 0 <= eeg_foc <= 100:
            eeg_score = eeg_foc
        else:
            # alpha, beta 비율로 간이 참여도 추정 (0~100 가정)
            a = getattr(brainwave, "alpha", None) or 0
            b = getattr(brainwave, "beta", None) or 0
            if a + b > 0:
                eeg_score = min(100.0, max(0.0, (a + b) * 10))  # 휴리스틱 스케일
            else:
                eeg_score = 50.0  # 미제공 시 중간값
            eeg_eng = eeg_eng if eeg_eng is not None else eeg_score
            eeg_foc = eeg_foc if eeg_foc is not None else eeg_score

        total_w = survey_weight + eeg_weight
        if total_w <= 0:
            total_w = 1.0
        combined_index = round(
            (survey_weight * sbi_normalized + eeg_weight * eeg_score) / total_w, 2
        )
        combined_index = min(100.0, max(0.0, combined_index))
        message = "설문(SBI)과 뇌파(EEG) 데이터가 결합된 종합 지수입니다."

    return CombinedAnalysisResult(
        survey_sbi_score=survey_result.전체평균,
        survey_sbi_normalized=sbi_normalized,
        eeg_engagement=eeg_eng,
        eeg_focus=eeg_foc,
        combined_index=combined_index,
        domain_scores=survey_result.영역별점수,
        message=message,
    )


def calculate_combined_sbi(
    survey_result: SurveyResult,
    eeg_metrics: EEGDomainMetrics,
) -> CombinedSBIResult:
    """
    설문 점수(S)와 뇌파 데이터(E)를 박사 논문 수식에 따라 영역별 가중 결합 후 통합 지수 산출.
    - 창업공감 및 동기부여:   (S*0.7) + (E*0.3)
    - 창업위기감수 및 극복:   (S*0.5) + (E*0.5)
    - 창업두뇌활용 및 계발:   (S*0.6) + (E*0.4)
    - 주체적책임 및 창업의식: (S*0.8) + (E*0.2)
    S, E는 모두 0~100 스케일로 정규화 후 적용.
    특정 역량에서 설문-뇌파 차이가 20% 이상이면 inconsistency_flag=True.
    """
    domain_combined: List[DomainCombinedScore] = []
    inconsistency_flag = False

    # 정규화된 영역명 -> (eeg_key, w_s, w_e) 매핑
    weights_by_normalized = {
        _normalize_domain_name(dname): (eeg_key, w_s, w_e)
        for dname, (eeg_key, w_s, w_e) in DOMAIN_EEG_WEIGHTS.items()
    }

    # CSV 영역명 변형 대비 키워드 폴백 (창업공감, 창업위기, 창업두뇌, 주체적/창업의식)
    keyword_to_weights = [
        ("창업공감", ("motivation", 0.7, 0.3)),
        ("위기감수", ("resilience", 0.5, 0.5)),
        ("두뇌활용", ("innovation", 0.6, 0.4)),
        ("주체적", ("responsibility", 0.8, 0.2)),
    ]

    def get_weights(norm_name: str):
        w = weights_by_normalized.get(norm_name)
        if w is not None:
            return w
        for keyword, w in keyword_to_weights:
            if keyword in norm_name:
                return w
        return None

    for domain_score in survey_result.영역별점수:
        norm_name = _normalize_domain_name(domain_score.영역명)
        weight_tuple = get_weights(norm_name)
        if weight_tuple is None:
            continue
        eeg_key, w_s, w_e = weight_tuple

        S = domain_score.평균점수  # 1~5
        S_norm = _normalize_1_5_to_100(S)
        E = getattr(eeg_metrics, eeg_key)  # 0~100
        E = max(0.0, min(100.0, float(E)))

        combined = round((S_norm * w_s) + (E * w_e), 2)
        combined = max(0.0, min(100.0, combined))

        diff = abs(S_norm - E)
        inconsistency = diff >= INCONSISTENCY_THRESHOLD
        if inconsistency:
            inconsistency_flag = True

        domain_combined.append(
            DomainCombinedScore(
                영역명=domain_score.영역명,
                survey_score=S,
                survey_normalized=S_norm,
                eeg_score=E,
                combined_score=combined,
                weight_survey=w_s,
                weight_eeg=w_e,
                inconsistency=inconsistency,
            )
        )

    survey_norm = _normalize_1_5_to_100(survey_result.전체평균)
    통합지수 = (
        round(sum(d.combined_score for d in domain_combined) / len(domain_combined), 2)
        if domain_combined
        else survey_norm
    )
    통합지수 = max(0.0, min(100.0, 통합지수))

    return CombinedSBIResult(
        survey_전체평균=survey_result.전체평균,
        survey_정규화_0_100=survey_norm,
        eeg_영역별=eeg_metrics,
        영역별_통합점수=domain_combined,
        통합지수_0_100=통합지수,
        inconsistency_flag=inconsistency_flag,
        사용된_문항수=survey_result.사용된_문항수,
        제외된_순번=survey_result.제외된_순번,
        message="설문(S)과 뇌파(E)를 영역별 가중치로 결합한 SBI 통합 지수입니다."
        + (" 설문-뇌파 불일치 역량이 있어 리포트 생성을 권장합니다." if inconsistency_flag else ""),
    )
