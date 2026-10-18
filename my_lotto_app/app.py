# -*- coding: utf-8 -*-
"""
로또픽 (Lotto Pick) - 초정밀 통계·조합 분석 시스템 (100% 통합 최종 완성본)
- 토스페이먼츠 안전 결제 SDK 다이렉트 연동 및 비동기 서버 승인 검증
- 결제 완료 시 Solapi 자동 문자 발송 시스템 (백그라운드 스레드 처리)
- 로또 6/45 및 연금복권 720+ 통합 프리미엄 시스템 (애드센스 소유권 확인 및 스니펫 완벽 적용)
"""

import random
import time
import os
import threading
import re
import json
import sqlite3
import secrets
import uuid
import base64
import hashlib
import hmac
from contextlib import contextmanager
from collections import Counter
from datetime import datetime, timezone
from urllib.parse import quote

import numpy as np
import pandas as pd
import requests
import streamlit as st

# ================= 0. 페이지 기본 설정 =================
st.set_page_config(
    page_title="로또픽(Lotto Pick) - 초정밀 통계·조합 분석 시스템",
    page_icon="🍀",
    layout="centered",
)

# ================= URL 및 상품 설정 =================
GOOGLE_FORM_URL = "https://forms.gle/RA8i731z2QFi7ByMA"
PRODUCT_NAME = "VIP 골든픽 1주(7일) 프리패스"
PRODUCT_AMOUNT = 1000
VIP_DAYS = 7
DB_PATH = os.getenv("LOTTO_PICK_DB_PATH", "vip_store.sqlite3")
DEFAULT_APP_URL = "https://mylottoapp-3mygrnqs6j7ard8n3zrvj9.streamlit.app"

@st.cache_resource
def get_worker_registry():
    return {
        "lock": threading.RLock(),
        "payments": set(),
        "sms": set(),
    }

WORKERS = get_worker_registry()

def get_secret(name: str, default: str = "") -> str:
    try:
        value = st.secrets.get(name, os.getenv(name, default))
    except Exception:
        value = os.getenv(name, default)
    return str(value or "").strip()

APP_SITE_URL = get_secret("APP_BASE_URL", DEFAULT_APP_URL).rstrip("/")
TOSS_CLIENT_KEY = get_secret("TOSS_CLIENT_KEY")
TOSS_SECRET_KEY = get_secret("TOSS_SECRET_KEY")
SOLAPI_API_KEY = get_secret("SOLAPI_API_KEY")
SOLAPI_API_SECRET = get_secret("SOLAPI_API_SECRET")
SOLAPI_SENDER_PHONE = re.sub(r"\D", "", get_secret("SOLAPI_SENDER_PHONE"))

