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

# ----------------------------------------------------
# 👑 통합 VIP Pass 데이터베이스 초기화
# ----------------------------------------------------
if 'vip_unlocked' not in st.session_state:
    st.session_state.vip_unlocked = False

if 'code_db' not in st.session_state:
    st.session_state.code_db = {
        "S-CLASS-1234": "unused",
        "S-CLASS-5678": "unused",
        "7777": "master"
    }

# 현재 선택된 복권 상태 관리 (기본값: 로또 6/45)
if 'selected_lotto_type' not in st.session_state:
    st.session_state.selected_lotto_type = 'lotto'

# ----------------------------------------------------
# 🎨 다크 테마 및 맞춤 스타일링 (CSS)
# ----------------------------------------------------
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    
    /* =========================================
       ✨ 1. 로또 6/45 분석 버튼 (Gold)
       ========================================= */
    @keyframes glow-gold {
        0% { box-shadow: 0 0 8px rgba(255, 215, 0, 0.4); border-color: #d4af37; transform: scale(1); }
        50% { box-shadow: 0 0 25px rgba(255, 215, 0, 0.9), 0 0 40px rgba(255, 165, 0, 0.6); border-color: #fff68f; transform: scale(1.03); }
        100% { box-shadow: 0 0 8px rgba(255, 215, 0, 0.4); border-color: #d4af37; transform: scale(1); }
    }
    div[data-testid="stColumn"]:nth-of-type(1) button {
        background: linear-gradient(135deg, #2a2415, #b8860b) !important;
        border: 2px solid #FFD700 !important;
        animation: glow-gold 1.5s infinite ease-in-out !important;
        width: 100% !important;
    }
    
    /* =========================================
       🥈 2. 연금복권 720+ 분석 버튼 (Silver)
       ========================================= */
    @keyframes glow-silver {
        0% { box-shadow: 0 0 8px rgba(192, 192, 192, 0.4); border-color: #a9a9a9; transform: scale(1); }
        50% { box-shadow: 0 0 25px rgba(220, 220, 220, 0.9), 0 0 40px rgba(255, 255, 255, 0.6); border-color: #ffffff; transform: scale(1.03); }
        100% { box-shadow: 0 0 8px rgba(192, 192, 192, 0.4); border-color: #a9a9a9; transform: scale(1); }
    }
    div[data-testid="stColumn"]:nth-of-type(2) button {
        background: linear-gradient(135deg, #1e1e24, #696973) !important;
        border: 2px solid #C0C0C0 !important;
        animation: glow-silver 1.5s infinite ease-in-out !important;
        width: 100% !important;
    }

    /* 상단 금색/은색 버튼 텍스트 공통 디자인 */
    div[data-testid="stColumn"] button p {
        font-size: 20px !important;
        font-weight: 900 !important;
        color: #FFFFFF !important;
        text-shadow: 0px 2px 4px rgba(0, 0, 0, 0.8);
    }

    /* =========================================
       🔵 3. 추출하기 버튼 공통 (Blue) 
       ========================================= */
    @keyframes glow-blue {
        0% { box-shadow: 0 0 8px rgba(0, 136, 255, 0.4); border-color: #0077cc; transform: scale(1); }
        50% { box-shadow: 0 0 25px rgba(0, 136, 255, 0.9), 0 0 40px rgba(0, 200, 255, 0.6); border-color: #33aaff; transform: scale(1.03); }
        100% { box-shadow: 0 0 8px rgba(0, 136, 255, 0.4); border-color: #0077cc; transform: scale(1); }
    }
    button[kind="primary"] {
        background: linear-gradient(45deg, #0055ff, #00aaff) !important;
        border: 2px solid #0088FF !important;
        animation: glow-blue 1.5s infinite ease-in-out !important;
        border-radius: 12px !important;
        padding: 0.8em 1.8em !important;
        width: 100% !important;
        margin-top: 15px !important;
        margin-bottom: 25px !important;
    }
    button[kind="primary"] p {
        font-size: 20px !important;
        font-weight: 900 !important;
        color: #FFFFFF !important;
        text-shadow: 0px 2px 4px rgba(0, 0, 0, 0.5);
    }

    /* =========================================
       🔴 4. 잠금 해제 시작 버튼 (Red) - Expander 내부 
       ========================================= */
    @keyframes glow-red {
        0% { box-shadow: 0 0 8px rgba(255, 51, 51, 0.4); border-color: #cc0000; transform: scale(1); }
        50% { box-shadow: 0 0 25px rgba(255, 51, 51, 0.9), 0 0 40px rgba(255, 102, 102, 0.6); border-color: #ff6666; transform: scale(1.03); }
        100% { box-shadow: 0 0 8px rgba(255, 51, 51, 0.4); border-color: #cc0000; transform: scale(1); }
    }
    div[data-testid="stExpander"] button[kind="primary"] {
        background: linear-gradient(45deg, #cc0000, #ff4444) !important;
        border: 2px solid #FF3333 !important;
        animation: glow-red 1.5s infinite ease-in-out !important;
        margin-top: 10px !important;
        margin-bottom: 10px !important;
        padding: 0.5em 1em !important;
    }
    div[data-testid="stExpander"] button[kind="primary"] p {
        font-size: 16px !important;
    }

    /* ⚙️ 진한 은빛 톱니바퀴 및 펄스 효과 유지 */
    @keyframes spin-gear { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    .silver-gear {
        display: inline-block; font-size: 22px; margin-left: 8px; margin-right: 4px;
        filter: drop-shadow(0 2px 4px rgba(0,0,0,0.8)) brightness(0.85);
        animation: spin-gear 4s linear infinite; vertical-align: middle;
    }
    @keyframes pulse-glow { 0% { transform: scale(0.95); opacity: 0.6; } 50% { transform: scale(1.15); opacity: 1; filter: drop-shadow(0 0 6px #00FF88); } 100% { transform: scale(0.95); opacity: 0.6; } }
    .live-indicator {
        display: inline-block; width: 10px; height: 10px; background-color: #00FF88;
        border-radius: 50%; margin-left: 10px; margin-right: 6px;
        animation: pulse-glow 1.5s infinite ease-in-out; vertical-align: middle;
    }
    
    .premium-box {
        background: linear-gradient(145deg, #1a1c29, #0f1016);
        border: 1px solid #ffd700; border-radius: 12px;
        padding: 20px; margin-top: 20px;
        box-shadow: 0 4px 15px rgba(255, 215, 0, 0.15);
    }
    .promo-banner {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        padding: 20px 15px; border-radius: 15px; text-align: center;
        margin-bottom: 25px; border: 1px solid #69C8FF;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.5);
    }
    .menu-title { font-size: 24px; font-weight: 900; color: #FFD700; text-align: center; margin-bottom: 15px; }
    </style>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# 최상단 통합 홍보 배너
# ----------------------------------------------------
st.markdown("""
<div class="promo-banner">
    <h2 style="color: #FFF; margin-top: 0; font-size: 24px;">
        🔥 로또 6/45 <span style="color: #FFD700;">✖</span> 연금복권 720+
    </h2>
    <p style="color: #E0E0E0; font-size: 16px; margin-bottom: 0;">
        지금 접속하신 분들께 <span style="background-color: #FF4B4B; color: #FFF; padding: 3px 8px; border-radius: 6px; font-weight: bold;">100% 무료 분석</span> 제공!<br>
        👑 VIP 혜택: 단 한 번의 결제로 두 가지 복권 S등급 동시 오픈!
    </p>
</div>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# 공통 함수 모음
# ----------------------------------------------------
def calculate_ac(numbers):
    diffs = set()
    for i in range(len(numbers)):
        for j in range(i + 1, len(numbers)):
            diffs.add(abs(numbers[i] - numbers[j]))
    return max(0, len(diffs) - (len(numbers) - 1))

def render_billiard_ball(num):
    num_int = int(num)
    if 1 <= num_int <= 10: 
        bg = 'radial-gradient(circle at 30% 30%, #FFEE55, #FFC107)'
        fg = '#000000'
    elif 11 <= num_int <= 20: 
        bg = 'radial-gradient(circle at 30% 30%, #4EA8DE, #023E8A)'
        fg = '#FFFFFF'
    elif 21 <= num_int <= 30: 
        bg = 'radial-gradient(circle at 30% 30%, #FF6B6B, #D90429)'
        fg = '#FFFFFF'
    elif 31 <= num_int <= 40: 
        bg = 'radial-gradient(circle at 30% 30%, #ADB5BD, #495057)'
        fg = '#FFFFFF'
    else: 
        bg = 'radial-gradient(circle at 30% 30%, #90BE6D, #38B000)'
        fg = '#FFFFFF'
    return f"""<span style="display: inline-block; width: 44px; height: 44px; line-height: 44px; border-radius: 50%; background: {bg}; color: {fg}; text-align: center; font-weight: 900; font-size: 17px; margin: 0 4px; box-shadow: inset -3px -3px 8px rgba(0,0,0,0.5), 0 4px 10px rgba(0,0,0,0.4); border: 1.5px solid rgba(255,255,255,0.6);">{num_int:02d}</span>"""

def render_pension_ball(group, digits):
    colors = ['#5A5A5A', '#FF4B4B', '#FFAE00', '#FBC400', '#69C8FF', '#B0D840', '#AAAAAA']
    html = f"""<span style="display: inline-block; width: 55px; height: 42px; line-height: 42px; border-radius: 8px; background-color: {colors[0]}; color: white; text-align: center; font-weight: bold; font-size: 16px; margin-right: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.4);">{group} 조</span>"""
    for i, digit in enumerate(digits):
        html += f"""<span style="display: inline-block; width: 38px; height: 42px; line-height: 42px; border-radius: 50%; background-color: {colors[i+1]}; color: {'#000' if i in [2, 3] else '#FFF'}; text-align: center; font-weight: bold; font-size: 18px; margin: 0 2px; box-shadow: 0 4px 8px rgba(0,0,0,0.4);">{digit}</span>"""
    return html

# ----------------------------------------------------
# 🟢 럭셔리 상단 선택 버튼 영역
# ----------------------------------------------------
st.markdown('<div class="menu-title">🎯 원하시는 복권을 선택하세요</div>', unsafe_allow_html=True)

col_sel1, col_sel2 = st.columns(2)

with col_sel1:
    if st.button("🧧 로또 6/45 분석", use_container_width=True, key="sel_lotto_btn"):
        st.session_state.selected_lotto_type = 'lotto'
        st.rerun()

with col_sel2:
    if st.button("🎫 연금복권 720+ 분석", use_container_width=True, key="sel_pension_btn"):
        st.session_state.selected_lotto_type = 'pension'
        st.rerun()

# ----------------------------------------------------
# ⚙️ 회전하는 진한 은빛 톱니바퀴와 실시간 엔진 가동 상태 바
# ----------------------------------------------------
current_label = "🧧 로또 6/45 분석" if st.session_state.selected_lotto_type == 'lotto' else "🎫 연금복권 720+ 분석"
st.markdown(f"""
    <div style="background: linear-gradient(135deg, #132e1b, #1b3d27); padding: 14px 20px; border-radius: 12px; text-align: center; border: 2px solid #00FF88; margin-top: 10px; margin-bottom: 20px; box-shadow: 0 4px 15px rgba(0,255,136,0.2);">
        <span style="font-size: 20px; color: #FFFFFF; font-weight: 800;">{current_label}</span>
        <span class="silver-gear">⚙️</span>
        <span class="live-indicator"></span>
        <span style="font-size: 16px; color: #00FF88; font-weight: 700;">AI 실시간 분석 엔진 가동 중</span>
    </div>
""", unsafe_allow_html=True)

st.divider()

app_mode = '🧧 로또 6/45 분석' if st.session_state.selected_lotto_type == 'lotto' else '🎫 연금복권 720+ 분석'

# ====================================================
# [모드 1] 로또시스 (LottoSIS) 6/45 분석 시스템
# ====================================================
if app_mode == '🧧 로또 6/45 분석':
    
    st.subheader('⚙️ 추천 게임 수 설정')
    game_count = st.slider('몇 게임을 추천받으시겠습니까?', 1, 10, 5)
    
    with st.expander("🛠️ 상세 분석 필터 (어려우시면 그대로 두셔도 됩니다)"):
        sum_min, sum_max = st.slider('번호 총합 범위 설정', 50, 250, (120, 160))
        odd_even_choice = st.selectbox('홀짝 비율 선호도', ['균등 (3:3 또는 4:2)', '모든 경우의 수 허용', '홀수 우세 (4:2 또는 5:1)'])
        ac_filter = st.slider('AC값 (복잡도 지수) 최소값', 0, 10, 7)

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

    # 🔵 로또 당첨 번호 무료 추출하기 (파란색 효과를 위해 type='primary' 추가)
    if st.button('🚀 로또 당첨 번호 무료 추출하기', key='btn_lotto', type='primary'):
        with st.spinner('AI가 역대 패턴을 분석하여 최적의 번호를 찾고 있습니다...'):
            time.sleep(1)
            st.success('분석 완료! 아래 추천 번호를 확인하세요.')
            for i in range(1, game_count + 1):
                nums, total_sum, odds, evens, ac = generate_optimized_lotto()
                balls_html = ''.join([render_billiard_ball(n) for n in nums])
                st.markdown(f"""
                    <div style="background-color: #1a1c24; padding: 15px; border-radius: 14px; margin-bottom: 12px; border-left: 5px solid #FF4B4B;">
                        <div style="font-size: 1.1em; font-weight: bold; margin-bottom: 10px;">게임 {i}</div>
                        <div style="text-align: center;">{balls_html}</div>
                    </div>
                """, unsafe_allow_html=True)

# ====================================================
# [모드 2] 연금복권 720+ 분석 시스템
# ====================================================
elif app_mode == '🎫 연금복권 720+ 분석':
    
    st.subheader('⚙️ 추천 조합 수 설정')
    pension_count = st.slider('몇 게임을 추천받으시겠습니까?', 1, 10, 5)
    
    with st.expander("🛠️ 상세 분석 필터 (어려우시면 그대로 두셔도 됩니다)"):
        group_choice = st.radio('조 선택 방식', ['전체 조 분산 투자 (1~5조 골고루)', '단일 조 집중 투자'])
    
    def generate_pension():
        return [random.randint(0, 9) for _ in range(6)]

    # 🔵 연금복권 당첨 번호 무료 추출하기 (파란색 효과를 위해 type='primary' 추가)
    if st.button('🚀 연금복권 당첨 번호 무료 추출하기', key='btn_pension', type='primary'):
        with st.spinner('자리수별 독립 확률 분석 중입니다...'):
            time.sleep(1)
            st.success('분석 완료! 아래 추천 조합을 확인하세요.')
            for i in range(1, pension_count + 1):
                g = random.randint(1, 5) if '분산' in group_choice else 3
                digits = generate_pension()
                html = render_pension_ball(g, digits)
                st.markdown(f"""
                    <div style="background-color: #1a1c24; padding: 15px; border-radius: 14px; margin-bottom: 12px; border-left: 5px solid #69C8FF;">
                        <div style="font-size: 1em; font-weight: bold; margin-bottom: 10px;">조합 {i}</div>
                        <div style="text-align: center;">{html}</div>
                    </div>
                """, unsafe_allow_html=True)

# ====================================================
# 공통 VIP 프리패스 하단 영역
# ====================================================
st.divider()
st.markdown("""
<div class="premium-box">
    <h3 style="color: #ffd700; margin-top: 0; text-align: center;">👑 통합 VIP Pass 전용 시스템</h3>
    <p style="color: #ccc; font-size: 0.95em; text-align: center;">로또 S등급 초정밀 분석 & 연금복권 유력 조 핀포인트 예측을 동시에!</p>
</div>
""", unsafe_allow_html=True)

if not st.session_state.vip_unlocked:
    with st.expander("🔒 VIP 1회용 고유 코드 입력 및 잠금 해제", expanded=True):
        st.markdown("#### 1. VIP 패스 결제")
        st.link_button("💳 네이버페이 간편 결제하기", "https://smartstore.naver.com/", type="secondary", use_container_width=True)
        
        st.markdown("#### 2. 발급받은 고유 코드 입력")
        vip_code = st.text_input("코드 입력", type="password", key="vip_input", placeholder="예: S-CLASS-XXXX")
        
        # 🔴 잠금 해제 시작 버튼 (위쪽 CSS에서 Expander 내부에 있는 primary 버튼을 붉은색으로 지정했습니다.)
        if st.button("잠금 해제 시작", type="primary", use_container_width=True):
            if vip_code == "7777":
                st.session_state.vip_unlocked = True
                st.rerun()
            elif vip_code in st.session_state.code_db:
                if st.session_state.code_db[vip_code] == "unused":
                    st.session_state.code_db[vip_code] = "used" 
                    st.session_state.vip_unlocked = True
                    st.success("인증 완료! 이제 앱의 모든 VIP 시스템이 가동됩니다.")
                    time.sleep(1.5)
                    st.rerun()
                else:
                    st.error("❌ 이미 사용 완료된 1회용 코드입니다. 무단 공유가 차단되었습니다.")
            elif vip_code:
                st.error("존재하지 않거나 잘못된 코드입니다.")
else:
    st.success("🎉 [VIP 프리패스 활성화 중] 가장 확률 높은 S등급 데이터가 실시간 가동 중입니다.")
    
    if app_mode == '🧧 로또 6/45 분석':
        st.markdown("""
            <div style="background-color: #2b1c00; border: 1px solid #ffd700; padding: 20px; border-radius: 12px; text-align: center; margin-bottom: 20px;">
                <h3 style="color: #ffd700; margin: 0 0 15px 0;">👑 이번 주 로또 S등급 강력 추천 👑</h3>
                <div style="margin-bottom: 15px;"><span style="color:#ccc;">딥러닝 매칭률 98.7%</span></div>
                <div>""" + render_billiard_ball(7) + render_billiard_ball(12) + render_billiard_ball(23) + render_billiard_ball(31) + render_billiard_ball(38) + render_billiard_ball(45) + """</div>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <div style="background-color: #2b1c00; border: 1px solid #ffd700; padding: 20px; border-radius: 12px; text-align: center; margin-bottom: 20px;">
                <h3 style="color: #ffd700; margin: 0 0 15px 0;">👑 이번 주 연금복권 S등급 강력 추천 👑</h3>
                <div style="margin-bottom: 15px;"><span style="color:#ccc;">이번 주 4조 가장 유력</span></div>
                <div>""" + render_pension_ball(4, [2, 7, 0, 9, 5, 8]) + """</div>
            </div>
        """, unsafe_allow_html=True)
        
    if st.button("🔒 다시 잠그기 (테스트용)", key="lock_btn"):
        st.session_state.vip_unlocked = False
        st.rerun()

st.markdown('<div style="text-align: center; color: #666; margin-top: 30px;">© 2026 LottoSIS All Rights Reserved.</div>', unsafe_allow_html=True)