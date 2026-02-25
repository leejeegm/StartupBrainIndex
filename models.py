"""
SBI(Startup Brain Index) 데이터 모델 정의
4대 영역을 클래스로 정의
"""
from dataclasses import dataclass
from typing import List, Dict, Optional


@dataclass
class SurveyItem:
    """개별 설문 문항 데이터"""
    전체순번: int
    영역: str
    하위역량: str
    하위요소: str
    하위요소순번: int
    문항보정: str
    예시문항: int  # 테스트 응답 (1~5점)
    비고: Optional[str] = None  # CSV 추가 컬럼 (있으면 로드)


@dataclass
class DomainScore:
    """영역별 점수"""
    영역명: str
    평균점수: float
    문항수: int
    포함된_순번: List[int]


@dataclass
class SurveyResult:
    """전체 설문 결과"""
    전체평균: float
    영역별점수: List[DomainScore]
    사용된_문항수: int
    제외된_순번: List[int]


class Domain:
    """4대 영역 클래스"""
    
    # 4대 영역 정의
    창업공감_및_동기부여 = "창업공감 및 동기부여"
    창업위기감수_및_극복 = "창업위기감수 및 극복"
    창업두뇌활용_및_계발 = "창업두뇌활용 및 계발"
    주체적책임_및_창업의식 = "주체적책임 및 창업의식"
    
    @classmethod
    def get_all_domains(cls) -> List[str]:
        """모든 영역 리스트 반환"""
        return [
            cls.창업공감_및_동기부여,
            cls.창업위기감수_및_극복,
            cls.창업두뇌활용_및_계발,
            cls.주체적책임_및_창업의식,
        ]
    
    @classmethod
    def is_valid_domain(cls, domain_name: str) -> bool:
        """유효한 영역인지 확인"""
        return domain_name in cls.get_all_domains()


# --- Step 2: 뇌파 데이터 결합 분석 ---

@dataclass
class BrainWaveMetrics:
    """뇌파(EEG) 요약 지표 (주파수 대역별 상대 파워 또는 정규화된 지표)"""
    alpha: Optional[float] = None   # alpha 대역 (8~13Hz) - 이완/집중
    beta: Optional[float] = None    # beta 대역 (13~30Hz) - 각성/사고
    theta: Optional[float] = None   # theta 대역 (4~8Hz) - 휴식/창의
    delta: Optional[float] = None   # delta 대역 (0.5~4Hz) - 수면/회복
    engagement: Optional[float] = None  # 종합 각성·참여도 지수 (0~100)
    focus: Optional[float] = None       # 집중도 지수 (0~100)


@dataclass
class CombinedAnalysisResult:
    """설문(SBI) + 뇌파 결합 분석 결과"""
    survey_sbi_score: float           # 설문 전체 평균 (1~5)
    survey_sbi_normalized: float      # 0~100 정규화
    eeg_engagement: Optional[float]   # 뇌파 참여도 (제공 시)
    eeg_focus: Optional[float]         # 뇌파 집중도 (제공 시)
    combined_index: float             # 결합 지수 (0~100)
    domain_scores: List[DomainScore]   # 영역별 설문 점수
    message: str


# --- Step 2: 뇌파 4대 역량 지표 (논문 수식용) ---

@dataclass
class EEGDomainMetrics:
    """4대 영역별 뇌파 지표 (0~100 스케일, Mock/실제 API 공통)"""
    motivation: float    # 전두엽 비대칭 지수 → 창업공감 및 동기부여
    resilience: float    # 알파파 회복 속도 → 창업위기감수 및 극복
    innovation: float   # SMR/Beta 코히어런스 → 창업두뇌활용 및 계발
    responsibility: float  # 전전두엽 안정도 → 주체적책임 및 창업의식


@dataclass
class DomainCombinedScore:
    """영역별 설문(S)+뇌파(E) 가중 결합 점수 및 불일치 여부"""
    영역명: str
    survey_score: float      # 설문 평균 (1~5)
    survey_normalized: float  # 0~100 정규화
    eeg_score: float          # 뇌파 지수 (0~100)
    combined_score: float    # (S_norm * w_s) + (E * w_e)
    weight_survey: float
    weight_eeg: float
    inconsistency: bool      # True if |S_norm - E| >= 20


@dataclass
class CombinedSBIResult:
    """SBI 통합 지수 산출 결과 (박사 논문 수식 적용)"""
    survey_전체평균: float
    survey_정규화_0_100: float
    eeg_영역별: EEGDomainMetrics
    영역별_통합점수: List[DomainCombinedScore]
    통합지수_0_100: float    # 영역별 통합점수의 평균
    inconsistency_flag: bool  # 어떤 역량에서든 설문-뇌파 차이 20% 이상 시 True
    사용된_문항수: int
    제외된_순번: List[int]
    message: str
