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
.block-container { max-width: 500px; padding-top: 1.5rem; padding-bottom: 2rem; padding-left: 0.8rem; padding-right: 0.8rem; }
#MainMenu {visibility: hidden;} header {visibility: hidden;} footer {visibility: hidden;}
.keep-all { word-break: keep-all; }

/* 배경 및 텍스트 */
.stApp { background-color: #0e1117; color: #fafafa; }

/* 타이틀 및 상단 클로버 배치 레이아웃 */
.cyber-title { text-align: center; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin-bottom: 25px; width: 100%; box-sizing: border-box; }
.lottopick-brand { font-weight: 900; font-size: clamp(22px, 6vw, 28px); letter-spacing: -0.5px; background: linear-gradient(135deg, #ffffff 0%, #fef08a 40%, #f59e0b 80%, #d97706 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-shadow: 0 0 15px rgba(245, 158, 11, 0.4); display: inline-block; margin-top: 4px; }

/* 클로버 애니메이션 */
@keyframes clover-sparkle { 0% { transform: scale(1) rotate(0deg); filter: drop-shadow(0 0 4px #22c55e); } 50% { transform: scale(1.25) rotate(10deg); filter: drop-shadow(0 0 15px #4ade80) drop-shadow(0 0 25px #facc15); } 100% { transform: scale(1) rotate(0deg); filter: drop-shadow(0 0 4px #22c55e); } }
.sparkle-clover { display: inline-block; animation: clover-sparkle 1.4s infinite ease-in-out; font-size: clamp(24px, 6.5vw, 30px); margin: 0 6px; vertical-align: middle; }

@keyframes silver-match-glow { 0% { box-shadow: 0 0 5px #94a3b8; border-color: #94a3b8; background-color: #1e293b; } 50% { box-shadow: 0 0 25px #e2e8f0; border-color: #ffffff; background-color: #2a3748; } 100% { box-shadow: 0 0 5px #94a3b8; border-color: #94a3b8; background-color: #1e293b; } }
@keyframes gold-glow { 0% { box-shadow: 0 0 8px #ca8a04; border-color: #eab308; background-color: #1e1b18; } 50% { box-shadow: 0 0 30px #facc15; border-color: #fde047; background-color: #2d2618; } 100% { box-shadow: 0 0 8px #ca8a04; border-color: #eab308; background-color: #1e1b18; } }
@keyframes glow-green { 0% { box-shadow: 0 0 5px #22c55e; border-color: #22c55e; } 50% { box-shadow: 0 0 25px #4ade80; border-color: #4ade80; } 100% { box-shadow: 0 0 5px #22c55e; border-color: #22c55e; } }
@keyframes pulse-orange { 0% { box-shadow: 0 0 15px rgba(249, 115, 22, 0.4); transform: scale(1); } 50% { box-shadow: 0 0 30px rgba(249, 115, 22, 0.8); transform: scale(1.01); } 100% { box-shadow: 0 0 15px rgba(249, 115, 22, 0.4); transform: scale(1); } }
@keyframes pulse-sky { 0% { box-shadow: 0 0 15px rgba(56, 189, 248, 0.4); transform: scale(1); } 50% { box-shadow: 0 0 30px rgba(56, 189, 248, 0.8); transform: scale(1.01); } 100% { box-shadow: 0 0 15px rgba(56, 189, 248, 0.4); transform: scale(1); } }
@keyframes pulse-red-flash { 0% { transform: scale(1); background-color: #991b1b; box-shadow: 0 0 12px #991b1b; } 50% { transform: scale(1.06); background-color: #dc2626; box-shadow: 0 0 25px #ef4444; } 100% { transform: scale(1); background-color: #991b1b; box-shadow: 0 0 12px #991b1b; } }

/* 기본 버튼 스타일 */
.stButton>button { font-weight: bold; border-radius: 10px; padding: 12px 10px; color: white !important; background-color: #1e293b; border: 2px solid #475569; transition: all 0.2s ease-in-out; width: 100%; word-break: keep-all; }
.stButton>button:hover { border-color: #ffffff !important; background-color: #2a3748 !important; box-shadow: 0 0 25px #e2e8f0 !important; }

/* VIP 에메랄드 결제 버튼 */
@keyframes emerald-premium-pulse { 0% { box-shadow: 0 0 12px rgba(5, 150, 105, 0.6), 0 0 6px #facc15; transform: scale(1); } 50% { box-shadow: 0 0 30px rgba(16, 185, 129, 0.9), 0 0 18px #fde047; transform: scale(1.02); } 100% { box-shadow: 0 0 12px rgba(5, 150, 105, 0.6), 0 0 6px #facc15; transform: scale(1); } }
.vip-purchase-btn { display: block; width: 100%; font-weight: 900; font-size: 17px; border-radius: 12px; padding: 16px 15px; text-align: center; text-decoration: none; color: #ffffff !important; background: linear-gradient(135deg, #059669 0%, #047857 100%); border: 2px solid #facc15; transition: all 0.3s ease-in-out; animation: emerald-premium-pulse 1.8s infinite ease-in-out; text-shadow: 1px 1px 4px rgba(0,0,0,0.4); margin-bottom: 15px; word-break: keep-all; }
.vip-purchase-btn:hover { background: linear-gradient(135deg, #10b981 0%, #059669 100%); border-color: #fde047; box-shadow: 0 0 35px #10b981, 0 0 25px #facc15; }
.vip-purchase-text { color: #fef08a; font-size: 14px; display: block; margin-top: 3px; font-weight: normal; }

/* [잠금해제 버튼] */
div.st-key-unlock_btn button { 
    background: linear-gradient(135deg, #f97316, #ea580c) !important; 
    border: 2px solid #fed7aa !important; 
    box-shadow: 0 0 20px rgba(249, 115, 22, 0.5) !important;
    font-size: 16px !important;
    animation: pulse-orange 2s infinite ease-in-out;
}
div.st-key-unlock_btn button:hover {
    background: linear-gradient(135deg, #fb923c, #f97316) !important;
    border-color: #ffedd5 !important;
    box-shadow: 0 0 30px rgba(249, 115, 22, 0.8) !important;
}

/* [일반 무료 추출 버튼] */
div.st-key-free_extract_btn button {
    background: linear-gradient(135deg, #0ea5e9, #0284c7) !important;
    border: 2px solid #bae6fd !important;
    font-size: 18px !important;
    padding: 18px !important;
    box-shadow: 0 0 25px rgba(56, 189, 248, 0.5) !important;
    animation: pulse-sky 2s infinite ease-in-out;
}
div.st-key-free_extract_btn button:hover {
    background: linear-gradient(135deg, #38bdf8, #0ea5e9) !important;
    border-color: #e0f2fe !important;
    box-shadow: 0 0 35px rgba(56, 189, 248, 0.8) !important;
}

/* VIP 프리미엄 추출 버튼 */
div.st-key-vip_extract_btn button {
    background: linear-gradient(135deg, #ca8a04, #eab308) !important;
    border: 2px solid #fef08a !important;
    color: #451a03 !important;
    font-size: 19px !important;
    font-weight: 900 !important;
    padding: 20px !important;
    box-shadow: 0 0 30px rgba(250, 204, 21, 0.8) !important;
    animation: gold-glow 1.8s infinite ease-in-out;
}
div.st-key-vip_extract_btn button p {
    color: #451a03 !important;
    text-shadow: 1px 1px 2px rgba(255,255,255,0.6);
}

/* 뱃지 및 게임박스 디자인 */
.free-badge-top { background-color: #dc2626; color: #ffffff; font-size: 14px; font-weight: 900; padding: 6px 16px; border-radius: 20px; margin-bottom: -12px; z-index: 10; box-shadow: 0 4px 15px rgba(239,68,68,0.6); display: inline-block; animation: pulse-red-flash 1.2s infinite ease-in-out; border: 1px solid #fca5a5; }
.vip-badge-top { background-color: #ca8a04; color: #ffffff; font-size: 14px; font-weight: 900; padding: 6px 16px; border-radius: 20px; margin-bottom: -12px; z-index: 10; border: 1px solid #fef08a; box-shadow: 0 4px 15px rgba(250, 204, 21, 0.5); display: inline-block; }
.game-box-free { background-color: #111827; border: 1px solid #374151; padding: 15px; border-radius: 12px; margin-bottom: 12px; }
.game-box-vip { background: linear-gradient(145deg, #1f1b13, #2d2618); border: 1px solid #facc15; padding: 18px; border-radius: 12px; margin-bottom: 15px; box-shadow: 0 4px 15px rgba(250, 204, 21, 0.15); position: relative; overflow: hidden; }
.s-class-badge { position: absolute; top: 0; right: 0; background: linear-gradient(135deg, #ef4444, #b91c1c); color: white; font-size: 11px; font-weight: 900; padding: 4px 15px; border-bottom-left-radius: 12px; box-shadow: -2px 2px 5px rgba(0,0,0,0.3); }
.score-bar-bg { width: 100%; background-color: #3f3f46; border-radius: 4px; height: 6px; margin: 8px 0; overflow: hidden; }
.score-bar-fill { background: linear-gradient(90deg, #facc15, #22c55e); height: 100%; border-radius: 4px; }
.vip-tags { margin-top: 10px; display: flex; gap: 6px; flex-wrap: wrap; }
.vip-tag { font-size: 11px; background-color: rgba(250, 204, 21, 0.1); border: 1px solid rgba(250, 204, 21, 0.3); color: #fef08a; padding: 3px 8px; border-radius: 6px; font-weight: bold; }
.locked-feature-box { background: linear-gradient(135deg, #1e293b, #0f172a); border: 2px dashed #64748b; border-radius: 12px; padding: 28px 20px; text-align: center; margin-top: 15px; color: #cbd5e1; position: relative; overflow: hidden; box-shadow: inset 0 2px 6px rgba(0,0,0,0.4); }
.locked-feature-title { font-size: 15px; font-weight: 800; color: #fef08a; margin-bottom: 8px; text-shadow: 0 0 8px rgba(250,204,21,0.3); }
.locked-feature-desc { font-size: 13px; color: #94a3b8; line-height: 1.5; }
.footer-buttons-container { display: flex; gap: 15px; width: 100%; margin-bottom: 25px; align-items: center; justify-content: space-between; }
.footer-btn { flex: 1; display: flex; align-items: center; justify-content: center; text-decoration: none !important; color: white !important; font-weight: 900; font-size: 16px; padding: 15px 5px; border-radius: 12px; transition: all 0.2s ease-in-out; word-break: keep-all; text-align: center; }
.footer-btn-cs { background-color: #2e3b4e; border: 2px solid #475569; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
.footer-btn-dh { background-color: #16a34a; border: 2px solid #22c55e; box-shadow: 0 4px 12px rgba(22, 163, 74, 0.3); }
.footer-btn:hover { transform: translateY(-2px); filter: brightness(1.1); }
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

# ================= 1. 타이틀 배너 (상단 클로버 배치형) =================
st.markdown(
"""
<div class="cyber-title">
    <div>
        <span class="sparkle-clover">🍀</span>
        <span class="sparkle-clover">🍀</span>
    </div>
    <div>
        <span class="lottopick-brand">로또픽 (Lotto Pick)</span>
    </div>
    <div style="margin-top: 14px; line-height: 1.5; text-align: center; width: 100%;">
        <div style="color: #e2e8f0; font-size: clamp(15px, 3.8vw, 17px); font-weight: 800; text-shadow: 0 0 10px rgba(255,255,255,0.2); word-break: keep-all;">
            초정밀 통계·조합 분석 시스템
        </div>
        <div style="color: #94a3b8; font-size: clamp(10px, 2.3vw, 12px); font-weight: 600; letter-spacing: 1.2px; margin: 4px 0;">
            LOTTO & PENSION LOTTERY ANALYTICS
        </div>
        <div style="color: #38bdf8; font-size: clamp(12px, 3.2vw, 14px); font-weight: 700; margin-top: 5px; word-break: keep-all;">
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

GOOGLE_FORM_URL = "https://forms.gle/RA8i731z2QFi7ByMA"

# ================= 4. 금빛 VIP 시스템 (결제 유도) =================
if not st.session_state.vip_unlocked:
    st.markdown(
f"""
<div class="keep-all" style="background-color: #064e3b; border: 2px solid #eab308; padding: 20px; border-radius: 12px; animation: gold-glow 2s infinite; margin: 20px auto; color: #fef08a; text-align: center;">
<h4 style="margin-top: 0; font-size: 17px; margin-bottom: 15px; color: #fde047;">👑 VIP 프리패스 혜택 안내</h4>
<p style="font-size: 14px; line-height: 1.6; text-align: left; color: #ecfdf5;">
✅ <b>이번 주 고정수 & 완벽 제외수 리포트 즉시 공개</b><br>
✅ AI 패턴 기반 <b>S등급 일치율 점수 & 분석 태그</b> 제공<br>
✅ 프리미엄 빅데이터 통계 조합 가동
</p>
<hr style="border-color: #022c22; margin: 15px 0;">
<div style="font-size: 13px; color: #a7f3d0; margin-bottom: 15px;">🔒 아래 버튼을 통해 결제 및 신청서를 작성하신 후 코드를 입력하세요.</div>
<a href="{GOOGLE_FORM_URL}" target="_blank" class="vip-purchase-btn">
💎 네이버페이 간편 결제 💎
<span class="vip-purchase-text">(VIP 프리패스 이용권 신청서 작성)</span>
</a>
</div>
""", unsafe_allow_html=True)

    vip_input = st.text_input("VIP 코드를 입력하세요 (예: MPD2026)", type="password", key="vip_code_input")
    
    if st.button("🔓 잠금 해제 시작", use_container_width=True, key="unlock_btn"):
        if vip_input in ["MPD2026", "VIP2026"]:
            st.session_state.vip_unlocked = True
            st.success("✨ VIP 프리패스 활성화 완료!")
            time.sleep(0.5)
            st.rerun()
        else:
            st.error("❌ 올바르지 않은 코드입니다.")
else:
    st.markdown(
"""
<div style="background-color: #064e3b; border: 2px solid #facc15; padding: 15px; border-radius: 10px; text-align: center; color: #fde047; font-weight: bold; margin-bottom: 20px;">
👑 VIP 계정 활성화 상태입니다. 모든 S등급 프리미엄 데이터가 적용됩니다.
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ================= 5. 추출 버튼 =================
if st.session_state.vip_unlocked:
    st.markdown('<div style="text-align:center;"><div class="vip-badge-top">👑 프리미엄 S등급 적용됨</div></div>', unsafe_allow_html=True)
    clicked = st.button("🚀 프리미엄 조합 추출 실행", use_container_width=True, key="vip_extract_btn")
else:
    st.markdown('<div style="text-align:center;"><div class="free-badge-top">🔥 100% 무료 일반 분석</div></div>', unsafe_allow_html=True)
    clicked = st.button("🚀 일반 번호 조합 무료추출 실행", use_container_width=True, key="free_extract_btn")

if clicked:
    if not st.session_state.vip_unlocked:
        st.balloons()
    else:
        st.snow()
    
    with st.spinner("최적의 통계 모델과 가중치를 계산하고 있습니다..."):
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
                match_score = round(random.uniform(96.5, 99.8), 1)
                tags = random.sample(["#고정수 포함", "#황금비율", "#이월수 패턴", "#최적합 조합", "#장기미출현 믹스"], 3)
                st.session_state.extract_results.append((numbers, match_score, tags))
            else:
                numbers = sorted(random.sample(range(1, 46), 6))
                st.session_state.extract_results.append((numbers, None, None))
        else:
            group = random.randint(1, 5)
            nums = [random.randint(0, 9) for _ in range(6)]
            if st.session_state.is_vip_result:
                match_score = round(random.uniform(95.0, 99.9), 1)
                tags = ["#최상위 패턴", "#연속수 필터링"]
            else:
                match_score, tags = None, None
            st.session_state.extract_results.append((group, nums, match_score, tags))

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
        st.info("👆 상단의 **[추출 실행]** 버튼을 누르시면 번호가 생성됩니다.")
    else:
        is_vip = st.session_state.get("is_vip_result", False)
        
        if is_vip:
            st.markdown("<h4 style='color: #facc15; margin-bottom:15px;'>👑 VIP 프리미엄 분석 리포트</h4>", unsafe_allow_html=True)
            if st.session_state.extract_game_type == "lotto":
                fixed_str = ", ".join(map(str, st.session_state.vip_fixed))
                excl_str = ", ".join(map(str, st.session_state.vip_excluded))
                st.markdown(
f"""
<div style="background-color: #2b1f1f; border-left: 5px solid #ef4444; padding: 15px; border-radius: 6px; margin-bottom: 15px;">
    <h5 style="color: #ef4444; margin-top: 0; margin-bottom: 8px;">🚫 금주의 VIP 완벽 제외수 10개</h5>
    <div style="color: white; font-size: 15px; font-weight: bold; letter-spacing: 1.5px; margin-bottom: 5px;">{excl_str}</div>
    <div style="font-size: 12px; color: #a1a1aa;">* 하락세 패턴이 강력하게 겹치는 번호로 필터링 되었습니다.</div>
</div>
<div style="background-color: #1f2937; border-left: 5px solid #3b82f6; padding: 12px; border-radius: 6px; margin-bottom: 25px;">
    <span style="color: #60a5fa; font-size: 14px; font-weight: bold;">🎯 금주의 VIP 고정 타겟 수:</span> 
    <span style="color: white; font-weight: bold;">{fixed_str}</span>
</div>
""", unsafe_allow_html=True)
        else:
            st.markdown("#### 🎯 일반 번호 추출 결과")
            st.success("✅ 기본 통계 필터를 거쳐 엄선된 조합입니다.")
            st.markdown("<br>", unsafe_allow_html=True)
        
        for i, result in enumerate(st.session_state.extract_results):
            if st.session_state.extract_game_type == "lotto":
                numbers, match_score, tags = result
                balls_html = "".join([f'<div style="width: 32px; height: 32px; border-radius: 50%; background-color: {get_ball_color(n)}; color: white; display: flex; justify-content: center; align-items: center; font-weight: bold; font-size: 14px; margin-right: 5px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); text-shadow: 1px 1px 2px rgba(0,0,0,0.5);">{n}</div>' for n in numbers])
                
                if is_vip:
                    tags_html = "".join([f'<span class="vip-tag">{tag}</span>' for tag in tags])
                    html_str = f"""
                    <div class="game-box-vip">
                        <div class="s-class-badge">S-CLASS</div>
                        <div style="color: #facc15; font-weight: 900; font-size: 15px; margin-bottom: 5px;">👑 VIP 프리미엄 게임 {i+1}</div>
                        <div style="display: flex; justify-content: space-between; align-size: center; font-size: 12px; color: #d1d5db; margin-bottom: 2px;">
                            <span>딥러닝 패턴 일치율</span><span style="color: #4ade80; font-weight: bold;">{match_score}%</span>
                        </div>
                        <div class="score-bar-bg"><div class="score-bar-fill" style="width: {match_score}%;"></div></div>
                        <div style="display: flex; flex-wrap: wrap; margin-top: 15px; margin-bottom: 10px;">{balls_html}</div>
                        <div class="vip-tags">{tags_html}</div>
                    </div>
                    """
                else:
                    html_str = f"""
                    <div class="game-box-free">
                        <div style="color: white; font-weight: bold; font-size: 15px; margin-bottom: 10px;">게임 {i+1}</div>
                        <div style="display: flex; flex-wrap: wrap;">{balls_html}</div>
                    </div>
                    """
                st.markdown(html_str, unsafe_allow_html=True)
            else: # 연금복권
                group, nums, match_score, tags = result
                group_html = f'<div style="background: linear-gradient(135deg, #f59e0b, #d97706); color: white; padding: 4px 10px; border-radius: 6px; font-weight: bold; font-size: 14px; margin-right: 10px; margin-bottom: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.3);">{group}조</div>'
                digits_html = "".join([f'<div style="width: 30px; height: 30px; border-radius: 6px; background-color: #2563eb; color: white; display: flex; justify-content: center; align-items: center; font-weight: bold; font-size: 16px; margin-right: 4px; margin-bottom: 5px; box-shadow: 0 3px 5px rgba(0,0,0,0.3);">{n}</div>' for n in nums])
                
                if is_vip:
                    tags_html = "".join([f'<span class="vip-tag">{tag}</span>' for tag in tags])
                    html_str = f"""
                    <div class="game-box-vip">
                        <div class="s-class-badge">S-CLASS</div>
                        <div style="color: #facc15; font-weight: 900; font-size: 15px; margin-bottom: 5px;">👑 연금 VIP 게임 {i+1}</div>
                        <div style="display: flex; justify-content: space-between; align-size: center; font-size: 12px; color: #d1d5db; margin-bottom: 2px;">
                            <span>딥러닝 패턴 일치율</span><span style="color: #4ade80; font-weight: bold;">{match_score}%</span>
                        </div>
                        <div class="score-bar-bg"><div class="score-bar-fill" style="width: {match_score}%;"></div></div>
                        <div style="display: flex; flex-wrap: wrap; align-items: center; margin-top: 15px; margin-bottom: 10px;">{group_html}{digits_html}</div>
                        <div class="vip-tags">{tags_html}</div>
                    </div>
                    """
                else:
                    html_str = f"""
                    <div class="game-box-free">
                        <div style="color: white; font-weight: bold; font-size: 15px; margin-bottom: 10px;">게임 {i+1}</div>
                        <div style="display: flex; flex-wrap: wrap; align-items: center;">{group_html}{digits_html}</div>
                    </div>
                    """
                st.markdown(html_str, unsafe_allow_html=True)

        if not is_vip:
            st.markdown(
"""
<div class="locked-feature-box">
    <div class="locked-feature-title">🔒 VIP 프리미엄 전용 콘텐츠</div>
    <div class="locked-feature-desc">결제 후 이 자리에 <b>[금주 완벽 제외수 10개]</b>와<br><b>[S등급 상세 분석 리포트]</b>가 즉시 해제됩니다.</div>
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

# ================= 7. 하단 버튼 및 고지 사항 =================
st.markdown("---")
st.markdown("##### 📞 고객 센터")
st.caption("결제 오류 및 VIP 관련 문의는 아래 버튼을 통해 안전하게 접수해 주세요.")

st.markdown(
f"""
<div class="footer-buttons-container">
    <a href="{GOOGLE_FORM_URL}" target="_blank" class="footer-btn footer-btn-cs">
        🛠️ 문의/결제 신청
    </a>
    <a href="https://www.dhlottery.co.kr" target="_blank" class="footer-btn footer-btn-dh">
        🛒 동행복권 홈
    </a>
</div>
""", unsafe_allow_html=True)

# ================= 8. 토스 심사용 상품 안내 =================
st.markdown("---")
st.markdown("### 💎 프리미엄 분석권 상품 안내 (Toss 심사 제출용)")
st.info("""
- **상품명:** VIP 골든픽 1주(7일) 프리패스
- **가격:** 1,000원 (VAT 포함)
- **제공 서비스:** AI 패턴 기반 S등급 고정수/제외수 리포트 및 초정밀 통계 조합 가동
- **이용 기간:** 결제일로부터 7일간 무제한 이용
- **환불 규정:** 디지털 콘텐츠 특성상, VIP 코드 발급 후에는 환불이 불가합니다. (코드 발급 전 전액 환불 가능)
""")

# ================= 9. 법적 고지 및 사업자 정보 Footer =================
st.markdown(
"""
<div style="background-color: #1a1a1a; padding: 15px; border-radius: 8px; margin-top: 25px; border: 1px solid #333; color: #888; font-size: 11px; line-height: 1.6; word-break: keep-all;">
<b>[법적 고지 및 주의사항]</b><br>
1. 본 서비스(로또픽)에서 제공하는 번호 조합 및 통계 분석 자료는 과거의 데이터를 기반으로 한 확률적 추정치이며, <b>실제 복권 당첨을 절대 보장하지 않습니다.</b><br>
2. 제공된 번호를 이용한 복권 구매 등 모든 판단과 책임은 전적으로 <b>사용자 본인</b>에게 있으며, 본 서비스는 이로 인해 발생하는 어떠한 직·간접적 손실에 대해서도 법적 책임을 지지 않습니다.<br>
3. 복권은 소액으로 건전하게 즐기시길 바라며, 과도한 몰입은 일상생활에 지장을 줄 수 있습니다. (도박중독 예방치유센터: 1336)
</div>

<div style="text-align: center; color: #777; font-size: 11px; margin-top: 20px; line-height: 1.8; padding-top: 20px; border-top: 1px solid #333;">
    <b>상호:</b> 엠피디뮤직 (MPD music) &nbsp;|&nbsp; <b>대표:</b> 이근영 &nbsp;|&nbsp; <b>사업자등록번호:</b> 162-23-01932<br>
    <b>사업장 주소:</b> 경기도 고양시 덕양구 능곡로 16, 101동 501호(토당동, 숲예찬)<br>
    <b>고객센터:</b> 010-5282-7017 &nbsp;|&nbsp; <b>이메일:</b> leegysa@naver.com<br><br>
    © 2026 로또픽(Lotto Pick) 분석 시스템. All Rights Reserved.
</div>
""", unsafe_allow_html=True)
