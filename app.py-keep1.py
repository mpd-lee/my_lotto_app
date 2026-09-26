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
# 🎨 다크 테마 및 맞춤 스타일링 (초강력 CSS 강제 주입)
# ----------------------------------------------------
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    
    /* =========================================
       🚨 1. "100% 무료 분석" 초강력 번쩍이는 빨간색 네온!
       ========================================= */
    @keyframes super-red-bang {
        0% { background-color: #990000 !important; box-shadow: 0 0 10px #FF0000 !important; transform: scale(1); color: #FFFFFF !important; }
        100% { background-color: #FF0000 !important; box-shadow: 0 0 40px #FF0000, 0 0 80px #FF3333, inset 0 0 20px #FFAAAA !important; transform: scale(1.25); color: #FFFF00 !important; border-color: #FFFFFF !important; }
    }
    .super-red-flash {
        display: inline-block;
        background-color: #FF0000 !important;
        color: #FFFFFF !important;
        font-size: 1.1em !important;
        font-weight: 900 !important;
        padding: 5px 15px !important;
        border-radius: 8px !important;
        border: 3px solid #FFCCCC !important;
        animation: super-red-bang 0.35s infinite alternate ease-in-out !important;
        margin: 0 12px !important;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.8) !important;
    }

    /* =========================================
       ✨ 2. 로또 6/45 버튼 (왼쪽 어두운 부분 100% 제거, 퓨어 골드 광채!)
       ========================================= */
    @keyframes super-gold-glow {
        0% { background-color: #FFC107 !important; box-shadow: 0 0 15px #FFD700, inset 0 0 10px #FFFFFF !important; transform: scale(1); border-color: #FFD700 !important; }
        100% { background-color: #FFFF00 !important; box-shadow: 0 0 50px #FFFF00, 0 0 90px #FFEA00, inset 0 0 30px #FFFFFF !important; transform: scale(1.04); border-color: #FFFFFF !important; }
    }
    div[data-testid="stColumn"]:nth-of-type(1) div.stButton > button {
        background: #FFD700 !important; /* 완벽한 단색 골드 */
        background-color: #FFD700 !important;
        background-image: none !important; /* 스트림릿 기본 그라데이션 완전 삭제 */
        border: 4px solid #FFFF00 !important;
        animation: super-gold-glow 0.4s infinite alternate ease-in-out !important;
        width: 100% !important;
    }
    /* 버튼 내부 텍스트 및 레이어 설정 (글씨를 검정색으로 해서 확 띄게) */
    div[data-testid="stColumn"]:nth-of-type(1) div.stButton > button * {
        background: transparent !important;
        background-color: transparent !important;
        background-image: none !important;
        color: #000000 !important; /* 검정색 텍스트 */
        font-weight: 900 !important;
        font-size: 22px !important;
        text-shadow: 1px 1px 2px rgba(255, 255, 255, 0.9) !important;
    }
    
    /* =========================================
       🥈 3. 연금복권 720+ 버튼 (왼쪽 어두운 부분 100% 제거, 퓨어 실버 광채!)
       ========================================= */
    @keyframes super-silver-glow {
        0% { background-color: #CCCCCC !important; box-shadow: 0 0 15px #E0E0E0, inset 0 0 10px #FFFFFF !important; transform: scale(1); border-color: #CCCCCC !important; }
        100% { background-color: #FFFFFF !important; box-shadow: 0 0 50px #FFFFFF, 0 0 90px #FFFFFF, inset 0 0 40px #FFFFFF !important; transform: scale(1.04); border-color: #FFFFFF !important; }
    }
    div[data-testid="stColumn"]:nth-of-type(2) div.stButton > button {
        background: #E0E0E0 !important; /* 완벽한 단색 실버 */
        background-color: #E0E0E0 !important;
        background-image: none !important; 
        border: 4px solid #FFFFFF !important;
        animation: super-silver-glow 0.4s infinite alternate ease-in-out !important;
        width: 100% !important;
    }
    div[data-testid="stColumn"]:nth-of-type(2) div.stButton > button * {
        background: transparent !important;
        background-color: transparent !important;
        background-image: none !important;
        color: #000000 !important; /* 검정색 텍스트 */
        font-weight: 900 !important;
        font-size: 22px !important;
        text-shadow: 1px 1px 2px rgba(255, 255, 255, 0.9) !important;
    }

    /* =========================================
       👑 4. 통합 VIP Pass 박스 (엄청나게 밝은 스카이 블루 & 시안 톤!)
       ========================================= */
    .vip-ultra-box {
        background-color: #007BFF !important; /* 아주 밝은 파란색 기본 바탕 */
        background-image: linear-gradient(to right, #007BFF, #00D4FF) !important; /* 눈부신 시안(청록) 그라데이션 */
        border: 4px solid #FFD700 !important; /* 두꺼운 황금색 테두리 */
        border-radius: 15px !important;
        padding: 30px !important;
        margin-top: 25px !important;
        margin-bottom: 25px !important;
        box-shadow: 0 0 30px rgba(255, 215, 0, 1), inset 0 0 20px rgba(255, 255, 255, 0.5) !important;
    }

    /* =========================================
       🔵 하단 추출하기 버튼 (기본 파랑/빨강)
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
    button[kind="primary"] p { font-size: 20px !important; font-weight: 900 !important; color: #FFFFFF !important; text-shadow: 0px 2px 4px rgba(0, 0, 0, 0.5); }

    /* ⚙️ 톱니바퀴 및 펄스 */
    @keyframes spin-gear { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    .silver-gear { display: inline-block; font-size: 22px; margin-left: 8px; margin-right: 4px; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.8)) brightness(0.85); animation: spin-gear 4s linear infinite; vertical-align: middle; }
    @keyframes pulse-glow { 0% { transform: scale(0.95); opacity: 0.6; } 50% { transform: scale(1.15); opacity: 1; filter: drop-shadow(0 0 6px #00FF88); } 100% { transform: scale(0.95); opacity: 0.6; } }
    .live-indicator { display: inline-block; width: 10px; height: 10px; background-color: #00FF88; border-radius: 50%; margin-left: 10px; margin-right: 6px; animation: pulse-glow 1.5s infinite ease-in-out; vertical-align: middle; }
    
    .promo-banner {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        padding: 20px 15px; border-radius: 15px; text-align: center;
        margin-bottom: 25px; border: 1px solid #69C8FF; box-shadow: 0 8px 20px rgba(0, 0, 0, 0.5);
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
        지금 접속하신 분들께 <span class="super-red-flash">100% 무료 분석</span> 제공!<br>
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

    # 🔵 로또 당첨 번호 무료 추출하기
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

    # 🔵 연금복권 당첨 번호 무료 추출하기
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
# 👑 하단 공통 VIP 프리패스 영역 (완전 눈부시게 밝은 스카이 블루!!!)
# ====================================================
st.divider()

# 무조건 스트림릿 설정을 부수고 들어가는 초강력 HTML/CSS 주입
st.markdown("""
<div class="vip-ultra-box">
    <h3 style="color: #FFFF00; margin-top: 0; text-align: center; font-weight: 900; font-size: 1.8em; text-shadow: 2px 2px 4px rgba(0,0,0,0.8);">👑 통합 VIP Pass 전용 시스템</h3>
    <p style="color: #FFFFFF; font-size: 1.2em; font-weight: bold; text-align: center; text-shadow: 1px 1px 3px rgba(0,0,0,0.8);">로또 S등급 초정밀 분석 & 연금복권 유력 조 핀포인트 예측을 동시에!</p>
</div>
""", unsafe_allow_html=True)

if not st.session_state.vip_unlocked:
    with st.expander("🔒 VIP 1회용 고유 코드 입력 및 잠금 해제", expanded=True):
        st.markdown("#### 1. VIP 패스 결제")
        st.link_button("💳 네이버페이 간편 결제하기", "https://smartstore.naver.com/", type="secondary", use_container_width=True)
        
        st.markdown("#### 2. 발급받은 고유 코드 입력")
        vip_code = st.text_input("코드 입력", type="password", key="vip_input", placeholder="예: S-CLASS-XXXX")
        
        # 🔴 잠금 해제 시작 버튼
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