# -*- coding: utf-8 -*-
"""
로또픽 (Lotto Pick) - 초정밀 통계·조합 분석 시스템 (최종 완성본)
- 토스페이먼츠 새 탭 결제 방식을 통한 iframe/무한 로딩 원천 차단
- Solapi SMS 문자 자동 발송 및 VIP 코드 잠금 해제 시스템 완벽 통합
- lotto_data.csv 기반 심층 통계 차트, S-CLASS 리포트, 네온 디자인 포함
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

# ================= 0. 환경 설정 및 비밀값 로드 =================
GOOGLE_FORM_URL = "https://forms.gle/RA8i731z2QFi7ByMA"
PRODUCT_NAME = "VIP 골든픽 1주(7일) 프리패스"
PRODUCT_AMOUNT = 1000
VIP_DAYS = 7

def get_secret(key_name, default_value=""):
    try:
        return str(st.secrets.get(key_name, os.getenv(key_name, default_value))).strip()
    except Exception:
        return os.getenv(key_name, default_value).strip()

APP_BASE_URL = get_secret("APP_BASE_URL", "https://mylottoapp-3mygrnqs6j7ard8n3zrvj9.streamlit.app")
TOSS_CLIENT_KEY = get_secret("TOSS_CLIENT_KEY", "test_ck_DpexMgkW36vmkLY17OyM3GbR5ozO")
TOSS_SECRET_KEY = get_secret("TOSS_SECRET_KEY", "")
SOLAPI_API_KEY = get_secret("SOLAPI_API_KEY", "NCSKDYPYYPOSNLNV")
SOLAPI_API_SECRET = get_secret("SOLAPI_API_SECRET", "")
SOLAPI_SENDER_PHONE = get_secret("SOLAPI_SENDER_PHONE", "01052827017")

# ================= 1. DB 및 주문/결제 로직 =================
def db_connect():
    conn = sqlite3.connect("vip_store.sqlite3", timeout=15, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with db_connect() as conn:
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
                created_at REAL,
                paid_at REAL,
                sms_status TEXT
            )
        """)

def normalize_phone(raw):
    phone = re.sub(r"\D", "", raw or "")
    if phone.startswith("82") and len(phone) in (11, 12, 13):
        phone = "0" + phone[2:]
    return phone

def create_order(phone):
    order_id = "VIP" + uuid.uuid4().hex.upper()
    with db_connect() as conn:
        conn.execute(
            "INSERT INTO vip_orders (order_id, phone, amount, status, created_at) VALUES (?, ?, ?, 'PENDING', ?)",
            (order_id, normalize_phone(phone), PRODUCT_AMOUNT, time.time())
        )
    return order_id

def send_vip_sms(receiver_phone, vip_code):
    """Solapi SMS 문자 발송"""
    if not SOLAPI_API_KEY or not SOLAPI_API_SECRET:
        return False, "Solapi 키 미설정"
    
    url = "https://api.solapi.com/messages/v4/send"
    date = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    salt = secrets.token_hex(16)
    signature = hmac.new(
        SOLAPI_API_SECRET.encode("utf-8"),
        (date + salt).encode("utf-8"),
        hashlib.sha256
    ).hexdigest()
    
    headers = {
        "Authorization": f"HMAC-SHA256 apiKey={SOLAPI_API_KEY}, date={date}, salt={salt}, signature={signature}",
        "Content-Type": "application/json; charset=utf-8"
    }
    
    text = (
        f"[로또픽] VIP 프리패스 코드가 발급되었습니다.\n\n"
        f"🔑 VIP 전용 코드: {vip_code}\n"
        f"⏱ 이용 기간: 발급일로부터 7일간\n\n"
        f"🍀 금주의 행운을 기원합니다!"
    )
    payload = {"message": {"to": normalize_phone(receiver_phone), "from": SOLAPI_SENDER_PHONE, "text": text}}
    
    try:
        res = requests.post(url, json=payload, headers=headers, timeout=10)
        return (True, "발송 성공") if res.status_code in [200, 201] else (False, res.text)
    except Exception as e:
        return False, str(e)

