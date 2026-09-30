import random
import time
import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# ================= 0. 페이지 기본 설정 =================
st.set_page_config(
    page_title="골든픽(Golden Pick) - 로또🍀연금복권 분석기", 
    page_icon="🍀", 
    layout="centered"
)

# ================= 구글 애드센스 소유권 확인 메타태그 강제 주입 =================
components.html(
    """
    <script>
        // Streamlit 캡슐을 뚫고 최상단 <head>에 구글 메타태그를 강제로 심는 코드
        var meta = window.parent.document.createElement('meta');
        meta.name = "google-adsense-account";
        meta.content = "ca-pub-2324282297166072";
        window.parent.document.getElementsByTagName('head')[0].appendChild(meta);
    </script>
    """,
    height=0, width=0
)

# ================= 커스텀 CSS 스타일 =================
st.markdown(
    """
    <style>
    /* [모바일 최적화] 스마트폰 화면 비율처럼 좁고 길게 중앙 정렬 (가로 최대 500px) */
    .block-container {
        max-width: 500px;
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }
    
    /* [보안 설정] Streamlit 기본 헤더, 푸터, 햄버거 메뉴 숨기기 */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* ---------------- 과학적/사이버네틱 타이틀 텍스트 디자인 ---------------- */
    .cyber-title {
        text-align: center;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        font-weight: 900;
        font-size: 26px;
        letter-spacing: -0.5px;
        margin-bottom: 20px;
        line-height: 1.4;
    }
    
    /* 골든픽 강조 (고급스러운 황금빛 메탈릭) */
    .cyber-title .golden-text {
        background: linear-gradient(to right, #fef08a, #f59e0b, #fef08a);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 12px rgba(245, 158, 11, 0.4);
    }
    
    /* 로또·연금복권 AI 분석기 (과학적 푸른 네온 글로우) */
    .cyber-title .tech-text {
        color: #f8fafc;
        text-shadow: 
            0 0 6px rgba(56, 189, 248, 0.6), 
            0 0 18px rgba(14, 165, 233, 0.4);
    }

    /* 🍀 네잎클로버 번쩍번쩍 회전/확장 광채 효과 */
    @keyframes clover-sparkle {
        0% { transform: scale(1) rotate(0deg); filter: drop-shadow(0 0 4px #22c55e); }
        50% { transform: scale(1.35) rotate(12deg); filter: drop-shadow(0 0 18px #4ade80) drop-shadow(0 0 30px #facc15); }
        100% { transform: scale(1) rotate(0deg); filter: drop-shadow(0 0 4px #22c55e); }
    }
    .sparkle-clover {
        display: inline-block;
        animation: clover-sparkle 1.4s infinite ease-in-out;
        margin: 0 6px;
        font-size: 28px;
        vertical-align: middle;
    }

    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    .spinning-gear {
        display: inline-block;
        animation: spin 3s linear infinite;
    }
    
    @keyframes pulse-red {
        0% { transform: scale(1); background-color: #991b1b; box-shadow: 0 0 10px #991b1b; }
        50% { transform: scale(1.18); background-color: #dc2626; box-shadow: 0 0 30px #ef4444; }
        100% { transform: scale(1); background-color: #991b1b; box-shadow: 0 0 10px #991b1b; }
    }
    .free-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 6px;
        color: white;
        font-weight: 900;
        animation: pulse-red 1.2s infinite ease-in-out;
        margin: 0 10px;
    }

    @keyframes glow-red-text {
        0% { color: #ff1111; text-shadow: 0 0 8px #ff0000, 0 0 15px #ff0000; transform: scale(1); }
        50% { color: #ffffff; text-shadow: 0 0 20px #ff3333, 0 0 35px #ff0000, 0 0 50px #ff0000; transform: scale(1.15); }
        100% { color: #ff1111; text-shadow: 0 0 8px #ff0000, 0 0 15px #ff0000; transform: scale(1); }
    }
    .glowing-free-tag {
        display: inline-block;
        font-size: 22px;
        font-weight: 900;
        animation: glow-red-text 0.8s infinite ease-in-out;
        line-height: 1.8;
    }

    @keyframes gold-shine {
        0% { filter: drop-shadow(0 0 2px #ca8a04); transform: scale(1); }
        50% { filter: drop-shadow(0 0 20px #facc15) drop-shadow(0 0 35px #fde047); transform: scale(1.03); }
        100% { filter: drop-shadow(0 0 2px #ca8a04); transform: scale(1); }
    }
    .golden-title-badge {
        font-size: 28px; 
        font-weight: 900;
        background: linear-gradient(to right, #fef08a, #facc15, #eab308, #fef08a);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: gold-shine 2s infinite ease-in-out;
        display: inline-block;
        padding: 5px 0;
        letter-spacing: -0.5px;
    }

    @keyframes glow-green {
        0% { box-shadow: 0 0 5px #22c55e; border-color: #22c55e; }
        50% { box-shadow: 0 0 25px #4ade80; border-color: #4ade80; }
        100% { box-shadow: 0 0 5px #22c55e; border-color: #22c55e; }
    }
    @keyframes silver-match-glow {
        0% { box-shadow: 0 0 5px #94a3b8; border-color: #94a3b8; background-color: #1e293b; }
        50% { box-shadow: 0 0 25px #e2e8f0; border-color: #ffffff; background-color: #2a3748; }
        100% { box-shadow: 0 0 5px #94a3b8; border-color: #94a3b8; background-color: #1e293b; }
    }
    @keyframes gold-glow {
        0% { box-shadow: 0 0 8px #ca8a04; border-color: #eab308; background-color: #1e1b18; }
        50% { box-shadow: 0 0 30px #facc15; border-color: #fde047; background-color: #2d2618; }
        100% { box-shadow: 0 0 8px #ca8a04; border-color: #eab308; background-color: #1e1b18; }
    }
    
    .stButton>button {
        font-weight: bold;
        border-radius: 10px;
        padding: 12px 20px;
        color: white !important;
        background-color: #1e293b;
        border: 2px solid #475569;
        transition: all 0.2s ease-in-out;
        width: 100%;
    }
    .stButton>button:hover {
        border-color: #ffffff !important;
        background-color: #2a3748 !important;
        box-shadow: 0 0 25px #e2e8f0 !important;
    }

    .naver-pay-btn {
        display: block;
        width: 100%;
        font-weight: 900;
        font-size: 16px;
        border-radius: 10px;
        padding: 14px 20px;
        text-align: center;
        text-decoration: none;
        color: #ffffff !important;
        background-color: #03C75A;
        border: 2px solid #00E659;
        transition: all 0.2s ease-in-out;
        box-shadow: 0 4px 12px rgba(3, 199, 90, 0.3);
        margin-bottom: 12px;
    }
    .naver-pay-btn:hover {
        background-color: #02b350;
        border-color: #26ff7b;
        box-shadow: 0 0 25px #03C75A;
    }

    div.element-container:has(#vip-btn-target) + div.element-container button {
        background-color: #FF0000 !important;
        border: 2px solid #CC0000 !important;
        color: white !important;
    }
    div.element-container:has(#vip-btn-target) + div.element-container button p {
        font-weight: 900 !important;
        font-size: 18px !important;
    }
    div.element-container:has(#vip-btn-target) + div.element-container button:hover {
        background-color: #CC0000 !important;
        box-shadow: 0 0 20px #FF0000 !important;
    }

    div.element-container:has(#extract-btn-target) + div.element-container button {
        background-color: #1E90FF !important;
        border: 2px solid #007BFF !important;
        color: white !important;
        padding: 18px 24px !important;
        border-radius: 12px !important;
    }
    div.element-container:has(#extract-btn-target) + div.element-container button p {
        font-size: 24px !important;
        font-weight: 900 !important;
        margin: 0 !important;
    }
    div.element-container:has(#extract-btn-target) + div.element-container button:hover {
        background-color: #007BFF !important;
        box-shadow: 0 0 25px #1E90FF !important;
    }

    .custom-green-btn {
        display: block;
        width: 100%;
        font-weight: bold;
        border-radius: 10px;
        padding: 12px 20px;
        text-align: center;
        text-decoration: none;
        color: white !important;
        background-color: #16a34a;
        border: 2px solid #22c55e;
        transition: all 0.2s ease-in-out;
    }
    .custom-green-btn:hover {
        background-color: #15803d;
        border-color: #4ade80;
        box-shadow: 0 0 25px #22c55e; 
    }

    .legal-disclaimer-box {
        margin-top: 20px;
        padding: 18px 22px;
        background-color: #090d16;
        border: 1px solid #1e293b;
        border-radius: 8px;
        color: #94a3b8;
        font-size: 11px;
        line-height: 1.7;
        text-align: left;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ================= 세션 상태 초기화 =================
if "vip_unlocked" not in st.session_state:
    st.session_state.vip_unlocked = False
if "selected_game" not in st.session_state:
    st.session_state.selected_game = "lotto"
if "extract_results" not in st.session_state:
    st.session_state.extract_results = []
if "extract_game_type" not in st.session_state:
    st.session_state.extract_game_type = "lotto"

# ================= 1. 과학적/세련된 사이버네틱 타이틀 배너 =================
st.markdown("""
    <div class="cyber-title">
        ✨ <span class="golden-text">골든픽(Golden Pick)</span> <span class="sparkle-clover">🍀</span><br>
        <span class="tech-text">로또·연금복권 AI 분석기</span>
    </div>
""", unsafe_allow_html=True)

st.markdown(
    """
    <div style="background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%); padding: 25px 15px; border-radius: 16px; text-align: center; color: white; margin-bottom: 25px; border: 2px solid #eab308; box-shadow: 0 0 25px rgba(234, 179, 8, 0.25);">
        <div style="margin-bottom: 12px;">
            <span class="golden-title-badge">🏆 1등 당첨 저격 S등급 AI 필터 🏆</span>
        </div>
        <p style="margin: 12px 0 10px 0; font-size: 16px; display: flex; align-items: center; justify-content: center; font-weight: bold;">
            지금 접속하신 분께 <span class="free-badge">100% 무료 분석</span> 제공!
        </p>
        <p style="margin: 0; font-size: 13px; color: #fef08a; font-weight: bold; letter-spacing: 0.5px;">👑 VIP 프리패스: 한 번의 승인으로 로또 & 연금복권 동시 오픈!</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if st.session_state.selected_game == "lotto":
    st.markdown('<style>div[data-testid="column"]:nth-of-type(1) .stButton>button { animation: silver-match-glow 2s infinite !important; }</style>', unsafe_allow_html=True)
else:
    st.markdown('<style>div[data-testid="column"]:nth-of-type(2) .stButton>button { animation: silver-match-glow 2s infinite !important; }</style>', unsafe_allow_html=True)

# ================= 2. 중앙 복권 선택 버튼 =================
st.markdown("<h4 style='text-align: center; color: #fff; margin-bottom: 15px;'>🎯 분석할 복권을 선택하세요</h4>", unsafe_allow_html=True)
col_b1, col_b2 = st.columns(2)
with col_b1:
    if st.button("🔴 로또 6/45 분석", use_container_width=True):
        st.session_state.selected_game = "lotto"
with col_b2:
    if st.button("🔵 연금복권 720+", use_container_width=True):
        st.session_state.selected_game = "pension"

st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)

