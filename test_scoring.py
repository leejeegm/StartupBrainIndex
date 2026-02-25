"""
유닛 테스트: 채점 로직 검증
"""
import unittest
from data_loader import SurveyDataLoader
from scoring import ScoringEngine


class TestScoring(unittest.TestCase):
    """채점 로직 테스트"""
    
    @classmethod
    def setUpClass(cls):
        """테스트 클래스 초기화"""
        cls.data_loader = SurveyDataLoader()
        cls.scoring_engine = ScoringEngine(cls.data_loader)
    
    def test_data_loading(self):
        """데이터 로딩 검증"""
        # 96개 문항이 모두 로드되었는지 확인
        self.assertEqual(len(self.data_loader.items), 96, "96개 문항이 모두 로드되어야 합니다")
        
        # 순번 검증
        validation = self.data_loader.validate_sequences()
        self.assertTrue(validation["검증_결과"], f"순번 검증 실패: {validation}")
        
        # 4대 영역 확인
        domains = set(item.영역 for item in self.data_loader.items)
        self.assertEqual(len(domains), 4, "4대 영역이 모두 존재해야 합니다")
    
    def test_full_survey_scoring(self):
        """전체 문항 분석 테스트"""
        # 예시문항 데이터로 전체 문항 점수 계산
        result = self.scoring_engine.calculate_with_test_data(excluded_sequences=[])
        
        # 검증
        self.assertGreater(result.전체평균, 0, "전체 평균은 0보다 커야 합니다")
        self.assertEqual(result.사용된_문항수, 96, "전체 96개 문항이 사용되어야 합니다")
        self.assertEqual(len(result.제외된_순번), 0, "제외된 순번이 없어야 합니다")
        self.assertEqual(len(result.영역별점수), 4, "4개 영역의 점수가 계산되어야 합니다")
        
        # 각 영역별 점수 검증
        for domain_score in result.영역별점수:
            self.assertGreater(domain_score.평균점수, 0, f"{domain_score.영역명} 평균점수는 0보다 커야 합니다")
            self.assertLessEqual(domain_score.평균점수, 5, f"{domain_score.영역명} 평균점수는 5 이하여야 합니다")
            self.assertEqual(domain_score.문항수, 24, f"{domain_score.영역명}는 24개 문항이어야 합니다")
        
        print("\n" + "=" * 80)
        print("전체 문항 분석 결과")
        print("=" * 80)
        print(f"전체 평균: {result.전체평균}")
        print(f"사용된 문항수: {result.사용된_문항수}")
        print(f"제외된 순번: {result.제외된_순번}")
        print("\n영역별 점수:")
        for domain_score in result.영역별점수:
            print(f"  - {domain_score.영역명}: {domain_score.평균점수}점 (문항수: {domain_score.문항수})")
    
    def test_filtered_survey_scoring(self):
        """일부 제외 분석 테스트"""
        # 24개 문항 제외 (예: 1~24번)
        excluded = list(range(1, 25))
        result = self.scoring_engine.calculate_with_test_data(excluded_sequences=excluded)
        
        # 검증
        self.assertGreater(result.전체평균, 0, "전체 평균은 0보다 커야 합니다")
        self.assertEqual(result.사용된_문항수, 72, "72개 문항이 사용되어야 합니다 (96 - 24)")
        self.assertEqual(len(result.제외된_순번), 24, "24개 순번이 제외되어야 합니다")
        self.assertEqual(result.제외된_순번, excluded, "제외된 순번이 일치해야 합니다")
        
        # 각 영역별 점수 검증 (일부 문항이 제외되었으므로 문항수가 줄어들 수 있음)
        total_items_used = sum(domain_score.문항수 for domain_score in result.영역별점수)
        self.assertEqual(total_items_used, 72, "총 72개 문항이 사용되어야 합니다")
        
        print("\n" + "=" * 80)
        print("일부 제외 분석 결과 (1~24번 제외)")
        print("=" * 80)
        print(f"전체 평균: {result.전체평균}")
        print(f"사용된 문항수: {result.사용된_문항수}")
        print(f"제외된 순번: {result.제외된_순번}")
        print("\n영역별 점수:")
        for domain_score in result.영역별점수:
            print(f"  - {domain_score.영역명}: {domain_score.평균점수}점 (문항수: {domain_score.문항수})")
    
    def test_custom_excluded_sequences(self):
        """임의의 순번 제외 테스트"""
        # 홀수 번호만 제외 (1, 3, 5, ..., 95)
        excluded = list(range(1, 97, 2))
        result = self.scoring_engine.calculate_with_test_data(excluded_sequences=excluded)
        
        # 검증
        self.assertEqual(result.사용된_문항수, 48, "48개 문항이 사용되어야 합니다 (96 - 48)")
        self.assertEqual(len(result.제외된_순번), 48, "48개 순번이 제외되어야 합니다")
        
        print("\n" + "=" * 80)
        print("임의 순번 제외 분석 결과 (홀수 번호 제외)")
        print("=" * 80)
        print(f"전체 평균: {result.전체평균}")
        print(f"사용된 문항수: {result.사용된_문항수}")
        print(f"제외된 순번 개수: {len(result.제외된_순번)}")
    
    def test_get_filtered_score_function(self):
        """get_filtered_score 함수 테스트"""
        # 예시문항 데이터로 응답 생성
        responses = {
            item.전체순번: item.예시문항
            for item in self.data_loader.items
        }
        
        # 10개 문항 제외
        excluded = [1, 2, 3, 4, 5, 10, 20, 30, 40, 50]
        result = self.scoring_engine.get_filtered_score(responses, excluded)
        
        # 검증
        self.assertEqual(result.사용된_문항수, 86, "86개 문항이 사용되어야 합니다 (96 - 10)")
        self.assertEqual(len(result.제외된_순번), 10, "10개 순번이 제외되어야 합니다")
        
        print("\n" + "=" * 80)
        print("get_filtered_score 함수 테스트 결과")
        print("=" * 80)
        print(f"전체 평균: {result.전체평균}")
        print(f"사용된 문항수: {result.사용된_문항수}")
        print(f"제외된 순번: {result.제외된_순번}")


def run_tests():
    """테스트 실행 및 결과 보고"""
    print("=" * 80)
    print("SBI 채점 시스템 유닛 테스트 시작")
    print("=" * 80)
    
    # 테스트 스위트 생성
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestScoring)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 80)
    print("테스트 결과 요약")
    print("=" * 80)
    print(f"실행된 테스트: {result.testsRun}")
    print(f"성공: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"실패: {len(result.failures)}")
    print(f"오류: {len(result.errors)}")
    
    if result.failures:
        print("\n실패한 테스트:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
    
    if result.errors:
        print("\n오류가 발생한 테스트:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
