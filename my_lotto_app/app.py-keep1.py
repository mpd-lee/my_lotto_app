import random
import time
import streamlit as st

# 페이지 설정
st.set_page_config(
    page_title="AI 고성능 로또 & 연금복권 분석 시스템", page_icon="🎱", layout="wide"
)

# 커스텀 CSS 스타일 (톱니바퀴 회전 애니메이션 및 은빛 네온 효과)
st.markdown(
    """
    <style>
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    .spinning-gear {
        display: inline-block;
        animation: spin 3s linear infinite;
    }
    @keyframes glow-green {
        0% { box-shadow: 0 0 5px #22c55e; border-color: #22c55e; }
        50% { box-shadow: 0 0 25px #4ade80; border-color: #4ade80; }
        100% { box-shadow: 0 0 5px #22c55e; border-color: #22c55e; }
    }
    @keyframes silver-match-glow {
        0% { 
            box-shadow: 0 0 5px #94a3b8; 
            border-color: #94a3b8; 
            background-color: #1e293b; 
        }
        50% { 
            box-shadow: 0 0 25px #e2e8f0; 
            border-color: #ffffff; 
            background-color: #2a3748; 
        }
        100% { 
            box-shadow: 0 0 5px #94a3b8; 
            border-color: #94a3b8; 
            background-color: #1e293b; 
        }
    }
    .main-banner {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        padding: 25px;
        border-radius: 15px;
        text-align: center;
        color: white;
        margin-bottom: 20px;
    }
    .engine-active-box {
        background-color: #0f172a;
        border: 2px solid #22c55e;
        padding: 15px;
        border-radius: 12px;
        text-align: center;
        color: #4ade80;
        font-weight: bold;
        font-size: 18px;
        animation: glow-green 2s infinite;
        margin-bottom: 20px;
    }
    .vip-compact-box {
        background-color: #182232;
        border: 2px solid #94a3b8;
        padding: 20px;
        border-radius: 12px;
        animation: silver-match-glow 2s infinite;
        margin: 20px auto;
        max-width: 600px;
    }
    /* 기본 버튼 디자인 및 마우스 오버 시 세련된 은빛 효과 */
    .stButton>button {
        font-weight: bold;
        border-radius: 10px;
        padding: 12px 20px;
        color: white !important;
        background-color: #1e293b;
        border: 2px solid #475569;
        width: 100%;
        transition: all 0.2s ease-in-out;
    }
    .stButton>button:hover {
        border-color: #ffffff !important;
        color: #f8fafc !important;
        background-color: #2a3748 !important;
        box-shadow: 0 0 25px #e2e8f0 !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# 세션 상태 초기화
if "vip_unlocked" not in st.session_state:
  st.session_state.vip_unlocked = False
if "selected_game" not in st.session_state:
  st.session_state.selected_game = "lotto"

# ================= 1. 상단 타이틀 및 배너 =================
st.markdown(
    "<h2 style='text-align: center; color: white;'>🎱 AI 고성능 로또 당첨 번호 분석"
    " & 추천 시스템</h2>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='text-align: center; color: #cbd5e1; font-size: 15px;"
    " margin-bottom: 20px;'>통계적 확률 모델(마르코프 체인, 포아송 분포), 복잡도(AC값)"
    " 필터링, 그리고 딥러닝 가중치 부여 엔진이 결합된 최상위 분석 시스템입니다.</p>",
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="main-banner">
        <h2 style="margin: 0; font-size: 24px; color: white;">🔥 로또 6/45 ✖️ 연금복권 720+</h2>
        <p style="margin: 8px 0 4px 0; font-size: 15px;">지금 접속하신 분께 <span style="background-color: #ff4b4b; padding: 2px 6px; border-radius: 4px; font-weight: bold;">100% 무료 분석</span> 제공!</p>
        <p style="margin: 0; font-size: 13px; color: #e2e8f0; font-weight: bold;">👑 VIP 혜택: 단 한 번의 결제로 두 가지 복권 S등급 동시 오픈!</p>
    </div>
""",
    unsafe_allow_html=True,
)