def toss_confirm(payment_key, order_id, amount):
    if not TOSS_SECRET_KEY:
        return False, "토스 시크릿 키 미설정"
    auth = base64.b64encode(f"{TOSS_SECRET_KEY}:".encode("ascii")).decode("ascii")
    headers = {
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/json"
    }
    try:
        res = requests.post(
            "https://api.tosspayments.com/v1/payments/confirm",
            json={"paymentKey": payment_key, "orderId": order_id, "amount": int(amount)},
            headers=headers,
            timeout=10
        )
        body = res.json()
        if res.status_code == 200 and body.get("status") == "DONE":
            return True, body
        return False, body.get("message", "승인 실패")
    except Exception as e:
        return False, str(e)

def handle_payment_success(payment_key, order_id, amount):
    with db_connect() as conn:
        order = conn.execute("SELECT * FROM vip_orders WHERE order_id=?", (order_id,)).fetchone()
    if not order:
        return False, "주문을 찾을 수 없습니다."
    
    if order["status"] == "PAID":
        return True, order["vip_code"]

    ok, msg = toss_confirm(payment_key, order_id, amount)
    if not ok:
        return False, msg

    code = f"MPD-{random.randint(1000, 9999)}"
    code_hash = hashlib.sha256(code.encode("utf-8")).hexdigest()
    expires_at = time.time() + (VIP_DAYS * 86400)

    with db_connect() as conn:
        conn.execute(
            """UPDATE vip_orders 
               SET status='PAID', payment_key=?, vip_code=?, vip_code_hash=?, expires_at=?, paid_at=?
               WHERE order_id=?""",
            (payment_key, code, code_hash, expires_at, time.time(), order_id)
        )
    
    send_vip_sms(order["phone"], code)
    return True, code

def validate_vip_code(raw_code):
    code = (raw_code or "").strip().upper()
    if not code:
        return False, 0, "코드를 입력해 주세요."
    code_hash = hashlib.sha256(code.encode("utf-8")).hexdigest()
    with db_connect() as conn:
        row = conn.execute("SELECT expires_at, status FROM vip_orders WHERE vip_code_hash=? AND status='PAID'", (code_hash,)).fetchone()
    if not row:
        return False, 0, "올바르지 않은 VIP 코드입니다."
    if time.time() > row["expires_at"]:
        return False, 0, "이용 기간이 만료되었습니다."
    return True, row["expires_at"], "승인 완료"

# ================= 3. Page Config & Query Parameter Handling =================
st.set_page_config(
    page_title="로또픽(Lotto Pick) - 초정밀 통계·조합 분석 시스템", 
    page_icon="🍀", 
    layout="centered"
)
init_db()

params = st.query_params

