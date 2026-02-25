"""
CSV 파일 로딩 및 데이터 구조화 모듈
"""
import os
import pandas as pd
from typing import List, Dict
from models import SurveyItem, Domain

# 프로젝트 루트 기준 경로 (Render 등 어떤 CWD에서도 동작)
_ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
_DEFAULT_CSV = os.path.join(_ROOT_DIR, "survey_items.csv")


class SurveyDataLoader:
    """설문 데이터 로더"""
    
    def __init__(self, csv_path: str = None):
        """
        Args:
            csv_path: CSV 파일 경로. None이면 프로젝트 루트의 survey_items.csv
        """
        self.csv_path = csv_path or _DEFAULT_CSV
        self.df: pd.DataFrame = None
        self.items: List[SurveyItem] = []
        self._load_data()
    
    def _load_data(self):
        """CSV 파일 로드 및 구조화"""
        if not os.path.isfile(self.csv_path):
            raise FileNotFoundError(
                f"survey_items.csv not found at {self.csv_path!r} (cwd={os.getcwd()!r})"
            )
        # UTF-8 우선, 실패 시 cp949 (한국어 Windows 저장)
        try:
            self.df = pd.read_csv(self.csv_path, encoding='utf-8')
        except UnicodeDecodeError:
            self.df = pd.read_csv(self.csv_path, encoding='cp949')
        
        # 컬럼명 정리 (공백 제거)
        self.df.columns = self.df.columns.str.strip()
        
        # 컬럼 인덱스로 접근 (컬럼명 인코딩 문제 대비)
        # 예상 순서: 영역(0), 하위역량(1), 하위요소(2), 하위요소순번(3), 문항보정(4), 전체순번(5), 문항보정(6), 예시문항(7)
        # 실제 확인 결과: 영역(0), 하위역량(1), 하위요소(2), 하위요소순번(3), 문항보정(4), 전체순번(5), 문항보정(6), 예시문항(7)
        
        # SurveyItem 객체 리스트 생성
        self.items = []
        has_비고 = '비고' in self.df.columns
        for idx, row in self.df.iterrows():
            try:
                # 컬럼 인덱스로 접근 (필수 컬럼), 추가 컬럼은 이름으로
                비고_val = None
                if has_비고 and ('비고' in row.index) and pd.notna(row.get('비고')) and str(row['비고']).strip():
                    비고_val = str(row['비고']).strip()
                item = SurveyItem(
                    전체순번=int(row.iloc[5]),  # 전체순번 (인덱스 5)
                    영역=str(row.iloc[0]).strip().replace('\n', ' '),  # 영역 (인덱스 0)
                    하위역량=str(row.iloc[1]).strip().replace('\n', ' '),  # 하위역량 (인덱스 1)
                    하위요소=str(row.iloc[2]).strip().replace('\n', ' '),  # 하위요소 (인덱스 2)
                    하위요소순번=int(row.iloc[3]),  # 하위요소순번 (인덱스 3)
                    문항보정=str(row.iloc[6]).strip(),  # 문항(보정) (인덱스 6)
                    예시문항=int(row.iloc[7]),  # 예시문항 (인덱스 7)
                    비고=비고_val
                )
                self.items.append(item)
            except (KeyError, ValueError, IndexError) as e:
                print(f"Warning: Row {idx} 처리 중 오류: {e}")
                print(f"  Row data: {row.to_dict()}")
                continue
        
        # 전체순번으로 정렬
        self.items.sort(key=lambda x: x.전체순번)
        
        print(f"총 {len(self.items)}개 문항 로드 완료")
    
    def get_item_by_sequence(self, sequence: int) -> SurveyItem:
        """전체순번으로 문항 조회"""
        for item in self.items:
            if item.전체순번 == sequence:
                return item
        return None
    
    def get_items_by_domain(self, domain: str) -> List[SurveyItem]:
        """영역별 문항 조회"""
        return [item for item in self.items if item.영역 == domain]
    
    def get_all_sequences(self) -> List[int]:
        """모든 전체순번 리스트 반환"""
        return [item.전체순번 for item in self.items]

    def get_selected_sequences(self) -> List[int]:
        """비고가 '선택'인 문항의 전체순번 리스트 (선택 71문항 등)."""
        return [item.전체순번 for item in self.items if (getattr(item, "비고", None) or "").strip() == "선택"]

    def get_excluded_sequences(self) -> List[int]:
        """비고가 '제외'인 문항의 전체순번 리스트."""
        return [item.전체순번 for item in self.items if (getattr(item, "비고", None) or "").strip() == "제외"]

    def validate_sequences(self) -> Dict:
        """문항 순번 검증"""
        sequences = self.get_all_sequences()
        expected = set(range(1, 97))
        actual = set(sequences)
        
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        
        return {
            "총_문항수": len(sequences),
            "예상_순번": list(range(1, 97)),
            "실제_순번": sorted(sequences),
            "누락된_순번": missing,
            "추가된_순번": extra,
            "검증_결과": len(missing) == 0 and len(extra) == 0
        }