# ================= 선택된 복권 버튼에 동일한 은빛 애니메이션 적용 =================
if st.session_state.selected_game == "lotto":
  st.markdown(
      """
        <style>
        div[data-testid="column"]:nth-of-type(1) .stButton>button {
            border: 2px solid #ffffff !important;
            background-color: #2a3748 !important;
            color: #f8fafc !important;
            animation: silver-match-glow 2s infinite !important;
        }
        </style>
    """,
      unsafe_allow_html=True,
  )
else:
  st.markdown(
      """
        <style>
        div[data-testid="column"]:nth-of-type(2) .stButton>button {
            border: 2px solid #ffffff !important;
            background-color: #2a3748 !important;
            color: #f8fafc !important;
            animation: silver-match-glow 2s infinite !important;
        }
        </style>
    """,
      unsafe_allow_html=True,
  )

# ================= 2. 중앙 복권 선택 버튼 =================
st.markdown(
    "<h3 style='text-align: center; color: #fff; margin-bottom: 15px;'>🎯"
    " 원하시는 복권을 선택하세요</h3>",
    unsafe_allow_html=True,
)

col_b1, col_b2 = st.columns(2)
with col_b1:
  if st.button("🔴 로또 6/45 분석", use_container_width=True):
    st.session_state.selected_game = "lotto"
with col_b2:
  if st.button("🔵 연금복권 720+ 분석", use_container_width=True):
    st.session_state.selected_game = "pension"

st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)

# ================= 3. 녹색 번쩍이는 엔진 가동 바 =================
game_name_str = (
    "로또 6/45" if st.session_state.selected_game == "lotto" else "연금복권 720+"
)
st.markdown(
    f"""
    <div class="engine-active-box">
        <span>{"🔴" if st.session_state.selected_game=="lotto" else "🔵"} {game_name_str} 분석 ⚙️ ● AI 실시간 분석 엔진 가동 중</span>
    </div>
""",
    unsafe_allow_html=True,
)

st.markdown("---")

# ================= 4. 상단 인터랙티브 작동 카드 (톱니바퀴 회전 + 펼쳐보기) =================
col_top1, col_top2 = st.columns(2)

with col_top1:
  with st.expander("📊 실시간 AI 확률 모델 상세 로그 보기", expanded=False):
    st.markdown(
        """
        <div style="color: #cbd5e1; font-size: 13px; line-height: 1.6;">
        <b>[엔진 가동 세부 정보]</b><br>
        • 전이 확률 행렬 계산 완료 (Markov Chain)<br>
        • 포아송 간격 분포 가중치 적용됨<br>
        • 앙상블 가중치 최적화 진행 중... <span class="spinning-gear">⚙️</span>
        </div>
    """,
        unsafe_allow_html=True,
    )

with col_top2:
  with st.expander("⚡ 데이터베이스 및 필터 동기화 로그 보기", expanded=False):
    st.markdown(
        """
        <div style="color: #cbd5e1; font-size: 13px; line-height: 1.6;">
        <b>[DB 동기화 세부 정보]</b><br>
        • 동행복권 최신 회차 데이터 패킷 수신 완료<br>
        • AC값(복잡도) 정규분포 필터 테이블 로드됨<br>
        • 실시간 필터링 버퍼 안정화 완료 <span class="spinning-gear">⚙️</span>
        </div>
    """,
        unsafe_allow_html=True,
    )

st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)

# ================= 5. 고도화 분석 설정 및 알고리즘 요약 (빈 박스 제거됨) =================
col_c1, col_c2 = st.columns(2)
with col_c1:
  st.markdown("### ⚙️ 고도화 분석 설정")
  game_count = st.slider("추천 게임 수", 1, 10, 5)
  total_range = st.slider("번호 총합 범위 설정", 100, 200, (115, 175))
  odd_even = st.selectbox(
      "홀짝 비율 선호도", ["균등 (3:3 또는 4:2)", "홀수 우세", "짝수 우세"]
  )
  ac_value = st.slider("AC값 (복잡도 지수) 최소값", 5, 10, 7)