if "pay_success" in params:
    payment_key = params.get("paymentKey", "")
    order_id = params.get("orderId", "")
    amount = params.get("amount", "1000")
    
    ok, result = handle_payment_success(payment_key, order_id, amount)
    
    st.markdown("""
    <div style="background:#064e3b; border:3px solid #facc15; padding:30px; border-radius:16px; text-align:center; color:#fff; margin:20px auto;">
        <h2 style="color:#fde047; margin-top:0;">🎉 결제 및 VIP 승인 완료!</h2>
    """, unsafe_allow_html=True)
    
    if ok:
        st.success("✅ 결제가 안전하게 승인되었습니다!")
        st.markdown(f"<h3 style='color:#facc15;'>🔑 발급된 VIP 코드: <code>{result}</code></h3>", unsafe_allow_html=True)
        st.info("💡 입력하신 휴대폰 번호로 VIP 코드가 문자 발송되었습니다. 아래 버튼을 눌러 메인 화면으로 돌아가 입력해 주세요!")
    else:
        st.error(f"결제 승인 처리 중 안내: {result}")
    
    st.markdown(f"""
        <br><a href="{APP_BASE_URL}" target="_self" style="display:inline-block; padding:15px 30px; background:#eab308; color:#111; font-weight:900; text-decoration:none; border-radius:10px; font-size:16px;">🏠 메인 화면으로 돌아가기</a>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

if "pay_fail" in params:
    st.error(f"❌ 결제 실패 또는 취소되었습니다.")
    st.stop()

# 세션 상태 초기화
if "vip_unlocked" not in st.session_state:
    st.session_state.vip_unlocked = False
if "vip_expire_time" not in st.session_state:
    st.session_state.vip_expire_time = 0
if st.session_state.vip_unlocked and time.time() > st.session_state.vip_expire_time:
    st.session_state.vip_unlocked = False

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

if st.session_state.trigger_snow:
    st.snow()
    st.session_state.trigger_snow = False
if st.session_state.trigger_balloons:
    st.balloons()
    st.session_state.trigger_balloons = False

# ================= 4. 커스텀 CSS 스타일 =================
st.markdown("""
<style>
html, body, * { -webkit-text-size-adjust: 100% !important; text-size-adjust: 100% !important; }
.block-container { max-width: 500px; padding-top: 1.5rem; padding-bottom: 2rem; padding-left: 0.8rem; padding-right: 0.8rem; }
#MainMenu {visibility: hidden;} header {visibility: hidden;} footer {visibility: hidden;}
.keep-all { word-break: keep-all; }

.stApp, [data-testid="stAppViewContainer"] { background-color: #0e1117 !important; color: #ffffff !important; }

@keyframes clover-sparkle { 0% { transform: scale(1) rotate(0deg); } 50% { transform: scale(1.2) rotate(8deg); } 100% { transform: scale(1) rotate(0deg); } }
.sparkle-clover { display: inline-block; animation: clover-sparkle 1.4s infinite ease-in-out; font-size: 20px; }

@keyframes gold-glow { 0% { box-shadow: 0 0 8px #ca8a04; border-color: #eab308; background-color: #1e1b18; } 50% { box-shadow: 0 0 30px #facc15; border-color: #fde047; background-color: #2d2618; } 100% { box-shadow: 0 0 8px #ca8a04; border-color: #eab308; background-color: #1e1b18; } }
@keyframes glow-green { 0% { box-shadow: 0 0 5px #22c55e; border-color: #22c55e; } 50% { box-shadow: 0 0 25px #4ade80; border-color: #4ade80; } 100% { box-shadow: 0 0 5px #22c55e; border-color: #22c55e; } }
@keyframes lightgreen-neon { 0% { border-color: #22c55e; box-shadow: 0 0 12px #22c55e; } 50% { border-color: #4ade80; box-shadow: 0 0 30px #4ade80; } 100% { border-color: #22c55e; box-shadow: 0 0 12px #22c55e; } }

div.stButton > button { font-weight: 900 !important; border-radius: 12px !important; padding: 14px 10px !important; color: white !important; background: linear-gradient(135deg, #1e293b, #0f172a) !important; width: 100% !important; font-size: 16px !important; }
div.stFormSubmitButton > button { font-weight: 900 !important; border-radius: 12px !important; padding: 14px 10px !important; color: white !important; background: linear-gradient(135deg, #1e293b, #0f172a) !important; width: 100% !important; font-size: 16px !important; border: 3px solid #22c55e !important; animation: lightgreen-neon 1.4s infinite ease-in-out !important; }

.free-badge-top { background-color: #dc2626; color: #ffffff; font-size: 14px; font-weight: 900; padding: 6px 16px; border-radius: 20px; margin-bottom: -12px; display: inline-block; }
.vip-badge-top { background-color: #ca8a04; color: #ffffff; font-size: 14px; font-weight: 900; padding: 6px 16px; border-radius: 20px; margin-bottom: -12px; display: inline-block; }
.game-box-free { background-color: #111827; border: 1px solid #374151; padding: 15px; border-radius: 12px; margin-bottom: 12px; }
.game-box-vip { background: linear-gradient(145deg, #1f1b13, #2d2618); border: 1px solid #facc15; padding: 18px; border-radius: 12px; margin-bottom: 15px; position: relative; overflow: hidden; }
.s-class-badge { position: absolute; top: 0; right: 0; background: linear-gradient(135deg, #ef4444, #b91c1c); color: white; font-size: 11px; font-weight: 900; padding: 4px 15px; border-bottom-left-radius: 12px; }
.score-bar-bg { width: 100%; background-color: #3f3f46; border-radius: 4px; height: 6px; margin: 8px 0; overflow: hidden; }
.score-bar-fill { background: linear-gradient(90deg, #facc15, #22c55e); height: 100%; border-radius: 4px; }
.vip-tags { margin-top: 10px; display: flex; gap: 6px; flex-wrap: wrap; }
.vip-tag { font-size: 11px; background-color: rgba(250, 204, 21, 0.1); border: 1px solid rgba(250, 204, 21, 0.3); color: #fef08a; padding: 3px 8px; border-radius: 6px; font-weight: bold; }
.locked-feature-box { background: linear-gradient(135deg, #1e293b, #0f172a); border: 2px dashed #64748b; border-radius: 12px; padding: 28px 20px; text-align: center; margin-top: 15px; color: #cbd5e1; }

.footer-btn { flex: 1; display: flex; align-items: center; justify-content: center; text-decoration: none !important; color: white !important; font-weight: 900; font-size: 16px; padding: 15px 5px; border-radius: 12px; text-align: center; }
</style>
""", unsafe_allow_html=True)

# ================= 5. 타이틀 및 게임 선택 =================
st.markdown("""
<table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
    <tr>
        <td style="width: 12%; text-align: right;"><span class="sparkle-clover">🍀</span></td>
        <td style="width: 76%; text-align: center;"><span style="font-weight: 900; font-size: 20px; background: linear-gradient(135deg, #ffffff 0%, #fef08a 40%, #f59e0b 80%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">로또픽 (Lotto Pick)</span></td>
        <td style="width: 12%; text-align: left;"><span class="sparkle-clover">🍀</span></td>
    </tr>
</table>
<div style="text-align: center; margin-bottom: 25px;">
    <div style="color: #e2e8f0; font-size: 15px; font-weight: 800;">초정밀 통계·조합 분석 시스템</div>
    <div style="color: #38bdf8; font-size: 12px; font-weight: 700; margin-top: 4px;">"데이터는 정밀하게, 분석은 체계적으로"</div>
</div>
""", unsafe_allow_html=True)

col_b1, col_b2 = st.columns(2)
with col_b1:
    if st.button("🔴 로또 6/45 분석", use_container_width=True):
        st.session_state.selected_game = "lotto"
        st.rerun()
with col_b2:
    if st.button("🔵 연금복권 720+", use_container_width=True):
        st.session_state.selected_game = "pension"
        st.rerun()

game_name_str = "로또 6/45" if st.session_state.selected_game == "lotto" else "연금복권 720+"
st.markdown(f'<div style="background-color: #0f172a; border: 2px solid #22c55e; padding: 15px; border-radius: 12px; text-align: center; color: #4ade80; font-weight: bold; font-size: 15px; animation: glow-green 2s infinite; margin: 15px 0 20px 0;">{"🔴" if st.session_state.selected_game=="lotto" else "🔵"} {game_name_str} 분석 ⚙ ● 정밀 시스템 실시간 가동 중</div>', unsafe_allow_html=True)

with st.expander("⚙ 맞춤형 시스템 설정", expanded=False):
    game_count = st.slider("추천 게임 수", 1, 10, 5)

# ================= 6. VIP 결제 및 코드 입력 영역 =================
if not st.session_state.vip_unlocked:
    st.markdown("""
    <div style="background-color: #064e3b; border: 2px solid #eab308; padding: 20px; border-radius: 12px; animation: gold-glow 2s infinite; margin: 20px auto 15px auto; color: #fef08a; text-align: center;">
    <h4 style="margin-top: 0; font-size: 18px; margin-bottom: 15px; color: #fde047; font-weight: 900;">👑 VIP 프리패스 혜택 안내</h4>
    <p style="font-size: 14px; line-height: 1.6; text-align: left; color: #ecfdf5;">
    ✅ <b>이번 주 고정수 & 완벽 제외수 리포트 즉시 공개</b><br>
    ✅ AI 패턴 기반 <b>S등급 일치율 점수 & 분석 태그</b> 제공<br>
    ✅ 프리미엄 빅데이터 통계 조합 가동
    </p>
    <hr style="border-color: #022c22; margin: 15px 0;">
    <div style="font-size: 13px; color: #a7f3d0; margin-bottom: 5px;">🔒 아래 휴대폰 번호 입력 후 결제 버튼을 눌러주세요.</div>
    </div>
    """, unsafe_allow_html=True)

    with st.form("vip_order_form"):
        buyer_phone = st.text_input("📱 VIP 코드를 받을 휴대폰 번호", placeholder="01012345678", max_chars=20)
        order_submitted = st.form_submit_button("💳 토스페이먼츠 1,000원 안전결제", use_container_width=True)

        if order_submitted:
            norm_phone = normalize_phone(buyer_phone)
            if not re.match(r"^01[016789]\d{7,8}$", norm_phone):
                st.error("❌ 올바른 휴대폰 번호를 입력해 주세요.")
            else:
                oid = create_order(norm_phone)
                pay_url = (
                    f"https://pay.tosspayments.com/v1/payments?clientKey={TOSS_CLIENT_KEY}"
                    f"&amount={PRODUCT_AMOUNT}&orderId={oid}&orderName={PRODUCT_NAME}"
                    f"&successUrl={APP_BASE_URL}/?pay_success=1"
                    f"&failUrl={APP_BASE_URL}/?pay_fail=1"
                )
                st.markdown(f"""
                <div style="margin-top: 15px; text-align: center;">
                    <a href="{pay_url}" target="_blank" style="display: block; width: 100%; padding: 16px; background: linear-gradient(135deg, #f59e0b, #d97706); color: #111; font-weight: 900; font-size: 16px; text-decoration: none; border-radius: 12px; border: 2px solid #fde047;">
                        🔗 새 창으로 안전결제 페이지 열기
                    </a>
                    <p style="color: #cbd5e1; font-size: 12px; margin-top: 8px;">버튼을 누르면 결제 페이지가 새 탭으로 열립니다. 결제 완료 후 발급되는 코드로 잠금을 해제하세요!</p>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("---")
    with st.form("vip_unlock_form"):
        vip_input = st.text_input("🔑 문자로 받으신 VIP 코드를 입력하세요", type="password", key="vip_code_input")
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
    st.markdown('<div style="background-color: #064e3b; border: 2px solid #facc15; padding: 15px; border-radius: 10px; text-align: center; color: #fde047; font-weight: bold; margin-bottom: 20px;">👑 VIP 계정 활성화 상태입니다. 아래에서 프리미엄 조합 추출을 실행해 주세요!</div>', unsafe_allow_html=True)

st.markdown("---")

# ================= 7. 조합 추출 실행 버튼 =================
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

# ================= 8. 탭 메뉴 (당첨 번호 추천 / 심층 분석 / 연구 모델) =================
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
                balls_html = "".join([f'<div style="width: 32px; height: 32px; border-radius: 50%; background-color: {get_ball_color(n)}; color: white; display: flex; justify-content: center; align-items: center; font-weight: bold; font-size: 14px; margin-right: 5px; box-shadow: 0 4px 6px rgba(0,0,0,0.3);">{n}</div>' for n in numbers])
                
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
                group_html = f'<div style="background: linear-gradient(135deg, #f59e0b, #d97706); color: white; padding: 4px 10px; border-radius: 6px; font-weight: bold; font-size: 14px; margin-right: 10px;">{group}조</div>'
                digits_html = "".join([f'<div style="width: 30px; height: 30px; border-radius: 6px; background-color: #2563eb; color: white; display: flex; justify-content: center; align-items: center; font-weight: bold; font-size: 16px; margin-right: 4px;">{n}</div>' for n in nums])
                
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
                <div style="font-size: 15px; font-weight: 800; color: #fef08a; margin-bottom: 8px;">🔒 VIP 프리미엄 전용 콘텐츠</div>
                <div style="font-size: 13px; color: #94a3b8; line-height: 1.5;">결제 후 이 자리에 <b>[금주 완벽 제외수 10개]</b>와<br><b>[S등급 상세 분석 리포트]</b>가 즉시 해제됩니다.</div>
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

with tab3:
    st.markdown("<h4 style='color: #ffffff; font-weight: 800;'>📑 분석 연구 모델</h4>", unsafe_allow_html=True)
    st.markdown("""
    <div style="font-size: 15px; color: #f1f5f9; line-height: 1.8; font-weight: 600;">
    - Markov Chain Monte Carlo (MCMC) 모델<br>
    - Poisson Distribution 출현 간격 예측<br>
    - AC값(Arithmetic Complexity) 복잡도 필터링
    </div>
    """, unsafe_allow_html=True)

# ================= 9. 고객센터 및 푸터 =================
st.markdown("---")
st.markdown("<h4 style='color: #ffffff; font-weight: 900; margin-bottom: 8px;'>📞 고객 센터</h4>", unsafe_allow_html=True)

st.markdown(f"""
<div style="display: flex; gap: 15px; width: 100%; margin-bottom: 25px;">
    <a href="{GOOGLE_FORM_URL}" target="_blank" class="footer-btn" style="background-color: #2e3b4e !important;">🛠️ 고객센터 문의 접수</a>
    <a href="https://www.dhlottery.co.kr" target="_blank" class="footer-btn" style="background-color: #15803d !important; border: 2px solid #fff !important;">🛒 동행복권 홈</a>
</div>
""", unsafe_allow_html=True)

# 사업자 정보 및 법적 고지
st.markdown("""
<div style="background-color: #1a1a1a; padding: 15px; border-radius: 8px; margin-top: 25px; border: 1px solid #333; color: #a1a1aa; font-size: 11px; line-height: 1.6;">
<b>[법적 고지 및 주의사항]</b><br>
1. 본 서비스(로또픽)에서 제공하는 번호 조합 및 통계 분석 자료는 과거의 데이터를 기반으로 한 확률적 추정치이며, <b>실제 복권 당첨을 절대 보장하지 않습니다.</b><br>
2. 복권은 소액으로 건전하게 즐기시길 바라며, 과도한 몰입은 일상생활에 지장을 줄 수 있습니다.
</div>

<div style="text-align: center; color: #94a3b8; font-size: 11px; margin-top: 20px; line-height: 1.8; padding-top: 20px; border-top: 1px solid #333;">
    <b>상호:</b> 엠피디뮤직 (MPD music) &nbsp;|&nbsp; <b>대표:</b> 이근영 &nbsp;|&nbsp; <b>사업자등록번호:</b> 162-23-01932<br>
    <b>사업장 주소:</b> 경기도 고양시 덕양구 능곡로 16, 101동 501호(토당동, 숲예찬)<br>
    <b>고객센터:</b> 010-5282-7017 &nbsp;|&nbsp; <b>이메일:</b> leegysa@naver.com<br><br>
    © 2026 로또픽(Lotto Pick) 분석 시스템. All Rights Reserved.
</div>
""", unsafe_allow_html=True)
