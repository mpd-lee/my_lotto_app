# -*- coding: utf-8 -*-
"""
로또픽 (Lotto Pick) - 초정밀 통계·조합 분석 시스템 (무한 로딩 멈춤 현상 완벽 해결 최종본)
- 토스페이먼츠 안전 결제창 및 Solapi 자동 문자 연동
- 로또 6/45 및 연금복권 720+ 통합 프리미엄 시스템
"""

import random
import time
import os
from collections import Counter
import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import requests
import hmac
import hashlib
from datetime import datetime, timezone

# ================= URL 및 키 관리 =================
TOSS_CLIENT_KEY = "test_ck_kYG57Eba3GblXWjwLeyw8pWDOxmA"    # 📌 토스 클라이언트 키
GOOGLE_FORM_URL = "https://forms.gle/RA8i731z2QFi7ByMA"    # 📌 고객센터 구글 폼 링크
APP_SITE_URL = "https://mylottoapp-3mygrnqs6j7ard8n3zrvj9.streamlit.app" # 📌 실제 배포 주소

# ================= 솔라피(Solapi) API 설정 =================
SOLAPI_API_KEY = "NCSKDYPYYPOSNLNV"
SOLAPI_API_SECRET = "DWIXUPBFG7ZGPOCNYY8MVNYWRUW9XTTA"
SOLAPI_SENDER_PHONE = "01052827017" # 등록하신 발신번호

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

# 구글 애드센스 소유권 확인 메타태그
st.markdown('<meta name="google-adsense-account" content="ca-pub-2324282297166072">', unsafe_allow_html=True)

# 세션 상태 초기화
if "vip_unlocked" not in st.session_state:
    st.session_state.vip_unlocked = False
if "vip_expire_time" not in st.session_state:
    st.session_state.vip_expire_time = 0
if "current_order_id" not in st.session_state:
    st.session_state.current_order_id = ""

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

# ================= 결제 성공/실패 쿼리 처리 (무한 로딩 방지 안정화) =================
try:
    query_params = st.query_params
    if "payment_success" in query_params:
        if not st.session_state.vip_unlocked:
            st.session_state.vip_unlocked = True
            st.session_state.is_vip_result = True
            st.session_state.vip_expire_time = time.time() + (7 * 24 * 60 * 60)
            
            generated_vip_code = f"MPD-{random.randint(1000, 9999)}"
            send_vip_sms(SOLAPI_SENDER_PHONE, generated_vip_code)
            
        st.session_state.trigger_snow = True
        st.query_params.clear()
        st.toast("🎉 토스 결제가 완료되었습니다! VIP 프리패스가 활성화되었습니다.", icon="✨")
    elif "payment_fail" in query_params:
        st.query_params.clear()
        st.error("❌ 결제가 취소되었거나 실패했습니다. 다시 시도해 주세요.")
except Exception:
    pass

