"""
concept.md에 정의된 용어와 로직을 반영한 SBI 리포트 생성.
- 지수 높음: 해당 역량 기반 강점·리더십 유형 정의
- 지수 낮음: 관련 뇌교육 단계(1~5) 처방 + BOS 5법칙 실천 과제
- 불일치 시: 설문(의식)·뇌파(무의식) 격차를 '정보 정화' 또는 '뇌 통합' 관점으로 해석
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

# concept.md: 뇌운영시스템(BOS) 5법칙
BOS_LAWS = [
    "정신차려라(깨어있어라): 현재의 상태를 자각하고 주체적으로 의식을 조절함.",
    "굿뉴스가 굿브레인을 만든다: 긍정적인 정보 선택을 통해 뇌의 환경을 최적화함.",
    "선택하면 이루어진다: 목표를 명확히 정하고 실행할 때 뇌의 잠재력이 발현됨.",
    "시간과 공간의 주인이 되라: 물리적 환경과 시간을 주도적으로 통제함.",
    "모든 환경을 디자인하라: 자신을 둘러싼 모든 조건을 창조적으로 재구성함.",
]

# concept.md: 뇌교육 5단계
BRAIN_STAGES = [
    "1단계 뇌 감각 깨우기(Brain Sensitizing): 뇌와 몸의 연결 회복, 뇌의 가치 자각.",
    "2단계 뇌 유연화하기(Brain Versatilizing): 고정관념 타파, 새로운 자극 수용.",
    "3단계 뇌 정화하기(Brain Refreshing): 부정적 정보 및 감정 정화, 본래 자아 회복.",
    "4단계 뇌 통합하기(Brain Integrating): 뇌의 각 영역(좌우뇌 등)을 조화롭게 연결 및 활성화.",
    "5단계 뇌 주인되기(Brain Mastering): 뇌를 완벽하게 운영하여 삶의 가치를 실현.",
]

# concept.md: 4대 역량 정의 및 하위요소 (키워드로 매칭)
DOMAIN_CONCEPT = {
    "창업공감": {
        "영역명": "창업공감 및 동기부여 역량",
        "정의": "창업생태계와 구성원에 대한 이해를 바탕으로 긍정적 동기와 공감능력을 향상하는 역량.",
        "하위요소": [
            "창업생태계이해: 창업의 의미 이해, 자아성찰, 사회적 유대관계 도모. (지표: 창업정보, 사회적유대)",
            "창업구성원공감: 구성원 정서 알아차림, 상호 신뢰와 인정. (지표: 알아차림, 인정)",
            "창업동기부여: 비전 공유, 책임감 기반의 동기 유발. (지표: 정보공유, 책임감)",
        ],
        "강점_리더십": "공감·동기부여형 리더십: 생태계 이해와 구성원 공감을 바탕으로 비전을 공유하고 팀 동기를 이끄는 유형.",
        "저점_추천_단계": [1, 2],  # 뇌 감각 깨우기, 뇌 유연화
        "저점_BOS_강조": [0, 1],   # 정신차려라, 굿뉴스
    },
    "위기감수": {
        "영역명": "창업위기감수 및 극복 역량",
        "정의": "불확실성 속에서 기회를 포착하고, 리스크를 감수하며 스트레스를 극복하는 역량.",
        "하위요소": [
            "창업기회도전: 신지식 탐색, 진취적인 계획과 행동. (지표: 탐험심, 시도성)",
            "실패위험감수: 시련을 수용하는 용기, 위기 돌파 능력. (지표: 위험감수, 위기극복)",
            "창업실패극복: 부정적 감정 관리, 회복탄력성 기반의 재기 의지. (지표: 긍정성, 재도전의지)",
        ],
        "강점_리더십": "위기돌파·회복탄력형 리더십: 불확실성을 기회로 전환하고, 실패 후 재기하는 회복력을 바탕으로 팀을 이끄는 유형.",
        "저점_추천_단계": [2, 3],  # 뇌 유연화, 뇌 정화
        "저점_BOS_강조": [1, 2],   # 굿뉴스, 선택하면 이루어진다
    },
    "두뇌활용": {
        "영역명": "창업두뇌활용 및 계발 역량",
        "정의": "신경가소성을 활성화하여 새로운 학습과 경험을 축적하고 혁신적 사업 모델을 창조하는 역량.",
        "하위요소": [
            "긍정두뇌활용: 긍정적 사고 기반의 기술 습득 및 학습. (지표: 긍정성, 습관화)",
            "창의두뇌계발: 확산적 사고, 몰입을 통한 문제 해결. (지표: 창의성, 몰입성)",
            "창업두뇌혁신: 이종 분야 융합, 개방적 자세로 아이디어 도출. (지표: 개방성, 융합성)",
        ],
        "강점_리더십": "혁신·학습형 리더십: 뇌의 유연성과 창의성을 활용해 새 학습과 혁신 모델을 주도하는 유형.",
        "저점_추천_단계": [1, 2, 4],  # 뇌 유연화, 뇌 정화, 뇌 통합
        "저점_BOS_강조": [2, 4],     # 선택하면 이루어진다, 모든 환경을 디자인하라
    },
    "주체적": {
        "영역명": "주체적책임 및 창업의식 역량",
        "정의": "지역사회 및 글로벌 공동체를 위한 사회적 협업과 공생적 책무성을 실현하는 역량.",
        "하위요소": [
            "주체적협업: 공동체 가치 인식, 지역사회 발전을 위한 주인의식. (지표: 관계성, 유대감)",
            "사회적책임: 기업의 공생적 책무(CSR/ESG) 이행과 윤리 경영. (지표: 책임성, 참여성)",
            "지구적창업의식: 글로벌 난제 해결 기여, 공생공존의 창업 철학. (지표: 자각성, 공동체의식)",
        ],
        "강점_리더십": "공생·책임형 리더십: 지역·글로벌 공동체에 대한 주인의식과 CSR/ESG를 실천하는 유형.",
        "저점_추천_단계": [4, 5],  # 뇌 통합, 뇌 주인되기
        "저점_BOS_강조": [0, 3, 4],  # 정신차려라, 시간과 공간의 주인, 모든 환경을 디자인하라
    },
}

# 결과/PDF 제시 순서: 파일의 영역 순 (고정)
DOMAIN_ORDER = [
    "창업공감 및 동기부여 역량",
    "창업위기감수 및 극복 역량",
    "창업두뇌활용 및 계발 역량",
    "주체적책임 및 창업의식 역량",
]
DOMAIN_KEY_ORDER = ["창업공감", "위기감수", "두뇌활용", "주체적"]


def _domain_order_index(영역명: str) -> int:
    """영역명에 해당하는 DOMAIN_ORDER 인덱스 반환 (정렬용)."""
    key = _domain_to_key(영역명)
    if key is None:
        return 999
    try:
        return DOMAIN_KEY_ORDER.index(key)
    except ValueError:
        return 999


# 영역명 → concept 키 매핑 (키워드)
def _domain_to_key(영역명: str) -> Optional[str]:
    if not 영역명:
        return None
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


# 점수 구간: 0~100 기준
THRESHOLD_HIGH = 65   # 이상이면 강점 해석
THRESHOLD_LOW = 45    # 미만이면 저점 처방


@dataclass
class DomainReportSection:
    """역량별 리포트 한 섹션 (영역 순·하위요소 키워드 정의 포함)"""
    영역명: str
    통합점수: float
    해석: str           # 하위요소 키워드 정의 + 강점/저점 해석
    추천_뇌교육단계: List[str] = field(default_factory=list)
    추천_BOS_실천: List[str] = field(default_factory=list)
    불일치: bool = False
    하위요소_정의: List[str] = field(default_factory=list)


@dataclass
class SBIReport:
    """전체 SBI 해석 리포트"""
    요약: str
    역량별: List[DomainReportSection]
    불일치_해석: Optional[str] = None
    뇌교육_5단계_참고: List[str] = field(default_factory=lambda: BRAIN_STAGES)
    BOS_5법칙_참고: List[str] = field(default_factory=lambda: BOS_LAWS)


def _profile_context_line(profile: Optional[Dict[str, Any]]) -> str:
    """사용자 프로필(연령·직업·습관)을 반영한 한 줄 문맥. 없으면 빈 문자열."""
    if not profile:
        return ""
    parts = []
    if profile.get("age") is not None:
        parts.append(f"연령 {profile['age']}세")
    if (profile.get("occupation") or "").strip():
        parts.append(f"직업 {str(profile['occupation']).strip()}")
    if (profile.get("sleep_hours") or "").strip():
        sh = str(profile.get("sleep_hours", "")).strip()
        parts.append("수면 " + (sh + "시간" if sh.replace(".", "").isdigit() else sh))
    for k, label in [("meal_habit", "식사"), ("bowel_habit", "배변"), ("exercise_habit", "운동")]:
        if (profile.get(k) or "").strip():
            parts.append(f"{label} {profile[k]}")
    if not parts:
        return ""
    return " (" + ", ".join(parts) + "를 고려한 맞춤 해석을 반영했습니다.)"


def generate_report(영역별_통합점수: List[Any], inconsistency_flag: bool, user_profile: Optional[Dict[str, Any]] = None) -> SBIReport:
    """
    concept.md 로직에 따라 역량별 해석과 불일치 해석을 생성합니다.
    영역별_통합점수: DomainCombinedScore 리스트(영역명, combined_score, inconsistency 등)
    user_profile: 이름·성별·연령·직업·수면·식사·배변·운동 등 개인 맞춤 반영용.
    """
    역량별: List[DomainReportSection] = []
    for d in 영역별_통합점수:
        영역명 = getattr(d, "영역명", "") or ""
        점수 = getattr(d, "combined_score", 0) or 0
        불일치 = getattr(d, "inconsistency", False)

        key = _domain_to_key(영역명)
        concept = DOMAIN_CONCEPT.get(key, {}) if key else {}
        하위요소 = concept.get("하위요소", [])

        if 점수 >= THRESHOLD_HIGH:
            해석_본문 = concept.get("강점_리더십", "해당 역량을 바탕으로 한 강점이 있습니다. 리더십으로 발휘할 수 있습니다.")
            추천_단계 = []
            추천_BOS = []
        elif 점수 < THRESHOLD_LOW:
            해석_본문 = f"해당 역량({concept.get('영역명', 영역명)}) 강화를 위해 뇌교육 단계와 BOS 법칙을 활용한 실천을 권장합니다."
            단계_인덱스 = concept.get("저점_추천_단계", [1, 2])
            추천_단계 = [BRAIN_STAGES[i] for i in 단계_인덱스 if 0 <= i < len(BRAIN_STAGES)]
            BOS_인덱스 = concept.get("저점_BOS_강조", [0, 1])
            추천_BOS = [BOS_LAWS[i] for i in BOS_인덱스 if 0 <= i < len(BOS_LAWS)]
        else:
            해석_본문 = "해당 역량이 중간 수준입니다. 강점으로 더 발휘하거나, 뇌교육·BOS 실천으로 보강할 수 있습니다."
            추천_단계 = []
            추천_BOS = []

        # 하위요소를 키워드로 정의한 문단 + 추가 설명(해석 본문)
        키워드_문단 = ""
        if 하위요소:
            키워드_문단 = "【하위요소 키워드】 본 역량은 다음 하위요소로 구성됩니다. " + ". ".join(하위요소) + ". "
        해석 = (키워드_문단 + "【해석】 " + 해석_본문).strip()

        역량별.append(
            DomainReportSection(
                영역명=영역명,
                통합점수=점수,
                해석=해석,
                추천_뇌교육단계=추천_단계,
                추천_BOS_실천=추천_BOS,
                불일치=불일치,
                하위요소_정의=하위요소,
            )
        )

    # 파일의 영역 순으로 정렬 (창업공감 → 위기감수 → 두뇌활용 → 주체적)
    역량별.sort(key=lambda s: _domain_order_index(s.영역명))

    # 불일치 해석: concept.md "설문(의식)과 뇌파(무의식)의 격차를 '정보 정화' 또는 '뇌 통합' 관점에서 해석"
    불일치_해석 = None
    if inconsistency_flag:
        불일치_해석 = (
            "설문(의식적 자기평가)과 뇌파(무의식적 상태) 간 차이가 20% 이상인 역량이 있습니다. "
            "이는 '정보 정화(뇌 정화하기)' 관점에서 부정적 자기관념을 정리하거나, "
            "'뇌 통합하기' 관점에서 의식·무의식을 조화롭게 연결하는 훈련을 권장합니다. "
            "뇌교육 3단계(뇌 정화하기), 4단계(뇌 통합하기)와 BOS 법칙을 함께 적용하면 도움이 됩니다."
        )

    호칭 = (user_profile or {}).get("name") or ""
    if not (호칭 or "").strip():
        호칭 = "고객"
    else:
        호칭 = (호칭 or "").strip() + "님"
    요약 = f"{호칭}의 4대 역량별 통합 지수를 뇌교육·BOS 관점에서 해석했습니다. 높은 역량은 강점 리더십으로, 낮은 역량은 뇌교육 단계와 BOS 실천 과제로 보강할 수 있습니다."
    요약 += _profile_context_line(user_profile)
    if 불일치_해석:
        요약 += " 설문-뇌파 불일치 역량은 정보 정화·뇌 통합 관점의 추가 해석을 반영했습니다."

    return SBIReport(
        요약=요약,
        역량별=역량별,
        불일치_해석=불일치_해석,
        뇌교육_5단계_참고=BRAIN_STAGES,
        BOS_5법칙_참고=BOS_LAWS,
    )


def report_to_dict(report: SBIReport) -> Dict[str, Any]:
    """API 응답용 딕셔너리로 변환 (영역 순 유지, 하위요소_정의 포함)"""
    return {
        "요약": report.요약,
        "역량별": [
            {
                "영역명": s.영역명,
                "통합점수": s.통합점수,
                "해석": s.해석,
                "추천_뇌교육단계": s.추천_뇌교육단계,
                "추천_BOS_실천": s.추천_BOS_실천,
                "불일치": s.불일치,
                "하위요소_정의": s.하위요소_정의,
            }
            for s in report.역량별
        ],
        "불일치_해석": report.불일치_해석,
        "뇌교육_5단계_참고": report.뇌교육_5단계_참고,
        "BOS_5법칙_참고": report.BOS_5법칙_참고,
    }


# 역량별 검색 키워드 (AI 검색 근거 문장 생성용)
_DOMAIN_SEARCH_KEYWORDS = {
    "창업공감": ["창업", "동기부여", "공감", "자아성찰", "창업생태계"],
    "위기감수": ["위기극복", "회복탄력성", "스트레스", "재도전", "위험감수"],
    "두뇌활용": ["뇌", "유연화", "창의성", "뇌교육", "혁신"],
    "주체적": ["주체적", "협업", "사회적 책임", "창업의식"],
}


def _snippet_from_content(content: str, max_len: int = 180) -> str:
    """content 앞부분을 문맥에 맞게 잘라 반환."""
    if not (content or "").strip():
        return ""
    s = (content or "").replace("\n", " ").strip()
    if len(s) <= max_len:
        return s
    return s[: max_len].rsplit(" ", 1)[0] + "…" if " " in s[: max_len + 1] else s[: max_len] + "…"


def augment_report_with_knowledge(
    report_dict: Dict[str, Any],
    knowledge_blog: List[Any],
    knowledge_youtube: List[Any],
) -> Dict[str, Any]:
    """
    AI가 검색한 블로그/유튜브 내용을 근거로 역량별 해석에 문맥·의미에 맞는 참고 문장을 추가합니다.
    knowledge_blog, knowledge_youtube: KnowledgeRow 또는 {title, url, content} 형태 리스트.
    report_dict를 in-place 보강하고 반환합니다.
    """
    역량별 = report_dict.get("역량별") or []
    all_sources = []
    for r in (knowledge_blog or []) + (knowledge_youtube or []):
        title = getattr(r, "title", None) or (r.get("title") if isinstance(r, dict) else "")
        url = getattr(r, "url", None) or (r.get("url") if isinstance(r, dict) else "")
        content = getattr(r, "content", None) or (r.get("content") if isinstance(r, dict) else "")
        if title and content:
            all_sources.append({"title": title, "url": url, "content": content})

    for section in 역량별:
        영역명 = section.get("영역명") or ""
        key = _domain_to_key(영역명)
        keywords = _DOMAIN_SEARCH_KEYWORDS.get(key, []) if key else []
        if not keywords or not all_sources:
            continue
        for src in all_sources:
            content = (src.get("content") or "").strip()
            if not content:
                continue
            for kw in keywords:
                if kw in content:
                    snippet = _snippet_from_content(content)
                    if snippet:
                        section["참고_검색근거"] = (
                            f"검색 자료에 따르면: {snippet} (출처: {src.get('title', '')})"
                        )
                    break
            if section.get("참고_검색근거"):
                break
    return report_dict
