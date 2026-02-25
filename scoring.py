"""
채점 로직 모듈
결과는 파일의 영역 순(창업공감 → 위기감수 → 두뇌활용 → 주체적)으로 정렬해 반환합니다.
"""
from typing import List, Dict, Optional
from models import SurveyItem, DomainScore, SurveyResult, Domain
from data_loader import SurveyDataLoader

# 영역 제시 순서 (리포트·PDF와 동일)
DOMAIN_ORDER = [
    "창업공감 및 동기부여 역량",
    "창업위기감수 및 극복 역량",
    "창업두뇌활용 및 계발 역량",
    "주체적책임 및 창업의식 역량",
]


def _domain_sort_key(영역명: str) -> int:
    """영역명에 해당하는 DOMAIN_ORDER 인덱스 반환 (정렬용)."""
    n = (영역명 or "").strip()
    for i, name in enumerate(DOMAIN_ORDER):
        if name in n or n == name:
            return i
    if "창업공감" in n or "동기부여" in n:
        return 0
    if "위기감수" in n or "극복" in n:
        return 1
    if "두뇌활용" in n or "계발" in n:
        return 2
    if "주체적" in n or "창업의식" in n:
        return 3
    return 999


class ScoringEngine:
    """채점 엔진"""
    
    def __init__(self, data_loader: SurveyDataLoader):
        """
        Args:
            data_loader: SurveyDataLoader 인스턴스
        """
        self.data_loader = data_loader
    
    def calculate_score(
        self, 
        responses: Dict[int, int], 
        excluded_sequences: Optional[List[int]] = None
    ) -> SurveyResult:
        """
        설문 응답 점수 계산
        
        Args:
            responses: {전체순번: 점수(1~5)} 형태의 응답 딕셔너리
            excluded_sequences: 제외할 문항 순번 리스트 (None이면 전체 사용)
        
        Returns:
            SurveyResult: 계산된 점수 결과
        """
        if excluded_sequences is None:
            excluded_sequences = []
        
        # 제외할 순번 집합
        excluded_set = set(excluded_sequences)
        
        # 필터링된 문항들
        filtered_items = [
            item for item in self.data_loader.items
            if item.전체순번 not in excluded_set
        ]
        
        # 각 영역별 점수 계산
        domain_scores = []
        all_scores = []
        
        # 실제 데이터에서 영역명 가져오기 (동적)
        actual_domains = sorted(set(item.영역 for item in filtered_items))
        
        for domain_name in actual_domains:
            domain_items = [
                item for item in filtered_items
                if item.영역 == domain_name
            ]
            
            domain_item_scores = []
            included_sequences = []
            
            for item in domain_items:
                if item.전체순번 in responses:
                    score = responses[item.전체순번]
                    # 1~5점 범위 검증
                    if 1 <= score <= 5:
                        domain_item_scores.append(score)
                        included_sequences.append(item.전체순번)
                        all_scores.append(score)
            
            if len(domain_item_scores) > 0:
                avg_score = sum(domain_item_scores) / len(domain_item_scores)
                domain_score = DomainScore(
                    영역명=domain_name,
                    평균점수=round(avg_score, 2),
                    문항수=len(domain_item_scores),
                    포함된_순번=included_sequences
                )
                domain_scores.append(domain_score)

        # 파일의 영역 순으로 정렬
        domain_scores.sort(key=lambda d: _domain_sort_key(d.영역명))
        
        # 전체 평균 계산
        overall_avg = round(sum(all_scores) / len(all_scores), 2) if all_scores else 0.0
        
        return SurveyResult(
            전체평균=overall_avg,
            영역별점수=domain_scores,
            사용된_문항수=len(all_scores),
            제외된_순번=sorted(excluded_sequences)
        )
    
    def get_filtered_score(
        self,
        responses: Dict[int, int],
        excluded_sequences: List[int]
    ) -> SurveyResult:
        """
        특정 문항을 제외하고 점수 계산
        
        Args:
            responses: {전체순번: 점수(1~5)} 형태의 응답 딕셔너리
            excluded_sequences: 제외할 문항 순번 리스트
        
        Returns:
            SurveyResult: 계산된 점수 결과
        """
        return self.calculate_score(responses, excluded_sequences=excluded_sequences)
    
    def calculate_with_test_data(
        self,
        excluded_sequences: Optional[List[int]] = None
    ) -> SurveyResult:
        """
        CSV의 '예시문항' 컬럼 데이터를 사용하여 점수 계산 (테스트용)
        
        Args:
            excluded_sequences: 제외할 문항 순번 리스트
        
        Returns:
            SurveyResult: 계산된 점수 결과
        """
        # 예시문항 데이터로 응답 딕셔너리 생성
        responses = {
            item.전체순번: item.예시문항
            for item in self.data_loader.items
        }
        
        return self.calculate_score(responses, excluded_sequences)