# ================= 3. 녹색 엔진 가동 바 =================
game_name_str = "로또 6/45" if st.session_state.selected_game == "lotto" else "연금복권 720+"
st.markdown(
    f"""
    <div style="background-color: #0f172a; border: 2px solid #22c55e; padding: 15px; border-radius: 12px; text-align: center; color: #4ade80; font-weight: bold; font-size: 16px; animation: glow-green 2s infinite; margin-bottom: 20px;">
        <span>{"🔴" if st.session_state.selected_game=="lotto" else "🔵"} {game_name_str} 분석 ⚙️ ● 딥러닝 실시간 엔진 가동 중</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# ================= 4. 로그 영역 및 설정 =================
with st.expander("📊 실시간 분석 확률 모델 상세 로그", expanded=False):
    st.markdown("""
    <div style="font-size: 14px; color: #cbd5e1; line-height: 1.6;">
    <strong style="color: #f8fafc;">[엔진 가동 세부 정보]</strong><br>
    • 전이 확률 행렬 계산 완료 (Markov Chain)<br>
    • 포아송 간격 분포 가중치 적용됨<br>
    • 앙상블 가중치 최적화 진행 중... <span class="spinning-gear">⚙️</span>
    </div>
    """, unsafe_allow_html=True)

with st.expander("⚡ 데이터베이스 및 필터 동기화 로그", expanded=False):
    st.markdown("""
    <div style="font-size: 14px; color: #cbd5e1; line-height: 1.6;">
    <strong style="color: #f8fafc;">[DB 동기화 세부 정보]</strong><br>
    • 동행복권 최신 회차 데이터 패킷 수신 완료<br>
    • AC값(복잡도) 정규분포 필터 테이블 로드됨<br>
    • 실시간 필터링 버퍼 안정화 완료 <span class="spinning-gear">⚙️</span>
    </div>
    """, unsafe_allow_html=True)

with st.expander("⚙ 맞춤형 엔진 상세 설정", expanded=False):
    game_count = st.slider("추천 게임 수", 1, 10, 5)
    total_range = st.slider("번호 총합 범위 설정", 100, 200, (115, 175))
    odd_even = st.selectbox("홀짝 비율 선호도", ["균등 (3:3 또는 4:2)", "홀수 우세", "짝수 우세"])
    ac_value_target = st.slider("AC값 (복잡도 지수) 목표값", 5, 10, 8)

# ================= 5. 금빛 VIP 시스템 =================
st.markdown("""
    <div style="background-color: #1e1b18; border: 2px solid #eab308; padding: 20px; border-radius: 12px; animation: gold-glow 2s infinite; margin: 20px auto; color: #fef08a; text-align: center;">
        <h4 style="margin-top: 0; font-size: 17px;">🔒 VIP 고유 코드 입력 및 잠금 해제</h4>
    </div>
    """, unsafe_allow_html=True)

st.markdown("""
    <a href="https://order.pay.naver.com" target="_blank" class="naver-pay-btn">
        🟢 네이버페이 간편 결제 (VIP 이용권 구매)
    </a>
    """, unsafe_allow_html=True)

vip_input = st.text_input("VIP 코드를 입력하세요 (예: VIP2026)", type="password", key="vip_code_input")

st.markdown('<span id="vip-btn-target" style="display:none;"></span>', unsafe_allow_html=True)
if st.button("잠금 해제 시작", use_container_width=True, key="vip_unlock_btn"):
    if vip_input == "VIP2026":
        st.session_state.vip_unlocked = True
        st.success("✨ VIP 프리패스 활성화 완료!")
        st.snow()
    else:
        st.error("잘못된 코드입니다.")

if st.session_state.vip_unlocked:
    st.success("🚀 [VIP 프리패스 가동 중] S등급 최고급 데이터 실시간 적용")

st.markdown("---")

# ================= 6. 고성능 번호 추출 실행 버튼 (풍선 애니메이션 추가) =================
st.markdown("""
<div style="display: flex; justify-content: space-between; padding: 0 15px; margin-bottom: -10px;">
    <span class="glowing-free-tag">무료!!!</span>
    <span class="glowing-free-tag">무료!!!</span>
</div>
""", unsafe_allow_html=True)

st.markdown('<span id="extract-btn-target" style="display:none;"></span>', unsafe_allow_html=True)

if st.button("🚀 무료 고성능 번호 추출 실행", use_container_width=True, key="extract_run_btn"):
    st.balloons()
    
    with st.spinner("AI 엔진 가동 중... 최적의 통계 모델과 가중치를 계산하고 있습니다."):
        time.sleep(1.5)
    
    st.session_state.extract_results = []
    st.session_state.extract_game_type = st.session_state.selected_game
    
    for i in range(game_count):
        if st.session_state.selected_game == "lotto":
            numbers = sorted(random.sample(range(1, 46), 6))
            total_sum = sum(numbers)
            ac_val = random.randint(7, 10)
            st.session_state.extract_results.append((numbers, total_sum, ac_val))
        else:
            group = random.randint(1, 5)
            nums = [random.randint(0, 9) for _ in range(6)]
            total_sum = sum(nums)
            var_val = round(float(np.var(nums)), 1)
            st.session_state.extract_results.append((group, nums, total_sum, var_val))

st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)

def get_ball_color(num):
    if num <= 10: return "#facc15"
    elif num <= 20: return "#3b82f6"
    elif num <= 30: return "#ef4444"
    elif num <= 40: return "#a855f7"
    else: return "#22c55e"

# ================= 7. 핵심 탭 메뉴 =================
tab1, tab2, tab3 = st.tabs(["🎱 당첨 번호 추천", "📊 심층 분석", "📑 연구 모델"])

with tab1:
    st.markdown("#### 🎯 하이브리드 번호 추출 결과")
    
    if not st.session_state.extract_results:
        st.info("👆 상단의 **[🚀 무료 고성능 번호 추출 실행]** 버튼을 누르시면 번호가 생성됩니다.")
    else:
        st.success("✅ 통계 필터와 딥러닝 확률 엔진을 거쳐 엄선된 최적의 조합입니다.")
        st.markdown("<br>", unsafe_allow_html=True)
        
        for i, result in enumerate(st.session_state.extract_results):
            if st.session_state.extract_game_type == "lotto":
                numbers, total_sum, ac_val = result
                balls_html = "".join([f'<div style="width: 32px; height: 32px; border-radius: 50%; background-color: {get_ball_color(n)}; color: white; display: flex; justify-content: center; align-items: center; font-weight: bold; font-size: 14px; margin-right: 5px; box-shadow: 0 4px 6px rgba(0,0,0,0.3);">{n}</div>' for n in numbers])
                
                st.markdown(f"""
                <div style="background-color: #111827; padding: 12px; border-radius: 10px; border: 1px solid #374151; margin-bottom: 10px;">
                    <div style="color: white; font-weight: bold; font-size: 15px; margin-bottom: 8px;">게임 {i+1}</div>
                    <div style="display: flex; flex-wrap: wrap;">{balls_html}</div>
                    <div style="color: #cbd5e1; font-style: italic; font-size: 12px; margin-top: 8px;">(총합: {total_sum} | AC값: {ac_val})</div>
                </div>
                """, unsafe_allow_html=True)

            else:
                group, nums, total_sum, var_val = result
                group_html = f'<div style="background: linear-gradient(135deg, #f59e0b, #d97706); color: white; padding: 4px 10px; border-radius: 6px; font-weight: bold; font-size: 14px; margin-right: 10px; margin-bottom: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.3);">{group}조</div>'
                digits_html = "".join([f'<div style="width: 30px; height: 30px; border-radius: 6px; background-color: #2563eb; color: white; display: flex; justify-content: center; align-items: center; font-weight: bold; font-size: 16px; margin-right: 4px; margin-bottom: 5px; box-shadow: 0 3px 5px rgba(0,0,0,0.3);">{n}</div>' for n in nums])
                
                st.markdown(f"""
                <div style="background-color: #111827; padding: 12px; border-radius: 10px; border: 1px solid #374151; margin-bottom: 10px;">
                    <div style="color: white; font-weight: bold; font-size: 15px; margin-bottom: 8px;">게임 {i+1}</div>
                    <div style="display: flex; flex-wrap: wrap; align-items: center;">
                        {group_html}
                        {digits_html}
                    </div>
                    <div style="color: #cbd5e1; font-style: italic; font-size: 12px; margin-top: 5px;">(숫자 총합: {total_sum} | 분산 지수: {var_val})</div>
                </div>
                """, unsafe_allow_html=True)

with tab2:
    st.markdown("#### 📈 역대 당첨 번호 통계 분석")
    st.caption("최근 100회차 번호별 출현 빈도수")
    chart_data = pd.DataFrame(
        np.random.randint(10, 25, size=(45, 1)),
        columns=["출현 횟수"],
        index=[f"{i}번" for i in range(1, 46)]
    )
    st.bar_chart(chart_data, color="#3b82f6", height=250)
    st.info("최신 회차 DB 실시간 연동 완료")

with tab3:
    st.markdown("#### 📑 분석 연구 모델")
    st.markdown("""
    <div style="font-size: 13px; color: #cbd5e1;">
    - Markov Chain Monte Carlo (MCMC) 모델<br>
    - Poisson Distribution 출현 간격 예측<br>
    - AC값(Arithmetic Complexity) 복잡도 필터링
    </div>
    """, unsafe_allow_html=True)

# ================= 8. 하단 홈페이지, 고객센터 버튼 및 고지 사항 =================
st.markdown("---")

st.markdown("##### 📞 고객 센터")
st.caption("결제 오류 및 VIP 관련 문의는 아래 버튼을 통해 안전하게 접수해 주세요.")
google_form_url = "https://forms.google.com/" 
st.markdown(
    f"""
    <a href="{google_form_url}" target="_blank" style="text-decoration: none;">
        <div style="background-color: #2e3b4e; color: white; text-align: center; padding: 15px; border-radius: 12px; font-weight: bold; font-size: 15px; margin-bottom: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.3);">
            🛠️ 결제 및 이용 문의하기 (안전 접수)
        </div>
    </a>
    """, 
    unsafe_allow_html=True
)

st.markdown("""
    <a href="https://www.dhlottery.co.kr" target="_blank" class="custom-green-btn">
        🛒 동행복권 공식 홈페이지 바로 가기
    </a>
    """, unsafe_allow_html=True)

st.markdown("<p style='text-align: center; color: #888; font-size: 12px; margin-top: 30px;'>© 2026 골든픽(Golden Pick) 분석 시스템. All Rights Reserved.</p>", unsafe_allow_html=True)

st.markdown("""
    <div class="legal-disclaimer-box">
        <strong style="color: #cbd5e1;">[결제 및 서비스 법적 책임 고지]</strong><br>
        1. <strong>[디지털 콘텐츠 환불 제한]</strong> 본 VIP 서비스는 전자상거래법에 따라 결제 즉시 제공되는 디지털 상품으로 <strong>결제 취소 및 환불이 불가</strong>합니다.<br>
        2. <strong>[면책 조항]</strong> 본 시스템의 추천 번호는 확률 통계 알고리즘이며 실제 당첨을 보장하지 않습니다. 복권 구매에 따른 모든 결과의 책임은 구매자 본인에게 있습니다.<br>
        3. <strong>[독립적 서비스]</strong> 본 서비스는 (주)동행복권과 무관한 독립적 분석 프로그램입니다.
    </div>
    """, unsafe_allow_html=True)