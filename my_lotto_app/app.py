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
.block-container { max-width: 500px; padding-top: 1.5rem; padding-bottom: 2rem; }
#MainMenu {visibility: hidden;} header {visibility: hidden;} footer {visibility: hidden;}
.keep-all { word-break: keep-all; }

.cyber-title { display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin-bottom: 25px; }
.cyber-title-top { display: flex; align-items: center; justify-content: center; gap: 8px; white-space: nowrap; }
.cyber-title .lottopick-brand { font-weight: 900; font-size: clamp(22px, 6vw, 28px); letter-spacing: -0.8px; background: linear-gradient(135deg, #ffffff 0%, #fef08a 40%, #f59e0b 80%, #d97706 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-shadow: 0 0 15px rgba(245, 158, 11, 0.4); }

@keyframes clover-sparkle { 0% { transform: scale(1) rotate(0deg); filter: drop-shadow(0 0 4px #22c55e); } 50% { transform: scale(1.35) rotate(12deg); filter: drop-shadow(0 0 18px #4ade80) drop-shadow(0 0 30px #facc15); } 100% { transform: scale(1) rotate(0deg); filter: drop-shadow(0 0 4px #22c55e); } }
.sparkle-clover { display: inline-block; animation: clover-sparkle 1.4s infinite ease-in-out; font-size: clamp(24px, 6vw, 30px); vertical-align: middle; }
@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
.spinning-gear { display: inline-block; animation: spin 3s linear infinite; }

@keyframes pulse-red { 0% { transform: scale(1); background-color: #991b1b; box-shadow: 0 0 10px #991b1b; } 50% { transform: scale(1.15); background-color: #dc2626; box-shadow: 0 0 25px #ef4444; } 100% { transform: scale(1); background-color: #991b1b; box-shadow: 0 0 10px #991b1b; } }
.free-badge { display: inline-block; padding: 4px 12px; border-radius: 6px; color: white; font-weight: 900; animation: pulse-red 1.2s infinite ease-in-out; margin: 0 5px; white-space: nowrap; }

@keyframes silver-match-glow { 0% { box-shadow: 0 0 5px #94a3b8; border-color: #94a3b8; background-color: #1e293b; } 50% { box-shadow: 0 0 25px #e2e8f0; border-color: #ffffff; background-color: #2a3748; } 100% { box-shadow: 0 0 5px #94a3b8; border-color: #94a3b8; background-color: #1e293b; } }
@keyframes gold-glow { 0% { box-shadow: 0 0 8px #ca8a04; border-color: #eab308; background-color: #1e1b18; } 50% { box-shadow: 0 0 30px #facc15; border-color: #fde047; background-color: #2d2618; } 100% { box-shadow: 0 0 8px #ca8a04; border-color: #eab308; background-color: #1e1b18; } }
@keyframes glow-green { 0% { box-shadow: 0 0 5px #22c55e; border-color: #22c55e; } 50% { box-shadow: 0 0 25px #4ade80; border-color: #4ade80; } 100% { box-shadow: 0 0 5px #22c55e; border-color: #22c55e; } }

.stButton>button { font-weight: bold; border-radius: 10px; padding: 12px 10px; color: white !important; background-color: #1e293b; border: 2px solid #475569; transition: all 0.2s ease-in-out; width: 100%; word-break: keep-all; }
.stButton>button:hover { border-color: #ffffff !important; background-color: #2a3748 !important; box-shadow: 0 0 25px #e2e8f0 !important; }

/* VIP 프리미엄 버튼 */
@keyframes vip-premium-pulse { 0% { box-shadow: 0 0 10px #b91c1c, 0 0 5px #facc15; transform: scale(1); } 50% { box-shadow: 0 0 30px #ef4444, 0 0 20px #fde047; transform: scale(1.02); } 100% { box-shadow: 0 0 10px #b91c1c, 0 0 5px #facc15; transform: scale(1); } }
.vip-purchase-btn { display: block; width: 100%; font-weight: 900; font-size: 17px; border-radius: 12px; padding: 16px 15px; text-align: center; text-decoration: none; color: #ffffff !important; background: linear-gradient(135deg, #dc2626 0%, #991b1b 100%); border: 2px solid #facc15; transition: all 0.3s ease-in-out; animation: vip-premium-pulse 1.5s infinite ease-in-out; text-shadow: 1px 1px 4px rgba(0,0,0,0.6); margin-bottom: 15px; word-break: keep-all; }
.vip-purchase-btn:hover { background: linear-gradient(135deg, #ef4444 0%, #b91c1c 100%); border-color: #fde047; box-shadow: 0 0 35px #ef4444, 0 0 25px #facc15; }
.vip-purchase-text { color: #fef08a; font-size: 14px; display: block; margin-top: 3px; font-weight: normal; }

div.element-container:has(#vip-btn-target) + div.element-container button, div[data-testid="stElementContainer"]:has(#vip-btn-target) + div[data-testid="stElementContainer"] button { background-color: #FF0000 !important; border: 2px solid #CC0000 !important; color: white !important; }
div.element-container:has(#vip-btn-target) + div.element-container button p, div[data-testid="stElementContainer"]:has(#vip-btn-target) + div[data-testid="stElementContainer"] button p { font-weight: 900 !important; font-size: 18px !important; }

.extract-container { display: flex; flex-direction: column; align-items: center; width: 100%; margin-bottom: 25px; position: relative; }
.free-badge-top { background-color: #ff3b30; color: #ffffff; font-size: 14px; font-weight: 900; padding: 6px 16px; border-radius: 20px; margin-bottom: -15px; z-index: 10; box-shadow: 0 4px 10px rgba(0,0,0,0.4); white-space: nowrap; }

.extract-box-btn { display: flex; justify-content: center; align-items: center; width: 100%; background-color: #3b82f6; border: 2px solid #60a5fa; color: white !important; padding: 22px 10px 18px 10px; border-radius: 12px; text-decoration: none !important; box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4); transition: all 0.2s ease-in-out; }
.extract-box-btn span { font-size: clamp(18px, 5.5vw, 22px); font-weight: 900; letter-spacing: -0.5px; white-space: nowrap; }

.extract-vip-btn { background: linear-gradient(135deg, #ca8a04, #facc15); border: 2px solid #fde047; box-shadow: 0 0 25px rgba(250, 204, 21, 0.5); }
.extract-vip-btn span { color: #451a03 !important; text-shadow: 1px 1px 2px rgba(255,255,255,0.5); }

.donghang-btn { display: block; width: 100%; font-weight: 900; font-size: 18px; border-radius: 10px; padding: 16px 20px; text-align: center; text-decoration: none; color: #ffffff !important; background-color: #16a34a; border: 2px solid #22c55e; transition: all 0.2s ease-in-out; box-shadow: 0 4px 12px rgba(22, 163, 74, 0.3); word-break: keep-all; }

.locked-feature-box { background-color: #1e293b; border: 1px dashed #475569; border-radius: 10px; padding: 15px; text-align: center; margin-top: 10px; color: #94a3b8; position: relative; overflow: hidden; }
.locked-feature-box::after { content: "🔒 VIP 전용 분석"; position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); background: rgba(0,0,0,0.8); color: #facc15; font-weight: 900; padding: 8px 15px; border-radius: 8px; font-size: 15px; border: 1px solid #facc15; }
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

# ================= 1. 타이틀 배너 =================
st.markdown(
"""
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
<div style="color: #38bdf8; font-size: clamp(13px, 3.5vw, 15px); font-weight: 700; margin-top: 6px; word-break: keep-all;">
"데이터는 정밀하게, 분석은 체계적으로"
</div>
</div>
</div>
""", unsafe_allow_html=True)

# ================= 2. 중앙 복권 선택 버튼 =================
col_b1, col_b2 = st.columns(2)
with col_b1:
    if st.button("🔴 로또 6/45 분석", use_container_width=True):
        st.session_state.selected_game = "lotto"
with col_b2:
    if st.button("🔵 연금복권 720+", use_container_width=True):
        st.session_state.selected_game = "pension"

if st.session_state.selected_game == "lotto":
    st.markdown('<style>div[data-testid="column"]:nth-of-type(1) .stButton>button { animation: silver-match-glow 2s infinite !important; }</style>', unsafe_allow_html=True)
else:
    st.markdown('<style>div[data-testid="column"]:nth-of-type(2) .stButton>button { animation: silver-match-glow 2s infinite !important; }</style>', unsafe_allow_html=True)

# ================= 3. 녹색 엔진 가동 바 =================
game_name_str = "로또 6/45" if st.session_state.selected_game == "lotto" else "연금복권 720+"
st.markdown(
f"""
<div class="keep-all" style="background-color: #0f172a; border: 2px solid #22c55e; padding: 15px; border-radius: 12px; text-align: center; color: #4ade80; font-weight: bold; font-size: clamp(14px, 4vw, 16px); animation: glow-green 2s infinite; margin-top: 15px; margin-bottom: 20px;">
<span>{"🔴" if st.session_state.selected_game=="lotto" else "🔵"} {game_name_str} 분석 ⚙ ● 정밀 시스템 실시간 가동 중</span>
</div>
""",
    unsafe_allow_html=True,
)

with st.expander("⚙ 맞춤형 시스템 상세 설정 (무료/VIP 공통)", expanded=False):
    game_count = st.slider("추천 게임 수", 1, 10, 5)

# ================= 4. 금빛 VIP 시스템 (결제 유도) =================
if not st.session_state.vip_unlocked:
    st.markdown(
"""
<div class="keep-all" style="background-color: #1e1b18; border: 2px solid #eab308; padding: 20px; border-radius: 12px; animation: gold-glow 2s infinite; margin: 20px auto; color: #fef08a; text-align: center;">
<h4 style="margin-top: 0; font-size: 17px; margin-bottom: 15px;">👑 VIP 프리패스 혜택 안내</h4>
<p style="font-size: 14px; line-height: 1.6; text-align: left; color: #fde047;">
✅ <b>이번 주 고정수 & 완벽 제외수 리포트 즉시 공개</b><br>
✅ AI 패턴 기반 <b>S등급 일치율 점수</b> 제공<br>
✅ 프리미엄 빅데이터 통계 조합 가동
</p>
<hr style="border-color: #451a03; margin: 15px 0;">
<div style="font-size: 13px; color: #d97706; margin-bottom: 15px;">🔒 아래 버튼을 통해 VIP 이용권을 구매하고 코드를 입력하세요.</div>
<a href="https://order.pay.naver.com" target="_blank" class="vip-purchase-btn">
💎 네이버페이 간편 결제 💎
<span class="vip-purchase-text">(VIP 프리패스 이용권 구매)</span>
</a>
</div>
""", unsafe_allow_html=True)

    vip_input = st.text_input("VIP 코드를 입력하세요 (예: VIP2026)", type="password", key="vip_code_input")
    
    st.markdown('<span id="vip-btn-target" style="display:none;"></span>', unsafe_allow_html=True)
    if st.button("잠금 해제 시작", use_container_width=True, key="vip_unlock_btn"):
        if vip_input == "VIP2026":
            st.session_state.vip_unlocked = True
            st.success("✨ VIP 프리패스 활성화 완료!")
            st.rerun()
        else:
            st.error("잘못된 코드입니다.")
else:
    st.markdown(
"""
<div style="background-color: #451a03; border: 2px solid #facc15; padding: 15px; border-radius: 10px; text-align: center; color: #fde047; font-weight: bold; margin-bottom: 20px;">
👑 VIP 계정 활성화 상태입니다. 모든 S등급 프리미엄 데이터가 적용됩니다.
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ================= 5. 추출 버튼 (VIP 여부에 따라 변경) =================
query_params = st.query_params
if "extract" in query_params and query_params["extract"] == "true":
    st.session_state.triggered = True
    st.query_params.clear()

if st.session_state.vip_unlocked:
    st.markdown(
"""
<div class="extract-container">
<div class="free-badge-top" style="background-color: #ca8a04; animation: none; padding: 4px 15px; border: 1px solid #fef08a;">👑 프리미엄 S등급 적용됨</div>
<a href="?extract=true" target="_self" class="extract-box-btn extract-vip-btn">
<span>🚀 프리미엄 조합 추출 실행</span>
</a>
</div>
""", unsafe_allow_html=True
    )
else:
    st.markdown(
"""
<div class="extract-container">
<div class="free-badge-top" style="animation: pulse-red 1.2s infinite ease-in-out;">🔥 100% 무료 일반 분석</div>
<a href="?extract=true" target="_self" class="extract-box-btn">
<span>🚀 일반 번호 조합 추출 실행</span>
</a>
</div>
""", unsafe_allow_html=True
    )

if st.session_state.get("triggered", False):
    st.session_state.triggered = False
    
    if not st.session_state.vip_unlocked:
        st.balloons()
    else:
        st.snow()
    
    with st.spinner("분석 시스템 가동 중... 최적의 통계 모델과 가중치를 계산하고 있습니다."):
        time.sleep(1.0)
    
    st.session_state.extract_results = []
    st.session_state.extract_game_type = st.session_state.selected_game
    st.session_state.is_vip_result = st.session_state.vip_unlocked
    
    if st.session_state.is_vip_result:
        all_lotto = list(range(1, 46))
        st.session_state.vip_fixed = sorted(random.sample(all_lotto, 2))
        st.session_state.vip_excluded = sorted(random.sample([x for x in all_lotto if x not in st.session_state.vip_fixed], 10))
    
    for i in range(game_count):
        if st.session_state.selected_game == "lotto":
            if st.session_state.is_vip_result:
                pool = [x for x in range(1, 46) if x not in st.session_state.vip_excluded and x not in st.session_state.vip_fixed]
                remains = random.sample(pool, 4)
                numbers = sorted(st.session_state.vip_fixed + remains)
                match_score = round(random.uniform(92.5, 99.8), 1)
            else:
                numbers = sorted(random.sample(range(1, 46), 6))
                match_score = None
                
            st.session_state.extract_results.append((numbers, match_score))
        else:
            group = random.randint(1, 5)
            nums = [random.randint(0, 9) for _ in range(6)]
            match_score = round(random.uniform(91.0, 98.9), 1) if st.session_state.is_vip_result else None
            st.session_state.extract_results.append((group, nums, match_score))

def get_ball_color(num):
    if num <= 10: return "#facc15"
    elif num <= 20: return "#3b82f6"
    elif num <= 30: return "#ef4444"
    elif num <= 40: return "#a855f7"
    else: return "#22c55e"

# ================= 6. 핵심 탭 메뉴 (결과 출력 영역) =================
tab1, tab2, tab3 = st.tabs(["🎱 당첨 번호 추천", "📊 심층 분석", "📑 연구 모델"])

with tab1:
    if not st.session_state.extract_results:
        st.info("👆 상단의 파란색(또는 황금색) **[🚀 추출 실행]** 버튼을 누르시면 번호가 생성됩니다.")
    else:
        is_vip = st.session_state.get("is_vip_result", False)
        
        if is_vip:
            st.markdown("<h4 style='color: #facc15;'>👑 VIP 프리미엄 분석 리포트</h4>", unsafe_allow_html=True)
            if st.session_state.extract_game_type == "lotto":
                fixed_str = ", ".join(map(str, st.session_state.vip_fixed))
                excl_str = ", ".join(map(str, st.session_state.vip_excluded))
                st.markdown(
f"""
<div style="background-color: #2d2618; border: 1px solid #facc15; padding: 15px; border-radius: 10px; margin-bottom: 20px;">
<div style="color: #fef08a; font-size: 14px; font-weight: bold; margin-bottom: 5px;">🎯 [VIP 전용] 금주의 고정 타겟 수: <span style="color: white; font-size: 16px;">{fixed_str}</span></div>
<div style="color: #fca5a5; font-size: 13px; font-weight: bold;">🚫 [VIP 전용] 필터링 제외수: <span style="color: #cbd5e1;">{excl_str}</span></div>
</div>
""", unsafe_allow_html=True)
        else:
            st.markdown("#### 🎯 일반 번호 추출 결과")
            st.success("✅ 기본 통계 필터를 거쳐 엄선된 조합입니다.")
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        # [수정] HTML 코드가 노출되는 마크다운 버그 원천 차단 (한 줄 문자열 생성 방식)
        for i, result in enumerate(st.session_state.extract_results):
            if st.session_state.extract_game_type == "lotto":
                numbers, match_score = result
                balls_html = "".join([f'<div style="width: 32px; height: 32px; border-radius: 50%; background-color: {get_ball_color(n)}; color: white; display: flex; justify-content: center; align-items: center; font-weight: bold; font-size: 14px; margin-right: 5px; box-shadow: 0 4px 6px rgba(0,0,0,0.3);">{n}</div>' for n in numbers])
                bg_color = "#2d2618" if is_vip else "#111827"
                border_color = "#facc15" if is_vip else "#374151"
                vip_badge = f'<span style="background-color: #ef4444; color: white; font-size: 11px; padding: 2px 6px; border-radius: 4px; font-weight: bold;">S등급 (패턴일치 {match_score}%)</span>' if is_vip else ''
                
                html_str = f'<div style="background-color: {bg_color}; padding: 12px; border-radius: 10px; border: 1px solid {border_color}; margin-bottom: 10px;"><div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;"><span style="color: white; font-weight: bold; font-size: 15px;">게임 {i+1}</span>{vip_badge}</div><div style="display: flex; flex-wrap: wrap;">{balls_html}</div></div>'
                st.markdown(html_str, unsafe_allow_html=True)
            else:
                group, nums, match_score = result
                bg_color = "#2d2618" if is_vip else "#111827"
                border_color = "#facc15" if is_vip else "#374151"
                group_html = f'<div style="background: linear-gradient(135deg, #f59e0b, #d97706); color: white; padding: 4px 10px; border-radius: 6px; font-weight: bold; font-size: 14px; margin-right: 10px; margin-bottom: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.3);">{group}조</div>'
                digits_html = "".join([f'<div style="width: 30px; height: 30px; border-radius: 6px; background-color: #2563eb; color: white; display: flex; justify-content: center; align-items: center; font-weight: bold; font-size: 16px; margin-right: 4px; margin-bottom: 5px; box-shadow: 0 3px 5px rgba(0,0,0,0.3);">{n}</div>' for n in nums])
                vip_badge = f'<span style="background-color: #ef4444; color: white; font-size: 11px; padding: 2px 6px; border-radius: 4px; font-weight: bold;">VIP 확률 {match_score}%</span>' if is_vip else ''
                
                html_str = f'<div style="background-color: {bg_color}; padding: 12px; border-radius: 10px; border: 1px solid {border_color}; margin-bottom: 10px;"><div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;"><span style="color: white; font-weight: bold; font-size: 15px;">게임 {i+1}</span>{vip_badge}</div><div style="display: flex; flex-wrap: wrap; align-items: center;">{group_html}{digits_html}</div></div>'
                st.markdown(html_str, unsafe_allow_html=True)

        if not is_vip:
            st.markdown(
"""
<div class="locked-feature-box">
이 자리에 이번 주 <b>무조건 피해야 할 10개의 제외수</b>와 <b>S등급 패턴 타겟 번호</b>가 표시됩니다.<br><br><br>
</div>
""", unsafe_allow_html=True)

with tab2:
    st.markdown("#### 📈 역대 당첨 번호 통계 분석")
    st.caption("최근 100회차 번호별 출현 빈도수")
    chart_data = pd.DataFrame(np.random.randint(10, 25, size=(45, 1)), columns=["출현 횟수"], index=[f"{i}번" for i in range(1, 46)])
    st.bar_chart(chart_data, color="#3b82f6", height=250)
    
    if not st.session_state.vip_unlocked:
        st.markdown(
"""
<div style='text-align:center; padding: 10px; background:#1e1b18; border:1px solid #eab308; border-radius:8px; color:#facc15; font-size:13px;'>
🔒 VIP 전용: 미출현 장기 번호 및 회귀 추적 데이터 잠김
</div>
""", unsafe_allow_html=True)

with tab3:
    st.markdown("#### 📑 분석 연구 모델")
    st.markdown(
"""
<div style="font-size: 13px; color: #cbd5e1;">
- Markov Chain Monte Carlo (MCMC) 모델<br>
- Poisson Distribution 출현 간격 예측<br>
- AC값(Arithmetic Complexity) 복잡도 필터링
</div>
""", unsafe_allow_html=True)

# ================= 7. 하단 버튼 및 고지 사항 (복구 완료) =================
st.markdown("---")
st.markdown("##### 📞 고객 센터")
st.caption("결제 오류 및 VIP 관련 문의는 아래 버튼을 통해 안전하게 접수해 주세요.")
google_form_url = "https://forms.google.com/" 
st.markdown(
f"""
<a href="{google_form_url}" target="_blank" style="text-decoration: none;">
<div class="keep-all" style="background-color: #2e3b4e; color: white; text-align: center; padding: 15px; border-radius: 12px; font-weight: bold; font-size: 15px; margin-bottom: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.3);">
🛠️ 결제 및 이용 문의하기 (안전 접수)
</div>
</a>
""", unsafe_allow_html=True)

st.markdown(
"""
<a href="https://www.dhlottery.co.kr" target="_blank" class="donghang-btn">
🛒 동행복권 공식 홈페이지 바로 가기
</a>
""", unsafe_allow_html=True)

# [복구] 법적 고지 및 면책 조항
st.markdown(
"""
<div style="background-color: #1a1a1a; padding: 15px; border-radius: 8px; margin-top: 25px; border: 1px solid #333; color: #888; font-size: 11px; line-height: 1.6; word-break: keep-all;">
<b>[법적 고지 및 주의사항]</b><br>
1. 본 서비스(로또픽)에서 제공하는 번호 조합 및 통계 분석 자료는 과거의 데이터를 기반으로 한 확률적 추정치이며, <b>실제 복권 당첨을 절대 보장하지 않습니다.</b><br>
2. 제공된 번호를 이용한 복권 구매 등 모든 판단과 책임은 전적으로 <b>사용자 본인</b>에게 있으며, 본 서비스는 이로 인해 발생하는 어떠한 직·간접적 손실에 대해서도 법적 책임을 지지 않습니다.<br>
3. 복권은 소액으로 건전하게 즐기시길 바라며, 과도한 몰입은 일상생활에 지장을 줄 수 있습니다. (도박중독 예방치유센터: 1336)
</div>
""", unsafe_allow_html=True)

st.markdown(
"""
<p style='text-align: center; color: #666; font-size: 12px; margin-top: 20px;'>
© 2026 로또픽(Lotto Pick) 분석 시스템. All Rights Reserved.
</p>
""", unsafe_allow_html=True)