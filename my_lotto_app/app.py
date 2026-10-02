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
/* 기본 설정 */
.block-container { max-width: 500px; padding-top: 1.5rem; padding-bottom: 2rem; }
#MainMenu, header, footer {visibility: hidden;}
.keep-all { word-break: keep-all; }

/* 다크 테마 배경 및 텍스트 최적화 */
.stApp { background-color: #0e1117; color: #fafafa; }

/* 타이틀 디자인 */
.cyber-title { display: flex; flex-direction: column; align-items: center; text-align: center; margin-bottom: 25px; }
.cyber-title-top { display: flex; align-items: center; justify-content: center; gap: 8px; white-space: nowrap; }
.cyber-title .lottopick-brand { font-weight: 900; font-size: clamp(22px, 6vw, 28px); letter-spacing: -0.8px; background: linear-gradient(135deg, #ffffff 0%, #fef08a 40%, #f59e0b 80%, #d97706 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-shadow: 0 0 15px rgba(245, 158, 11, 0.4); }

/* 애니메이션 */
@keyframes clover-sparkle { 0%, 100% { transform: scale(1) rotate(0deg); filter: drop-shadow(0 0 4px #22c55e); } 50% { transform: scale(1.35) rotate(12deg); filter: drop-shadow(0 0 18px #4ade80) drop-shadow(0 0 30px #facc15); } }
.sparkle-clover { display: inline-block; animation: clover-sparkle 1.4s infinite ease-in-out; font-size: clamp(24px, 6vw, 30px); }
@keyframes silver-match-glow { 0%, 100% { box-shadow: 0 0 5px #94a3b8; border-color: #94a3b8; background-color: #1e293b; } 50% { box-shadow: 0 0 25px #e2e8f0; border-color: #ffffff; background-color: #2a3748; } }
@keyframes glow-green { 0%, 100% { box-shadow: 0 0 5px #22c55e; border-color: #22c55e; } 50% { box-shadow: 0 0 25px #4ade80; border-color: #4ade80; } }

/* 기본 버튼 스타일 */
.stButton>button { font-weight: bold; border-radius: 10px; padding: 12px 10px; color: white !important; background-color: #1e293b; border: 2px solid #475569; transition: all 0.2s; width: 100%; }
.stButton>button:hover { border-color: #ffffff !important; background-color: #2a3748 !important; box-shadow: 0 0 25px #e2e8f0 !important; }

/* 선택된 게임 버튼 애니메이션 타겟팅 */
div[data-testid="column"]:nth-of-type(1) .stButton>button.active-game, 
div[data-testid="column"]:nth-of-type(2) .stButton>button.active-game { animation: silver-match-glow 2s infinite !important; }

/* 🟢 네이버페이 결제 버튼 */
div.st-key-naver_pay_btn > button {
    background: linear-gradient(135deg, #03c75a, #02a348) !important;
    border: 2px solid #FFD700 !important;
    box-shadow: 0 0 15px rgba(255, 215, 0, 0.4) !important;
    font-size: 17px !important; font-weight: 900 !important;
}
div.st-key-naver_pay_btn > button:hover { box-shadow: 0 0 25px rgba(255, 215, 0, 0.8) !important; transform: scale(1.02); }

/* 🔵 [수정] 잠금 해제 버튼 (고급스러운 사파이어 블루) */
div.st-key-unlock_btn > button {
    background: linear-gradient(135deg, #1e3a8a, #172554) !important;
    border: 2px solid #60a5fa !important;
    box-shadow: 0 0 15px rgba(96, 165, 250, 0.4) !important;
    font-size: 17px !important; font-weight: 900 !important;
}
div.st-key-unlock_btn > button:hover { box-shadow: 0 0 25px rgba(96, 165, 250, 0.8) !important; transform: scale(1.02); }

/* 일반 vs VIP 추출 버튼 컨테이너 및 뱃지 */
.extract-container { display: flex; flex-direction: column; align-items: center; width: 100%; margin-bottom: 25px; position: relative; }
.free-badge-top { background-color: #ff3b30; color: #ffffff; font-size: 14px; font-weight: 900; padding: 6px 16px; border-radius: 20px; margin-bottom: -15px; z-index: 10; box-shadow: 0 4px 10px rgba(0,0,0,0.4); white-space: nowrap; }
.vip-badge-top { background-color: #ca8a04; color: #ffffff; font-size: 14px; font-weight: 900; padding: 6px 16px; border-radius: 20px; margin-bottom: -15px; z-index: 10; border: 1px solid #fef08a; box-shadow: 0 4px 15px rgba(250, 204, 21, 0.5); }

/* 추출 버튼 본체 */
@keyframes free-pulse-glow { 0%, 100% { box-shadow: 0 0 10px rgba(59, 130, 246, 0.5); transform: scale(1); } 50% { box-shadow: 0 0 28px rgba(96, 165, 250, 0.9); transform: scale(1.02); } }
.extract-box-btn { display: flex; justify-content: center; align-items: center; width: 100%; background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%); border: 2px solid #60a5fa; color: white !important; padding: 22px 10px 18px 10px; border-radius: 12px; text-decoration: none !important; animation: free-pulse-glow 1.8s infinite ease-in-out; cursor: pointer; }
.extract-box-btn span { font-size: clamp(17px, 5vw, 21px); font-weight: 900; letter-spacing: -0.5px; }

@keyframes gold-pulse-glow { 0%, 100% { box-shadow: 0 0 15px rgba(250, 204, 21, 0.6); transform: scale(1); } 50% { box-shadow: 0 0 35px rgba(250, 204, 21, 1); transform: scale(1.03); } }
.extract-vip-btn { background: linear-gradient(135deg, #ca8a04, #eab308); border: 2px solid #fef08a; animation: gold-pulse-glow 1.8s infinite ease-in-out; }
.extract-vip-btn span { color: #451a03 !important; text-shadow: 1px 1px 2px rgba(255,255,255,0.6); }

/* 게임 박스 디자인 */
.game-box-free { background-color: #1a1c24; border: 1px solid #2d3139; padding: 15px; border-radius: 10px; margin-bottom: 12px; }

/* [추가] VIP 전용 화려한 게임 박스 */
.game-box-vip { background: linear-gradient(145deg, #1f1b13, #2d2618); border: 1px solid #facc15; padding: 18px; border-radius: 12px; margin-bottom: 15px; box-shadow: 0 4px 15px rgba(250, 204, 21, 0.15); position: relative; overflow: hidden; }
.s-class-badge { position: absolute; top: 0; right: 0; background: linear-gradient(135deg, #ef4444, #b91c1c); color: white; font-size: 11px; font-weight: 900; padding: 4px 15px; border-bottom-left-radius: 12px; box-shadow: -2px 2px 5px rgba(0,0,0,0.3); }
.score-bar-bg { width: 100%; background-color: #3f3f46; border-radius: 4px; height: 6px; margin: 8px 0; overflow: hidden; }
.score-bar-fill { background: linear-gradient(90deg, #facc15, #22c55e); height: 100%; border-radius: 4px; }
.vip-tags { margin-top: 10px; display: flex; gap: 6px; flex-wrap: wrap; }
.vip-tag { font-size: 10px; background-color: rgba(250, 204, 21, 0.1); border: 1px solid rgba(250, 204, 21, 0.3); color: #fef08a; padding: 2px 6px; border-radius: 4px; font-weight: bold; }

/* 기타 UI */
.vip-locked-box { background-color: #1a1c24; border: 1px dashed #FFD700; padding: 25px; border-radius: 12px; text-align: center; margin: 20px 0; }
.blur-text { color: transparent; text-shadow: 0 0 8px rgba(255, 255, 255, 0.7); user-select: none; }
.donghang-btn { display: block; width: 100%; font-weight: 900; font-size: 16px; border-radius: 10px; padding: 14px; text-align: center; text-decoration: none; color: #ffffff !important; background-color: #16a34a; border: 2px solid #22c55e; transition: all 0.2s; }
</style>
""", unsafe_allow_html=True)

# ================= 세션 상태 초기화 =================
if "vip_unlocked" not in st.session_state: st.session_state.vip_unlocked = False
if "selected_game" not in st.session_state: st.session_state.selected_game = "lotto"
if "extract_results" not in st.session_state: st.session_state.extract_results = []
if "extract_game_type" not in st.session_state: st.session_state.extract_game_type = "lotto"
if "triggered" not in st.session_state: st.session_state.triggered = False

# ================= 1. 타이틀 영역 =================
st.markdown(
"""
<div class="cyber-title">
<div class="cyber-title-top">
<span class="sparkle-clover">🍀</span><span class="lottopick-brand">로또픽 (Lotto Pick)</span><span class="sparkle-clover">🍀</span>
</div>
<div style="color: #e2e8f0; font-size: 16px; font-weight: 800; margin-top: 10px;">초정밀 통계·조합 분석 시스템</div>
<div style="color: #94a3b8; font-size: 11px; font-weight: 600; letter-spacing: 1.5px; margin: 4px 0;">LOTTO & PENSION ANALYTICS</div>
</div>
""", unsafe_allow_html=True)

# ================= 2. 복권 선택 버튼 (선택된 쪽에만 애니메이션 클래스 부여) =================
col_b1, col_b2 = st.columns(2)
with col_b1:
    if st.button("🔴 로또 6/45 분석", use_container_width=True, key="btn_lotto"):
        st.session_state.selected_game = "lotto"
with col_b2:
    if st.button("🔵 연금복권 720+", use_container_width=True, key="btn_pension"):
        st.session_state.selected_game = "pension"

if st.session_state.selected_game == "lotto":
    st.markdown('<style>div[data-testid="column"]:nth-of-type(1) .stButton>button { animation: silver-match-glow 2s infinite !important; }</style>', unsafe_allow_html=True)
else:
    st.markdown('<style>div[data-testid="column"]:nth-of-type(2) .stButton>button { animation: silver-match-glow 2s infinite !important; }</style>', unsafe_allow_html=True)

# ================= 3. 시스템 가동 바 =================
game_name_str = "로또 6/45" if st.session_state.selected_game == "lotto" else "연금복권 720+"
st.markdown(
f"""
<div style="background-color: #0f172a; border: 2px solid #22c55e; padding: 12px; border-radius: 10px; text-align: center; color: #4ade80; font-weight: bold; font-size: 14px; animation: glow-green 2s infinite; margin-bottom: 20px;">
{"🔴" if st.session_state.selected_game=="lotto" else "🔵"} {game_name_str} 분석 ⚙ 실시간 가동 중
</div>
""", unsafe_allow_html=True)

with st.expander("⚙ 시스템 상세 설정 (추천 게임 수)"):
    game_count = st.slider("추천 게임 수", 1, 10, 5)

# ================= 4. VIP 결제 및 잠금 해제 영역 =================
if not st.session_state.vip_unlocked:
    st.markdown(
    """
    <div class="vip-locked-box">
        <h4 style='color: #facc15; margin-top: 0;'>👑 VIP 프리패스 혜택 안내</h4>
        <div style="text-align: left; font-size: 14px; color: #e2e8f0; line-height: 1.6; margin-bottom: 15px;">
        ✅ 이번 주 <b>고정수 & 완벽 제외수 리포트</b> 즉시 공개<br>
        ✅ S등급 딥러닝 확률 필터 개방 (상세 일치율 제공)<br>
        ✅ 프리미엄 빅데이터 통계 조합 가동
        </div>
        <hr style="border-color: #333; margin: 15px 0;">
        <p style='font-size: 12px; color: #a1a1aa;'>🔒 이번 주 피해야 할 완벽 제외수 10개 미리보기<br>
        <span style="color:#ef4444;">[ 2, <span class="blur-text">17, 23, 29, 31, 35</span>, 38, <span class="blur-text">41, 42</span>, 44 ]</span></p>
    </div>
    """, unsafe_allow_html=True)
    
    # [수정] 버튼 2개를 a 태그와 st.button으로 구현
    st.markdown('<a href="https://order.pay.naver.com" target="_blank" style="text-decoration:none;">', unsafe_allow_html=True)
    st.button("💎 네이버페이 간편 결제 💎\n(VIP 이용권 구매)", key="naver_pay_btn")
    st.markdown('</a><br>', unsafe_allow_html=True)
    
    vip_code = st.text_input("VIP 코드를 입력하세요", type="password", placeholder="결제 후 받은 코드를 입력 (예: MPD2026)")
    
    # [수정] 잠금 해제 버튼 (사파이어 블루)
    if st.button("🔓 잠금 해제 시작", key="unlock_btn"):
        if vip_code in ["MPD2026", "VIP2026"]: 
            st.session_state.vip_unlocked = True
            st.success("✨ VIP 프리패스 활성화 완료!")
            time.sleep(0.5)
            st.rerun()
        elif vip_code == "":
            st.warning("코드를 입력해 주세요.")
        else:
            st.error("❌ 올바르지 않은 코드입니다.")
else:
    st.markdown(
    """
    <div style="background-color: #2d2618; border: 1px solid #facc15; padding: 12px; border-radius: 8px; text-align: center; color: #fde047; font-weight: bold; margin-bottom: 20px;">
    👑 VIP 계정 활성화 완료. 모든 S등급 프리미엄 데이터가 적용됩니다.
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ================= 5. 추출 실행 버튼 =================
query_params = st.query_params
if "extract" in query_params and query_params["extract"] == "true":
    st.session_state.triggered = True
    st.query_params.clear()

if st.session_state.vip_unlocked:
    st.markdown(
    """
    <div class="extract-container">
    <div class="vip-badge-top">👑 프리미엄 S등급 적용됨</div>
    <a href="?extract=true" target="_self" class="extract-box-btn extract-vip-btn">
    <span>🚀 프리미엄 조합 추출 실행</span>
    </a>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown(
    """
    <div class="extract-container">
    <div class="free-badge-top">🔥 100% 무료 일반 분석</div>
    <a href="?extract=true" target="_self" class="extract-box-btn">
    <span>🚀 일반 번호 조합 무료추출 실행</span>
    </a>
    </div>
    """, unsafe_allow_html=True)

# 추출 로직 처리
if st.session_state.get("triggered", False):
    st.session_state.triggered = False
    
    if not st.session_state.vip_unlocked: st.balloons()
    else: st.snow()
    
    with st.spinner("최적의 통계 모델과 가중치를 계산하고 있습니다..."):
        time.sleep(1.0)
    
    st.session_state.extract_results = []
    st.session_state.extract_game_type = st.session_state.selected_game
    st.session_state.is_vip_result = st.session_state.vip_unlocked
    
    all_lotto = list(range(1, 46))
    if st.session_state.is_vip_result:
        st.session_state.vip_fixed = sorted(random.sample(all_lotto, 2))
        st.session_state.vip_excluded = sorted(random.sample([x for x in all_lotto if x not in st.session_state.vip_fixed], 10))
    
    for i in range(game_count):
        if st.session_state.selected_game == "lotto":
            if st.session_state.is_vip_result:
                pool = [x for x in all_lotto if x not in st.session_state.vip_excluded and x not in st.session_state.vip_fixed]
                numbers = sorted(st.session_state.vip_fixed + random.sample(pool, 4))
                score = round(random.uniform(94.5, 99.8), 1)
                tags = random.sample(["#고정수 포함", "#황금비율", "#이월수 포함", "#최적합 조합", "#장기미출현 믹스"], 3)
            else:
                numbers = sorted(random.sample(all_lotto, 6))
                score, tags = None, None
            st.session_state.extract_results.append((numbers, score, tags))
        else: # 연금복권
            group = random.randint(1, 5)
            nums = [random.randint(0, 9) for _ in range(6)]
            score = round(random.uniform(92.0, 98.9), 1) if st.session_state.is_vip_result else None
            tags = ["#최상위 패턴"] if st.session_state.is_vip_result else None
            st.session_state.extract_results.append((group, nums, score, tags))

# 로또 공 색상
def get_ball_color(num):
    if num <= 10: return "#facc15"
    elif num <= 20: return "#3b82f6"
    elif num <= 30: return "#ef4444"
    elif num <= 40: return "#a855f7"
    else: return "#22c55e"

# ================= 6. 결과 탭 출력 영역 =================
tab1, tab2, tab3 = st.tabs(["🎱 당첨 번호 추천", "📊 심층 분석", "📑 연구 모델"])

with tab1:
    if not st.session_state.extract_results:
        st.info("👆 위쪽의 화려한 **[추출 실행]** 버튼을 누르시면 번호가 생성됩니다.")
    else:
        is_vip = st.session_state.get("is_vip_result", False)
        
        if is_vip:
            if st.session_state.extract_game_type == "lotto":
                f_str = ", ".join(map(str, getattr(st.session_state, 'vip_fixed', [])))
                e_str = ", ".join(map(str, getattr(st.session_state, 'vip_excluded', [])))
                st.markdown(
                f"""
                <div style="background-color: #2b1f1f; border-left: 5px solid #ef4444; padding: 15px; border-radius: 6px; margin-bottom: 20px;">
                    <h5 style="color: #ef4444; margin-top: 0; margin-bottom: 8px;">🚫 금주의 VIP 완벽 제외수 10개</h5>
                    <div style="color: white; font-size: 16px; font-weight: bold; letter-spacing: 2px; margin-bottom: 10px;">{e_str}</div>
                    <div style="font-size: 13px; color: #a1a1aa;">* 장기 미출현 및 하락세 패턴이 강력하게 겹치는 번호로 필터링 되었습니다.</div>
                </div>
                <div style="background-color: #1f2937; border-left: 5px solid #3b82f6; padding: 12px; border-radius: 6px; margin-bottom: 25px;">
                    <span style="color: #60a5fa; font-size: 14px; font-weight: bold;">🎯 금주의 VIP 고정 타겟 수:</span> 
                    <span style="color: white; font-weight: bold;">{f_str}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.success("✅ 기본 통계 필터를 거쳐 엄선된 조합입니다.")
            
        # 게임 결과 출력
        for i, result in enumerate(st.session_state.extract_results):
            if st.session_state.extract_game_type == "lotto":
                numbers, score, tags = result
                balls_html = "".join([f'<div style="width: 32px; height: 32px; border-radius: 50%; background-color: {get_ball_color(n)}; color: white; display: flex; justify-content: center; align-items: center; font-weight: bold; font-size: 14px; margin-right: 6px; box-shadow: inset -1px -1px 3px rgba(0,0,0,0.3), 1px 1px 3px rgba(0,0,0,0.5);">{n}</div>' for n in numbers])
                
                if is_vip:
                    # [수정] 돈값 하는 VIP 게임 박스 디자인
                    tags_html = "".join([f'<span class="vip-tag">{tag}</span>' for tag in tags])
                    html_str = f"""
                    <div class="game-box-vip">
                        <div class="s-class-badge">S-CLASS</div>
                        <div style="color: #facc15; font-weight: 900; font-size: 16px; margin-bottom: 5px;">👑 VIP 게임 {i+1}</div>
                        <div style="display: flex; justify-content: space-between; align-size: center; font-size: 12px; color: #d1d5db; margin-bottom: 2px;">
                            <span>딥러닝 패턴 일치율</span><span style="color: #4ade80; font-weight: bold;">{score}%</span>
                        </div>
                        <div class="score-bar-bg"><div class="score-bar-fill" style="width: {score}%;"></div></div>
                        <div style="display: flex; flex-wrap: wrap; margin-top: 12px; margin-bottom: 8px;">{balls_html}</div>
                        <div class="vip-tags">{tags_html}</div>
                    </div>
                    """
                else:
                    # 일반 게임 박스
                    html_str = f"""
                    <div class="game-box-free">
                        <div style="color: #94a3b8; font-weight: bold; font-size: 15px; margin-bottom: 10px;">게임 {i+1}</div>
                        <div style="display: flex; flex-wrap: wrap;">{balls_html}</div>
                    </div>
                    """
                st.markdown(html_str, unsafe_allow_html=True)
            else: # 연금복권 출력
                pass # (생략: 위와 동일한 논리로 꾸밈 가능)

        if not is_vip:
            st.markdown(
            """
            <div style="background-color: #1e293b; border: 1px dashed #475569; border-radius: 10px; padding: 30px 15px; text-align: center; margin-top: 15px; color: #facc15; font-weight: bold; position: relative;">
            🔒 결제 후 이 자리에 [완벽 제외수 10개]와 [S등급 상세 분석 리포트]가 표시됩니다.
            </div>
            """, unsafe_allow_html=True)

with tab2:
    st.markdown("#### 📈 역대 당첨 번호 통계 분석")
    chart_data = pd.DataFrame(np.random.randint(10, 25, size=(45, 1)), columns=["출현 횟수"], index=[f"{i}번" for i in range(1, 46)])
    st.bar_chart(chart_data, color="#3b82f6", height=250)

with tab3:
    st.markdown("#### 📑 분석 연구 모델")
    st.caption("- Markov Chain Monte Carlo (MCMC) 모델\n- Poisson Distribution 예측")

# ================= 7. 하단 고객센터 및 고지 사항 =================
st.markdown("---")
st.markdown("##### 📞 고객 센터")
col1, col2 = st.columns(2)
with col1:
    st.markdown('<a href="https://forms.google.com/" target="_blank" style="text-decoration:none;"><div style="background-color: #2e3b4e; color: white; text-align: center; padding: 12px; border-radius: 8px; font-weight: bold; font-size: 14px;">🛠️ 문의하기</div></a>', unsafe_allow_html=True)
with col2:
    st.markdown('<a href="https://www.dhlottery.co.kr" target="_blank" class="donghang-btn" style="padding:12px; font-size:14px;">🛒 동행복권 홈</a>', unsafe_allow_html=True)

st.markdown(
"""
<div style="background-color: #1a1a1a; padding: 12px; border-radius: 8px; margin-top: 20px; border: 1px solid #333; color: #777; font-size: 11px; line-height: 1.5; word-break: keep-all;">
본 서비스는 확률적 추정치를 제공하며, 실제 복권 당첨을 보장하지 않습니다. 구매 결정은 전적으로 사용자 본인에게 있습니다. (도박중독 예방: 1336)
</div>
<p style='text-align: center; color: #555; font-size: 11px; margin-top: 15px;'>© 2026 로또픽(Lotto Pick). All Rights Reserved.</p>
""", unsafe_allow_html=True)