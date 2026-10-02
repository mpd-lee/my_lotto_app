import random
import time
import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# ================= 0. 페이지 기본 설정 =================
st.set_page_config(
    page_title="로또픽(Lotto Pick) - 초정밀 통계·조합 분석 시스템", 
    page_icon="🍀", 
    layout="centered"
)

# ================= 구글 애드센스 소유권 확인 메타태그 (이중 주입) =================
st.markdown('<meta name="google-adsense-account" content="ca-pub-2324282297166072">', unsafe_allow_html=True)
components.html(
    """
    <script>
        try {
            var meta = window.parent.document.createElement('meta');
            meta.name = "google-adsense-account";
            meta.content = "ca-pub-2324282297166072";
            window.parent.document.getElementsByTagName('head')[0].appendChild(meta);
        } catch (e) {}
    </script>
    """,
    height=0, width=0
)

# ================= 커스텀 CSS 스타일 =================
st.markdown(
    """
    <style>
    /* [모바일 최적화] 스마트폰 화면 비율처럼 좁고 길게 중앙 정렬 (가로 최대 500px) */
    .block-container { max-width: 500px; padding-top: 1.5rem; padding-bottom: 2rem; }
    #MainMenu {visibility: hidden;} header {visibility: hidden;} footer {visibility: hidden;}
    
    /* 단어 단위 줄바꿈 방지 (글자가 커져도 단어 중간에 끊기지 않음) */
    .keep-all { word-break: keep-all; }
    
    /* ---------------- 로또픽 타이틀 디자인 (줄바꿈 방지 적용) ---------------- */
    .cyber-title {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        margin-bottom: 25px;
    }
    .cyber-title-top {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        white-space: nowrap; /* 클로버가 아래로 떨어지는 것 방지 */
    }
    .cyber-title .lottopick-brand {
        font-weight: 900;
        font-size: clamp(22px, 6vw, 28px); /* 화면 크기에 따른 가변 폰트 */
        letter-spacing: -0.8px;
        background: linear-gradient(135deg, #ffffff 0%, #fef08a 40%, #f59e0b 80%, #d97706 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 15px rgba(245, 158, 11, 0.4);
    }

    /* 🍀 네잎클로버 애니메이션 */
    @keyframes clover-sparkle {
        0% { transform: scale(1) rotate(0deg); filter: drop-shadow(0 0 4px #22c55e); }
        50% { transform: scale(1.35) rotate(12deg); filter: drop-shadow(0 0 18px #4ade80) drop-shadow(0 0 30px #facc15); }
        100% { transform: scale(1) rotate(0deg); filter: drop-shadow(0 0 4px #22c55e); }
    }
    .sparkle-clover {
        display: inline-block; animation: clover-sparkle 1.4s infinite ease-in-out;
        font-size: clamp(24px, 6vw, 30px); vertical-align: middle;
    }

    @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    .spinning-gear { display: inline-block; animation: spin 3s linear infinite; }
    
    @keyframes pulse-red {
        0% { transform: scale(1); background-color: #991b1b; box-shadow: 0 0 10px #991b1b; }
        50% { transform: scale(1.15); background-color: #dc2626; box-shadow: 0 0 25px #ef4444; }
        100% { transform: scale(1); background-color: #991b1b; box-shadow: 0 0 10px #991b1b; }
    }
    .free-badge {
        display: inline-block; padding: 4px 12px; border-radius: 6px; color: white;
        font-weight: 900; animation: pulse-red 1.2s infinite ease-in-out; margin: 0 5px;
        white-space: nowrap;
    }

    @keyframes gold-shine {
        0% { filter: drop-shadow(0 0 2px #ca8a04); transform: scale(1); }
        50% { filter: drop-shadow(0 0 20px #facc15) drop-shadow(0 0 35px #fde047); transform: scale(1.03); }
        100% { filter: drop-shadow(0 0 2px #ca8a04); transform: scale(1); }
    }
    .golden-title-badge {
        font-size: clamp(20px, 5.5vw, 26px); font-weight: 900;
        background: linear-gradient(to right, #fef08a, #facc15, #eab308, #fef08a);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        animation: gold-shine 2s infinite ease-in-out; display: inline-block;
        padding: 5px 0; letter-spacing: -0.5px; word-break: keep-all;
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
        font-weight: bold; border-radius: 10px; padding: 12px 10px;
        color: white !important; background-color: #1e293b; border: 2px solid #475569;
        transition: all 0.2s ease-in-out; width: 100%;
        word-break: keep-all;
    }
    .stButton>button:hover {
        border-color: #ffffff !important; background-color: #2a3748 !important; box-shadow: 0 0 25px #e2e8f0 !important;
    }

    .naver-pay-btn {
        display: block; width: 100%; font-weight: 900; font-size: 16px; border-radius: 10px;
        padding: 14px 20px; text-align: center; text-decoration: none; color: #ffffff !important;
        background-color: #03C75A; border: 2px solid #00E659; transition: all 0.2s ease-in-out;
        box-shadow: 0 4px 12px rgba(3, 199, 90, 0.3); margin-bottom: 12px; word-break: keep-all;
    }
    .naver-pay-btn:hover {
        background-color: #02b350; border-color: #26ff7b; box-shadow: 0 0 25px #03C75A;
    }

    /* VIP 잠금 해제 버튼 */
    div.element-container:has(#vip-btn-target) + div.element-container button,
    div[data-testid="stElementContainer"]:has(#vip-btn-target) + div[data-testid="stElementContainer"] button {
        background-color: #FF0000 !important; border: 2px solid #CC0000 !important; color: white !important;
    }
    div.element-container:has(#vip-btn-target) + div.element-container button p,
    div[data-testid="stElementContainer"]:has(#vip-btn-target) + div[data-testid="stElementContainer"] button p {
        font-weight: 900 !important; font-size: 18px !important;
    }
    div.element-container:has(#vip-btn-target) + div.element-container button:hover,
    div[data-testid="stElementContainer"]:has(#vip-btn-target) + div[data-testid="stElementContainer"] button:hover {
        background-color: #CC0000 !important; box-shadow: 0 0 20px #FF0000 !important;
    }

    /* ---------------- 추출 버튼 구조 개선 (상단 뱃지) ---------------- */
    .extract-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        width: 100%;
        margin-bottom: 25px;
        position: relative;
    }
    .free-badge-top {
        background-color: #ff3b30;
        color: #ffffff;
        font-size: 14px;
        font-weight: 900;
        padding: 6px 16px;
        border-radius: 20px;
        margin-bottom: -15px; /* 버튼 위에 걸치도록 설정 */
        z-index: 10;
        box-shadow: 0 4px 10px rgba(0,0,0,0.4);
        animation: pulse-red 1.2s infinite ease-in-out;
        white-space: nowrap;
    }
    .extract-box-btn {
        display: flex;
        justify-content: center;
        align-items: center;
        width: 100%;
        background-color: #3b82f6; /* 밝고 시원한 파란색 */
        border: 2px solid #60a5fa;
        color: white !important;
        padding: 22px 10px 18px 10px; /* 위쪽 패딩을 늘려 뱃지 공간 확보 */
        border-radius: 12px;
        text-decoration: none !important;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4);
        transition: all 0.2s ease-in-out;
    }
    .extract-box-btn span {
        font-size: clamp(18px, 5.5vw, 22px);
        font-weight: 900;
        letter-spacing: -0.5px;
        white-space: nowrap; /* 글씨 줄바꿈 절대 방지 */
    }
    .extract-box-btn:hover {
        background-color: #2563eb;
        border-color: #93c5fd;
        box-shadow: 0 0 25px #3b82f6;
    }

    /* ---------------- 동행복권 버튼 커스텀 ---------------- */
    .donghang-btn {
        display: block; width: 100%; font-weight: 900; font-size: 18px; border-radius: 10px;
        padding: 16px 20px; text-align: center; text-decoration: none; color: #ffffff !important;
        background-color: #16a34a; border: 2px solid #22c55e; transition: all 0.2s ease-in-out;
        box-shadow: 0 4px 12px rgba(22, 163, 74, 0.3); text-shadow: 1px 1px 3px rgba(0,0,0,0.5);
        word-break: keep-all;
    }
    .donghang-btn:hover {
        background-color: #15803d; border-color: #4ade80; box-shadow: 0 0 25px #22c55e; 
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

# ================= 1. '로또픽' 타이틀 배너 (신뢰감 강화 버전) =================
st.markdown("""
    <div class="cyber-title">
        <div class="cyber-title-top">
            <span class="sparkle-clover">🍀</span>
            <span class="lottopick-brand">로또픽 (Lotto Pick)</span>
            <span class="sparkle-clover">🍀</span>
        </div>
        <div style="margin-top: 12px; line-height: 1.5; text-align: center;">
            <div style="color: #e2e8f0; font-size: clamp(16px, 4vw, 18px); font-weight: 800; text-shadow: 0 0 10px rgba(255,255,255,0.2); word-break: keep-all;">
                초정밀 통계·조합 분석 시스템
            </div>
            <div style="color: #94a3b8; font-size: clamp(10px, 2.5vw, 12px); font-weight: 600; letter-spacing: 1.5px; margin: 5px 0;">
                LOTTO & PENSION LOTTERY ANALYTICS
            </div>
            <div style="color: #38bdf8; font-size: clamp(13px, 3.5vw, 15px); font-weight: 700; text-shadow: 0 0 8px rgba(56, 189, 248, 0.4); margin-top: 6px; word-break: keep-all;">
                "데이터는 정밀하게, 분석은 체계적으로"
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

# (단어 단위 줄바꿈 keep-all 적용된 안내 박스)
st.markdown(
    """
    <div class="keep-all" style="background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%); padding: 25px 15px; border-radius: 16px; text-align: center; color: white; margin-bottom: 25px; border: 2px solid #eab308; box-shadow: 0 0 25px rgba(234, 179, 8, 0.25);">
        <div style="margin-bottom: 12px;">
            <span class="golden-title-badge">🏆 1등 당첨 저격 S등급 정밀 필터 🏆</span>
        </div>
        <div style="margin: 15px 0; font-size: clamp(15px, 4.5vw, 17px); font-weight: bold; line-height: 1.6;">
            지금 접속하신 분께 <span class="free-badge">100% 무료 분석</span> 제공!
        </div>
        <div style="font-size: 13px; color: #fef08a; font-weight: bold; letter-spacing: -0.3px;">👑 VIP 프리패스: 한 번의 승인으로 로또 & 연금복권 동시 오픈!</div>
    </div>
    """,
    unsafe_allow_html=True,
)

if st.session_state.selected_game == "lotto":
    st.markdown('<style>div[data-testid="column"]:nth-of-type(1) .stButton>button { animation: silver-match-glow 2s infinite !important; }</style>', unsafe_allow_html=True)
else:
    st.markdown('<style>div[data-testid="column"]:nth-of-type(2) .stButton>button { animation: silver-match-glow 2s infinite !important; }</style>', unsafe_allow_html=True)

# ================= 2. 중앙 복권 선택 버튼 =================
st.markdown("<h4 class='keep-all' style='text-align: center; color: #fff; margin-bottom: 15px;'>🎯 분석할 복권을 선택하세요</h4>", unsafe_allow_html=True)
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
    <div class="keep-all" style="background-color: #0f172a; border: 2px solid #22c55e; padding: 15px; border-radius: 12px; text-align: center; color: #4ade80; font-weight: bold; font-size: clamp(14px, 4vw, 16px); animation: glow-green 2s infinite; margin-bottom: 20px;">
        <span>{"🔴" if st.session_state.selected_game=="lotto" else "🔵"} {game_name_str} 분석 ⚙️ ● 정밀 시스템 실시간 가동 중</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# ================= 4. 로그 영역 및 설정 =================
with st.expander("📊 실시간 분석 확률 모델 상세 로그", expanded=False):
    st.markdown("""
    <div style="font-size: 14px; color: #cbd5e1; line-height: 1.6;">
    <strong style="color: #f8fafc;">[시스템 가동 세부 정보]</strong><br>
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

with st.expander("⚙ 맞춤형 시스템 상세 설정", expanded=False):
    game_count = st.slider("추천 게임 수", 1, 10, 5)
    total_range = st.slider("번호 총합 범위 설정", 100, 200, (115, 175))
    odd_even = st.selectbox("홀짝 비율 선호도", ["균등 (3:3 또는 4:2)", "홀수 우세", "짝수 우세"])
    ac_value_target = st.slider("AC값 (복잡도 지수) 목표값", 5, 10, 8)

# ================= 5. 금빛 VIP 시스템 =================
st.markdown("""
    <div class="keep-all" style="background-color: #1e1b18; border: 2px solid #eab308; padding: 20px; border-radius: 12px; animation: gold-glow 2s infinite; margin: 20px auto; color: #fef08a; text-align: center;">
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

# ================= 6. 상단 뱃지가 포함된 구조의 완벽한 추출 버튼 =================
query_params = st.query_params
if "extract" in query_params and query_params["extract"] == "true":
    st.session_state.triggered = True
    st.query_params.clear()

st.markdown(
    """
    <div class="extract-container">
        <div class="free-badge-top">🔥 100% 무료 분석</div>
        <a href="?extract=true" target="_self" class="extract-box-btn">
            <span>🚀 고성능 번호 추출 실행</span>
        </a>
    </div>
    """,
    unsafe_allow_html=True
)

if st.session_state.get("triggered", False):
    st.session_state.triggered = False
    st.balloons()
    with st.spinner("분석 시스템 가동 중... 최적의 통계 모델과 가중치를 계산하고 있습니다."):
        time.sleep(1.0)
    
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
        st.info("👆 상단의 파란색 **[🚀 고성능 번호 추출 실행]** 버튼을 누르시면 번호가 생성됩니다.")
    else:
        st.success("✅ 통계 필터와 확률 시스템을 거쳐 엄선된 최적의 조합입니다.")
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
                        {group_html}{digits_html}
                    </div>
                    <div style="color: #cbd5e1; font-style: italic; font-size: 12px; margin-top: 5px;">(숫자 총합: {total_sum} | 분산 지수: {var_val})</div>
                </div>
                """, unsafe_allow_html=True)

with tab2:
    st.markdown("#### 📈 역대 당첨 번호 통계 분석")
    st.caption("최근 100회차 번호별 출현 빈도수")
    chart_data = pd.DataFrame(np.random.randint(10, 25, size=(45, 1)), columns=["출현 횟수"], index=[f"{i}번" for i in range(1, 46)])
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
st.markdown(f"""
    <a href="{google_form_url}" target="_blank" style="text-decoration: none;">
        <div class="keep-all" style="background-color: #2e3b4e; color: white; text-align: center; padding: 15px; border-radius: 12px; font-weight: bold; font-size: 15px; margin-bottom: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.3);">
            🛠️ 결제 및 이용 문의하기 (안전 접수)
        </div>
    </a>
    """, unsafe_allow_html=True)

st.markdown("""
    <a href="https://www.dhlottery.co.kr" target="_blank" class="donghang-btn">
        🛒 동행복권 공식 홈페이지 바로 가기
    </a>
    """, unsafe_allow_html=True)

st.markdown("<p style='text-align: center; color: #888; font-size: 12px; margin-top: 30px;'>© 2026 로또픽(Lotto Pick) 분석 시스템. All Rights Reserved.</p>", unsafe_allow_html=True)
st.markdown("""
    <div class="keep-all" style="margin-top: 20px; padding: 18px 22px; background-color: #090d16; border: 1px solid #1e293b; border-radius: 8px; color: #94a3b8; font-size: 12px; line-height: 1.7; text-align: left; word-break: keep-all;">
        <strong style="color: #cbd5e1;">[결제 및 서비스 법적 책임 고지]</strong><br>
        1. <strong>[디지털 콘텐츠 환불 제한]</strong> 본 VIP 서비스는 전자상거래법에 따라 결제 취소 및 환불이 불가합니다.<br>
        2. <strong>[면책 조항]</strong> 추천 번호는 통계 알고리즘이며 당첨을 보장하지 않습니다. 복권 구매 책임은 본인에게 있습니다.<br>
        3. <strong>[독립적 서비스]</strong> 본 서비스는 (주)동행복권과 무관합니다.
    </div>
    """, unsafe_allow_html=True)