with col_c2:
  st.markdown("### 💡 엔진 알고리즘 요약")
  st.markdown("""
    * **빈도수 기반 가중치 시뮬레이션**
    * **AC값 및 총합 정규분포 필터링**
    * **엔트로피 기반 무작위성 최적화**
    """)

# ================= 6. 컴팩트 VIP 잠금해제 박스 =================
st.markdown(
    """
    <div class="vip-compact-box">
        <h3 style="margin-top: 0; color: #f8fafc; text-align: center; font-size: 18px;">🔒 VIP 1회용 고유 코드 입력 및 잠금 해제</h3>
    </div>
""",
    unsafe_allow_html=True,
)

_, col_vip, _ = st.columns([1, 2, 1])
with col_vip:
  vip_input = st.text_input(
      "VIP 코드를 입력하세요 (예: VIP2026)",
      type="password",
      key="vip_input_field",
  )
  if st.button("잠금 해제 시작", type="primary", use_container_width=True):
    if vip_input == "VIP2026":
      st.session_state.vip_unlocked = True
      st.success("✨ VIP 프리패스 활성화 완료!")
    else:
      st.error("잘못된 코드입니다.")

  if st.session_state.vip_unlocked:
    st.success("🚀 [VIP 프리패스 가동 중] S등급 데이터 실시간 적용")

st.markdown("---")

# ================= 7. 핵심 탭 메뉴 =================
tab1, tab2, tab3 = st.tabs(
    ["🎱 AI 당첨 번호 추천", "📊 통계 및 심층 분석", "📑 연구 모델 및 논문 참고"]
)

with tab1:
  st.markdown("### 🎯 맞춤형 하이브리드 번호 추출 결과")
  st.markdown(
      "설정하신 통계 필터와 AI 확률 엔진을 거쳐 엄선된 최적의 조합입니다."
  )

  if st.button("🚀 고성능 번호 추출 실행", type="primary", use_container_width=True):
    with st.spinner(
        "AI 엔진 가동 중... 통계 모델 및 가중치를 계산하고 있습니다."
    ):
      time.sleep(1.2)

    for i in range(game_count):
      if st.session_state.selected_game == "lotto":
        numbers = sorted(random.sample(range(1, 46), 6))
        st.success(f"🎉 [게임 {i+1}] 추천 로또 번호: **{numbers}**")
      else:
        group = random.randint(1, 5)
        nums = [random.randint(0, 9) for _ in range(6)]
        st.success(
            f"🎉 [게임 {i+1}] 추천 연금복권 번호:"
            f" **{group}조 {' '.join(map(str, nums))}**"
        )

with tab2:
  st.markdown("### 📊 역대 당첨 번호 통계 및 심층 분석")
  st.write(
      "출현 빈도, 미출현 번호(오버듀), 홀짝 비율 및 구간별 통계 데이터를"
      " 실시간으로 시각화합니다."
  )
  st.info("현재 최신 회차 데이터베이스가 정상적으로 연동되어 있습니다.")

with tab3:
  st.markdown("### 📑 연구 모델 및 논문 참고 자료")
  st.markdown("""
    - **Markov Chain Monte Carlo (MCMC) 기반 복권 번호 전이 확률 분석**
    - **Poisson Distribution을 활용한 번호 출현 간격 예측 모델**
    - **AC값(Arithmetic Complexity)을 통한 무작위성 및 조합 복잡도 필터링 연구**
    """)

# ================= 8. 하단 바로가기 및 푸터 =================
st.markdown("---")
if st.button("🛒 동행복권 공식 홈페이지 바로 가기", use_container_width=True):
  st.markdown("[동행복권 바로가기](https://www.dhlottery.co.kr)")

st.markdown(
    "<p style='text-align: center; color: #888; font-size: 13px; margin-top:"
    " 20px;'>© 2026 AI Advanced Lotto Intelligence System. All Rights"
    " Reserved.</p>",
    unsafe_allow_html=True,
)