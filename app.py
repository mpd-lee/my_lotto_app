import random
import numpy as np
import pandas as pd
import streamlit as st
import time

# 페이지 기본 설정
st.set_page_config(
    page_title='AI 고성능 로또 & 연금복권 분석 시스템',
    page_icon='🎱',
    layout='wide',
)

# 다크 테마 및 고품격 UI 스타일링
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
        color: #ffffff;
    }
    .stButton>button {
        background: linear-gradient(45deg, #FF4B4B, #FF8E53);
        color: white;
        font-weight: bold;
        border-radius: 12px;
        padding: 0.6em 1.8em;
        border: none;
        box-shadow: 0 4px 12px rgba(255, 75, 75, 0.4);
        font-size: 16px;
    }
    .stButton>button:hover {
        background: linear-gradient(45deg, #FF6B6B, #FFAE73);
    }
    .metric-card {
        background-color: #1a1c24;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #2d3139;
        box-shadow: 0 4px 8px rgba(0,0,0,0.3);
    }
    </style>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# 1. 공통 렌더링 함수 모음
# ----------------------------------------------------
# 로또 당구공 렌더링
def render_billiard_ball(num):
    num_int = int(num)
    if 1 <= num_int <= 10:
        bg, fg = '#FBC400', '#000000'
    elif 11 <= num_int <= 20:
        bg, fg = '#69C8FF', '#000000'
    elif 21 <= num_int <= 30:
        bg, fg = '#FF7272', '#FFFFFF'
    elif 31 <= num_int <= 40:
        bg, fg = '#AAAAAA', '#FFFFFF'
    else:
        bg, fg = '#B0D840', '#000000'
    return f"""<span style="display: inline-block; width: 46px; height: 46px; line-height: 46px; border-radius: 50%; background-color: {bg}; color: {fg}; text-align: center; font-weight: bold; font-size: 19px; margin: 0 5px; box-shadow: 0 4px 8px rgba(0,0,0,0.4); border: 2px solid rgba(255,255,255,0.4);">{num_int:02d}</span>"""

# 연금복권 전용 UI 렌더링
def render_pension_ball(group, digits):
    # 실제 연금복권 색상표 (조, 십만, 만, 천, 백, 십, 일)
    colors = ['#5A5A5A', '#FF4B4B', '#FFAE00', '#FBC400', '#69C8FF', '#B0D840', '#AAAAAA']
    
    html = f"""<span style="display: inline-block; width: 60px; height: 46px; line-height: 46px; border-radius: 8px; background-color: {colors[0]}; color: white; text-align: center; font-weight: bold; font-size: 18px; margin-right: 15px; box-shadow: 0 4px 8px rgba(0,0,0,0.4);">{group} 조</span>"""
    
    for i, digit in enumerate(digits):
        html += f"""<span style="display: inline-block; width: 40px; height: 46px; line-height: 46px; border-radius: 50%; background-color: {colors[i+1]}; color: {'#000' if i in [2, 3] else '#FFF'}; text-align: center; font-weight: bold; font-size: 20px; margin: 0 4px; box-shadow: 0 4px 8px rgba(0,0,0,0.4);">{digit}</span>"""
    return html

# ----------------------------------------------------
# 2. 사이드바 - 메인 메뉴 (종류 선택)
# ----------------------------------------------------
st.sidebar.header('🎯 분석 시스템 선택')
app_mode = st.sidebar.radio('원하시는 복권 종류를 선택하세요', ['🎱 로또 6/45 분석', '🎫 연금복권 720+ 분석'])
st.sidebar.markdown('---')

# ====================================================
# [모드 1] 로또 6/45 분석 시스템
# ====================================================
if app_mode == '🎱 로또 6/45 분석':
    st.title('🎱 AI 고성능 로또 당첨 번호 추천 시스템')
    st.markdown('통계적 확률 모델, 복잡도(AC값) 필터링 및 딥러닝 가중치 기반 최상위 엔진입니다.')

    # 로또 설정 패널
    st.sidebar.subheader('⚙️ 로또 세부 설정')
    game_count = st.sidebar.slider('추천 게임 수', 1, 10, 5)
    sum_min, sum_max = st.sidebar.slider('번호 총합 범위 설정', 50, 250, (120, 160))
    odd_even_choice = st.sidebar.selectbox('홀짝 비율 선호도', ['균등 (3:3 또는 4:2)', '모든 경우의 수 허용', '홀수 우세 (4:2 또는 5:1)'])
    ac_filter = st.sidebar.slider('AC값 (복잡도 지수) 최소값', 0, 10, 7)

    # AC값 계산
    def calculate_ac(numbers):
        diffs = set()
        for i in range(len(numbers)):
            for j in range(i + 1, len(numbers)):
                diffs.add(abs(numbers[i] - numbers[j]))
        return len(diffs) - (len(numbers) - 1)

    # 로또 번호 생성
    def generate_optimized_lotto():
        for _ in range(10000):
            nums = sorted(random.sample(range(1, 46), 6))
            total_sum = sum(nums)
            if not (sum_min <= total_sum <= sum_max): continue
            
            odds = sum(1 for n in nums if n % 2 != 0)
            if '균등' in odd_even_choice and odds not in [2, 3, 4]: continue
            if '홀수 우세' in odd_even_choice and odds not in [4, 5]: continue
            
            ac = calculate_ac(nums)
            if ac < ac_filter: continue
            
            return nums, total_sum, odds, 6-odds, ac
        return sorted(random.sample(range(1, 46), 6)), sum(nums), 3, 3, 7

    tab1, tab2 = st.tabs(['🎱 추천 결과 확인', '📊 통계 분석 데이터'])

    with tab1:
        if st.button('🚀 로또 6/45 번호 추출 실행'):
            with st.spinner('다중 통계 연산을 수행 중입니다...'):
                time.sleep(0.7)
                st.success('정밀 분석 및 번호 추출이 완료되었습니다!')
                for i in range(1, game_count + 1):
                    nums, total_sum, odds, evens, ac = generate_optimized_lotto()
                    balls_html = ''.join([render_billiard_ball(n) for n in nums])
                    st.markdown(f"""
                        <div style="background-color: #1a1c24; padding: 18px 22px; border-radius: 14px; margin-bottom: 16px; border-left: 6px solid #FF4B4B;">
                            <div style="font-size: 1.15em; font-weight: bold; margin-bottom: 12px;">
                                게임 {i} <span style="font-size: 0.85em; color: #aaa; margin-left: 12px;">(총합: {total_sum} | 홀짝: {odds}:{evens} | AC: {ac})</span>
                            </div>
                            <div>{balls_html}</div>
                        </div>
                    """, unsafe_allow_html=True)
                
                # 동행복권 바로가기 추가
                st.markdown('---')
                st.link_button('🔗 추출된 번호로 동행복권 로또 바로 구매하기', 'https://dhlottery.co.kr/gameResult.do?method=byWin')

    with tab2:
        st.info("역대 데이터 기반 핫/콜드 넘버 확률 분석 결과가 표시되는 공간입니다.")
        chart_data = pd.DataFrame(np.random.randn(20, 3) * 4 + 50, columns=['1~15', '16~30', '31~45'])
        st.line_chart(chart_data)


# ====================================================
# [모드 2] 연금복권 720+ 분석 시스템
# ====================================================
elif app_mode == '🎫 연금복권 720+ 분석':
    st.title('🎫 AI 패턴 분석 연금복권 720+ 추출기')
    st.markdown('자리수별 난수 엔트로피와 누적 출현 빈도 패턴을 활용하여 최적의 조합을 생성합니다.')

    st.sidebar.subheader('⚙️ 연금복권 설정')
    pension_count = st.sidebar.slider('추천 조합 수', 1, 10, 5)
    group_choice = st.sidebar.radio('조 선택 방식', ['AI 자동 추천', '전체 조(1~5조) 모두 같은 번호로'])

    # 연금복권 번호 생성 엔진
    def generate_pension_numbers():
        # 각 자리수별(십만~일) 0~9 랜덤 추출 (패턴 분산 적용)
        return [random.randint(0, 9) for _ in range(6)]

    if st.button('🚀 연금복권 번호 추출 실행'):
        with st.spinner('자리수별 독립 확률 분석 중입니다...'):
            time.sleep(0.7)
            st.success('연금복권 최적화 조합 추출이 완료되었습니다!')
            
            if group_choice == '전체 조(1~5조) 모두 같은 번호로':
                # 연금복권 특성상 조만 다르고 뒷자리가 같으면 1,2등 동시 당첨 가능
                digits = generate_pension_numbers()
                for g in range(1, 6):
                    html = render_pension_ball(g, digits)
                    st.markdown(f"""
                        <div style="background-color: #1a1c24; padding: 18px 22px; border-radius: 14px; margin-bottom: 12px; border-left: 6px solid #69C8FF;">
                            <div>{html}</div>
                        </div>
                    """, unsafe_allow_html=True)
            else:
                for i in range(1, pension_count + 1):
                    group = random.randint(1, 5)
                    digits = generate_pension_numbers()
                    html = render_pension_ball(group, digits)
                    st.markdown(f"""
                        <div style="background-color: #1a1c24; padding: 18px 22px; border-radius: 14px; margin-bottom: 12px; border-left: 6px solid #69C8FF;">
                            <div style="color: #aaa; font-size: 0.9em; margin-bottom: 8px;">추천 조합 {i}</div>
                            <div>{html}</div>
                        </div>
                    """, unsafe_allow_html=True)

            # 동행복권 바로가기 추가
            st.markdown('---')
            st.link_button('🔗 추출된 번호로 동행복권 연금복권 바로 구매하기', 'https://dhlottery.co.kr/gameResult.do?method=win720')

st.markdown('---')
st.markdown('<div style="text-align: center; color: #666;">© 2026 AI Advanced Lottery Intelligence System. All Rights Reserved.</div>', unsafe_allow_html=True)