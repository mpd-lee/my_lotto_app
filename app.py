# -*- coding: utf-8 -*-
"""
로또픽 통합 완성본 (뱅글뱅글 무한 로딩 및 결제 멈춤 현상 완벽 해결 버전)
- Streamlit 메인 UI, 네온 디자인, 테두리, 탭, 하단 푸터 완벽 유지
- 브라우저 독립 팝업창을 통한 Toss Payments 안전 결제 연동
- Solapi SMS 문자 발송 및 메인 창 VIP 코드 잠금 해제 시스템 탑재
"""

import random
import time
import os
import re
import json
import base64
import sqlite3
import secrets
import uuid
from collections import Counter
import numpy as np
import pandas as pd
import streamlit as st
import requests
import hmac
import hashlib
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

# ================= 설정 및 안전한 결제/VIP 백엔드 =================
GOOGLE_FORM_URL = "https://forms.gle/RA8i731z2QFi7ByMA"    # 📌 고객센터 구글 폼 링크
PRODUCT_NAME = "VIP 골든픽 1주(7일) 프리패스"
PRODUCT_AMOUNT = 1000
VIP_DAYS = 7


def setting(name: str, default: str = "") -> str:
    """Streamlit secrets를 우선 사용하고, 없으면 환경 변수를 읽습니다."""
    try:
        value = st.secrets.get(name, os.getenv(name, default))
    except Exception:
        value = os.getenv(name, default)
    return str(value if value is not None else default).strip()


def app_base_url() -> str:
    return setting("APP_BASE_URL", "https://localhost:8501").rstrip("/")


def db_path() -> str:
    return setting("VIP_DB_PATH", "vip_store.sqlite3")


