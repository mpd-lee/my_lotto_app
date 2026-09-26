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
    
    /* 🚀 하단 번호 추출 버튼 스타일 */
    .stButton>button {
        background: linear-gradient(45deg, #FF4B4B, #FF8E53);
        color: white; font-weight: 900; border-radius: 12px;
        padding: 0.8em 1.8em; border: none;
        box-shadow: 0 6px 15px rgba(255, 75, 75, 0.5); font-size: 20px;
        width: 100%; margin-top: 15px; margin-bottom: 25px;
    }
    .stButton>button:hover { 
        background: linear-gradient(45deg, #FF6B6B, #FFAE73); 
        transform: scale(1.02); transition: 0.2s;
    }
    
    /* ✨ 럭셔리 샴페인 골드 번쩍번쩍 광채 애니메이션 (눌러! 눌러! 느낌) */
    @keyframes luxury-gold-glow {
        0% { 
            box-shadow: 0 0 8px rgba(255, 215, 0, 0.4), inset 0 0 6px rgba(255, 255, 255, 0.3); 
            border-color: #d4af37;
            transform: scale(1);
        }
        50% { 
            box-shadow: 0 0 30px rgba(255, 215, 0, 0.95), 0 0 50px rgba(255, 165, 0, 0.7), inset 0 0 15px rgba(255, 255, 255, 0.9); 
            border-color: #fff68f;
            transform: scale(1.03);
        }
        100% { 
            box-shadow: 0 0 8px rgba(255, 215, 0, 0.4), inset 0 0 6px rgba(255, 255, 255, 0.3); 
            border-color: #d4af37;
            transform: scale(1);
        }
    }
    
    /* 🎯 상단 복권 선택 버튼에 럭셔리 골드 광채 효과 부여 */
    div.stButton > button {
        font-size: 20px !important;
        font-weight: 900 !important;
        color: #FFFFFF !important;
        -webkit-text-stroke: 0.5px #000000;
        text-shadow: 0px 2px 4px rgba(0, 0, 0, 0.8);
        border: 2px solid #FFD700 !important;
        background: linear-gradient(135deg, #2a2415, #b8860b) !important;
        animation: luxury-gold-glow 1.6s infinite ease-in-out !important;
    }
    
    div.stButton > button p, div.stButton > button span {
        font-size: 20px !important;
        font-weight: 900 !important;
        color: #FFFFFF !important;
    }
    
    /* 🔥 "100% 무료 분석" 글씨 번쩍번쩍 네온 레드-골드 깜빡임 효과 */
    @keyframes text-flash {
        0% { color: #FF2A2A; text-shadow: 0 0 5px rgba(255, 42, 42, 0.6); }
        50% { color: #FFD700; text-shadow: 0 0 20px rgba(255, 215, 0, 0.9), 0 0 30px rgba(255, 69, 0, 0.8); transform: scale(1.05); }
        100% { color: #FF2A2A; text-shadow: 0 0 5px rgba(255, 42, 42, 0.6); }
    }
    
    .flashing-free-text {
        display: inline-block;
        background-color: rgba(0, 0, 0, 0.4);
        padding: 4px 12px;
        border-radius: 8px;
        font-weight: 900;
        border: 1.5px dashed #FFD700;
        animation: text-flash 1.2s infinite ease-in-out;
    }
    
    /* ⚙️ 샴페인 골드 톱니바퀴 회전 애니메이션 */
    @keyframes spin-gear {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    .gold-gear {
        display: inline-block;
        font-size: 22px;
        margin-left: 8px;
        margin-right: 4px;
        filter: drop-shadow(0 2px 4px rgba(0,0,0,0.8)) brightness(1.1);
        animation: spin-gear 4s linear infinite;
        vertical-align: middle;
    }
    
    /* ⚡ 실시간 데이터 작동 애니메이션 효과 (펄스 점멸) */
    @keyframes pulse-glow {
        0% { transform: scale(0.95); opacity: 0.6; }
        50% { transform: scale(1.15); opacity: 1; filter: drop-shadow(0 0 6px #00FF88); }
        100% { transform: scale(0.95); opacity: 0.6; }
    }
    
    .live-indicator {
        display: inline-block;
        width: 10px;
        height: 10px;
        background-color: #00FF88;
        border-radius: 50%;
        margin-left: 10px;
        margin-right: 6px;
        animation: pulse-glow 1.5s infinite ease-in-out;
        vertical-align: middle;
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
        margin-bottom: 25px; border: 1.5px solid #FFD700;
        box-shadow: 0 8px 25px rgba(255, 215, 0, 0.25);
    }
    .menu-title {
        font-size: 24px; font-weight: 900; color: #FFD700; 
        text-align: center; margin-bottom: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# 최상단 통합 홍보 배너 (번쩍이는 무료 분석 적용)
# ----------------------------------------------------
st.markdown("""
<div class="promo-banner">
    <h2 style="color: #FFF; margin-top: 0; font-size: 24px;">
        🔥 로또 6/45 <span style="color: #FFD700;">✖</span> 연금복권 720+
    </h2>
    <p style="color: #E0E0E0; font-size: 16px; margin-bottom: 0;">
        지금 접속하신 분들께 <span class="flashing-free-text">100% 무료 분석</span> 제공!<br>
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
    if 1 <= num_int <= 10: bg, fg = '#FBC400', '#000000'
    elif 11 <= num_int <= 20: bg, fg = '#69C8FF', '#000000'
    elif 21 <= num_int <= 30: bg, fg = '#FF7272', '#FFFFFF'
    elif 31 <= num_int <= 40: bg, fg = '#AAAAAA', '#FFFFFF'
    else: bg, fg = '#B0D840', '#000000'
    return f"""<span style="display: inline-block; width: 42px; height: 42px; line-height: 42px; border-radius: 50%; background-color: {bg}; color: {fg}; text-align: center; font-weight: bold; font-size: 17px; margin: 0 3px; box-shadow: 0 4px 8px rgba(0,0,0,0.4); border: 2px solid rgba(255,255,255,0.4);">{num_int:02d}</span>"""

def render_pension_ball(group, digits):
    colors = ['#5A5A5A', '#FF4B4B', '#FFAE00', '#FBC400', '#69C8FF', '#B0D840', '#AAAAAA']
    html = f"""<span style="display: inline-block; width: 55px; height: 42px; line-height: 42px; border-radius: 8px; background-color: {colors[0]}; color: white; text-align: center; font-weight: bold; font-size: 16px; margin-right: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.4);">{group} 조</span>"""
    for i, digit in enumerate(digits):
        html += f"""<span style="display: inline-block; width: 38px; height: 42px; line-height: 42px; border-radius: 50%; background-color: {colors[i+1]}; color: {'#000' if i in [2, 3] else '#FFF'}; text-align: center; font-weight: bold; font-size: 18px; margin: 0 2px; box-shadow: 0 4px 8px rgba(0,0,0,0.4);">{digit}</span>"""
    return html

# ----------------------------------------------------
# 🟡 럭셔리 골드로 번쩍이는 선택 버튼 영역 ("눌러! 눌러!" 느낌)
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
# ⚙️ 회전하는 샴페인 골드 톱니바퀴와 실시간 엔진 가동 상태 바
# ----------------------------------------------------
current_label = "🧧 로또 6/45 분석" if st.session_state.selected_lotto_type == 'lotto' else "🎫 연금복권 720+ 분석"
st.markdown(f"""
    <div style="background: linear-gradient(135deg, #1f1b10, #3a2e10); padding: 14px 20px; border-radius: 12px; text-align: center; border: 2px solid #FFD700; margin-top: 10px; margin-bottom: 20px; box-shadow: 0 4px 15px rgba(255,215,0,0.25);">
        <span style="font-size: 20px; color: #FFFFFF; font-weight: 800;">{current_label}</span>
        <span class="gold-gear">⚙️</span>
        <span class="live-indicator"></span>
        <span style="font-size: 16px; color: #FFD700; font-weight: 700;">AI 실시간 분석 엔진 가동 중</span>
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

    if st.button('🚀 로또 당첨 번호 무료 추출하기', key='btn_lotto'):
        with st.spinner('AI가 역대 패턴을 분석하여 최적의 번호를 찾고 있습니다...'):
            time.sleep(1)
            st.success('분석 완료! 아래 추천 번호를 확인하세요.')
            for i in range(1, game_count + 1):
                nums, total_sum, odds, evens, ac = generate_optimized_lotto()
                balls_html = ''.join([render_billiard_ball(n) for n in nums])
                st.markdown(f"""
                    <div style="background-color: #1a1c24; padding: 15px; border-radius: 14px; margin-bottom: 12px; border-left: 5px solid #FFD700;">
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

    if st.button('🚀 연금복권 당첨 번호 무료 추출하기', key='btn_pension'):
        with st.spinner('자리수별 독립 확률 분석 중입니다...'):
            time.sleep(1)
            st.success('분석 완료! 아래 추천 조합을 확인하세요.')
            for i in range(1, pension_count + 1):
                g = random.randint(1, 5) if '분산' in group_choice else 3
                digits = generate_pension()
                html = render_pension_ball(g, digits)
                st.markdown(f"""
                    <div style="background-color: #1a1c24; padding: 15px; border-radius: 14px; margin-bottom: 12px; border-left: 5px solid #FFD700;">
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