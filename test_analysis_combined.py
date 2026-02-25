"""
Step 2: 뇌파 결합 분석 엔진 유닛 테스트
"""
import unittest
from data_loader import SurveyDataLoader
from scoring import ScoringEngine
from analysis_engine import run_combined_analysis
from models import BrainWaveMetrics, SurveyResult, DomainScore


class TestCombinedAnalysis(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.loader = SurveyDataLoader()
        cls.scoring = ScoringEngine(cls.loader)

    def test_survey_only(self):
        """뇌파 없이 설문만으로 결합 지수 = 정규화된 SBI"""
        responses = {item.전체순번: item.예시문항 for item in self.loader.items}
        survey_result = self.scoring.calculate_score(responses, excluded_sequences=[])
        combined = run_combined_analysis(survey_result, brainwave=None)
        self.assertIsNone(combined.eeg_engagement)
        self.assertIsNone(combined.eeg_focus)
        self.assertEqual(combined.combined_index, combined.survey_sbi_normalized)
        self.assertGreaterEqual(combined.combined_index, 0)
        self.assertLessEqual(combined.combined_index, 100)

    def test_survey_with_eeg(self):
        """설문 + 뇌파(engagement) 결합"""
        responses = {item.전체순번: item.예시문항 for item in self.loader.items}
        survey_result = self.scoring.calculate_score(responses, excluded_sequences=[])
        eeg = BrainWaveMetrics(engagement=80.0, focus=70.0)
        combined = run_combined_analysis(
            survey_result, brainwave=eeg, survey_weight=0.6, eeg_weight=0.4
        )
        self.assertEqual(combined.eeg_engagement, 80.0)
        self.assertEqual(combined.eeg_focus, 70.0)
        self.assertGreaterEqual(combined.combined_index, 0)
        self.assertLessEqual(combined.combined_index, 100)


if __name__ == "__main__":
    unittest.main(verbosity=2)
