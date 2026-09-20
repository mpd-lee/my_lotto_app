import sqlite3
import pandas as pd
import random
from collections import Counter

def load_data():
    conn = sqlite3.connect("lotto_history.db")
    df = pd.read_sql("SELECT * FROM lotto_results", conn)
    conn.close()
    return df

def analyze_lotto():
    df = load_data()
    print(f"📊 총 {len(df)}회차 데이터를 기반으로 분석을 시작합니다.\n")
    
    # 모든 당첨 번호 하나로 합치기
    all_numbers = []
    for col in ['num1', 'num2', 'num3', 'num4', 'num5', 'num6']:
        all_numbers.extend(df[col].tolist())
        
    counts = Counter(all_numbers)
    most_common = counts.most_common(10)
    least_common = counts.most_common()[:-11:-1]
    
    print("🔥 [역대 가장 많이 나온 번호 TOP 10]")
    for num, count in most_common:
        print(f"  - {num}번: {count}회 출현")
        
    print("\n❄️ [역대 가장 적게 나온 번호 TOP 10]")
    for num, count in least_common:
        print(f"  - {num}번: {count}회 출현")
        
    # 가중치 기반 번호 추천 (자주 나온 번호일수록 확률 UP)
    weighted_pool = []
    for num, count in counts.items():
        weighted_pool.extend([num] * count)
        
    recommended_numbers = set()
    while len(recommended_numbers) < 6:
        recommended_numbers.add(random.choice(weighted_pool))
        
    sorted_recommendation = sorted(list(recommended_numbers))
    print("\n🔮 [통계 기반 이번 주 추천 번호 6개]")
    print(f"  👉 {sorted_recommendation}")

if __name__ == "__main__":
    analyze_lotto()