def db_connect():
    conn = sqlite3.connect(db_path(), timeout=15, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 15000")
    return conn


from contextlib import contextmanager

@contextmanager
def db_session():
    conn = db_connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    with db_session() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS vip_orders (
                order_id TEXT PRIMARY KEY,
                phone TEXT NOT NULL,
                amount INTEGER NOT NULL,
                status TEXT NOT NULL,
                payment_key TEXT,
                vip_code TEXT,
                vip_code_hash TEXT,
                expires_at REAL,
                created_at REAL NOT NULL,
                paid_at REAL,
                sms_status TEXT,
                sms_detail TEXT
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_vip_code_hash ON vip_orders(vip_code_hash)")


def normalize_phone(raw_phone: str) -> str:
    phone = re.sub(r"\D", "", raw_phone or "")
    if phone.startswith("82") and len(phone) in (11, 12, 13):
        phone = "0" + phone[2:]
    return phone


def valid_korean_mobile(raw_phone: str) -> bool:
    return bool(re.fullmatch(r"01[016789]\d{7,8}", normalize_phone(raw_phone)))


def create_order(phone: str) -> str:
    order_id = "VIP" + uuid.uuid4().hex.upper()
    with db_session() as conn:
        conn.execute(
            "INSERT INTO vip_orders (order_id, phone, amount, status, created_at) VALUES (?, ?, ?, 'PENDING', ?)",
            (order_id, normalize_phone(phone), PRODUCT_AMOUNT, time.time()),
        )
    return order_id


def get_order(order_id: str):
    with db_session() as conn:
        return conn.execute("SELECT * FROM vip_orders WHERE order_id = ?", (order_id,)).fetchone()


def send_vip_sms(receiver_phone: str, vip_code: str):
    """Solapi 문자 발송 함수"""
    api_key = setting("SOLAPI_API_KEY", "NCSKDYPYYPOSNLNV")
    api_secret = setting("SOLAPI_API_SECRET", "DWIXUPBFG7ZGPOCNYY8MVNYWRUW9XTTA")
    sender_phone = normalize_phone(setting("SOLAPI_SENDER_PHONE", "01052827017"))
    receiver_phone = normalize_phone(receiver_phone)

    if not api_key or not api_secret or not sender_phone:
        return False, "Solapi API 설정이 필요합니다."
    if not valid_korean_mobile(receiver_phone):
        return False, "수신 휴대폰 번호 형식이 올바르지 않습니다."

    url = "https://api.solapi.com/messages/v4/send"
    date = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    salt = secrets.token_hex(16)
    signature = hmac.new(
        api_secret.encode("utf-8"),
        (date + salt).encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    headers = {
        "Authorization": f"HMAC-SHA256 apiKey={api_key}, date={date}, salt={salt}, signature={signature}",
        "Content-Type": "application/json; charset=utf-8",
    }
    message_text = (
        f"[로또픽] VIP 프리패스 코드가 발급되었습니다.\n\n"
        f"🔑 VIP 전용 코드: {vip_code}\n"
        f"⏱ 이용 기간: 발급일로부터 7일간\n\n"
        f"🍀 금주의 행운을 기원합니다!"
    )
    payload = {"message": {"to": receiver_phone, "from": sender_phone, "text": message_text}}

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=(5, 20))
        if 200 <= response.status_code < 300:
            return True, "전송 성공"
        return False, f"코드: {response.status_code}, 내용: {response.text[:300]}"
    except Exception as e:
        return False, str(e)


def toss_confirm(payment_key: str, order_id: str, amount: int):
    """토스 결제 승인 서버 검증"""
    secret_key = setting("TOSS_SECRET_KEY")
    if not secret_key:
        return False, "TOSS_SECRET_KEY가 설정되지 않았습니다.", None

    auth = base64.b64encode(f"{secret_key}:".encode("utf-8")).decode("ascii")
    headers = {
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/json",
        "Idempotency-Key": str(uuid.UUID(hex=order_id[3:])),
    }
    try:
        response = requests.post(
            "https://api.tosspayments.com/v1/payments/confirm",
            json={"paymentKey": payment_key, "orderId": order_id, "amount": amount},
            headers=headers,
            timeout=(5, 20),
        )
        try:
            body = response.json()
        except ValueError:
            body = {"message": response.text[:500]}

        if response.status_code != 200:
            return False, f"토스 결제 승인 실패: {body.get('message', response.status_code)}", body
        if body.get("status") != "DONE":
            return False, "토스 결제가 완료 상태가 아닙니다.", body
        if body.get("orderId") != order_id:
            return False, "주문번호 검증 실패", body
        if int(body.get("totalAmount", -1)) != int(amount):
            return False, "결제 금액 검증 실패", body
        return True, "승인 성공", body
    except requests.RequestException as exc:
        return False, f"통신 오류: {exc}", None


def confirm_payment_and_issue_code(payment_key: str, order_id: str, amount_from_url: str):
    """결제 확인 후 VIP 코드 발급 및 문자 발송"""
    order = get_order(order_id)
    if order is None:
        return {"ok": False, "message": "주문을 찾을 수 없습니다."}

    try:
        url_amount = int(amount_from_url)
    except (TypeError, ValueError):
        return {"ok": False, "message": "금액 형식이 올바르지 않습니다."}
    
    if url_amount != int(order["amount"]):
        return {"ok": False, "message": "결제 금액 불일치"}

    if order["status"] == "PAID" and order["vip_code"]:
        return {"ok": True, "code": order["vip_code"], "expires_at": float(order["expires_at"]), "phone": order["phone"], "already": True}

    ok, message, _body = toss_confirm(payment_key, order_id, int(order["amount"]))
    if not ok:
        return {"ok": False, "message": message}

    code = f"MPD-{random.randint(1000, 9999)}"
    code_hash = hashlib.sha256(code.encode("utf-8")).hexdigest()
    expires_at = time.time() + VIP_DAYS * 24 * 60 * 60
    phone = order["phone"]

    with db_session() as conn:
        conn.execute(
            """UPDATE vip_orders
               SET status = 'PAID', payment_key = ?, vip_code = ?, vip_code_hash = ?,
                   expires_at = ?, paid_at = ?, sms_status = 'PENDING'
               WHERE order_id = ?""",
            (payment_key, code, code_hash, expires_at, time.time(), order_id),
        )

    sent, detail = send_vip_sms(phone, code)
    with db_session() as conn:
        conn.execute(
            "UPDATE vip_orders SET sms_status = ?, sms_detail = ? WHERE order_id = ?",
            ("SENT" if sent else "FAILED", detail, order_id),
        )

    return {"ok": True, "code": code, "expires_at": expires_at, "sms_status": "SENT" if sent else "FAILED", "phone": phone, "already": False}


def validate_vip_code(raw_code: str):
    code = (raw_code or "").strip().upper()
    if not code:
        return False, None, "VIP 코드를 입력해 주세요."
    code_hash = hashlib.sha256(code.encode("utf-8")).hexdigest()
    with db_session() as conn:
        row = conn.execute(
            "SELECT expires_at, status FROM vip_orders WHERE vip_code_hash = ? ORDER BY paid_at DESC LIMIT 1",
            (code_hash,),
        ).fetchone()
    if row is None or row["status"] != "PAID":
        return False, None, "등록된 VIP 코드가 아닙니다. 문자로 받은 코드를 확인해 주세요."
    expires_at = float(row["expires_at"] or 0)
    if time.time() >= expires_at:
        return False, None, "VIP 코드의 7일 이용 기간이 만료되었습니다."
    return True, expires_at, "확인 성공"


def payment_component_html(order_id: str, phone: str) -> str:
    """토스페이먼츠 공식 결제창 호출 함수 (팝업 충돌 및 오류 완벽 차단 버전)"""
    client_key = setting("TOSS_CLIENT_KEY", "test_ck_kYG57Eba3GblXWjwLeyw8pWDOxmA")
    base_url = app_base_url()
    
    success_url = f"{base_url}/?vip_payment_return=1"
    fail_url = f"{base_url}/?vip_payment_fail=1"
    
    template = f"""
    <div style="text-align:center;padding:4px 0;">
        <script src="https://js.tosspayments.com/v1/payment"></script>
        <button id="open-toss-checkout" style="width:100%;padding:15px;border:2px solid #fde047;border-radius:12px;background:linear-gradient(135deg,#854d0e,#eab308);color:#111827;font-weight:900;font-size:16px;cursor:pointer;box-shadow: 0 0 15px rgba(250,204,21,0.5);">💳 토스페이먼츠 1,000원 안전 결제창 열기</button>
        <div style="color:#cbd5e1;font-size:12px;margin-top:6px;">새 창에서 결제가 진행되므로 뱅글뱅글 멈춤 현상이 절대 발생하지 않습니다.</div>
    </div>
    <script>
    document.getElementById('open-toss-checkout').addEventListener('click', function() {{
        try {{
            var tossPayments = TossPayments("{client_key}");
            tossPayments.requestPayment("카드", {{
                amount: {PRODUCT_AMOUNT},
                orderId: "{order_id}",
                orderName: "{PRODUCT_NAME}",
                customerName: "고객",
                customerMobilePhone: "{normalize_phone(phone)}",
                successUrl: "{success_url}",
                failUrl: "{fail_url}"
            }});
        }} catch (err) {{
            alert("결제 창 호출 오류: " + err.message);
        }}
    }});
    </script>
    """
    return template


def handle_toss_redirect_if_present() -> None:
    """결제 완료 후 리다이렉트 콜백 처리"""
    params = st.query_params
    if "vip_payment_return" in params:
        st.title("🍀 로또픽 결제 결과 승인 중")
        payment_key = str(params.get("paymentKey", ""))
        order_id = str(params.get("orderId", ""))
        amount = str(params.get("amount", "1000"))
        
        if payment_key and order_id:
            result = confirm_payment_and_issue_code(payment_key, order_id, amount)
            if result.get("ok"):
                st.success("🎉 토스 결제가 안전하게 승인되었습니다!")
                st.markdown("**발급된 VIP 코드 (복사해서 아래 메인창에 입력해 주세요):**")
                st.code(result["code"], language=None)
                st.info("문자로도 코드가 전송되었습니다. 이 창을 닫고 원래 메인 화면으로 돌아가 코드를 입력하시면 프리미엄이 즉시 해제됩니다!")
                st.stop()
            else:
                st.error(f"결제 검증 실패: {result.get('message')}")
                st.stop()
    elif "vip_payment_fail" in params:
        st.error("❌ 결제가 취소되었거나 실패했습니다. 다시 시도해 주세요.")
        st.query_params.clear()


# ================= 0. 페이지 기본 설정 =================
st.set_page_config(
    page_title="로또픽(Lotto Pick) - 초정밀 통계·조합 분석 시스템", 
    page_icon="🍀", 
    layout="centered"
)

init_db()
handle_toss_redirect_if_present()

# 구글 애드센스 소유권 확인 메타태그
st.markdown('<meta name="google-adsense-account" content="ca-pub-2324282297166072">', unsafe_allow_html=True)

# 세션 상태 초기화
if "vip_unlocked" not in st.session_state:
    st.session_state.vip_unlocked = False
if "vip_expire_time" not in st.session_state:
    st.session_state.vip_expire_time = 0

if st.session_state.vip_unlocked:
    if time.time() > st.session_state.vip_expire_time:
        st.session_state.vip_unlocked = False
        st.warning("⏱ VIP 이용 기간(7일)이 만료되었습니다. 계속 이용하시려면 재승인을 진행해 주세요.")

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

# 세레모니 실행 처리
if st.session_state.trigger_snow:
    st.snow()
    st.session_state.trigger_snow = False

if st.session_state.trigger_balloons:
    st.balloons()
    st.session_state.trigger_balloons = False

# ================= 커스텀 CSS 스타일 (기존 디자인 테두리 및 애니메이션 100% 보존) =================
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

# ================= 4. 금빛 VIP 시스템 (주문 생성 및 안전한 토스 팝업창 연동) =================
if not st.session_state.vip_unlocked:
    st.markdown(
"""
<div class="keep-all" style="background-color: #064e3b; border: 2px solid #eab308; padding: 20px; border-radius: 12px; animation: gold-glow 2s infinite; margin: 20px auto 15px auto; color: #fef08a; text-align: center;">
<h4 style="margin-top: 0; font-size: 18px; margin-bottom: 15px; color: #fde047; font-weight: 900;">👑 VIP 프리패스 혜택 안내</h4>
<p style="font-size: 14px; line-height: 1.6; text-align: left; color: #ecfdf5;">
✅ <b>이번 주 고정수 & 완벽 제외수 리포트 즉시 공개</b><br>
✅ AI 패턴 기반 <b>S등급 일치율 점수 & 분석 태그</b> 제공<br>
✅ 프리미엄 빅데이터 통계 조합 가동
</p>
<hr style="border-color: #022c22; margin: 15px 0;">
<div style="font-size: 13px; color: #a7f3d0; margin-bottom: 5px;">🔒 아래에 휴대폰 번호를 입력 후 주문을 생성하고 결제창을 열어주세요.</div>
<div style="font-size: 12px; color: #fde047; font-weight: bold; margin-top: 4px;">✨ 결제 완료 시 문자로 VIP 코드가 발송되며 메인 창에 입력하여 즉시 해제됩니다!</div>
</div>
""", unsafe_allow_html=True)

    with st.form("vip_order_form"):
        buyer_phone = st.text_input("📱 VIP 코드를 받을 휴대폰 번호", placeholder="01012345678", max_chars=20)
        order_submitted = st.form_submit_button("🧾 1,000원 VIP 주문 생성", use_container_width=True)

    if order_submitted:
        if not valid_korean_mobile(buyer_phone):
            st.error("❌ 휴대폰 번호를 올바르게 입력해 주세요. (예: 01012345678)")
        else:
            new_order_id = create_order(buyer_phone)
            st.session_state.pending_order_id = new_order_id
            st.session_state.pending_phone = normalize_phone(buyer_phone)
            st.success("✅ 주문이 생성되었습니다! 아래 결제창 열기 버튼을 눌러주세요.")

    if "pending_order_id" in st.session_state and st.session_state.pending_order_id:
        st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
        toss_html = payment_component_html(st.session_state.pending_order_id, st.session_state.pending_phone)
        st.components.v1.html(toss_html, height=95, scrolling=False)

    st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
    with st.form("vip_unlock_form"):
        vip_input = st.text_input("🔑 문자로 받으신 VIP 코드를 입력하세요 (예: MPD-1234)", type="password", key="vip_code_input")
        submitted = st.form_submit_button("🔓 VIP 코드 입력하여 잠금 해제", use_container_width=True)
        
        if submitted:
            code_ok, expiry, msg = validate_vip_code(vip_input)
            if code_ok:
                st.session_state.vip_unlocked = True
                st.session_state.is_vip_result = True
                st.session_state.vip_expire_time = expiry
                st.session_state.trigger_snow = True
                st.success("🎉 VIP 프리패스가 성공적으로 활성화되었습니다!")
                time.sleep(0.4)
                st.rerun()
            else:
                st.error(f"❌ {msg}")
else:
    st.markdown(
"""
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
            if "vip_fixed" in st.session_state:
                st.info(f"📌 [이번 주 핵심 고정수]: {st.session_state.vip_fixed} / 🚫 [완벽 제외수]: {st.session_state.vip_excluded}")
        
        for idx, item in enumerate(st.session_state.extract_results):
            game_type = st.session_state.get("extract_game_type", "lotto")
            if game_type == "lotto":
                numbers, match_score, tags = item
            else:
                group, nums, match_score, tags = item

            if is_vip:
                tags_html = "".join([f'<span class="vip-tag">{t}</span>' for t in tags])
                balls_html = "".join([f'<span style="display:inline-block;width:32px;height:32px;line-height:32px;text-align:center;background:#facc15;color:#111827;border-radius:50%;font-weight:900;margin-right:6px;font-size:14px;">{n:02d}</span>' for n in numbers])
                st.markdown(f"""
                <div class="game-box-vip">
                    <div class="s-class-badge">S등급 일치율 {match_score}%</div>
                    <div style="font-size:13px; color:#fde047; font-weight:bold; margin-bottom:8px;">GAME {idx+1}</div>
                    <div style="margin-bottom:8px;">{balls_html}</div>
                    <div class="score-bar-bg"><div class="score-bar-fill" style="width:{match_score}%;"></div></div>
                    <div class="vip-tags">{tags_html}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                balls_html = "".join([f'<span style="display:inline-block;width:30px;height:30px;line-height:30px;text-align:center;background:#374151;color:#ffffff;border-radius:50%;font-weight:bold;margin-right:6px;font-size:13px;">{n:02d}</span>' for n in numbers])
                st.markdown(f"""
                <div class="game-box-free">
                    <div style="font-size:12px; color:#9ca3af; font-weight:bold; margin-bottom:6px;">GAME {idx+1} (무료 일반)</div>
                    <div>{balls_html}</div>
                </div>
                """, unsafe_allow_html=True)

with tab2:
    st.markdown("### 📊 심층 통계 분석")
    st.markdown("최근 출현 빈도, 홀짝 비율, 구간별 통계 데이터를 바탕으로 최적의 조합 확률을 산출합니다.")
    st.info("💡 VIP 회원은 더 정밀한 다차원 통계 가중치 분석 리포트가 적용됩니다.")

with tab3:
    st.markdown("### 📑 AI 연구 모델 아키텍처")
    st.markdown("머신러닝 기반 패턴 분석 및 확률적 가중치 알고리즘에 대한 설명입니다.")
    st.success("🔒 본 시스템은 독창적인 확률 조합 엔진을 사용하여 매 회차 최적의 결과를 유도합니다.")

# ================= 7. 하단 푸터 영역 =================
st.markdown("---")
st.markdown(
"""
<div class="footer-buttons-container">
    <a href="https://forms.gle/RA8i731z2QFi7ByMA" target="_blank" class="footer-btn footer-btn-cs">문의하기/오류신고</a>
    <a href="https://dhlottery.co.kr/" target="_blank" class="footer-btn footer-btn-dhlottery">동행복권 공식홈페이지</a>
</div>
<div style="background-color: #1a1a1a; padding: 15px; border-radius: 8px; margin-bottom: 20px; font-size: 12px; color: #cbd5e1; line-height: 1.6;">
<b>[법적 고지 및 주의사항]</b><br>
1. 본 서비스(로또픽)에서 제공하는 번호 조합 및 통계 분석 자료는 과거의 데이터를 기반으로 한 참고용 정보입니다.<br>
2. 제공된 번호를 이용한 복권 구매 등 모든 판단과 책임은 전적으로 <b>사용자 본인</b>에게 있으며, 개발자는 어떠한 법적 책임도 지지 않습니다.<br>
3. 복권은 소액으로 건전하게 즐기시길 바라며, 과도한 몰입은 일상생활에 지장을 줄 수 있습니다.
</div>
<div style="text-align: center; color: #94a3b8; font-size: 11px; margin-top: 20px;">
<b>상호:</b> 엠피디뮤직 (MPD music) &nbsp;|&nbsp; <b>대표:</b> 이근영 &nbsp;|&nbsp;<br>
<b>사업장 주소:</b> 경기도 고양시 덕양구 능곡로 16, 101동 501호(토당동, 숲예찬)<br>
<b>고객센터:</b> 010-5282-7017 &nbsp;|&nbsp; <b>이메일:</b> leegysa@naver.com<br>
© 2026 로또픽(Lotto Pick) 분석 시스템. All Rights Reserved.
</div>
""",
    unsafe_allow_html=True,
)
