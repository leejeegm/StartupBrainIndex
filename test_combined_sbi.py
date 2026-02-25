"""
Step 2: SBI 통합 지수 산출 로직 유닛 테스트
- 영역별 가중치 (S*ws + E*we) 정확성 검증
- 불일치 플래그(20% 차이) 검증
"""
import sys
import unittest
from data_loader import SurveyDataLoader
from scoring import ScoringEngine
from analysis_engine import calculate_combined_sbi, _normalize_1_5_to_100, DOMAIN_EEG_WEIGHTS
from eeg_provider import MockEEGProvider
from models import SurveyResult, DomainScore, EEGDomainMetrics, Domain


class TestCombinedSBIWeights(unittest.TestCase):
    """가상 설문+뇌파로 가중치 수식 검증"""

    @classmethod
    def setUpClass(cls):
        cls.loader = SurveyDataLoader()
        cls.scoring = ScoringEngine(cls.loader)

    def test_normalize_1_5_to_100(self):
        """1~5점이 0~100으로 정확히 변환되는지"""
        self.assertEqual(_normalize_1_5_to_100(1), 0.0)
        self.assertEqual(_normalize_1_5_to_100(5), 100.0)
        self.assertEqual(_normalize_1_5_to_100(3), 50.0)
        self.assertAlmostEqual(_normalize_1_5_to_100(2.5), 37.5, places=1)

    def test_domain_weights_formula(self):
        """영역별 가중치가 논문 수식대로 적용되는지 (고정 설문·뇌파)"""
        # 설문: 모든 영역 5점 → S_norm = 100
        # 뇌파: 모든 지표 0 → E = 0
        survey_result = SurveyResult(
            전체평균=5.0,
            영역별점수=[
                DomainScore(영역명=Domain.창업공감_및_동기부여,     평균점수=5.0, 문항수=24, 포함된_순번=list(range(1, 25))),
                DomainScore(영역명=Domain.창업위기감수_및_극복,     평균점수=5.0, 문항수=24, 포함된_순번=list(range(25, 49))),
                DomainScore(영역명=Domain.창업두뇌활용_및_계발,     평균점수=5.0, 문항수=24, 포함된_순번=list(range(49, 73))),
                DomainScore(영역명=Domain.주체적책임_및_창업의식,   평균점수=5.0, 문항수=24, 포함된_순번=list(range(73, 97))),
            ],
            사용된_문항수=96,
            제외된_순번=[],
        )
        eeg = EEGDomainMetrics(motivation=0, resilience=0, innovation=0, responsibility=0)
        result = calculate_combined_sbi(survey_result, eeg)

        # S=100, E=0 → combined = 100*ws + 0*we = 100*ws
        # 창업공감: 0.7*100 = 70
        # 창업위기: 0.5*100 = 50
        # 창업두뇌: 0.6*100 = 60
        # 주체적책임: 0.8*100 = 80
        by_domain = {d.영역명: d.combined_score for d in result.영역별_통합점수}
        self.assertAlmostEqual(by_domain[Domain.창업공감_및_동기부여],     70.0, places=2, msg="창업공감 (S*0.7+E*0.3)")
        self.assertAlmostEqual(by_domain[Domain.창업위기감수_및_극복],     50.0, places=2, msg="창업위기 (S*0.5+E*0.5)")
        self.assertAlmostEqual(by_domain[Domain.창업두뇌활용_및_계발],     60.0, places=2, msg="창업두뇌 (S*0.6+E*0.4)")
        self.assertAlmostEqual(by_domain[Domain.주체적책임_및_창업의식],   80.0, places=2, msg="주체적책임 (S*0.8+E*0.2)")

        # 통합지수 = (70+50+60+80)/4 = 65
        self.assertAlmostEqual(result.통합지수_0_100, 65.0, places=2)

    def test_domain_weights_eeg_only(self):
        """E만 100, S=0일 때 영역별 combined = 100*we"""
        survey_result = SurveyResult(
            전체평균=1.0,
            영역별점수=[
                DomainScore(영역명=Domain.창업공감_및_동기부여,     평균점수=1.0, 문항수=24, 포함된_순번=list(range(1, 25))),
                DomainScore(영역명=Domain.창업위기감수_및_극복,     평균점수=1.0, 문항수=24, 포함된_순번=list(range(25, 49))),
                DomainScore(영역명=Domain.창업두뇌활용_및_계발,     평균점수=1.0, 문항수=24, 포함된_순번=list(range(49, 73))),
                DomainScore(영역명=Domain.주체적책임_및_창업의식,   평균점수=1.0, 문항수=24, 포함된_순번=list(range(73, 97))),
            ],
            사용된_문항수=96,
            제외된_순번=[],
        )
        eeg = EEGDomainMetrics(motivation=100, resilience=100, innovation=100, responsibility=100)
        result = calculate_combined_sbi(survey_result, eeg)

        # S_norm=0 → combined = 0*ws + 100*we = 100*we
        by_domain = {d.영역명: d.combined_score for d in result.영역별_통합점수}
        self.assertAlmostEqual(by_domain[Domain.창업공감_및_동기부여],     30.0, places=2)  # 0.3*100
        self.assertAlmostEqual(by_domain[Domain.창업위기감수_및_극복],     50.0, places=2)  # 0.5*100
        self.assertAlmostEqual(by_domain[Domain.창업두뇌활용_및_계발],     40.0, places=2)  # 0.4*100
        self.assertAlmostEqual(by_domain[Domain.주체적책임_및_창업의식],   20.0, places=2)  # 0.2*100

    def test_inconsistency_flag_20_percent(self):
        """설문-뇌파 차이 20 이상(0~100 스케일)이면 inconsistency_flag=True"""
        # S_norm=100, E=75 → diff=25 >= 20 → inconsistency
        survey_result = SurveyResult(
            전체평균=5.0,
            영역별점수=[
                DomainScore(영역명=Domain.창업공감_및_동기부여,     평균점수=5.0, 문항수=24, 포함된_순번=list(range(1, 25))),
                DomainScore(영역명=Domain.창업위기감수_및_극복,     평균점수=5.0, 문항수=24, 포함된_순번=list(range(25, 49))),
                DomainScore(영역명=Domain.창업두뇌활용_및_계발,     평균점수=5.0, 문항수=24, 포함된_순번=list(range(49, 73))),
                DomainScore(영역명=Domain.주체적책임_및_창업의식,   평균점수=5.0, 문항수=24, 포함된_순번=list(range(73, 97))),
            ],
            사용된_문항수=96,
            제외된_순번=[],
        )
        eeg = EEGDomainMetrics(motivation=75, resilience=75, innovation=75, responsibility=75)  # diff=25
        result = calculate_combined_sbi(survey_result, eeg)
        self.assertTrue(result.inconsistency_flag, "|100-75|=25 >= 20 이므로 inconsistency_flag=True")

    def test_inconsistency_flag_under_20(self):
        """차이 20 미만이면 inconsistency_flag=False"""
        survey_result = SurveyResult(
            전체평균=3.0,  # S_norm=50
            영역별점수=[
                DomainScore(영역명=Domain.창업공감_및_동기부여,     평균점수=3.0, 문항수=24, 포함된_순번=list(range(1, 25))),
                DomainScore(영역명=Domain.창업위기감수_및_극복,     평균점수=3.0, 문항수=24, 포함된_순번=list(range(25, 49))),
                DomainScore(영역명=Domain.창업두뇌활용_및_계발,     평균점수=3.0, 문항수=24, 포함된_순번=list(range(49, 73))),
                DomainScore(영역명=Domain.주체적책임_및_창업의식,   평균점수=3.0, 문항수=24, 포함된_순번=list(range(73, 97))),
            ],
            사용된_문항수=96,
            제외된_순번=[],
        )
        eeg = EEGDomainMetrics(motivation=55, resilience=55, innovation=55, responsibility=55)  # diff=5
        result = calculate_combined_sbi(survey_result, eeg)
        self.assertFalse(result.inconsistency_flag)

    def test_mock_eeg_provider_returns_four_metrics(self):
        """MockEEGProvider가 4개 지표를 0~100 범위로 반환하는지"""
        provider = MockEEGProvider(seed=42)
        m = provider.get_metrics()
        self.assertIsInstance(m, EEGDomainMetrics)
        self.assertGreaterEqual(m.motivation, 0)
        self.assertLessEqual(m.motivation, 100)
        self.assertGreaterEqual(m.resilience, 0)
        self.assertLessEqual(m.resilience, 100)
        self.assertGreaterEqual(m.innovation, 0)
        self.assertLessEqual(m.innovation, 100)
        self.assertGreaterEqual(m.responsibility, 0)
        self.assertLessEqual(m.responsibility, 100)

    def test_real_survey_plus_mock_eeg_integration(self):
        """실제 설문(예시문항) + Mock 뇌파로 통합 지수 산출 통합 테스트"""
        responses = {item.전체순번: item.예시문항 for item in self.loader.items}
        survey_result = self.scoring.calculate_score(responses, excluded_sequences=[])
        eeg = MockEEGProvider(seed=99).get_metrics()
        result = calculate_combined_sbi(survey_result, eeg)

        self.assertGreaterEqual(result.통합지수_0_100, 0)
        self.assertLessEqual(result.통합지수_0_100, 100)
        self.assertEqual(len(result.영역별_통합점수), 4)
        self.assertEqual(result.사용된_문항수, 96)


def run_and_report():
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestCombinedSBIWeights)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "=" * 60)
    print("Step 2 가중치 검증 요약")
    print("=" * 60)
    print(f"실행: {result.testsRun}, 성공: {result.testsRun - len(result.failures) - len(result.errors)}, 실패: {len(result.failures)}, 오류: {len(result.errors)}")
    if result.failures:
        for t, tb in result.failures:
            print(f"  실패: {t}: {tb}")
    if result.errors:
        for t, tb in result.errors:
            print(f"  오류: {t}: {tb}")
    print("=" * 60)

    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_and_report())
