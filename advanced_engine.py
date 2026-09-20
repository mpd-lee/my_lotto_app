import sqlite3
import pandas as pd
import numpy as np
import random
from collections import Counter

class AdvancedLottoEngine:
    def __init__(self, db_path="lotto_history.db"):
        self.conn = sqlite3.connect(db_path)
        self.df = pd.read_sql("SELECT * FROM lotto_results", self.conn)
        self.conn.close()
        
        self.total_draws = len(self.df)
        self.co_occurrence_matrix = np.zeros((46, 46))
        self.num_counts = Counter()
        self._build_statistical_matrices()

    def _build_statistical_matrices(self):
        """역대 데이터를 바탕으로 동시 출현 행렬 및 출현 빈도 구축"""
        for _, row in self.df.iterrows():
            nums = [int(row['num1']), int(row['num2']), int(row['num3']), int(row['num4']), int(row['num5']), int(row['num6'])]
            for n in nums:
                self.num_counts[n] += 1
            for i in range(len(nums)):
                for j in range(i + 1, len(nums)):
                    u, v = nums[i], nums[j]
                    self.co_occurrence_matrix[u][v] += 1
                    self.co_occurrence_matrix[v][u] += 1

    def calculate_ac(self, numbers):
        """산술적 복잡도 (AC값) 계산"""
        diffs = set()
        for i in range(len(numbers)):
            for j in range(i + 1, len(numbers)):
                diffs.add(abs(numbers[i] - numbers[j]))
        return len(diffs) - 5

    def get_omr_spatial_score(self, numbers):
        """OMR 용지 4분면 공간 균형도 검증 (1~45번 OMR 그리드 배치 기준)"""
        q1 = q2 = q3 = q4 = 0
        for n in numbers:
            row = (n - 1) // 7
            col = (n - 1) % 7
            if row < 3 and col < 3: q1 += 1
            elif row < 3 and col >= 3: q2 += 1
            elif row >= 3 and col < 3: q3 += 1
            else: q4 += 1
        
        # 특정 사분면에 4개 이상 쏠리면 감점
        max_quad = max(q1, q2, q3, q4)
        return 1.0 if max_quad <= 3 else 0.3

    def get_co_occurrence_score(self, numbers):
        """동시 출현 연관성(Lift) 점수 계산"""
        score = 0
        pair_count = 0
        for i in range(len(numbers)):
            for j in range(i + 1, len(numbers)):
                u, v = numbers[i], numbers[j]
                # Expected vs Observed
                expected = (self.num_counts[u] * self.num_counts[v]) / self.total_draws
                observed = self.co_occurrence_matrix[u][v]
                lift = observed / expected if expected > 0 else 1.0
                score += lift
                pair_count += 1
        return score / pair_count

    def evaluate_chromosome(self, numbers):
        """다목적 적합도 평가 함수 (Fitness Function)"""
        numbers = sorted(numbers)
        total_sum = sum(numbers)
        odds = sum(1 for n in numbers if n % 2 != 0)
        ac = self.calculate_ac(numbers)
        
        # 1. Hard Constraints (필수 필터)
        if not (100 <= total_sum <= 170): return 0
        if odds not in [2, 3, 4]: return 0
        if not (7 <= ac <= 10): return 0
        
        # 3연속 번호 제외
        for i in range(4):
            if numbers[i+2] == numbers[i+1] + 1 and numbers[i+1] == numbers[i] + 1:
                return 0
        
        # 2. Soft Scoring (점수제 가중치)
        spatial_score = self.get_omr_spatial_score(numbers)
        co_score = self.get_co_occurrence_score(numbers)
        
        # 기댓값(EV) 점수: 생일 범위(1~31) 밖의 번호(32~45)가 적절히 섞였는지 검증
        high_range_count = sum(1 for n in numbers if n >= 32)
        ev_score = 1.2 if high_range_count >= 2 else 0.8
        
        final_fitness = (co_score * 0.4) + (spatial_score * 0.3) + (ev_score * 0.3)
        return final_fitness

    def generate_optimal_combinations(self, count=5):
        """최우수 적합도를 가진 번호 조합 생성"""
        results = []
        weighted_pool = []
        for num, cnt in self.num_counts.items():
            weighted_pool.extend([num] * cnt)
            
        attempts = 0
        while len(results) < count and attempts < 100000:
            attempts += 1
            # 가중치 기반 무작위 6개 추출 (에러 수정 위치)
            candidate_set = set()
            while len(candidate_set) < 6:
                candidate_set.add(random.choice(weighted_pool))
            candidate = sorted(list(candidate_set))
            
            fitness = self.evaluate_chromosome(candidate)
            if fitness > 0.8:  # 우수한 조합만 최종 선정
                results.append((candidate, round(fitness, 3)))
                
        # 적합도 점수 내림차순 정렬
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:count]

if __name__ == "__main__":
    engine = AdvancedLottoEngine()
    print("🚀 고도화된 엔진으로 최적 추천 번호 추출 중...\n")
    top_picks = engine.generate_optimal_combinations(5)
    for idx, (numbers, score) in enumerate(top_picks, 1):
        print(f"Top {idx} 추천: {numbers} | 적합도 점수: {score}")