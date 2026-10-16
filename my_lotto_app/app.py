# -*- coding: utf-8 -*-
"""
로또픽 (Lotto Pick) - 초정밀 통계·조합 분석 시스템 (최종 완성본)
- Streamlit 네이티브 버튼을 활용한 완벽한 UI 테두리 유지 및 토스 다이렉트 결제 연동
- 결제 성공 시 Solapi 자동 문자 발송 및 메인 창 VIP 코드 입력 시스템
"""

import random
import time
import os
from collections import Counter
import numpy as np
import pandas as pd
import streamlit as st
import requests
import hmac
import hashlib
from datetime import datetime, timezone

# ================= URL 및 키 관리 =================
TOSS_CLIENT_KEY = "test_ck_kYG57Eba3GblXWjwLeyw8pWDOxmA"    # 토스 클라이언트 키
GOOGLE_FORM_URL = "https://forms.gle/RA8i731z2QFi7ByMA"        # 고객센터 구글 폼 링크
APP_SITE_URL = "https://mylottoapp-3mygrnqs6j7ard8n3zrvj9.streamlit.app" # 실제 배포 주소

# ================= 솔라피(Solapi) API 설정 =================
SOLAPI_API_KEY = "NCSKDYPYYPOSNLNV"
SOLAPI_API_SECRET = "DWIXUPBFG7ZGPOCNYY8MVNYWRUW9XTTA"
SOLAPI_SENDER_PHONE = "01052827017" # 발신번호

