import streamlit as st
import sqlite3
import pandas as pd
import random
from collections import Counter

st.set_page_config(page_title="고급 로또 분석기", page_icon="🎰", layout="centered")
st.title("🎰 고급 로또 당첨 번호 분석 & 추천 시스템")
st.write("통계 필터링(총합, 홀짝, 연속수) 및 AC(복잡도) 알고리즘이 적용된 엔진입니다.")

@st.cache_data
def load_data():
    conn = sqlite3.connect("lotto_history.db")
    df = pd.read_sql("SELECT * FROM lotto_results", conn)
    conn.close()
    return df

# AC 값(산술적 복잡도) 계산 함수
def calculate_ac(numbers):
    diffs = set()
    for i in range(len(numbers)):
        for j in range(i+1, len(numbers)):
            diffs.add(abs(numbers[i] - numbers[j]))
    return len(diffs) - 5  # 6개 번호의 기본 복잡도 차감

# 3연속 번호 확인 함수
def has_3_consec(numbers):
    for i in range(4):
        if numbers[i+2] == numbers[i+1] + 1 and numbers[i+1] == numbers[i] + 1:
            return True
    return False

try:
    df = load_data()
    
    # 1. 가중치 풀 생성 (빈도 기반)
    all_numbers = []
    for col in ['num1', 'num2', 'num3', 'num4', 'num5', 'num6']:
        all_numbers.extend(df[col].tolist())
    counts = Counter(all_numbers)
    
    weighted_pool = []
    for num, cnt in counts.items():
        weighted_pool.extend([num] * cnt)

    st.subheader("🎲 AI 하이브리드 번호 생성기")
    st.caption("가중치 무작위 추출 후 4단계 정밀 필터링(총합, 홀짝, 연속수, AC값)을 거친 최적의 조합만 출력합니다.")
    
    games = st.slider("생성할 게임 수 선택", min_value=1, max_value=10, value=5)
    
    if st.button("🚀 고급 필터링으로 추첨하기", type="primary"):
        st.markdown("---")
        
        valid_games = []
        attempts = 0 # 무한 루프 방지용
        
        # 사용자가 원하는 게임 수만큼 필터 통과 번호 찾기
        with st.spinner("AI가 수만 번의 조합을 시뮬레이션 중입니다..."):
            while len(valid_games) < games and attempts < 50000:
                attempts += 1
                
                # 가중치 기반 임의 추출
                candidate = set()
                while len(candidate) < 6:
                    candidate.add(random.choice(weighted_pool))
                candidate = sorted(list(candidate))
                
                # [필터 1] 총합(Sum)이 100 ~ 170 사이인가?
                if not (100 <= sum(candidate) <= 170):
                    continue
                    
                # [필터 2] 홀짝 비율이 2:4, 3:3, 4:2 인가?
                odds = sum(1 for n in candidate if n % 2 != 0)
                if odds not in [2, 3, 4]:
                    continue
                    
                # [필터 3] 3연속 번호가 없는가?
                if has_3_consec(candidate):
                    continue
                    
                # [필터 4 - 고급] AC 값이 7 이상 10 이하인가?
                ac_value = calculate_ac(candidate)
                if not (7 <= ac_value <= 10):
                    continue
                
                # 모든 필터를 통과하면 추가
                valid_games.append(candidate)

        if len(valid_games) < games:
            st.warning("조건이 너무 빡빡하여 추천 조합을 다 찾지 못했습니다. 다시 시도해주세요.")
        else:
            for i, game in enumerate(valid_games):
                balls_str = "  ".join([f"` {n:02d} `" for n in game])
                st.success(f"**게임 {i+1}:** {balls_str}  (총합:{sum(game)}, 홀짝:{sum(1 for n in game if n%2!=0)}:{6-sum(1 for n in game if n%2!=0)}, AC:{calculate_ac(game)})")
                
except Exception as e:
    st.error(f"오류 발생: {e}")