# ================= 🚨 전체 화면 결제 모드 (pay_popup=true 시 구동) =================
if "pay_popup" in st.query_params and st.query_params["pay_popup"] == "true" and not st.session_state.vip_unlocked:
    st.markdown("""
    <style>
    .block-container { max-width: 800px !important; padding-top: 1.5rem !important; }
    
    div.stButton > button[kind="secondary"] {
        background: linear-gradient(135deg, #1e293b, #0f172a) !important;
        border: 2px solid #ef4444 !important;
        color: #ffffff !important;
        font-weight: 900 !important;
        font-size: 16px !important;
        box-shadow: 0 0 15px rgba(239, 68, 68, 0.6) !important;
        border-radius: 12px !important;
        padding: 14px 10px !important;
        transition: all 0.2s ease-in-out !important;
    }
    div.stButton > button[kind="secondary"]:hover {
        background: #dc2626 !important;
        border-color: #fca5a5 !important;
        box-shadow: 0 0 25px rgba(239, 68, 68, 1) !important;
        transform: translateY(-2px) !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    col_c1, col_c2, col_c3 = st.columns([1, 4, 1])
    with col_c2:
        if st.button("❌ 결제 취소하고 메인으로 돌아가기", use_container_width=True, key="cancel_pay_mode"):
            st.query_params.clear()
            st.rerun()
            
    if not st.session_state.current_order_id:
        st.session_state.current_order_id = f"lotto{int(time.time())}{random.randint(100, 999)}"
        
    order_id_gen = st.session_state.current_order_id
    
    toss_button_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <script src="https://js.tosspayments.com/v1/payment"></script>
        <style>
            body {{ margin: 0; padding: 0; background-color: transparent; }}
        </style>
    </head>
    <body>
        <script>
            window.onload = function() {{
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
                            alert("결제 알림: " + error.message);
                        }}
                    }});
                }} catch(e) {{
                    alert("결제창 초기화 중 오류가 발생했습니다: " + e.message);
                }}
            }};
        </script>
    </body>
    </html>
    """
    components.html(toss_button_html, height=680, scrolling=True)
    st.stop()

# ================= 세레모니 실행 처리 =================
if st.session_state.trigger_snow:
    st.snow()
    st.session_state.trigger_snow = False

if st.session_state.trigger_balloons:
    st.balloons()
    st.session_state.trigger_balloons = False

# ================= 자바스크립트 기반 버튼 및 네온 스타일 강제 적용 =================
components.html("""
<script>
function applyStrictStyles() {
    try {
        const doc = window.parent.document;
        const buttons = doc.querySelectorAll('button');
        buttons.forEach(btn => {
            const text = btn.innerText || btn.textContent || "";
            if (text.includes('토스페이먼츠 안전 결제창 열기')) {
                btn.style.setProperty('background', 'linear-gradient(135deg, #059669 0%, #047857 100%)', 'important');
                btn.style.setProperty('border', '2px solid #facc15', 'important');
                btn.style.setProperty('box-shadow', '0 0 20px rgba(250, 204, 21, 0.8)', 'important');
                btn.style.setProperty('color', '#ffffff', 'important');
            } else if (text.includes('결제 취소하고 메인으로 돌아가기')) {
                btn.style.setProperty('border', '2px solid #ef4444', 'important');
                btn.style.setProperty('box-shadow', '0 0 15px rgba(239, 68, 68, 0.8)', 'important');
                btn.style.setProperty('background', '#1e293b', 'important');
                btn.style.setProperty('color', '#ffffff', 'important');
                btn.style.setProperty('font-weight', '900', 'important');
            } else if (text.includes('로또 6/45 분석')) {
                btn.style.setProperty('border', '3px solid #ef4444', 'important');
                btn.style.setProperty('box-shadow', '0 0 16px #ef4444, inset 0 0 8px #ef4444', 'important');
            } else if (text.includes('연금복권 720+')) {
                btn.style.setProperty('border', '3px solid #3b82f6', 'important');
                btn.style.setProperty('box-shadow', '0 0 16px #3b82f6, inset 0 0 8px #3b82f6', 'important');
            } else if (text.includes('일반 번호 조합 무료추출 실행')) {
                btn.style.setProperty('border', '3px solid #38bdf8', 'important');
                btn.style.setProperty('box-shadow', '0 0 16px #38bdf8, inset 0 0 8px #38bdf8', 'important');
            } else if (text.includes('프리미엄 조합 추출 실행')) {
                btn.style.setProperty('border', '3px solid #eab308', 'important');
                btn.style.setProperty('box-shadow', '0 0 16px #eab308, inset 0 0 8px #eab308', 'important');
            }
        });
    } catch(e) {}
}
setInterval(applyStrictStyles, 50);
</script>
""", height=0)

# ================= 커스텀 CSS 스타일 =================
st.markdown(
"""
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
""",
    unsafe_allow_html=True,
)

# ================= 1. 타이틀 배너 =================
st.markdown(
"""
<table style="width: 100%; border-collapse: collapse; margin-bottom: 20px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
    <tr>
        <td style="width: 12%; text-align: right; vertical-align: middle; padding-right: 2px;">
            <span class="sparkle-clover">🍀</span>
        </td>
        <td style="width: 76%; text-align: center; vertical-align: middle; white-space: nowrap;">
            <span style="font-weight: 900; font-size: 20px; letter-spacing: -0.5px; background: linear-gradient(135deg, #ffffff 0%, #fef08a 40%, #f59e0b 80%,