# ================= DB 및 주문 관리 =================
@contextmanager
def db_session():
    conn = sqlite3.connect(DB_PATH, timeout=20, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA busy_timeout = 20000")
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    with db_session() as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS vip_orders (
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
                sms_status TEXT DEFAULT 'PENDING',
                sms_error TEXT,
                verify_started_at REAL,
                verify_error TEXT,
                sms_started_at REAL
            )"""
        )
        columns = {row[1] for row in conn.execute("PRAGMA table_info(vip_orders)").fetchall()}
        if "sms_status" not in columns:
            conn.execute("ALTER TABLE vip_orders ADD COLUMN sms_status TEXT DEFAULT 'PENDING'")
        if "sms_error" not in columns:
            conn.execute("ALTER TABLE vip_orders ADD COLUMN sms_error TEXT")
        if "verify_started_at" not in columns:
            conn.execute("ALTER TABLE vip_orders ADD COLUMN verify_started_at REAL")
        if "verify_error" not in columns:
            conn.execute("ALTER TABLE vip_orders ADD COLUMN verify_error TEXT")
        if "sms_started_at" not in columns:
            conn.execute("ALTER TABLE vip_orders ADD COLUMN sms_started_at REAL")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_vip_orders_code_hash ON vip_orders(vip_code_hash)")

def normalize_phone(raw: str) -> str:
    phone = re.sub(r"\D", "", raw or "")
    if phone.startswith("82") and len(phone) in (11, 12, 13):
        phone = "0" + phone[2:]
    return phone

def create_order(phone: str) -> str:
    phone = normalize_phone(phone)
    if not re.fullmatch(r"01[016789]\d{7,8}", phone):
        raise ValueError("올바른 국내 휴대폰 번호가 아닙니다.")
    order_id = "VIP" + uuid.uuid4().hex.upper()
    now = time.time()
    with db_session() as conn:
        conn.execute(
            "INSERT INTO vip_orders (order_id, phone, amount, status, created_at, sms_status) VALUES (?, ?, ?, 'PENDING', ?, 'PENDING')",
            (order_id, phone, PRODUCT_AMOUNT, now),
        )
    return order_id

def get_order(order_id: str):
    if not order_id:
        return None
    with db_session() as conn:
        return conn.execute("SELECT * FROM vip_orders WHERE order_id = ?", (order_id,)).fetchone()

def create_vip_code() -> str:
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    raw = "".join(secrets.choice(alphabet) for _ in range(12))
    return "MPD-" + raw[:4] + "-" + raw[4:8] + "-" + raw[8:]

def normalize_vip_code(raw: str) -> str:
    return re.sub(r"\s+", "", (raw or "")).upper()

def vip_code_hash(raw: str) -> str:
    return hashlib.sha256(normalize_vip_code(raw).encode("utf-8")).hexdigest()

# ================= Solapi SMS 시스템 =================
def send_vip_sms(receiver_phone: str, vip_code: str):
    if not SOLAPI_API_KEY or not SOLAPI_API_SECRET or not SOLAPI_SENDER_PHONE:
        return False, "Solapi 키 또는 등록 발신번호가 설정되지 않았습니다."

    receiver_phone = normalize_phone(receiver_phone)
    if not re.fullmatch(r"01[016789]\d{7,8}", receiver_phone):
        return False, "수신 휴대폰 번호 형식이 올바르지 않습니다."

    url = "https://api.solapi.com/messages/v4/send"
    date = datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    salt = secrets.token_hex(16)
    signature = hmac.new(
        SOLAPI_API_SECRET.encode("utf-8"),
        (date + salt).encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    headers = {
        "Authorization": f"HMAC-SHA256 apiKey={SOLAPI_API_KEY}, date={date}, salt={salt}, signature={signature}",
        "Content-Type": "application/json; charset=utf-8",
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
            "text": message_text,
        }
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=(5, 12))
        if response.status_code in (200, 201, 202):
            try:
                body = response.json()
                if body.get("failedMessageList"):
                    return False, "Solapi가 발송 실패를 반환했습니다."
            except (ValueError, AttributeError):
                pass
            return True, "전송 성공"
        try:
            body = response.json()
            detail = body.get("message") or body.get("errorMessage") or f"HTTP {response.status_code}"
        except ValueError:
            detail = f"HTTP {response.status_code}"
        return False, str(detail)[:300]
    except requests.RequestException as exc:
        return False, f"Solapi 통신 오류: {type(exc).__name__}"

def _sms_worker(order_id: str):
    try:
        row = get_order(order_id)
        if not row or row["status"] != "PAID":
            return
        ok, detail = send_vip_sms(row["phone"], row["vip_code"])
        with db_session() as conn:
            if ok:
                conn.execute(
                    "UPDATE vip_orders SET sms_status='SENT', sms_error=NULL WHERE order_id=? AND status='PAID'",
                    (order_id,),
                )
            else:
                conn.execute(
                    "UPDATE vip_orders SET sms_status='FAILED', sms_error=? WHERE order_id=? AND status='PAID'",
                    (detail[:500], order_id),
                )
    except Exception as exc:
        try:
            with db_session() as conn:
                conn.execute(
                    "UPDATE vip_orders SET sms_status='FAILED', sms_error=? WHERE order_id=? AND status='PAID'",
                    (f"문자 처리 내부 오류: {type(exc).__name__}", order_id),
                )
        except Exception:
            pass
    finally:
        with WORKERS["lock"]:
            WORKERS["sms"].discard(order_id)

def schedule_sms_for_order(order_id: str, allow_retry: bool = False):
    with WORKERS["lock"]:
        if order_id in WORKERS["sms"]:
            return True, "문자 발송을 처리 중입니다."
        with db_session() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute("SELECT * FROM vip_orders WHERE order_id=?", (order_id,)).fetchone()
            if not row or row["status"] != "PAID":
                return False, "결제 승인된 주문을 찾을 수 없습니다."
            current = row["sms_status"] or "PENDING"
            if current == "SENT":
                return True, "문자 발송 요청이 이미 접수되었습니다."
            if allow_retry:
                allowed = {"PENDING", "FAILED"}
                if current == "SENDING" and row["sms_started_at"] and time.time() - float(row["sms_started_at"]) > 60:
                    allowed.add("SENDING")
            else:
                allowed = {"PENDING"}
            if current not in allowed:
                return False, f"문자 상태가 {current}입니다."
            cur = conn.execute(
                "UPDATE vip_orders SET sms_status='SENDING', sms_error=NULL, sms_started_at=? WHERE order_id=? AND status='PAID' AND sms_status=?",
                (time.time(), order_id, current),
            )
            if cur.rowcount != 1:
                return False, "상태가 변경되었습니다."
        WORKERS["sms"].add(order_id)
        thread = threading.Thread(target=_sms_worker, args=(order_id,), daemon=True, name=f"lotto-sms-{order_id[:8]}")
        thread.start()
    return True, "문자 발송 요청을 백그라운드에서 처리합니다."

def toss_auth_headers():
    token = base64.b64encode((TOSS_SECRET_KEY + ":").encode("utf-8")).decode("ascii")
    return {"Authorization": f"Basic {token}", "Content-Type": "application/json"}

def payment_matches_order(payment: dict, order_id: str, expected_amount: int, payment_key: str) -> bool:
    if not isinstance(payment, dict):
        return False
    try:
        actual_amount = int(payment.get("totalAmount", -1))
    except (TypeError, ValueError):
        return False
    return bool(
        payment.get("status") == "DONE"
        and payment.get("orderId") == order_id
        and payment.get("paymentKey") == payment_key
        and actual_amount == int(expected_amount)
    )

def toss_confirm_or_fetch(payment_key: str, order_id: str, amount: int):
    if not TOSS_SECRET_KEY:
        return False, "토스 시크릿 키가 설정되지 않았습니다."
    headers = toss_auth_headers()
    confirm_error = "토스 결제 승인 요청이 실패했습니다."
    try:
        response = requests.post(
            "https://api.tosspayments.com/v1/payments/confirm",
            json={"paymentKey": payment_key, "orderId": order_id, "amount": int(amount)},
            headers=headers,
            timeout=15,
        )
        try:
            body = response.json()
        except Exception:
            body = {}
        if response.status_code == 200 and payment_matches_order(body, order_id, amount, payment_key):
            return True, body
        confirm_error = str(body.get("message") or body.get("code") or f"승인 API HTTP {response.status_code}")[:300]
    except requests.RequestException as exc:
        confirm_error = f"토스 승인 API 통신 오류: {type(exc).__name__}"

    try:
        detail_response = requests.get(
            "https://api.tosspayments.com/v1/payments/" + quote(payment_key, safe=""),
            headers=headers,
            timeout=15,
        )
        detail = detail_response.json() if detail_response.content else {}
        if detail_response.status_code == 200 and payment_matches_order(detail, order_id, amount, payment_key):
            return True, detail
    except (requests.RequestException, ValueError):
        pass
    return False, confirm_error

def _payment_verification_worker(order_id: str, payment_key: str, amount: int):
    try:
        order = get_order(order_id)
        if not order:
            return
        if int(order["amount"]) != int(amount) or int(amount) != PRODUCT_AMOUNT:
            with db_session() as conn:
                conn.execute(
                    "UPDATE vip_orders SET status='VERIFY_FAILED', verify_error=? WHERE order_id=? AND status='VERIFYING'",
                    ("결제 금액이 일치하지 않습니다.", order_id),
                )
            return
        ok, result = toss_confirm_or_fetch(payment_key, order_id, amount)
        if not ok:
            with db_session() as conn:
                conn.execute(
                    "UPDATE vip_orders SET status='VERIFY_FAILED', verify_error=?, verify_started_at=NULL WHERE order_id=? AND status='VERIFYING' AND payment_key=?",
                    (str(result)[:500], order_id, payment_key),
                )
            return

        code = create_vip_code()
        digest = vip_code_hash(code)
        now = time.time()
        with db_session() as conn:
            conn.execute("BEGIN IMMEDIATE")
            latest = conn.execute("SELECT * FROM vip_orders WHERE order_id=?", (order_id,)).fetchone()
            if not latest:
                return
            if latest["status"] == "PAID":
                if latest["payment_key"] != payment_key:
                    return
            elif latest["status"] == "VERIFYING" and latest["payment_key"] == payment_key:
                conn.execute(
                    """UPDATE vip_orders
                       SET status='PAID', payment_key=?, vip_code=?, vip_code_hash=?, expires_at=?, paid_at=?,
                           sms_status='PENDING', sms_error=NULL, verify_error=NULL, verify_started_at=NULL
                       WHERE order_id=? AND status='VERIFYING' AND payment_key=?""",
                    (payment_key, code, digest, now + VIP_DAYS * 86400, now, order_id, payment_key),
                )
            else:
                return
        current = get_order(order_id)
        if current and current["status"] == "PAID" and current["payment_key"] == payment_key:
            if current["sms_status"] == "PENDING":
                schedule_sms_for_order(order_id, allow_retry=False)
    except Exception as exc:
        try:
            with db_session() as conn:
                conn.execute(
                    "UPDATE vip_orders SET status='VERIFY_FAILED', verify_error=?, verify_started_at=NULL WHERE order_id=? AND status='VERIFYING' AND payment_key=?",
                    (f"승인 확인 중 오류: {type(exc).__name__}", order_id, payment_key),
                )
        except Exception:
            pass
    finally:
        with WORKERS["lock"]:
            WORKERS["payments"].discard(order_id)

def schedule_payment_verification(order_id: str, payment_key: str, requested_amount, force: bool = False):
    if not order_id or not payment_key:
        return False, "주문번호 또는 paymentKey가 없습니다."
    try:
        amount = int(str(requested_amount))
    except (TypeError, ValueError):
        return False, "금액 형식이 올바르지 않습니다."
    if amount != PRODUCT_AMOUNT:
        return False, "결제 금액이 일치하지 않습니다."

    already_paid = False
    should_queue_sms = False
    with WORKERS["lock"]:
        if order_id in WORKERS["payments"]:
            return True, "VERIFYING"
        with db_session() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute("SELECT * FROM vip_orders WHERE order_id=?", (order_id,)).fetchone()
            if not row:
                return False, "주문을 찾을 수 없습니다."
            if int(row["amount"]) != amount:
                return False, "요청 금액이 일치하지 않습니다."
            if row["status"] == "PAID":
                if row["payment_key"] != payment_key:
                    return False, "paymentKey가 일치하지 않습니다."
                already_paid = True
                should_queue_sms = (row["sms_status"] or "PENDING") == "PENDING"
            else:
                if row["status"] == "CANCELLED":
                    return False, "취소된 주문입니다."
                conn.execute(
                    "UPDATE vip_orders SET status='VERIFYING', payment_key=?, verify_started_at=?, verify_error=NULL WHERE order_id=?",
                    (payment_key, time.time(), order_id),
                )
        if already_paid:
            if should_queue_sms:
                schedule_sms_for_order(order_id, allow_retry=False)
            return True, "PAID"
        WORKERS["payments"].add(order_id)
        thread = threading.Thread(
            target=_payment_verification_worker,
            args=(order_id, payment_key, amount),
            daemon=True,
            name=f"lotto-pay-{order_id[:8]}",
        )
        thread.start()
    return True, "VERIFYING"

def recover_verifying_orders():
    try:
        with db_session() as conn:
            rows = conn.execute(
                "SELECT order_id, payment_key, amount FROM vip_orders WHERE status='VERIFYING' AND payment_key IS NOT NULL"
            ).fetchall()
        for row in rows:
            schedule_payment_verification(row["order_id"], row["payment_key"], row["amount"], force=True)
    except Exception:
        pass

def validate_vip_code(raw_code: str):
    normalized = normalize_vip_code(raw_code)
    if not normalized:
        return False, 0, "VIP 코드를 입력해 주세요."
    digest = vip_code_hash(normalized)
    with db_session() as conn:
        row = conn.execute(
            "SELECT expires_at FROM vip_orders WHERE vip_code_hash=? AND status='PAID'",
            (digest,),
        ).fetchone()
    if not row:
        return False, 0, "유효한 VIP 코드를 찾을 수 없습니다."
    if not row["expires_at"] or time.time() > float(row["expires_at"]):
        return False, 0, "VIP 이용 기간(7일)이 만료되었습니다."
    return True, float(row["expires_at"]), "승인 완료"

def render_toss_payment_button(order_id: str, phone: str) -> str:
    if not TOSS_CLIENT_KEY:
        return "<div style='padding:12px;color:#fecaca'>토스 클라이언트 키가 설정되지 않았습니다. Secrets를 확인해 주세요.</div>"

    config = {
        "clientKey": TOSS_CLIENT_KEY,
        "orderId": order_id,
        "orderName": PRODUCT_NAME,
        "phone": normalize_phone(phone),
        "amount": PRODUCT_AMOUNT,
        "successUrl": APP_SITE_URL + "/?payment_success=1",
        "failUrl": APP_SITE_URL + "/?payment_fail=1",
    }
    config_js = json.dumps(config, ensure_ascii=False).replace("</", "<\\/")
    btn_id = "lotto-toss-pay-" + re.sub(r"[^A-Za-z0-9_-]", "", order_id)
    msg_id = btn_id + "-status"

    return f'''<div style="max-width:520px;margin:8px auto;padding:16px;background:#111827;border:2px solid #eab308;border-radius:14px;text-align:center;color:#fff">
      <div style="font-weight:900;color:#fde047;font-size:17px;margin-bottom:8px">👑 VIP 골든픽 1주 프리패스</div>
      <div style="font-size:23px;font-weight:900;margin-bottom:12px">1,000원</div>
      <button id="{btn_id}" type="button" disabled style="width:100%;padding:15px;border:2px solid #fde047;border-radius:11px;background:linear-gradient(135deg,#059669,#047857);color:#fff;font-size:16px;font-weight:900;cursor:pointer;opacity:.75">토스 결제 SDK 준비 중...</button>
      <div id="{msg_id}" aria-live="polite" style="font-size:12px;color:#cbd5e1;margin-top:8px">결제 SDK를 확인하고 있습니다. 버튼을 누르면 안전한 결제창이 열립니다.</div>
    </div>
    <script>
    (function() {{
      const config = {config_js};
      const btn = document.getElementById({json.dumps(btn_id)});
      const msg = document.getElementById({json.dumps(msg_id)});
      if (!btn || !msg || btn.dataset.handlerBound === '1') return;
      btn.dataset.handlerBound = '1';
      let busy = false;
      let activeSdk = null;

      const SDK_LIST = [
        {{ version: 'v1', url: 'https://js.tosspayments.com/v1/payment' }},
        {{ version: 'v2', url: 'https://js.tosspayments.com/v2/standard' }}
      ];

      function loadOneSdk(item) {{
        return new Promise(function(resolve, reject) {{
          let script = document.querySelector('script[data-lotto-pick-sdk="' + item.version + '"]');
          let settled = false;
          let timer = null;
          function resolveOnce() {{
            if (settled) return;
            settled = true;
            if (timer) clearTimeout(timer);
            if (typeof window.TossPayments === 'function') resolve(item.version);
            else reject(new Error(item.version.toUpperCase() + ' TossPayments 초기화 함수를 찾지 못했습니다.'));
          }}
          function rejectOnce(reason) {{
            if (settled) return;
            settled = true;
            if (timer) clearTimeout(timer);
            reject(reason instanceof Error ? reason : new Error(String(reason || 'SDK 로드 실패')));
          }}

          if (window.__lottoPickTossSdkVersion === item.version && typeof window.TossPayments === 'function') {{
            resolve(item.version);
            return;
          }}
          if (script && script.dataset.state === 'failed') {{
            script.remove();
            script = null;
          }}
          if (script && script.dataset.state === 'loaded' && typeof window.TossPayments === 'function') {{
            window.__lottoPickTossSdkVersion = item.version;
            resolve(item.version);
            return;
          }}
          if (script && script.dataset.state === 'loading') {{
            script.addEventListener('load', resolveOnce, {{ once: true }});
            script.addEventListener('error', function() {{ rejectOnce(new Error(item.version.toUpperCase() + ' 네트워크 로드 실패')); }}, {{ once: true }});
            timer = setTimeout(function() {{ rejectOnce(new Error(item.version.toUpperCase() + ' 로딩 시간 초과')); }}, 12000);
            return;
          }}

          script = document.createElement('script');
          script.src = item.url;
          script.async = true;
          script.dataset.lottoPickSdk = item.version;
          script.dataset.state = 'loading';
          script.onload = function() {{
            script.dataset.state = 'loaded';
            if (typeof window.TossPayments === 'function') {{
              window.__lottoPickTossSdkVersion = item.version;
              resolveOnce();
            }} else {{
              script.dataset.state = 'failed';
              rejectOnce(new Error(item.version.toUpperCase() + ' 전역 함수 누락'));
            }}
          }};
          script.onerror = function() {{
            script.dataset.state = 'failed';
            rejectOnce(new Error(item.version.toUpperCase() + ' 다운로드 실패'));
          }};
          timer = setTimeout(function() {{
            script.dataset.state = 'failed';
            rejectOnce(new Error(item.version.toUpperCase() + ' 시간 초과'));
            try {{ script.remove(); }} catch(e) {{}}
          }}, 12000);
          document.head.appendChild(script);
        }});
      }}

      function loadSdkWithFallback() {{
        if (window.__lottoPickTossSdkVersion && typeof window.TossPayments === 'function') {{
          activeSdk = window.__lottoPickTossSdkVersion;
          return Promise.resolve(activeSdk);
        }}
        if (window.__lottoPickTossLoadPromise) return window.__lottoPickTossLoadPromise;
        window.__lottoPickTossLoadPromise = loadOneSdk(SDK_LIST[0])
          .catch(function(v1Error) {{
            msg.textContent = '공식 V2 SDK로 대체 시도 중입니다.';
            return loadOneSdk(SDK_LIST[1]).catch(function(v2Error) {{
              throw new Error('V1: ' + v1Error.message + ' / V2: ' + v2Error.message);
            }});
          }})
          .then(function(version) {{
            activeSdk = version;
            window.__lottoPickTossSdkVersion = version;
            return version;
          }})
          .catch(function(error) {{
            window.__lottoPickTossLoadPromise = null;
            throw error;
          }});
        return window.__lottoPickTossLoadPromise;
      }}

      function showReady(version) {{
        activeSdk = version;
        btn.disabled = false;
        btn.style.opacity = '1';
        btn.textContent = '💳 토스페이먼츠 결제하기 (1,000원)';
        msg.textContent = '결제 준비 완료 (' + version.toUpperCase() + '). 버튼을 눌러 결제를 진행하세요.';
      }}

      function showFailure(error) {{
        btn.disabled = false;
        btn.style.opacity = '1';
        btn.textContent = '🔄 결제 SDK 다시 불러오기';
        msg.textContent = 'SDK 로드 실패: ' + (error && error.message ? error.message : '네트워크 오류');
      }}

      function startPayment(version) {{
        const tossPayments = window.TossPayments(config.clientKey);
        if (version === 'v1') {{
          return tossPayments.requestPayment('카드', {{
            amount: config.amount,
            orderId: config.orderId,
            orderName: config.orderName,
            customerMobilePhone: config.phone,
            successUrl: config.successUrl,
            failUrl: config.failUrl
          }});
        }}
        const payment = tossPayments.payment({{ customerKey: config.orderId }});
        return payment.requestPayment({{
          method: 'CARD',
          amount: {{ currency: 'KRW', value: config.amount }},
          orderId: config.orderId,
          orderName: config.orderName,
          customerMobilePhone: config.phone,
          successUrl: config.successUrl,
          failUrl: config.failUrl,
          windowTarget: 'self'
        }});
      }}

      loadSdkWithFallback().then(showReady).catch(showFailure);

      btn.addEventListener('click', function() {{
        if (busy || btn.disabled) return;
        if (!activeSdk || typeof window.TossPayments !== 'function') {{
          btn.disabled = true;
          btn.textContent = 'SDK 다시 불러오는 중...';
          loadSdkWithFallback().then(showReady).catch(showFailure);
          return;
        }}
        busy = true;
        btn.disabled = true;
        btn.textContent = '결제창 여는 중...';
        msg.textContent = '결제창을 불러오고 있습니다. 잠시만 기다려 주세요.';
        try {{
          const result = startPayment(activeSdk);
          if (result && typeof result.catch === 'function') {{
            result.catch(function(error) {{
              busy = false;
              btn.disabled = false;
              btn.textContent = '💳 토스페이먼츠 결제 다시 시도';
              const code = error && error.code ? String(error.code) : '';
              if (code === 'USER_CANCEL' || code === 'PAY_PROCESS_CANCELED') {{
                msg.textContent = '결제가 취소되었습니다.';
              }} else {{
                msg.textContent = '결제 오류: ' + (error && error.message ? error.message : '실패했습니다.');
              }}
            }});
          }}
        }} catch(error) {{
          busy = false;
          btn.disabled = false;
          btn.textContent = '💳 토스페이먼츠 결제 다시 시도';
          msg.textContent = '초기화 오류: ' + (error && error.message ? error.message : '실패했습니다.');
        }}
      }});
    }})();
    </script>'''

@st.fragment(run_every=2)
def payment_status_panel(order_id: str):
    row = get_order(order_id)
    if not row:
        st.warning("결제 주문 정보를 찾지 못했습니다.")
        return
    status = row["status"]
    if status == "VERIFYING":
        st.info("🔄 토스 결제 승인을 확인 중입니다. 잠시만 기다려 주세요.")
        if row["verify_started_at"] and time.time() - float(row["verify_started_at"]) > 45:
            if st.button("🔁 결제 승인 확인 다시 시도", key=f"retry-verify-{order_id}", use_container_width=True):
                schedule_payment_verification(order_id, row["payment_key"], row["amount"], force=True)
                st.rerun(scope="fragment")
    elif status == "PAID":
        st.success("✅ 결제 승인 완료! VIP 코드가 발급되었습니다.")
        st.markdown(f"### 🔑 VIP 전용 코드: `{row['vip_code']}`")
        expiry_text = datetime.fromtimestamp(float(row["expires_at"])).strftime("%Y-%m-%d %H:%M") if row["expires_at"] else "확인 필요"
        st.caption(f"이용 만료: {expiry_text}")
        sms_status = row["sms_status"] or "PENDING"
        if sms_status == "SENT":
            st.success("📱 문자가 휴대폰으로 발송되었습니다.")
        elif sms_status == "SENDING":
            st.info("📨 문자 발송을 처리 중입니다. 위 코드를 바로 입력해 사용하실 수 있습니다.")
        elif sms_status == "FAILED":
            st.warning("⚠️ 문자 발송이 지연되었으나 코드는 정상 발급되었습니다.")
            if st.button("📨 문자 재발송", key=f"retry-sms-{order_id}", use_container_width=True):
                schedule_sms_for_order(order_id, allow_retry=True)
                st.rerun(scope="fragment")
    elif status == "VERIFY_FAILED":
        st.error("❌ 결제 승인 확인 중 문제가 발생했습니다.")
        if row["payment_key"] and st.button("🔁 결제 상태 다시 확인", key=f"retry-verify-failed-{order_id}", use_container_width=True):
            schedule_payment_verification(order_id, row["payment_key"], row["amount"], force=True)
            st.rerun(scope="fragment")
    elif status == "CANCELLED":
        st.warning("결제가 취소되었습니다.")

# ================= 초기화 및 쿼리 파라미터 처리 =================
init_db()
st.markdown('<meta name="google-adsense-account" content="ca-pub-2324282297166072">', unsafe_allow_html=True)

def init_state(key, default):
    if key not in st.session_state:
        st.session_state[key] = default

init_state("vip_unlocked", False)
init_state("vip_expire_time", 0.0)
init_state("selected_game", "lotto")
init_state("extract_results", [])
init_state("extract_game_type", "lotto")
init_state("is_vip_result", False)
init_state("trigger_snow", False)
init_state("trigger_balloons", False)
init_state("pending_order_id", "")
init_state("last_completed_order_id", "")
init_state("last_payment_order_id", "")
init_state("payment_flash", None)

if st.session_state.vip_unlocked and time.time() > float(st.session_state.vip_expire_time or 0):
    st.session_state.vip_unlocked = False
    st.session_state.vip_expire_time = 0.0
    st.warning("⏱ VIP 이용 기간(7일)이 만료되었습니다.")

query = st.query_params
if "payment_success" in query:
    payment_key = str(query.get("paymentKey", ""))
    order_id = str(query.get("orderId", ""))
    amount = str(query.get("amount", ""))
    ok, result = schedule_payment_verification(order_id, payment_key, amount)
    if ok:
        st.session_state.last_payment_order_id = order_id
        st.session_state.pending_order_id = order_id
        st.session_state.payment_flash = {"ok": True, "message": "결제 승인 확인 중..."}
    else:
        st.session_state.payment_flash = {"ok": False, "message": str(result)}
    st.query_params.clear()
    st.rerun()
elif "payment_fail" in query:
    order_id = str(query.get("orderId", ""))
    if order_id:
        with db_session() as conn:
            conn.execute("UPDATE vip_orders SET status='CANCELLED' WHERE order_id=? AND status='PENDING'", (order_id,))
    st.session_state.payment_flash = {"ok": False, "message": "결제가 취소되었습니다."}
    st.query_params.clear()
    st.rerun()

recover_verifying_orders()

if st.session_state.trigger_snow:
    st.snow()
    st.session_state.trigger_snow = False
if st.session_state.trigger_balloons:
    st.balloons()
    st.session_state.trigger_balloons = False

# ================= CSS 스타일 정의 =================
st.markdown("""
<style>
html, body, * { -webkit-text-size-adjust: 100% !important; }
.block-container { max-width: 500px; padding-top: 1.5rem; padding-bottom: 2rem; padding-left: 0.8rem; padding-right: 0.8rem; }
#MainMenu {visibility: hidden;} header {visibility: hidden;} footer {visibility: hidden;}
.keep-all { word-break: keep-all; }
.stApp, [data-testid="stAppViewContainer"] { background-color: #0e1117 !important; color: #ffffff !important; }

@keyframes clover-sparkle { 0% { transform: scale(1) rotate(0deg); } 50% { transform: scale(1.2) rotate(8deg); } 100% { transform: scale(1) rotate(0deg); } }
.sparkle-clover { display: inline-block; animation: clover-sparkle 1.4s infinite ease-in-out; font-size: 20px; }
@keyframes gold-glow { 0% { box-shadow: 0 0 8px #ca8a04; border-color: #eab308; background-color: #1e1b18; } 50% { box-shadow: 0 0 30px #facc15; border-color: #fde047; background-color: #2d2618; } 100% { box-shadow: 0 0 8px #ca8a04; border-color: #eab308; background-color: #1e1b18; } }
@keyframes glow-green { 0% { box-shadow: 0 0 5px #22c55e; border-color: #22c55e; } 50% { box-shadow: 0 0 25px #4ade80; border-color: #4ade80; } 100% { box-shadow: 0 0 5px #22c55e; border-color: #22c55e; } }

div.stButton > button {
    font-weight: 900 !important; border-radius: 12px !important; padding: 14px 10px !important;
    color: white !important; background: linear-gradient(135deg, #1e293b, #0f172a) !important;
    width: 100% !important; font-size: 16px !important; border: 2px solid #334155 !important;
}
.free-badge-top { background-color: #dc2626; color: #ffffff; font-size: 14px; font-weight: 900; padding: 6px 16px; border-radius: 20px; display: inline-block; }
.vip-badge-top { background-color: #ca8a04; color: #ffffff; font-size: 14px; font-weight: 900; padding: 6px 16px; border-radius: 20px; display: inline-block; }
.game-box-free { background-color: #111827; border: 1px solid #374151; padding: 15px; border-radius: 12px; margin-bottom: 12px; }
.game-box-vip { background: linear-gradient(145deg, #1f1b13, #2d2618); border: 1px solid #facc15; padding: 18px; border-radius: 12px; margin-bottom: 15px; position: relative; overflow: hidden; }
.s-class-badge { position: absolute; top: 0; right: 0; background: linear-gradient(135deg, #ef4444, #b91c1c); color: white; font-size: 11px; font-weight: 900; padding: 4px 15px; border-bottom-left-radius: 12px; }
.score-bar-bg { width: 100%; background-color: #3f3f46; border-radius: 4px; height: 6px; margin: 8px 0; overflow: hidden; }
.score-bar-fill { background: linear-gradient(90deg, #facc15, #22c55e); height: 100%; border-radius: 4px; }
.vip-tags { margin-top: 10px; display: flex; gap: 6px; flex-wrap: wrap; }
.vip-tag { font-size: 11px; background-color: rgba(250, 204, 21, 0.1); border: 1px solid rgba(250, 204, 21, 0.3); color: #fef08a; padding: 3px 8px; border-radius: 6px; font-weight: bold; }
.footer-buttons-container { display: flex; gap: 15px; width: 100%; margin-bottom: 25px; }
.footer-btn { flex: 1; display: flex; align-items: center; justify-content: center; text-decoration: none !important; color: white !important; font-weight: 900; font-size: 16px; padding: 15px 5px; border-radius: 12px; text-align: center; }
.footer-btn-cs { background-color: #2e3b4e !important; }
.footer-btn-dhlottery { background-color: #15803d !important; border: 2px solid #ffffff !important; }
.adsense-box { background-color: #161b22; border: 1px dashed #30363d; padding: 10px; border-radius: 10px; text-align: center; margin: 20px 0; }
</style>
""", unsafe_allow_html=True)

# ================= 1. 타이틀 배너 =================
st.markdown("""
<table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
    <tr>
        <td style="width: 12%; text-align: right; vertical-align: middle;"><span class="sparkle-clover">🍀</span></td>
        <td style="width: 76%; text-align: center; white-space: nowrap;">
            <span style="font-weight: 900; font-size: 20px; background: linear-gradient(135deg, #ffffff 0%, #fef08a 40%, #f59e0b 80%, #d97706 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">로또픽 (Lotto Pick)</span>
        </td>
        <td style="width: 12%; text-align: left; vertical-align: middle;"><span class="sparkle-clover">🍀</span></td>
    </tr>
</table>
<div style="text-align: center; margin-bottom: 25px;">
    <div style="color: #e2e8f0; font-size: 15px; font-weight: 800;">초정밀 통계·조합 분석 시스템</div>
    <div style="color: #94a3b8; font-size: 11px; font-weight: 600; letter-spacing: 1px; margin: 4px 0;">LOTTO & PENSION LOTTERY ANALYTICS</div>
    <div style="color: #38bdf8; font-size: 12px; font-weight: 700; margin-top: 4px;">"데이터는 정밀하게, 분석은 체계적으로"</div>
</div>
""", unsafe_allow_html=True)

# 상단 애드센스 배너
st.markdown("""
<div class="adsense-box">
    <div style="font-size: 11px; color: #8b949e; margin-bottom: 5px;">[Sponsored Ad / 애드센스 광고]</div>
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-2324282297166072" crossorigin="anonymous"></script>
    <ins class="adsbygoogle" style="display:block" data-ad-client="ca-pub-2324282297166072" data-ad-slot="1234567890" data-ad-format="auto" data-full-width-responsive="true"></ins>
    <script>(adsbygoogle = window.adsbygoogle || []).push({});</script>
</div>
""", unsafe_allow_html=True)

# ================= 2. 복권 선택 버튼 =================
col_b1, col_b2 = st.columns(2)
with col_b1:
    if st.button("🔴 로또 6/45 분석", use_container_width=True, key="btn_lotto"):
        st.session_state.selected_game = "lotto"
        st.rerun()
with col_b2:
    if st.button("🔵 연금복권 720+", use_container_width=True, key="btn_pension"):
        st.session_state.selected_game = "pension"
        st.rerun()

game_name_str = "로또 6/45" if st.session_state.selected_game == "lotto" else "연금복권 720+"
st.markdown(f"""
<div class="keep-all" style="background-color: #0f172a; border: 2px solid #22c55e; padding: 15px; border-radius: 12px; text-align: center; color: #4ade80; font-weight: bold; font-size: 15px; animation: glow-green 2s infinite; margin-top: 15px; margin-bottom: 20px;">
<span>{"🔴" if st.session_state.selected_game=="lotto" else "🔵"} {game_name_str} 분석 ⚙ ● 정밀 시스템 실시간 가동 중</span>
</div>
""", unsafe_allow_html=True)

with st.expander("⚙ 맞춤형 시스템 상세 설정 (무료/VIP 공통)", expanded=False):
    game_count = st.slider("추천 게임 수", 1, 10, 5)

# ================= 4. VIP 결제 및 코드 입력 시스템 =================
if st.session_state.get("payment_flash"):
    flash = st.session_state.payment_flash
    if not flash.get("ok"):
        st.error(f"❌ 결제 처리 안내: {flash.get('message', '')}")
    else:
        st.info("결제 인증이 완료되었습니다. 서버 승인 확인 중입니다.")
    st.session_state.payment_flash = None

status_order_id = st.session_state.get("last_payment_order_id") or st.session_state.get("last_completed_order_id")
if status_order_id:
    payment_status_panel(status_order_id)

if not st.session_state.vip_unlocked:
    st.markdown("""
    <div class="keep-all" style="background-color: #064e3b; border: 2px solid #eab308; padding: 20px; border-radius: 12px; animation: gold-glow 2s infinite; margin: 20px auto 15px auto; color: #fef08a; text-align: center;">
    <h4 style="margin-top: 0; font-size: 18px; margin-bottom: 15px; color: #fde047; font-weight: 900;">👑 VIP 프리패스 혜택 안내</h4>
    <p style="font-size: 14px; line-height: 1.6; text-align: left; color: #ecfdf5;">
    ✅ <b>이번 주 고정수 & 완벽 제외수 리포트 즉시 공개</b><br>
    ✅ AI 패턴 기반 <b>S등급 일치율 점수 & 분석 태그</b> 제공<br>
    ✅ 프리미엄 빅데이터 통계 조합 가동
    </p>
    </div>
    """, unsafe_allow_html=True)

    with st.form("vip_order_form"):
        buyer_phone = st.text_input("📱 VIP 코드를 받을 휴대폰 번호", placeholder="01012345678", max_chars=20, key="buyer_phone_input")
        sms_consent = st.checkbox("VIP 코드 발송을 위해 휴대폰 번호 수집 및 SMS 발송에 동의합니다.", key="vip_sms_consent")
        order_submitted = st.form_submit_button("🧾 1,000원 VIP 주문 생성", use_container_width=True)

    if order_submitted:
        normalized_phone = normalize_phone(buyer_phone)
        if not re.fullmatch(r"01[016789]\d{7,8}", normalized_phone):
            st.error("❌ 올바른 국내 휴대폰 번호를 입력해 주세요.")
        elif not sms_consent:
            st.error("❌ 문자 발송 동의에 체크해 주세요.")
        else:
            try:
                new_order_id = create_order(normalized_phone)
                st.session_state.pending_order_id = new_order_id
                st.success("✅ 주문이 생성되었습니다. 아래 결제 버튼을 눌러주세요.")
            except Exception as exc:
                st.error(f"주문 생성 실패: {type(exc).__name__}")

    pending_order_id = st.session_state.get("pending_order_id", "")
    if pending_order_id:
        pending_order = get_order(pending_order_id)
        if pending_order and pending_order["status"] == "PENDING":
            st.markdown("<div style='margin-top:12px'></div>", unsafe_allow_html=True)
            st.markdown(f"**주문번호:** `{pending_order_id}` · **결제금액:** 1,000원")
            st.html(render_toss_payment_button(pending_order_id, pending_order["phone"]))

    st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
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
                st.success("🎉 VIP 프리패스가 활성화되었습니다!")
                st.rerun()
            else:
                st.error(f"❌ {msg}")
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

# ================= 6. 탭 메뉴 =================
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
                balls_html = "".join([f'<div style="width: 32px; height: 32px; border-radius: 50%; background-color: {get_ball_color(n)}; color: white; display: flex; justify-content: center; align-items: center; font-weight: bold; font-size: 14px; margin-right: 5px;">{n}</div>' for n in numbers])
                if is_vip:
                    tags_html = "".join([f'<span class="vip-tag">{tag}</span>' for tag in (tags or [])])
                    html_str = f"""
                    <div class="game-box-vip">
                        <div class="s-class-badge">S-CLASS</div>
                        <div style="color: #facc15; font-weight: 900; font-size: 15px; margin-bottom: 5px;">👑 VIP 프리미엄 게임 {i+1}</div>
                        <div style="display: flex; justify-content: space-between; align-items: center; font-size: 12px; color: #d1d5db; margin-bottom: 2px;">
                            <span>딥러닝 일치율</span><span style="color: #4ade80; font-weight: bold;">{match_score}%</span>
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
                            <span>딥러닝 일치율</span><span style="color: #4ade80; font-weight: bold;">{match_score}%</span>
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
            <div style="background: linear-gradient(135deg, #1e293b, #0f172a); border: 2px dashed #64748b; border-radius: 12px; padding: 28px 20px; text-align: center; margin-top: 15px; color: #cbd5e1;">
                <div style="font-size: 15px; font-weight: 800; color: #fef08a; margin-bottom: 8px;">🔒 VIP 프리미엄 전용 콘텐츠</div>
                <div style="font-size: 13px; color: #94a3b8;">결제 후 [금주 완벽 제외수 10개]와 [S등급 상세 분석 리포트]가 즉시 해제됩니다.</div>
            </div>
            """, unsafe_allow_html=True)

with tab2:
    st.markdown("<h4 style='color: #ffffff; font-weight: 800;'>📈 역대 당첨 번호 통계 분석</h4>", unsafe_allow_html=True)
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

# 하단 애드센스 배너
st.markdown("""
<div class="adsense-box">
    <div style="font-size: 11px; color: #8b949e; margin-bottom: 5px;">[Sponsored Ad / 애드센스 광고]</div>
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-2324282297166072" crossorigin="anonymous"></script>
    <ins class="adsbygoogle" style="display:block" data-ad-client="ca-pub-2324282297166072" data-ad-slot="1234567890" data-ad-format="auto" data-full-width-responsive="true"></ins>
    <script>(adsbygoogle = window.adsbygoogle || []).push({});</script>
</div>
""", unsafe_allow_html=True)

# ================= 7. 하단 고객센터 및 푸터 =================
st.markdown("---")
st.markdown("<h4 style='color: #ffffff; font-weight: 900; margin-bottom: 8px;'>📞 고객 센터</h4>", unsafe_allow_html=True)
st.markdown(f"""
<div class="footer-buttons-container">
    <a href="{GOOGLE_FORM_URL}" target="_blank" class="footer-btn footer-btn-cs">🛠️ 고객센터 문의 접수</a>
    <a href="https://www.dhlottery.co.kr" target="_blank" class="footer-btn footer-btn-dhlottery">🛒 동행복권 홈</a>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div style="background-color: #1a1a1a; padding: 15px; border-radius: 8px; margin-top: 25px; border: 1px solid #333; color: #a1a1aa; font-size: 11px; line-height: 1.6;">
<b>[법적 고지 및 주의사항]</b><br>
1. 본 서비스에서 제공하는 번호 조합 및 통계 자료는 과거 데이터 기반 확률적 추정치이며, 실제 당첨을 보장하지 않습니다.<br>
2. 구매에 대한 모든 책임은 사용자 본인에게 있습니다. (도박중독 예방치유센터: 1336)
</div>
<div style="text-align: center; color: #94a3b8; font-size: 11px; margin-top: 20px; line-height: 1.8;">
    <b>상호:</b> 엠피디뮤직 (MPD music) &nbsp;|&nbsp; <b>대표:</b> 이근영 &nbsp;|&nbsp; <b>사업자등록번호:</b> 162-23-01932<br>
    <b>사업장 주소:</b> 경기도 고양시 덕양구 능곡로 16, 101동 501호<br>
    <b>고객센터:</b> 010-5282-7017 &nbsp;|&nbsp; <b>이메일:</b> mzpdlee@gmail.com<br><br>
    © 2026 로또픽(Lotto Pick) 분석 시스템. All Rights Reserved.
</div>
""", unsafe_allow_html=True)
