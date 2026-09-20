import sqlite3
import pandas as pd
import numpy as np
import random
from collections import Counter

class UltraLottoEngine:
    def __init__(self, db_path="lotto_history.db"):
        self.db_path = db_path
        self.df = self._load_data()
        self.total_draws = len(self.df)
        self.co_occurrence_matrix = np.zeros((46, 46))
        self.num_counts = Counter()
        self.gap_dict = {}  # 번호별 미출현 기간
        self._analyze_history()

    def _load_data(self):
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql("SELECT * FROM lotto_results ORDER BY drw_no ASC", conn)
        conn.close()
        return df

    def _analyze_history(self):
        """동시 출현 행렬 및 번호별 미출현 주기(Gap) 계산"""
        latest_draw = self.df['drw_no'].max()
        last_seen = {i: 0 for i in range(1, 46)}
        
        for _, row in self.df.iterrows():
            drw = int(row['drw_no'])
            nums = [int(row['num1']), int(row['num2']), int(row['num3']), 
                    int(row['num4']), int(row['num5']), int(row['num6'])]
            
            for n in nums:
                self.num_counts[n] += 1
                last_seen[n] = drw
                
            for i in range(len(nums)):
                for j in range(i + 1, len(nums)):
                    u, v = nums[i], nums[j]
                    self.co_occurrence_matrix[u][v] += 1
                    self.co_occurrence_matrix[v][u] += 1

        # 미출현 회차수(Gap) 계산
        for n in range(1, 46):
            self.gap_dict[n] = latest_draw - last_seen[n]

    def calculate_ac(self, numbers):
        """산술적 복잡도 (AC)"""
        diffs = set()
        for i in range(len(numbers)):
            for j in range(i + 1, len(numbers)):
                diffs.add(abs(numbers[i] - numbers[j]))
        return len(diffs) - 5

    def get_gap_score(self, numbers):
        """미출현 주기 적정성 평가 (너무 오래 안 나오거나 너무 연속으로 나온 수 보정)"""
        avg_gap = np.mean([self.gap_dict[n] for n in numbers])
        # 평균 미출현 회차수가 3~12회 사이에 분포할 때 가장 높은 점수
        if 3 <= avg_gap <= 12:
            return 1.2
        return 0.8

    def evaluate_combination(self, numbers):
        """다목적 적합도 평가 (Fitness Function)"""
        numbers = sorted(numbers)
        total_sum = sum(numbers)
        odds = sum(1 for n in numbers if n % 2 != 0)
        ac = self.calculate_ac(numbers)
        
        # [하드 필터] 필수 조건
        if not (100 <= total_sum <= 170): return 0
        if odds not in [2, 3, 4]: return 0
        if not (7 <= ac <= 10): return 0
        
        for i in range(4):
            if numbers[i+2] == numbers[i+1] + 1 and numbers[i+1] == numbers[i] + 1:
                return 0
                
        # [소프트 스코어] 통계적 연관성 & 미출현 모멘텀
        gap_score = self.get_gap_score(numbers)
        high_range_count = sum(1 for n in numbers if n >= 32)
        ev_score = 1.15 if high_range_count >= 2 else 0.85
        
        return round(gap_score * ev_score, 3)

    def generate_recommendations(self, count=5):
        """최적 조합 생성"""
        results = []
        weighted_pool = []
        for num, cnt in self.num_counts.items():
            weighted_pool.extend([num] * cnt)
            
        attempts = 0
        while len(results) < count and attempts < 100000:
            attempts += 1
            candidate_set = set()
            while len(candidate_set) < 6:
                candidate_set.add(random.choice(weighted_pool))
            candidate = sorted(list(candidate_set))
            
            score = self.evaluate_combination(candidate)
            if score >= 1.0:
                results.append({"numbers": candidate, "score": score, "sum": sum(candidate), "ac": self.calculate_ac(candidate)})
                
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:count]

    def run_backtest(self, test_draws=30):
        """과거 회차 백테스팅 엔진 (알고리즘 당첨 성과 검증)"""
        print(f"\n🧪 최근 {test_draws}회차 대상 백테스팅 시뮬레이션 수행 중...")
        hits = {5: 0, 4: 0, 3: 0, "total_games": test_draws * 5}
        
        for idx in range(self.total_draws - test_draws, self.total_draws):
            row = self.df.iloc[idx]
            winning_set = set([int(row['num1']), int(row['num2']), int(row['num3']), 
                               int(row['num4']), int(row['num5']), int(row['num6'])])
            
            # 해당 회차 시뮬레이션 추출 (5게임)
            picks = self.generate_recommendations(5)
            for p in picks:
                match_count = len(set(p['numbers']) & winning_set)
                if match_count == 3: hits[5] += 1  # 5등
                elif match_count == 4: hits[4] += 1 # 4등
                elif match_count >= 5: hits[3] += 1 # 3등 이상
                
        print(f"✅ 백테스팅 완료 (총 {hits['total_games']}게임 검증)")
        print(f"  - 5등 당첨(3개 일치): {hits[5]}회")
        print(f"  - 4등 당첨(4개 일치): {hits[4]}회")
        print(f"  - 3등 이상 당첨(5개+ 일치): {hits[3]}회")

if __name__ == "__main__":
    engine = UltraLottoEngine()
    print("🚀 최적 조합 추첨 결과:")
    for i, res in enumerate(engine.generate_recommendations(5), 1):
        print(f" Top {i}: {res['numbers']} | 점수: {res['score']} | 총합: {res['sum']} | AC: {res['ac']}")
    
    # 백테스팅 검증 실행
    engine.run_backtest(30)