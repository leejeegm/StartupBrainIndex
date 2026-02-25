"""
Step 2: 가상 뇌파(EEG) 데이터 인터페이스
실제 업체 API 확정 전 Mock 데이터를 반환하는 MockEEGProvider
"""
import random
from typing import Optional
from models import EEGDomainMetrics


class MockEEGProvider:
    """
    가상 뇌파 데이터 제공자.
    포함 지표:
    - Motivation: 전두엽 비대칭 지수 (창업공감 및 동기부여)
    - Resilience: 알파파 회복 속도 (창업위기감수 및 극복)
    - Innovation: SMR/Beta 코히어런스 (창업두뇌활용 및 계발)
    - Responsibility: 전전두엽 안정도 (주체적책임 및 창업의식)
    모든 값은 0~100 스케일로 반환.
    """

    def __init__(self, seed: Optional[int] = None):
        if seed is not None:
            random.seed(seed)

    def get_metrics(self) -> EEGDomainMetrics:
        """
        가상의 4대 역량 뇌파 지표를 반환합니다.
        실제 API 연동 시 이 메서드만 교체하면 됩니다.
        """
        return EEGDomainMetrics(
            motivation=round(random.uniform(30.0, 95.0), 2),      # 전두엽 비대칭 지수
            resilience=round(random.uniform(35.0, 90.0), 2),     # 알파파 회복 속도
            innovation=round(random.uniform(40.0, 92.0), 2),     # SMR/Beta 코히어런스
            responsibility=round(random.uniform(25.0, 88.0), 2), # 전전두엽 안정도
        )

    def get_metrics_fixed(self, motivation: float, resilience: float, innovation: float, responsibility: float) -> EEGDomainMetrics:
        """테스트용: 고정값 반환."""
        return EEGDomainMetrics(
            motivation=float(motivation),
            resilience=float(resilience),
            innovation=float(innovation),
            responsibility=float(responsibility),
        )