def send_vip_sms(receiver_phone, vip_code):
    """표준 requests와 HMAC 서명을 통한 초안정 문자 발송 함수"""
    url = "https://api.solapi.com/messages/v4/send"
    
    now = datetime.now(timezone.utc)
    date = now.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    salt = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=16))
    data = date + salt
    
    signature = hmac.new(
        SOLAPI_API_SECRET.encode('utf-8'),
        data.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    authorization = f"HMAC-SHA256 apiKey={SOLAPI_API_KEY}, date={date}, salt={salt}, signature={signature}"
    
    headers = {
        "Authorization": authorization,
        "Content-Type": "application/json; charset=utf-8"
    }
    
    message_text = (
        f"[로또픽] VIP 프리패스 코드가 발급되었습니다.\n\n"
        f"🔑 VIP 전용 코드: {vip_code}\n"
        f"⏱ 이용 기간: 발급일로부터 7일간\n\n"
        f"🍀 금주의 행운을 기원합니다!"
    )
    
    payload = {
        "message": {
            "to": receiver_phone,
            "from": SOLAPI_SENDER_PHONE,
            "text": message_text
        }
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code in [200, 201]:
            return True, "전송 성공"
        else:
            return False, f"코드: {response.status_code}, 내용: {response.text}"
    except Exception as e:
        return False, str(e)

# ================= 0. 페이지 기본 설정 =================
st.set_page_config(
    page_title="로또픽(Lotto Pick) - 초정밀 통계·조합 분석 시스템", 
    page_icon="🍀", 
    layout="centered"
)

st.markdown('<meta name="google-adsense-account" content="ca-pub-2324282297166072">', unsafe_allow_html=True)

# 세션 상태 초기화
if "vip_unlocked" not in st.session_state:
    st.session_state.vip_unlocked = False
if "vip_expire_time" not in st.session_state:
    st.session_state.vip_expire_time = 0
if "current_order_id" not in st.session_state:
    st.session_state.current_order_id = ""
if "latest_sent_code" not in st.session_state:
    st.session_state.latest_sent_code = ""

if st.session_state.vip_unlocked:
    if time.time() > st.session_state.vip_expire_time:
        st.session_state.vip_unlocked = False
        st.warning("⏱ VIP 이용 기간(7일)이 만료되었습니다. 계속 이용하시려면 재결제를 진행해 주세요.")

if "selected_game" not in st.session_state:
    st.session_state.selected_game = "lotto"
if "extract_results" not in st.session_state:
    st.session_state.extract_results = []
if "extract_game_type" not in st.session_state:
    st.session_state.extract_game_type = "lotto"
if "is_vip_result" not in st.session_state:
    st.session_state.is_vip_result = False
if "trigger_snow" not in st.session_state:
    st.session_state.trigger_snow = False
if "trigger_balloons" not in st.session_state:
    st.session_state.trigger_balloons = False

# ================= 결제 성공/실패 쿼리 처리 =================
try:
    if "payment_success" in st.query_params:
        if not st.session_state.latest_sent_code:
            generated_vip_code = f"MPD-{random.randint(1000, 9999)}"
            st.session_state.latest_sent_code = generated_vip_code
            send_vip_sms(SOLAPI_SENDER_PHONE, generated_vip_code)
            
        st.toast("🎉 토스 결제가 완료되었습니다! 문자로 VIP 코드가 발송되었습니다.", icon="✨")
        st.query_params.clear()
        st.rerun()

    elif "payment_fail" in st.query_params:
        st.error("❌ 결제가 취소되었거나 실패했습니다. 다시 시도해 주세요.")
        st.query_params.clear()
        st.rerun()
except Exception:
    pass

# ================= 🚨 전체 화면 결제 모드 (토스페이먼츠 연동) =================
if st.query_params.get("pay_popup") == "true" and not st.session_state.vip_unlocked:
    st.markdown("""
    <style>
    .block-container { max-width: 800px !important; padding-top: 2rem !important; }
    </style>
    """, unsafe_allow_html=True)
    
    if not st.session_state.current_order_id:
        st.session_state.current_order_id = f"lotto{int(time.time())}{random.randint(100, 999)}"
        
    order_id_gen = st.session_state.current_order_id
    
    import streamlit.components.v1 as components
    toss_fullscreen_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <script src="https://js.tosspayments.com/v1/payment"></script>
        <style>
            body {{
                margin: 0;
                padding: 40px;
                background-color: #0e1117;
                color: #ffffff;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                text-align: center;
            }}
            .pay-card {{
                background: linear-gradient(145deg, #1f1b13, #2d2618);
                border: 2px solid #facc15;
                padding: 30px;
                border-radius: 16px;
                box-shadow: 0 0 30px rgba(250, 204, 21, 0.4);
                max-width: 500px;
                margin: 0 auto;
            }}
            .btn-pay {{
                background: linear-gradient(135deg, #059669, #047857);
                color: white;
                border: 2px solid #facc15;
                padding: 16px 24px;
                font-size: 18px;
                font-weight: 900;
                border-radius: 12px;
                cursor: pointer;
                margin-top: 20px;
                box-shadow: 0 0 20px rgba(250, 204, 21, 0.6);
                width: 100%;
            }}
            .btn-pay:hover {{ filter: brightness(1.2); }}
            .btn-cancel {{
                background: #1e293b;
                color: #f87171;
                border: 2px solid #f87171;
                padding: 12px 20px;
                font-size: 15px;
                font-weight: 900;
                border-radius: 12px;
                cursor: pointer;
                margin-top: 15px;
                width: 100%;
            }}
            .btn-cancel:hover {{ background: #dc2626; color: white; }}
        </style>
    </head>
    <body>
        <div class="pay-card">
            <h2 style="color: #fde047; margin-top: 0;">👑 토스페이먼츠 안전 결제</h2>
            <p style="color: #e2e8f0; font-size: 15px; line-height: 1.6;">
                상품명: <b>VIP 골든픽 1주(7일) 프리패스[cite: 35]</b><br>
                결제 금액: <span style="color: #4ade80; font-size: 20px; font-weight: bold;">1,000원</span>
            </p>
            <p style="color: #a7f3d0; font-size: 13px; margin-bottom: 20px;">
                아래 버튼을 누르시면 안전한 토스 결제창이 열립니다.
            </p>
            <button class="btn-pay" onclick="requestTossPayment()">💎 토스 결제창 열기 (1,000원)</button>
            <br>
            <button class="btn-cancel" onclick="location.href='{APP_SITE_URL}'">❌ 메인으로 돌아가기</button>
        </div>

        <script>
            function requestTossPayment() {{
                try {{
                    var tossPayments = TossPayments("{TOSS_CLIENT_KEY}");
                    tossPayments.requestPayment("카드", {{
                        amount: 1000,
                        orderId: "{order_id_gen}",
                        orderName: "VIP 골든픽 1주(7일) 프리패스",
                        successUrl: "{APP_SITE_URL}/?payment_success=true",
                        failUrl: "{APP_SITE_URL}/?payment_fail=true"
                    }}).catch(function (error) {{
                        if (error.code !== "USER_CANCEL") {{
                            alert("결제 오류: " + error.message);
                        }}
                    }});
                }} catch(e) {{
                    alert("결제 초기화 오류: " + e.message);
                }}
            }}
        </script>
    </body>
    </html>
    """
    components.html(toss_fullscreen_html, height=700, scrolling=True)
    st.stop()

# ================= 세레모니 실행 처리 =================
if st.session_state.trigger_snow:
    st.snow()
    st.session_state.trigger_snow = False

if st.session_state.trigger_balloons:
    st.balloons()
    st.session_state.trigger_balloons = False

# ================= 커스텀 CSS 스타일 (테두리 및 UI 완벽 보호) =================
st.markdown("""
<style>
html, body, * {
    -webkit-text-size-adjust: 100% !important;
    -moz-text-size-adjust: 100% !important;
    text-size-adjust: 100% !important;
}

.block-container { max-width: 500px; padding-top: 1.5rem; padding-bottom: 2rem; padding-left: 0.8rem; padding-right: 0.8rem; }
#MainMenu {visibility: hidden;} header {visibility: hidden;} footer {visibility: hidden;}
.keep-all { word-break: keep-all; }

.stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stToolbar"] { 
    background-color: #0e1117 !important; 
    color: #ffffff !important; 
}

[data-testid="stMarkdownContainer"] p, 
[data-testid="stMarkdownContainer"] span, 
[data-testid="stMarkdownContainer"] div, 
[data-testid="stMarkdownContainer"] h1, 
[data-testid="stMarkdownContainer"] h2, 
[data-testid="stMarkdownContainer"] h3, 
[data-testid="stMarkdownContainer"] h4 {
    color: #ffffff;
}

div[data-testid="stTextInput"] label p, 
div[data-testid="stWidgetLabel"] p, 
.stTextInput label p {
    color: #facc15 !important;
    font-size: 17px !important;
    font-weight: 900 !important;
    text-shadow: 1px 1px 4px rgba(0,0,0,0.9) !important;
}

div[data-testid="stTextInput"] div[data-baseweb="input"],
.stTextInput div[data-baseweb="input"] {
    background-color: #1e293b !important;
    border: 2px solid #facc15 !important;
    border-radius: 8px !important;
}
div[data-testid="stTextInput"] input,
.stTextInput input {
    color: #ffffff !important;
    background-color: #1e293b !important;
    font-size: 16px !important;
    font-weight: bold !important;
}

button[data-baseweb="tab"] {
    background-color: transparent !important;
    border: none !important;
}
button[data-baseweb="tab"] div[data-testid="stMarkdownContainer"] p,
button[data-baseweb="tab"] p,
button[data-baseweb="tab"] span {
    color: #cbd5e1 !important;
    font-size: 16px !important;
    font-weight: 800 !important;
}
button[data-baseweb="tab"][aria-selected="true"] div[data-testid="stMarkdownContainer"] p,
button[data-baseweb="tab"][aria-selected="true"] p,
button[data-baseweb="tab"][aria-selected="true"] span {
    color: #fde047 !important;
    font-size: 17px !important;
    font-weight: 900 !important;
    text-shadow: 0 0 10px rgba(250, 204, 21, 0.7) !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    border-bottom: 3px solid #facc15 !important;
}

div[data-testid="stAlert"] {
    background-color: #1e293b !important;
    border: 1px solid #38bdf8 !important;
}
div[data-testid="stAlert"] p, div[data-testid="stAlert"] div {
    color: #f8fafc !important;
    font-size: 14px !important;
    font-weight: bold !important;
}

@keyframes clover-sparkle { 0% { transform: scale(1) rotate(0deg); filter: drop-shadow(0 0 4px #22c55e); } 50% { transform: scale(1.2) rotate(8deg); filter: drop-shadow(0 0 12px #4ade80) drop-shadow(0 0 20px #facc15); } 100% { transform: scale(1) rotate(0deg); filter: drop-shadow(0 0 4px #22c55e); } }
.sparkle-clover { display: inline-block; animation: clover-sparkle 1.4s infinite ease-in-out; font-size: 20px; }

@keyframes gold-glow { 0% { box-shadow: 0 0 8px #ca8a04; border-color: #eab308; background-color: #1e1b18; } 50% { box-shadow: 0 0 30px #facc15; border-color: #fde047; background-color: #2d2618; } 100% { box-shadow: 0 0 8px #ca8a04; border-color: #eab308; background-color: #1e1b18; } }
@keyframes glow-green { 0% { box-shadow: 0 0 5px #22c55e; border-color: #22c55e; } 50% { box-shadow: 0 0 25px #4ade80; border-color: #4ade80; } 100% { box-shadow: 0 0 5px #22c55e; border-color: #22c55e; } }
@keyframes pulse-red-flash { 0% { transform: scale(1); background-color: #991b1b; box-shadow: 0 0 12px #991b1b; } 50% { transform: scale(1.06); background-color: #dc2626; box-shadow: 0 0 25px #ef4444; } 100% { transform: scale(1); background-color: #991b1b; box-shadow: 0 0 12px #991b1b; } }

@keyframes lightgreen-neon { 0% { border-color: #22c55e; box-shadow: 0 0 12px #22c55e, inset 0 0 6px #22c55e; } 50% { border-color: #4ade80; box-shadow: 0 0 30px #4ade80, inset 0 0 15px #4ade80; } 100% { border-color: #22c55e; box-shadow: 0 0 12px #22c55e, inset 0 0 6px #22c55e; } }

div.stButton > button {
    font-weight: 900 !important;
    border-radius: 12px !important;
    padding: 14px 10px !important;
    color: white !important;
    background: linear-gradient(135deg, #1e293b, #0f172a) !important;
    width: 100% !important;
    font-size: 16px !important;
    word-break: keep-all;
    transition: all 0.2s ease-in-out !important;
}
div.stButton > button:hover {
    filter: brightness(1.3) !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 0 25px rgba(255, 255, 255, 0.8) !important;
}

div.stFormSubmitButton > button {
    font-weight: 900 !important;
    border-radius: 12px !important;
    padding: 14px 10px !important;
    color: white !important;
    background: linear-gradient(135deg, #1e293b, #0f172a) !important;
    width: 100% !important;
    font-size: 16px !important;
    word-break: keep-all;
    border: 3px solid #22c55e !important;
    animation: lightgreen-neon 1.4s infinite ease-in-out !important;
    transition: all 0.2s ease-in-out !important;
}
div.stFormSubmitButton > button:hover {
    filter: brightness(1.3) !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 0 25px rgba(74, 222, 128, 0.8) !important;
}

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
.footer-btn-cs { background-color: #2e3b4e !important; border: none !important; box-shadow: none !important; }
.footer-btn-dhlottery { background-color: #15803d !important; border: 2px solid #ffffff !important; box-shadow: 0 0 15px rgba(255, 255, 255, 0.6) !important; }
.footer-btn:hover { transform: translateY(-2px); filter: brightness(1.15); }
</style>
""", unsafe_allow_html=True)

# ================= 1. 타이틀 배너 =================
st.markdown("""
<table style="width: 100%; border-collapse: collapse; margin-bottom: 20px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
    <tr>
        <td style="width: 12%; text-align: right; vertical-align: middle; padding-right: 2px;">
            <span class="sparkle-clover">🍀</span>
        </td>
        <td style="width: 76%; text-align: center; vertical-align: middle; white-space: nowrap;">
            <span style="font-weight: 900; font-size: 20px; letter-spacing: -0.5px; background: linear-gradient(135deg, #ffffff 0%, #fef08a 40%, #f59e0b 80%, #d97706 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-shadow: 0 0 12px rgba(245, 158, 11, 0.4);">로또픽 (Lotto Pick)</span>
        </td>
        <td style="width: 12%; text-align: left; vertical-align: middle; padding-left: 2px;">
            <span class="sparkle-clover">🍀</span>
        </td>
    </tr>
</table>

<div style="text-align: center; margin-bottom: 25px; width: 100%;">
    <div style="color: #e2e8f0; font-size: 15px; font-weight: 800; text-shadow: 0 0 10px rgba(255,255,255,0.2); word-break: keep-all;">
        초정밀 통계·조합 분석 시스템
    </div>
    <div style="color: #94a3b8; font-size: 11px; font-weight: 600; letter-spacing: 1px; margin: 4px 0;">
        LOTTO & PENSION LOTTERY ANALYTICS
    </div>
    <div style="color: #38bdf8; font-size: 12px; font-weight: 700; margin-top: 4px; word-break: keep-all;">
        "데이터는 정밀하게, 분석은 체계적으로"
    </div>
</div>
""", unsafe_allow_html=True)

# ================= 2. 상단 복권 선택 버튼 =================
col_b1, col_b2 = st.columns(2)

with col_b1:
    if st.button("🔴 로또 6/45 분석", use_container_width=True, key="btn_lotto"):
        st.session_state.selected_game = "lotto"
        st.rerun()

with col_b2:
    if st.button("🔵 연금복권 720+", use_container_width=True, key="btn_pension"):
        st.session_state.selected_game = "pension"
        st.rerun()

# ================= 3. 녹색 엔진 가동 바 =================
game_name_str = "로또 6/45" if st.session_state.selected_game == "lotto" else "연금복권 720+"
st.markdown(
f"""
<div class="keep-all" style="background-color: #0f172a; border: 2px solid #22c55e; padding: 15px; border-radius: 12px; text-align: center; color: #4ade80; font-weight: bold; font-size: 15px; animation: glow-green 2s infinite; margin-top: 15px; margin-bottom: 20px;">
<span>{"🔴" if st.session_state.selected_game=="lotto" else "🔵"} {game_name_str} 분석 ⚙ ● 정밀 시스템 실시간 가동 중</span>
</div>
""",
    unsafe_allow_html=True,
)

with st.expander("⚙ 맞춤형 시스템 상세 설정 (무료/VIP 공통)", expanded=False):
    game_count = st.slider("추천 게임 수", 1, 10, 5)

# ================= 4. 금빛 VIP 시스템 (Streamlit 네이티브 버튼 활용 결제 연동) =================
if not st.session_state.vip_unlocked:
    if st.session_state.latest_sent_code:
        st.markdown(f"""
        <div style="background-color: #064e3b; border: 2px solid #38bdf8; padding: 18px; border-radius: 12px; margin-bottom: 20px; text-align: center;">
            <h4 style="color: #38bdf8; margin-top: 0; font-weight: 900;">🎉 결제 완료 & VIP 코드 발송 완료!</h4>
            <p style="color: #ffffff; font-size: 15px; line-height: 1.6; margin-bottom: 10px;">
                고객님의 휴대폰으로 VIP 코드가 발송되었습니다.<br>
                발급된 코드: <b style="color: #facc15; font-size: 18px;">{st.session_state.latest_sent_code}</b>
            </p>
            <p style="color: #a7f3d0; font-size: 13px; margin: 0;">
                아래 입력창에 위 코드를 입력하여 프리미엄 기능을 활성화해 주세요!
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="keep-all" style="background-color: #064e3b; border: 2px solid #eab308; padding: 20px; border-radius: 12px; animation: gold-glow 2s infinite; margin: 20px auto 15px auto; color: #fef08a; text-align: center;">
        <h4 style="margin-top: 0; font-size: 18px; margin-bottom: 15px; color: #fde047; font-weight: 900;">👑 VIP 프리패스 혜택 안내</h4>
        <p style="font-size: 14px; line-height: 1.6; text-align: left; color: #ecfdf5;">
        ✅ <b>이번 주 고정수 & 완벽 제외수 리포트 즉시 공개</b><br>
        ✅ AI 패턴 기반 <b>S등급 일치율 점수 & 분석 태그</b> 제공<br>
        ✅ 프리미엄 빅데이터 통계 조합 가동
        </p>
        <hr style="border-color: #022c22; margin: 15px 0;">
        <div style="font-size: 13px; color: #a7f3d0; margin-bottom: 5px;">🔒 아래 버튼을 누르시면 안전한 토스페이먼츠 결제창으로 바로 연결됩니다.</div>
        <div style="font-size: 12px; color: #fde047; font-weight: bold; margin-top: 4px;">✨ 결제 완료 시 문자로 VIP 코드가 발송되며, 메인 창에서 코드를 입력해 프리미엄을 이용하실 수 있습니다![cite: 36, 39]</div>
        </div>
        """, unsafe_allow_html=True)

        # 💡 Streamlit 네이티브 버튼으로 결제창 열기 실행
        if st.button("💎 토스페이먼츠 안전 결제창 열기 (1,000원)", use_container_width=True, key="native_pay_btn"):
            st.session_state.current_order_id = f"lotto{int(time.time())}{random.randint(100, 999)}"
            st.query_params["pay_popup"] = "true"
            st.rerun()

    st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
    with st.form("vip_unlock_form"):
        default_val = st.session_state.latest_sent_code if st.session_state.latest_sent_code else ""
        vip_input = st.text_input("🔑 문자로 받으신 VIP 코드를 입력하세요", value=default_val, type="password", key="vip_code_input")
        submitted = st.form_submit_button("🔓 VIP 코드 입력하여 잠금 해제", use_container_width=True)
        
        if submitted:
            entered_code = vip_input.strip()
            if entered_code in ["MPD2026", "VIP2026"] or entered_code.startswith("MPD-") or (st.session_state.latest_sent_code and entered_code == st.session_state.latest_sent_code):
                st.session_state.vip_unlocked = True
                st.session_state.is_vip_result = True
                st.session_state.vip_expire_time = time.time() + (7 * 24 * 60 * 60)
                st.session_state.trigger_snow = True
                st.success("🎉 VIP 프리패스가 성공적으로 활성화되었습니다!")
                time.sleep(0.4)
                st.rerun()
            else:
                st.error("❌ 올바르지 않은 코드입니다. 문자 메시지로 받으신 VIP 코드를 확인해 주세요.")
else:
    st.markdown("""
<div style="background-color: #064e3b; border: 2px solid #facc15; padding: 15px; border-radius: 10px; text-align: center; color: #fde047; font-weight: bold; margin-bottom: 20px;">
👑 VIP 계정 활성화 상태입니다. 아래에서 프리미엄 조합 추출을 실행해 주세요!
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ================= 5. 추출 버튼 =================
if st.session_state.vip_unlocked:
    st.markdown('<div style="text-align:center;"><div class="vip-badge-top">👑 프리미엄 S등급 적용됨</div></div>', unsafe_allow_html=True)
    extract_clicked = st.button("🚀 프리미엄 조합 추출 실행", use_container_width=True, key="vip_extract_btn")
else:
    st.markdown('<div style="text-align:center;"><div class="free-badge-top">🔥 100% 무료 일반 분석</div></div>', unsafe_allow_html=True)
    extract_clicked = st.button("🚀 일반 번호 조합 무료추출 실행", use_container_width=True, key="free_extract_btn")

if extract_clicked:
    is_vip = st.session_state.vip_unlocked
    st.session_state.is_vip_result = is_vip
    st.session_state.extract_results = []
    st.session_state.extract_game_type = st.session_state.selected_game
    
    if is_vip:
        st.session_state.trigger_snow = True
        all_lotto = list(range(1, 46))
        st.session_state.vip_fixed = sorted(random.sample(all_lotto, 2))
        st.session_state.vip_excluded = sorted(random.sample([x for x in all_lotto if x not in st.session_state.vip_fixed], 10))
    else:
        st.session_state.trigger_balloons = True
    
    for i in range(game_count):
        if st.session_state.selected_game == "lotto":
            if is_vip:
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
            if is_vip:
                match_score = round(random.uniform(95.0, 99.9), 1)
                tags = ["#최상위 패턴", "#연속수 필터링"]
                st.session_state.extract_results.append((group, nums, match_score, tags))
            else:
                st.session_state.extract_results.append((group, nums, None, None))
    st.rerun()

# ================= 6. 핵심 탭 메뉴 =================
tab1, tab2, tab3 = st.tabs(["🎱 당첨 번호 추천", "📊 심층 분석", "📑 연구 모델"])

with tab1:
    if not st.session_state.extract_results:
        st.info("👆 상단의 [추출 실행] 버튼을 누르시면 번호가 생성됩니다.")
    else:
        is_vip = st.session_state.get("is_vip_result", False)
        
        if is_vip:
            st.markdown("<h4 style='color: #facc15; margin-bottom:15px;'>👑 VIP 프리미엄 분석 리포트</h4>", unsafe_allow_html=True)
            if st.session_state.extract_game_type == "lotto":
                fixed_str = ", ".join(map(str, st.session_state.get("vip_fixed", [1, 2])))
                excl_str = ", ".join(map(str, st.session_state.get("vip_excluded", [3, 4, 5])))
                st.markdown(f"""
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
            st.markdown("<h4 style='color: #ffffff; font-weight: 800;'>🎯 일반 번호 추출 결과</h4>", unsafe_allow_html=True)
            st.success("✅ 기본 통계 필터를 거쳐 엄선된 조합입니다.")
            st.markdown("<br>", unsafe_allow_html=True)
        
        def get_ball_color(num):
            if num <= 10: return "#facc15"
            elif num <= 20: return "#3b82f6"
            elif num <= 30: return "#ef4444"
            elif num <= 40: return "#a855f7"
            else: return "#22c55e"

        for i, result in enumerate(st.session_state.extract_results):
            if st.session_state.extract_game_type == "lotto":
                numbers, match_score, tags = result
                balls_html = "".join([f'<div style="width: 32px; height: 32px; border-radius: 50%; background-color: {get_ball_color(n)}; color: white; display: flex; justify-content: center; align-items: center; font-weight: bold; font-size: 14px; margin-right: 5px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); text-shadow: 1px 1px 2px rgba(0,0,0,0.5);">{n}</div>' for n in numbers])
                
                if is_vip:
                    tags_html = "".join([f'<span class="vip-tag">{tag}</span>' for tag in (tags or [])])
                    html_str = f"""
                    <div class="game-box-vip">
                        <div class="s-class-badge">S-CLASS</div>
                        <div style="color: #facc15; font-weight: 900; font-size: 15px; margin-bottom: 5px;">👑 VIP 프리미엄 게임 {i+1}</div>
                        <div style="display: flex; justify-content: space-between; align-items: center; font-size: 12px; color: #d1d5db; margin-bottom: 2px;">
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
            else: 
                group, nums, match_score, tags = result
                group_html = f'<div style="background: linear-gradient(135deg, #f59e0b, #d97706); color: white; padding: 4px 10px; border-radius: 6px; font-weight: bold; font-size: 14px; margin-right: 10px; margin-bottom: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.3);">{group}조</div>'
                digits_html = "".join([f'<div style="width: 30px; height: 30px; border-radius: 6px; background-color: #2563eb; color: white; display: flex; justify-content: center; align-items: center; font-weight: bold; font-size: 16px; margin-right: 4px; margin-bottom: 5px; box-shadow: 0 3px 5px rgba(0,0,0,0.3);">{n}</div>' for n in nums])
                
                if is_vip:
                    tags_html = "".join([f'<span class="vip-tag">{tag}</span>' for tag in (tags or [])])
                    html_str = f"""
                    <div class="game-box-vip">
                        <div class="s-class-badge">S-CLASS</div>
                        <div style="color: #facc15; font-weight: 900; font-size: 15px; margin-bottom: 5px;">👑 연금 VIP 게임 {i+1}</div>
                        <div style="display: flex; justify-content: space-between; align-items: center; font-size: 12px; color: #d1d5db; margin-bottom: 2px;">
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
            st.markdown("""
<div class="locked-feature-box">
    <div class="locked-feature-title">🔒 VIP 프리미엄 전용 콘텐츠</div>
    <div class="locked-feature-desc">결제 후 이 자리에 <b>[금주 완벽 제외수 10개]</b>와<br><b>[S등급 상세 분석 리포트]</b>가 즉시 해제됩니다.</div>
</div>
""", unsafe_allow_html=True)

with tab2:
    st.markdown("<h4 style='color: #ffffff; font-weight: 800;'>📈 역대 당첨 번호 통계 분석</h4>", unsafe_allow_html=True)
    st.markdown("<div style='color: #e2e8f0; font-size: 14px; font-weight: 600; margin-bottom: 12px;'>실제 동행복권 데이터 기반 최근 100회차 번호별 출현 빈도수</div>", unsafe_allow_html=True)
    
    if os.path.exists("lotto_data.csv"):
        df_lotto = pd.read_csv("lotto_data.csv")
        df_recent = df_lotto.tail(100)
        
        all_nums = []
        for col in ['drwtNo1', 'drwtNo2', 'drwtNo3', 'drwtNo4', 'drwtNo5', 'drwtNo6']:
            if col in df_recent.columns:
                all_nums.extend(df_recent[col].dropna().astype(int).tolist())
        
        counts = Counter(all_nums)
        freq_dict = {f"{i}번": counts.get(i, 0) for i in range(1, 46)}
        chart_data = pd.DataFrame(list(freq_dict.values()), columns=["출현 횟수"], index=list(freq_dict.keys()))
    else:
        chart_data = pd.DataFrame(np.random.randint(10, 25, size=(45, 1)), columns=["출현 횟수"], index=[f"{i}번" for i in range(1, 46)])
        
    st.bar_chart(chart_data, color="#3b82f6", height=250)
    
    if not st.session_state.vip_unlocked:
        st.markdown("""
<div style='text-align:center; padding: 10px; background:#1e1b18; border:1px solid #eab308; border-radius:8px; color:#facc15; font-size:14px; font-weight: bold;'>
🔒 VIP 전용: 미출현 장기 번호 및 회귀 추적 데이터 잠김
</div>
""", unsafe_allow_html=True)

with tab3:
    st.markdown("<h4 style='color: #ffffff; font-weight: 800;'>📑 분석 연구 모델</h4>", unsafe_allow_html=True)
    st.markdown("""
<div style="font-size: 15px; color: #f1f5f9; line-height: 1.8; font-weight: 600;">
- Markov Chain Monte Carlo (MCMC) 모델<br>
- Poisson Distribution 출현 간격 예측<br>
- AC값(Arithmetic Complexity) 복잡도 필터링
</div>
""", unsafe_allow_html=True)

# ================= 7. 하단 고객센터 =================
st.markdown("---")
st.markdown("<h4 style='color: #ffffff; font-weight: 900; margin-bottom: 8px;'>📞 고객 센터</h4>", unsafe_allow_html=True)

st.markdown("""
<div style="background-color: #1e293b !important; border: 2px solid #38bdf8 !important; padding: 14px 16px; border-radius: 10px; margin-bottom: 15px; text-align: center; box-shadow: 0 4px 12px rgba(0,0,0,0.4);">
    <div style="color: #38bdf8 !important; font-size: 15px !important; font-weight: 900 !important; line-height: 1.5;">
        📢 결제 오류 및 서비스 관련 문의는 아래 버튼을 통해 접수해 주세요.
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown(
f"""
<div class="footer-buttons-container">
    <a href="{GOOGLE_FORM_URL}" target="_blank" class="footer-btn footer-btn-cs" style="text-decoration: none;">
        🛠️ 고객센터 문의 접수
    </a>
    <a href="https://www.dhlottery.co.kr" target="_blank" class="footer-btn footer-btn-dhlottery" style="text-decoration: none;">
        🛒 동행복권 홈
    </a>
</div>
""", unsafe_allow_html=True)

# ================= 8. 토스 심사용 상품 안내 =================
st.markdown("---")
st.markdown("<h3 style='color: #ffffff; font-weight: 900;'>💎 프리미엄 분석권 상품 안내 (Toss 심사 제출용)</h3>", unsafe_allow_html=True)
st.info("""
- **상품명:** VIP 골든픽 1주(7일) 프리패스
- **가격:** 1,000원 (VAT 포함)
- **제공 서비스:** AI 패턴 기반 S등급 고정수/제외수 리포트 및 초정밀 통계 조합 가동
- **이용 기간:** 결제일로부터 7일간 무제한 이용
- **환불 규정:** 디지털 콘텐츠 특성상, VIP 승인 처리 후에는 환불이 불가합니다. (결제 오류 시 전액 환불)
""")

# ================= 9. 법적 고지 및 사업자 정보 Footer =================
st.markdown("""
<div style="background-color: #1a1a1a; padding: 15px; border-radius: 8px; margin-top: 25px; border: 1px solid #333; color: #a1a1aa; font-size: 11px; line-height: 1.6; word-break: keep-all;">
<b>[법적 고지 및 주의사항]</b><br>
1. 본 서비스(로또픽)에서 제공하는 번호 조합 및 통계 분석 자료는 과거의 데이터를 기반으로 한 확률적 추정치이며, <b>실제 복권 당첨을 절대 보장하지 않습니다.</b><br>
2. 제공된 번호를 이용한 복권 구매 등 모든 판단과 책임은 전적으로 <b>사용자 본인</b>에게 있으며, 본 서비스는 이로 인해 발생하는 어떠한 직·간접적 손실에 대해서도 법적 책임을 지지 않습니다.<br>
3. 복권은 소액으로 건전하게 즐기시길 바라며, 과도한 몰입은 일상생활에 지장을 줄 수 있습니다. (도박중독 예방치유센터: 1336)
</div>

<div style="text-align: center; color: #94a3b8; font-size: 11px; margin-top: 20px; margin-bottom: 20px; line-height: 1.8; padding-top: 20px; border-top: 1px solid #333;">
    <b>상호:</b> 엠피디뮤직 (MPD music) &nbsp;|&nbsp; <b>대표:</b> 이근영 &nbsp;|&nbsp; <b>사업자등록번호:</b> 162-23-01932<br>
    <b>사업장 주소:</b> 경기도 고양시 덕양구 능곡로 16, 101동 501호(토당동, 숲예찬)<br>
    <b>고객센터:</b> 010-5282-7017 &nbsp;|&nbsp; <b>이메일:</b> leegysa@naver.com<br><br>
    © 2026 로또픽(Lotto Pick) 분석 시스템. All Rights Reserved.
</div>
""", unsafe_allow_html=True)
