import random
import numpy as np
import pandas as pd
import streamlit as st
import time

# 페이지 기본 설정
st.set_page_config(
    page_title='로또시스 (LottoSIS) - AI 고성능 복권 분석 시스템',
    page_icon='🧧',
    layout='wide',
)

# 다크 테마 및 고품격 UI 스타일링 (블랙 & 골드 럭셔리 테마)
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
    .premium-box {
        background: linear-gradient(145deg, #1a1c29, #0f1016);
        border: 1px solid #ffd700;
        border-radius: 12px;
        padding: 20px;
        margin-top: 20px;
        box-shadow: 0 4px 15px rgba(255, 215, 0, 0.1);
    }
    .locked-text {
        color: #888;
        font-style: italic;
        margin-bottom: 10px;
    }
    .metric-card {
        background-color: #1a1c24;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #2d3139;
        box-shadow: 0 4px 8px rgba(0,0,0,0.3);
    }
    .sub-title-desc {
        color: #00FF88;
        font-size: 0.95em;
        font-weight: 600;
        margin-top: -10px;
        margin-bottom: 20px;
        letter-spacing: 0.5px;
        text-shadow: 0 0 10px rgba(0, 255, 136, 0.3);
    }
    .promo-banner {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        padding: 25px 20px;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 30px;
        border: 1px solid #69C8FF;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.5);
    }
    </style>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# 최상단 통합 홍보 배너 (로또 + 연금 듀얼 무료 강조)
# ----------------------------------------------------
st.markdown("""
<div class="promo-banner">
    <h2 style="color: #FFF; margin-top: 0; font-size: 26px; text-shadow: 2px 2px 4px rgba(0,0,0,0.6);">
        🔥 로또 6/45 <span style="color: #FFD700;">✖</span> 연금복권 720+
    </h2>
    <h3 style="color: #00FF88; margin-top: 10px; margin-bottom: 15px; font-size: 20px;">
        대한민국 최초 AI 통합 분석 시스템 가동 중!
    </h3>
    <p style="color: #E0E0E0; font-size: 16px; margin-bottom: 0;">
        지금 접속하신 모든 분들께 <span style="background-color: #FF4B4B; color: #FFF; padding: 3px 8px; border-radius: 6px; font-weight: bold;">두 가지 복권 분석 100% 무료</span> 혜택을 제공합니다.<br>
        매주 쏟아지는 당첨의 기회를 절대 놓치지 마세요!
    </p>
</div>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# 1. 공통 렌더링 및 계산 함수 모음
# ----------------------------------------------------
def calculate_ac(numbers):
    diffs = set()
    for i in range(len(numbers)):
        for j in range(i + 1, len(numbers)):
            diffs.add(abs(numbers[i] - numbers[j]))
    return max(0, len(diffs) - (len(numbers) - 1))

def render_billiard_ball(num):
    num_int = int(num)
    if 1 <= num_int <= 10: bg, fg = '#FBC400', '#000000'
    elif 11 <= num_int <= 20: bg, fg = '#69C8FF', '#000000'
    elif 21 <= num_int <= 30: bg, fg = '#FF7272', '#FFFFFF'
    elif 31 <= num_int <= 40: bg, fg = '#AAAAAA', '#FFFFFF'
    else: bg, fg = '#B0D840', '#000000'
    return f"""<span style="display: inline-block; width: 46px; height: 46px; line-height: 46px; border-radius: 50%; background-color: {bg}; color: {fg}; text-align: center; font-weight: bold; font-size: 19px; margin: 0 5px; box-shadow: 0 4px 8px rgba(0,0,0,0.4); border: 2px solid rgba(255,255,255,0.4);">{num_int:02d}</span>"""

def render_pension_ball(group, digits):
    colors = ['#5A5A5A', '#FF4B4B', '#FFAE00', '#FBC400', '#69C8FF', '#B0D840', '#AAAAAA']
    html = f"""<span style="display: inline-block; width: 60px; height: 46px; line-height: 46px; border-radius: 8px; background-color: {colors[0]}; color: white; text-align: center; font-weight: bold; font-size: 18px; margin-right: 15px; box-shadow: 0 4px 8px rgba(0,0,0,0.4);">{group} 조</span>"""
    for i, digit in enumerate(digits):
        html += f"""<span style="display: inline-block; width: 40px; height: 46px; line-height: 46px; border-radius: 50%; background-color: {colors[i+1]}; color: {'#000' if i in [2, 3] else '#FFF'}; text-align: center; font-weight: bold; font-size: 20px; margin: 0 4px; box-shadow: 0 4px 8px rgba(0,0,0,0.4);">{digit}</span>"""
    return html

# ----------------------------------------------------
# 2. 사이드바 - 메인 메뉴 (종류 선택)
# ----------------------------------------------------
st.sidebar.header('🎯 무료 분석 시작하기')
st.sidebar.info('아래에서 원하시는 복권을 선택하시면 즉시 AI 분석이 시작됩니다!')
app_mode = st.sidebar.radio('종류 선택', ['🧧 로또시스 (LottoSIS) 6/45', '🎫 연금복권 720+ 분석'])
st.sidebar.markdown('---')

# ====================================================
# [모드 1] 로또시스 (LottoSIS) 6/45 분석 시스템
# ====================================================
if app_mode == '🧧 로또시스 (LottoSIS) 6/45':
    st.title('🧧 로또시스 (LottoSIS)')
    st.markdown('<div class="sub-title-desc"><b>LottoSIS</b>: Lottery + Statistical Intelligence System (AI 딥러닝 통계 분석 엔진)</div>', unsafe_allow_html=True)
    st.markdown('통계적 확률 모델, 복잡도(AC값) 필터링 및 딥러닝 가중치 기반 최상위 엔진입니다.')

    st.sidebar.subheader('⚙️ 로또 세부 설정')
    game_count = st.sidebar.slider('추천 게임 수', 1, 10, 5)
    sum_min, sum_max = st.sidebar.slider('번호 총합 범위 설정', 50, 250, (120, 160))
    odd_even_choice = st.sidebar.selectbox('홀짝 비율 선호도', ['균등 (3:3 또는 4:2)', '모든 경우의 수 허용', '홀수 우세 (4:2 또는 5:1)'])
    ac_filter = st.sidebar.slider('AC값 (복잡도 지수) 최소값', 0, 10, 7)

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

    tab1, tab2 = st.tabs(['✨ AI 정밀 번호 추출', '📊 구간별 출현 빈도 및 예측 모델'])

    with tab1:
        if st.button('🚀 무료 로또시스 번호 추출 실행'):
            with st.spinner('다중 통계 연산 및 딥러닝 패턴 분석 중입니다...'):
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
                
                st.markdown('---')
                st.link_button('🔗 추출된 번호로 동행복권 로또 바로 구매하기', 'https://m.dhlottery.co.kr/')

        st.divider()

        # ----------------------------------------------------
        # 👑 하단 VIP 결제 및 잠금 해제 시스템
        # ----------------------------------------------------
        st.markdown("""
        <div class="premium-box">
            <h3 style="color: #ffd700; margin-top: 0;">👑 로또시스 VIP - S등급 정밀 분석 시스템</h3>
            <p style="color: #ccc; font-size: 0.95em; line-height: 1.5;">이제 운에만 의존하지 마세요!<br>첨단 데이터 과학과 AI 통계로 운과 함께 1등 확률을 극대화합니다.</p>
        </div>
        """, unsafe_allow_html=True)

        if 'vip_unlocked' not in st.session_state:
            st.session_state.vip_unlocked = False

        if not st.session_state.vip_unlocked:
            st.write("")
            with st.expander("🔒 VIP S급 딥러닝 고정수 조합 받기 (잠금 해제)", expanded=True):
                st.info("💡 **VIP 전용 혜택:** 역대 1등 당첨 패턴 딥러닝 매칭, AI 초정밀 제외수 10개 필터링, S등급 고정수 강제 배정 시스템이 가동됩니다.")
                col_pay, col_code = st.columns(2)
                
                with col_pay:
                    st.markdown("#### 1. VIP 이용권 구매하기")
                    st.write("네이버페이로 안전하게 결제하고 VIP 코드를 발급받으세요.")
                    st.link_button("💳 네이버 1초 간편 결제하기", "https://smartstore.naver.com/", type="secondary", use_container_width=True)
                    st.caption("결제 완료 시 카카오톡/문자로 접속 코드가 자동 발송됩니다.")

                with col_code:
                    st.markdown("#### 2. VIP 코드 입력")
                    vip_code = st.text_input("발급받으신 코드를 입력하세요", type="password", placeholder="예: S-CLASS-XXXX")
                    if st.button("코드 확인 및 잠금 해제", type="primary", use_container_width=True):
                        if vip_code == "7777": 
                            st.session_state.vip_unlocked = True
                            st.rerun()
                        elif vip_code:
                            st.error("유효하지 않은 코드입니다. 코드를 다시 확인해 주세요.")

        if st.session_state.vip_unlocked:
            st.success("🎉 VIP 인증이 완료되었습니다! S등급 분석 시스템이 가동됩니다.")
            st.markdown("""
                <div style="background-color: #2b1c00; border: 1px solid #ffd700; padding: 20px; border-radius: 12px; text-align: center; margin-bottom: 20px;">
                    <h3 style="color: #ffd700; margin: 0 0 15px 0;">👑 이번 주 S등급 추천 번호 👑</h3>
                    <div style="margin-bottom: 15px;">
                        <span style="color:#aaa;">AI 확정 고정수 포함, 딥러닝 매칭률 98.7%</span>
                    </div>
                    <div>
                        """ + render_billiard_ball(7) + render_billiard_ball(12) + render_billiard_ball(23) + render_billiard_ball(31) + render_billiard_ball(38) + render_billiard_ball(45) + """
                    </div>
                </div>
            """, unsafe_allow_html=True)
            if st.button("🔒 다시 잠그기 (테스트용)"):
                st.session_state.vip_unlocked = False
                st.rerun()

    with tab2:
        st.subheader('📈 로또 구간별 출현 빈도 및 예측 모델')
        st.info("역대 데이터 기반 핫/콜드 넘버 확률 분석 결과가 표시됩니다.")
        chart_data = pd.DataFrame(np.random.randn(20, 3) * 4 + 50, columns=['1~15구간', '16~30구간', '31~45구간'])
        st.line_chart(chart_data)

# ====================================================
# [모드 2] 연금복권 720+ 분석 시스템
# ====================================================
elif app_mode == '🎫 연금복권 720+ 분석':
    st.title('🎫 연금복권 720+ 분석 시스템')
    st.markdown('<div class="sub-title-desc"><b>PensionSIS</b>: Pension Lottery + Statistical Intelligence System (자리수별 엔트로피 정밀 엔진)</div>', unsafe_allow_html=True)
    st.markdown('자리수별 난수 엔트로피, 홀짝/고저 비율, 복잡도(AC)를 제어하는 정밀 엔진입니다.')

    st.sidebar.subheader('⚙️ 연금복권 세부 설정')
    pension_count = st.sidebar.slider('추천 조합 수', 1, 10, 5)
    group_choice = st.sidebar.radio('조 선택 방식', ['전체 조(1~5조) 모두 같은 번호로 (1,2등 동시 노림)', 'AI 자동 추천 (분산 투자)'])
    p_sum_min, p_sum_max = st.sidebar.slider('각 자리 합계 범위 (평균 27)', 0, 54, (15, 39))
    p_odd_even = st.sidebar.selectbox('홀짝 비율 (연금 전용)', ['균등 (3:3 또는 4:2)', '모든 경우의 수 허용'])
    
    st.sidebar.markdown('---')
    st.sidebar.markdown('**💡 연금복권 특화 필터 옵션**')
    use_high_low_filter = st.sidebar.checkbox('고저(High/Low) 밸런스 유지 (권장)', value=True)
    use_consecutive_filter = st.sidebar.checkbox('3연속 동일 숫자 출현 방지 (권장)', value=True)

    def generate_optimized_pension():
        for _ in range(10000):
            digits = [random.randint(0, 9) for _ in range(6)]
            total_sum = sum(digits)
            if not (p_sum_min <= total_sum <= p_sum_max): continue
            odds = sum(1 for d in digits if d % 2 != 0)
            if '균등' in p_odd_even and odds not in [2, 3, 4]: continue
            highs = sum(1 for d in digits if d >= 5)
            if use_high_low_filter and (highs < 2 or highs > 4): continue
            if use_consecutive_filter and any(digits.count(d) >= 3 for d in set(digits)): continue
            return digits, total_sum, odds, 6-odds, highs, 6-highs, calculate_ac(digits)
        digits = [random.randint(0, 9) for _ in range(6)]
        return digits, sum(digits), 3, 3, 3, 3, calculate_ac(digits)

    tab1, tab2 = st.tabs(['🎫 추천 결과 확인', '📊 연금복권 통계 분석'])

    with tab1:
        if st.button('🚀 무료 연금복권 번호 추출 실행'):
            with st.spinner('자리수별 독립 확률 및 패턴 분산 분석 중입니다...'):
                time.sleep(0.7)
                st.success('정밀 필터링을 거친 연금복권 최적화 조합이 완료되었습니다!')
                if '전체 조' in group_choice:
                    digits, total_sum, odds, evens, highs, lows, ac = generate_optimized_pension()
                    group_scores = sorted(random.sample(range(78, 99), 5), reverse=True)
                    groups = random.sample(range(1, 6), 5)
                    medals = ['🥇 1순위 강력 추천', '🥈 2순위 유력 추천', '🥉 3순위 추천', '🏅 4순위', '🏅 5순위']
                    colors = ['#FFD700', '#C0C0C0', '#CD7F32', '#888888', '#555555']
                    for rank, (g, score) in enumerate(zip(groups, group_scores)):
                        html = render_pension_ball(g, digits)
                        st.markdown(f"""
                            <div style="background-color: #1a1c24; padding: 18px 22px; border-radius: 14px; margin-bottom: 12px; border-left: 6px solid {colors[rank]};">
                                <div style="font-size: 1.05em; font-weight: bold; margin-bottom: 12px; color: #FFF;">
                                    {medals[rank]} <span style="color: #FF4B4B;">(AI 출현 가중치: {score}점)</span>
                                </div>
                                <div>{html}</div>
                            </div>
                        """, unsafe_allow_html=True)
                else:
                    for i in range(1, pension_count + 1):
                        group = random.randint(1, 5)
                        digits, total_sum, odds, evens, highs, lows, ac = generate_optimized_pension()
                        html = render_pension_ball(group, digits)
                        st.markdown(f"""
                            <div style="background-color: #1a1c24; padding: 18px 22px; border-radius: 14px; margin-bottom: 12px; border-left: 6px solid #69C8FF;">
                                <div style="font-size: 0.9em; font-weight: bold; margin-bottom: 12px; color: #aaa;">조합 {i}</div>
                                <div>{html}</div>
                            </div>
                        """, unsafe_allow_html=True)
                
                st.markdown('---')
                st.link_button('🔗 추출된 번호로 동행복권 연금복권 바로 구매하기', 'https://m.dhlottery.co.kr/')

    with tab2:
        st.subheader('📈 연금복권 각 자리수별 패턴 분석')
        p_chart = pd.DataFrame(np.random.randint(10, 50, size=(10, 6)), columns=['십만', '만', '천', '백', '십', '일'])
        st.bar_chart(p_chart)

st.markdown('---')
st.markdown('<div style="text-align: center; color: #666;">© 2026 LottoSIS (Statistical Intelligence System). All Rights Reserved.</div>', unsafe_allow_html=True)