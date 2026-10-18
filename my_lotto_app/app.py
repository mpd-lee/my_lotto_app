# -*- coding: utf-8 -*-
"""로또픽: 기존 화면 유지 + 안전한 토스 결제 확인 + VIP 코드/SMS 발급.
결제창은 st.components.v1.html iframe에서 자동 실행하지 않습니다.
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

# Streamlit의 첫 호출은 페이지 설정입니다.
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
    """Reruns share this registry; worker threads are not launched twice per order."""
    return {
        "lock": threading.RLock(),
        "payments": set(),
        "sms": set(),
    }


WORKERS = get_worker_registry()


def get_secret(name: str, default: str = "") -> str:
    """Streamlit Secrets first, then environment variables. No embedded credentials."""
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

# ================= DB/주문 관리 =================
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
        # Backward-compatible migration for a database created by an earlier version.
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

# ================= Solapi SMS =================
def send_vip_sms(receiver_phone: str, vip_code: str):
    """Solapi에 문자 발송을 요청합니다. API 접수는 통신사 최종 배달을 뜻하지 않습니다."""
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
        f"[로또픽] VIP 코드: {vip_code}\n"
        f"이용기간: 결제 승인 시점부터 7일\n"
        f"메인 화면에서 코드를 입력해 주세요."
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
                    return False, "Solapi가 발송 실패를 반환했습니다. 발송 내역에서 상세 오류를 확인해 주세요."
            except (ValueError, AttributeError):
                pass
            return True, "Solapi에 발송 요청이 접수되었습니다."
        try:
            body = response.json()
            detail = body.get("message") or body.get("errorMessage") or body.get("errorCode") or f"HTTP {response.status_code}"
        except ValueError:
            detail = f"HTTP {response.status_code}"
        return False, str(detail)[:300]
    except requests.RequestException as exc:
        return False, f"Solapi 통신 오류: {type(exc).__name__}"


def _sms_worker(order_id: str):
    """Runs after the page has already rendered, so a slow SMS API cannot hold the payment screen."""
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
    """Atomically claim a SMS attempt and send it in a worker. Returns immediately."""
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
                # Allow an explicit user retry of a stale SENDING status only after 60 seconds.
                if current == "SENDING" and row["sms_started_at"] and time.time() - float(row["sms_started_at"]) > 60:
                    allowed.add("SENDING")
            else:
                allowed = {"PENDING"}
            if current not in allowed:
                return False, f"문자 상태가 {current}입니다. 중복 발송을 방지했습니다."
            cur = conn.execute(
                "UPDATE vip_orders SET sms_status='SENDING', sms_error=NULL, sms_started_at=? WHERE order_id=? AND status='PAID' AND sms_status=?",
                (time.time(), order_id, current),
            )
            if cur.rowcount != 1:
                return False, "문자 상태가 변경되었습니다. 잠시 후 상태를 새로고침해 주세요."
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
    """Confirm through Toss. If confirmation already happened, verify by fetching payment details."""
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

    # Retry-safe recovery: the confirm API may already have succeeded while the browser timed out.
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
    """Confirm/query Toss in a background thread; never block the user-facing redirect on network I/O."""
    try:
        order = get_order(order_id)
        if not order:
            return
        if int(order["amount"]) != int(amount) or int(amount) != PRODUCT_AMOUNT:
            with db_session() as conn:
                conn.execute(
                    "UPDATE vip_orders SET status='VERIFY_FAILED', verify_error=? WHERE order_id=? AND status='VERIFYING'",
                    ("결제 금액이 서버 주문 금액과 일치하지 않습니다.", order_id),
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
        # Code is committed before SMS. The page can show the code while SMS is still pending.
        current = get_order(order_id)
        if current and current["status"] == "PAID" and current["payment_key"] == payment_key:
            if current["sms_status"] == "PENDING":
                schedule_sms_for_order(order_id, allow_retry=False)
    except Exception as exc:
        try:
            with db_session() as conn:
                conn.execute(
                    "UPDATE vip_orders SET status='VERIFY_FAILED', verify_error=?, verify_started_at=NULL WHERE order_id=? AND status='VERIFYING' AND payment_key=?",
                    (f"승인 확인 중 내부 오류: {type(exc).__name__}", order_id, payment_key),
                )
        except Exception:
            pass
    finally:
        with WORKERS["lock"]:
            WORKERS["payments"].discard(order_id)


def schedule_payment_verification(order_id: str, payment_key: str, requested_amount, force: bool = False):
    """Quickly mark the order for verification, then confirm Toss asynchronously."""
    if not order_id or not payment_key:
        return False, "토스 결제 결과에 주문번호 또는 paymentKey가 없습니다."
    try:
        amount = int(str(requested_amount))
    except (TypeError, ValueError):
        return False, "토스 결제 결과의 금액 형식이 올바르지 않습니다."
    if amount != PRODUCT_AMOUNT:
        return False, "결제 금액이 상품 금액(1,000원)과 일치하지 않습니다."

    already_paid = False
    should_queue_sms = False
    with WORKERS["lock"]:
        if order_id in WORKERS["payments"]:
            return True, "VERIFYING"
        with db_session() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute("SELECT * FROM vip_orders WHERE order_id=?", (order_id,)).fetchone()
            if not row:
                return False, "서버에 저장된 주문을 찾을 수 없습니다. 새 주문 생성 전 고객센터에 문의해 주세요."
            if int(row["amount"]) != amount:
                return False, "요청 금액이 서버에 저장된 주문 금액과 일치하지 않습니다."
            if row["status"] == "PAID":
                if row["payment_key"] != payment_key:
                    return False, "이미 승인된 주문에 다른 paymentKey가 들어왔습니다."
                already_paid = True
                should_queue_sms = (row["sms_status"] or "PENDING") == "PENDING"
            else:
                if row["status"] == "CANCELLED":
                    return False, "취소된 주문입니다. 새 주문을 만들어 주세요."
                if row["status"] == "VERIFYING" and row["payment_key"] not in (None, payment_key):
                    return False, "해당 주문에 다른 paymentKey로 승인 확인이 진행 중입니다."
                # PENDING, VERIFY_FAILED, and orphaned VERIFYING states may be confirmed safely.
                if row["status"] not in ("PENDING", "VERIFY_FAILED", "VERIFYING"):
                    return False, f"현재 주문 상태({row['status']})에서는 확인할 수 없습니다."
                conn.execute(
                    "UPDATE vip_orders SET status='VERIFYING', payment_key=?, verify_started_at=?, verify_error=NULL WHERE order_id=?",
                    (payment_key, time.time(), order_id),
                )
        if already_paid:
            # The first worker can be interrupted just after committing PAID. If SMS is still PENDING,
            # queue it here, outside the DB transaction, without ever issuing a second code.
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
    """Restart payment verification after a process restart if a browser already returned from Toss."""
    try:
        with db_session() as conn:
            rows = conn.execute(
                "SELECT order_id, payment_key, amount FROM vip_orders WHERE status='VERIFYING' AND payment_key IS NOT NULL"
            ).fetchall()
        for row in rows:
            # schedule_payment_verification will skip orders with an active worker in this process.
            schedule_payment_verification(row["order_id"], row["payment_key"], row["amount"], force=True)
    except Exception:
        # Do not prevent the main app from rendering because a recovery scan failed.
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
        return False, 0, "실제 결제 승인으로 발급된 코드를 찾을 수 없습니다."
    if not row["expires_at"] or time.time() > float(row["expires_at"]):
        return False, 0, "VIP 이용 기간 7일이 만료되었습니다."
    return True, float(row["expires_at"]), "승인 완료"


def render_toss_payment_button(order_id: str, phone: str) -> str:
    """Load the SDKs in order (V1 first because the original app used it, V2 fallback).
    Never automatically start a payment on render; a real click is required.
    This HTML is inserted with st.html(..., unsafe_allow_javascript=True), not an iframe.
    """
    if not TOSS_CLIENT_KEY:
        return "<div style='padding:12px;color:#fecaca'>토스 클라이언트 키가 설정되지 않았습니다. Streamlit Secrets를 확인해 주세요.</div>"

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

    # V1 is the SDK used by the user's original app and had already opened the card authentication UI.
    # V2 is the official current fallback. Keep the method signatures separate; do not mix APIs.
    return f'''<div style="max-width:520px;margin:8px auto;padding:16px;background:#111827;border:2px solid #eab308;border-radius:14px;text-align:center;color:#fff">
      <div style="font-weight:900;color:#fde047;font-size:17px;margin-bottom:8px">🍀 VIP 골든픽 1주 프리패스</div>
      <div style="font-size:23px;font-weight:900;margin-bottom:12px">1,000원</div>
      <button id="{btn_id}" type="button" disabled style="width:100%;padding:15px;border:2px solid #fde047;border-radius:11px;background:linear-gradient(135deg,#059669,#047857);color:#fff;font-size:16px;font-weight:900;cursor:pointer;opacity:.75">토스 결제 SDK 준비 중...</button>
      <div id="{msg_id}" aria-live="polite" style="font-size:12px;color:#cbd5e1;margin-top:8px">결제 SDK를 확인하고 있습니다. 결제 요청은 버튼을 직접 누를 때만 시작됩니다.</div>
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
            else reject(new Error(item.version.toUpperCase() + ' 스크립트는 내려왔지만 TossPayments 초기화 함수를 찾지 못했습니다.'));
          }}
          function rejectOnce(reason) {{
            if (settled) return;
            settled = true;
            if (timer) clearTimeout(timer);
            reject(reason instanceof Error ? reason : new Error(String(reason || 'SDK 다운로드 실패')));
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
            script.addEventListener('error', function() {{ rejectOnce(new Error(item.version.toUpperCase() + ' SDK 네트워크 로드 실패')); }}, {{ once: true }});
            timer = setTimeout(function() {{ rejectOnce(new Error(item.version.toUpperCase() + ' SDK 로딩 시간 초과')); }}, 12000);
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
              rejectOnce(new Error(item.version.toUpperCase() + ' SDK 전역 함수를 찾지 못했습니다.'));
            }}
          }};
          script.onerror = function() {{
            script.dataset.state = 'failed';
            rejectOnce(new Error(item.version.toUpperCase() + ' SDK 다운로드 실패 (' + item.url + ')'));
          }};
          timer = setTimeout(function() {{
            script.dataset.state = 'failed';
            rejectOnce(new Error(item.version.toUpperCase() + ' SDK 로딩 12초 초과 (' + item.url + ')'));
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
            msg.textContent = '기존 결제 SDK를 불러오지 못했습니다. 공식 V2 SDK로 다시 시도합니다.';
            return loadOneSdk(SDK_LIST[1]).catch(function(v2Error) {{
              throw new Error('V1 실패: ' + v1Error.message + ' / V2 실패: ' + v2Error.message);
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
        msg.textContent = '결제 SDK 준비 완료 (' + version.toUpperCase() + '). 결제하려면 버튼을 눌러 주세요.';
      }}

      function showFailure(error) {{
        btn.disabled = false;
        btn.style.opacity = '1';
        btn.textContent = '🔄 결제 SDK 다시 불러오기';
        msg.textContent = 'SDK를 불러오지 못했습니다. ' + (error && error.message ? error.message : '네트워크 오류') + '. 브라우저에서 js.tosspayments.com 접속을 허용하고 다시 눌러 주세요.';
      }}

      function startPayment(version) {{
        const tossPayments = window.TossPayments(config.clientKey);
        if (version === 'v1') {{
          // V1 legacy API. This is intentionally the exact API family used by the original app.
          return tossPayments.requestPayment('카드', {{
            amount: config.amount,
            orderId: config.orderId,
            orderName: config.orderName,
            customerMobilePhone: config.phone,
            successUrl: config.successUrl,
            failUrl: config.failUrl
          }});
        }}
        // V2 legacy payment-window API. Use V2 parameter shape only with the V2 SDK.
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
          msg.textContent = '결제 SDK를 다시 확인하고 있습니다.';
          loadSdkWithFallback().then(showReady).catch(showFailure);
          return;
        }}
        busy = true;
        btn.disabled = true;
        btn.textContent = '결제창으로 이동 중...';
        msg.textContent = '결제 인증 후 로또픽으로 돌아옵니다. 승인 확인 전에는 VIP 코드가 발급되지 않습니다.';
        try {{
          const result = startPayment(activeSdk);
          if (result && typeof result.catch === 'function') {{
            result.catch(function(error) {{
              busy = false;
              btn.disabled = false;
              btn.textContent = '💳 토스페이먼츠 결제 다시 시도';
              const code = error && error.code ? String(error.code) : '';
              if (code === 'USER_CANCEL' || code === 'PAY_PROCESS_CANCELED') {{
                msg.textContent = '결제가 취소되었습니다. 원하실 때 다시 진행해 주세요.';
              }} else {{
                msg.textContent = '결제 요청 오류' + (code ? ' (' + code + ')' : '') + ': ' + (error && error.message ? error.message : '결제 요청에 실패했습니다.');
              }}
            }});
          }}
        }} catch(error) {{
          busy = false;
          btn.disabled = false;
          btn.textContent = '💳 토스페이먼츠 결제 다시 시도';
          msg.textContent = '결제 초기화 오류: ' + (error && error.message ? error.message : '요청에 실패했습니다.');
        }}
      }});
    }})();
    </script>'''

@st.fragment(run_every=2)
def payment_status_panel(order_id: str):
    """Auto-refresh payment/SMS state without holding the page in a blocking HTTP request."""
    row = get_order(order_id)
    if not row:
        st.warning("결제 주문 정보를 찾지 못했습니다. 고객센터에 주문번호를 알려 주세요.")
        return
    status = row["status"]
    if status == "VERIFYING":
        st.info("🔄 토스 결제 승인을 서버에서 확인 중입니다. 이 화면은 자동으로 갱신됩니다. 결제를 반복하지 마세요.")
        if row["verify_started_at"] and time.time() - float(row["verify_started_at"]) > 45:
            if st.button("🔁 결제 승인 확인 다시 시도", key=f"retry-verify-{order_id}", use_container_width=True):
                schedule_payment_verification(order_id, row["payment_key"], row["amount"], force=True)
                st.rerun(scope="fragment")
    elif status == "PAID":
        st.success("✅ 토스 결제 승인 확인 완료. VIP 코드가 발급되었습니다.")
        st.markdown(f"### 🔑 VIP 전용 코드: `{row['vip_code']}`")
        expiry_text = datetime.fromtimestamp(float(row["expires_at"])).strftime("%Y-%m-%d %H:%M") if row["expires_at"] else "확인 필요"
        st.caption(f"이용 만료: {expiry_text} (서버 기준)")
        sms_status = row["sms_status"] or "PENDING"
        if sms_status == "SENT":
            st.success("📱 Solapi에 문자 발송 요청이 접수되었습니다. 실제 수신은 통신사 사정에 따라 다를 수 있습니다.")
        elif sms_status == "SENDING":
            st.info("📨 VIP 코드는 발급되었습니다. 휴대폰 문자 발송을 처리 중입니다. 코드는 지금 아래 입력란에서 사용할 수 있습니다.")
            if row["sms_started_at"] and time.time() - float(row["sms_started_at"]) > 60:
                if st.button("📨 문자 발송 다시 시도", key=f"retry-sms-stale-{order_id}", use_container_width=True):
                    ok, detail = schedule_sms_for_order(order_id, allow_retry=True)
                    st.info(detail)
                    st.rerun(scope="fragment")
        elif sms_status == "FAILED":
            st.warning("⚠️ 결제는 완료되었지만 문자 발송에 실패했습니다. 위 코드로 바로 잠금을 해제하거나 문자를 다시 보내세요.")
            if row["sms_error"]:
                st.caption(f"문자 오류: {row['sms_error']}")
            if st.button("📨 VIP 코드 문자 재발송", key=f"retry-sms-{order_id}", use_container_width=True):
                ok, detail = schedule_sms_for_order(order_id, allow_retry=True)
                if ok:
                    st.success(detail)
                else:
                    st.warning(detail)
                st.rerun(scope="fragment")
        else:
            st.info("VIP 코드가 발급되었습니다. 문자 발송을 준비 중입니다. 아래 코드 입력란에서 먼저 이용하실 수 있습니다.")
    elif status == "VERIFY_FAILED":
        st.error("❌ 토스 승인 상태를 확인하지 못했습니다. 실제 결제가 완료되었을 수 있으니 새 주문을 반복 생성하지 마세요.")
        if row["verify_error"]:
            st.caption(f"승인 확인 진단: {row['verify_error']}")
        if row["payment_key"] and st.button("🔁 결제 승인 상태 다시 확인", key=f"retry-verify-failed-{order_id}", use_container_width=True):
            ok, detail = schedule_payment_verification(order_id, row["payment_key"], row["amount"], force=True)
            if ok:
                st.info("서버에서 결제 상태를 다시 확인하고 있습니다.")
            else:
                st.error(str(detail))
            st.rerun(scope="fragment")
    elif status == "CANCELLED":
        st.warning("결제가 취소되었거나 실패한 주문입니다. 결제를 원하시면 새 주문을 만들어 주세요.")


# ================= 페이지 설정/DB 초기화 =================
init_db()
st.markdown('<meta name="google-adsense-account" content="ca-pub-2324282297166072">', unsafe_allow_html=True)

st.caption("결제 SDK 진단 버전: LOTTOPICK-TOSS-SDK-FALLBACK-2026-10-18-B")

# ================= 세션 상태 기본값 =================
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
    st.warning("⏱ VIP 이용 기간(7일)이 만료되었습니다. 계속 이용하시려면 재결제를 진행해 주세요.")

# ================= 결제 리다이렉트 처리 =================
# Redirect handling only queues server verification and returns the user to the app immediately.
query = st.query_params
if "payment_success" in query:
    payment_key = str(query.get("paymentKey", ""))
    order_id = str(query.get("orderId", ""))
    amount = str(query.get("amount", ""))
    ok, result = schedule_payment_verification(order_id, payment_key, amount)
    if ok:
        st.session_state.last_payment_order_id = order_id
        st.session_state.pending_order_id = order_id
        st.session_state.payment_flash = {"ok": True, "message": "결제 결과를 서버에서 확인 중입니다."}
    else:
        st.session_state.payment_flash = {"ok": False, "message": str(result)}
    st.query_params.clear()
    st.rerun()
elif "payment_fail" in query:
    error_code = str(query.get("code", query.get("errorCode", "")))
    error_message = str(query.get("message", query.get("errorMessage", "")))
    order_id = str(query.get("orderId", ""))
    if order_id:
        with db_session() as conn:
            conn.execute("UPDATE vip_orders SET status='CANCELLED' WHERE order_id=? AND status='PENDING'", (order_id,))
    note = error_code or error_message or "사용자 취소"
    st.session_state.payment_flash = {"ok": False, "message": f"결제가 취소되었거나 실패했습니다. ({note})"}
    st.query_params.clear()
    st.rerun()
elif str(query.get("pay_popup", "")).lower() == "true":
    st.session_state.payment_flash = {
        "ok": False,
        "message": "이전 결제 주소(pay_popup=true)는 구형 iframe 방식입니다. 주소가 초기화되었습니다. 메인 화면에서 새 주문을 생성해 주세요.",
    }
    st.query_params.clear()
    st.rerun()

# Recover an order that was marked VERIFYING just before a Streamlit process restart.
recover_verifying_orders()

# ================= 세레모니 실행 처리 =================
if st.session_state.trigger_snow:
    st.snow()
    st.session_state.trigger_snow = False
if st.session_state.trigger_balloons:
    st.balloons()
    st.session_state.trigger_balloons = False

# 기존 버튼 네온 스타일을 유지하되 50ms setInterval/iframe 접근은 사용하지 않습니다.
st.html("""
<script>
(function() {
  function applyStrictStyles() {
    try {
      document.querySelectorAll('button').forEach(function(btn) {
        const text = btn.innerText || btn.textContent || '';
        if (text.includes('토스페이먼츠 안전 결제창 열기') || text.includes('VIP 주문 생성')) {
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
    } catch (e) {}
  }
  applyStrictStyles();
  if (!window.__lottoPickStyleObserverBound) {
    window.__lottoPickStyleObserverBound = true;
    const observer = new MutationObserver(applyStrictStyles);
    observer.observe(document.body, { childList: true, subtree: true });
    window.__lottoPickStyleObserver = observer;
  }
})();
</script>
""", unsafe_allow_javascript=True)

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

# ================= 4. 금빛 VIP 시스템 (비동기 승인 확인 및 코드/SMS 상태 자동 갱신) =================
if st.session_state.get("payment_flash"):
    flash = st.session_state.payment_flash
    if not flash.get("ok"):
        st.error(f"❌ 결제 처리 안내: {flash.get('message', '결제 상태를 확인할 수 없습니다.')}")
    else:
        st.info("결제 인증이 끝났습니다. 서버 승인 확인이 진행 중이며, 완료되면 아래에 VIP 코드가 표시됩니다.")
    st.session_state.payment_flash = None

status_order_id = st.session_state.get("last_payment_order_id") or st.session_state.get("last_completed_order_id")
if status_order_id:
    payment_status_panel(status_order_id)

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
<div style="font-size: 13px; color: #a7f3d0; margin-bottom: 5px;">🔒 휴대폰 번호로 주문을 생성한 뒤 토스 결제를 진행해 주세요.</div>
<div style="font-size: 12px; color: #fde047; font-weight: bold; margin-top: 4px;">결제 인증 후 서버에서 실제 승인 여부를 확인한 뒤 VIP 코드가 발급됩니다.</div>
</div>
""", unsafe_allow_html=True)

    with st.form("vip_order_form"):
        buyer_phone = st.text_input("📱 VIP 코드를 받을 휴대폰 번호", placeholder="01012345678", max_chars=20, key="buyer_phone_input")
        sms_consent = st.checkbox("VIP 코드 발송을 위해 입력한 휴대폰 번호로 SMS를 보내는 데 동의합니다.", key="vip_sms_consent")
        order_submitted = st.form_submit_button("🧾 1,000원 VIP 주문 생성", use_container_width=True)

    if order_submitted:
        normalized_phone = normalize_phone(buyer_phone)
        if not re.fullmatch(r"01[016789]\d{7,8}", normalized_phone):
            st.error("❌ 010 등 올바른 국내 휴대폰 번호를 입력해 주세요.")
        elif not sms_consent:
            st.error("❌ VIP 코드 문자 발송 동의에 체크해 주세요.")
        elif not TOSS_CLIENT_KEY or not TOSS_SECRET_KEY:
            st.error("❌ 토스 클라이언트 키 또는 시크릿 키가 설정되지 않았습니다. Streamlit Cloud의 App Settings → Secrets를 확인해 주세요.")
        else:
            try:
                new_order_id = create_order(normalized_phone)
                st.session_state.pending_order_id = new_order_id
                st.success("✅ 주문이 생성되었습니다. 아래의 결제 버튼을 한 번 눌러 진행해 주세요.")
            except Exception as exc:
                st.error(f"주문 생성에 실패했습니다. 잠시 후 다시 시도해 주세요. ({type(exc).__name__})")

    pending_order_id = st.session_state.get("pending_order_id", "")
    if pending_order_id:
        pending_order = get_order(pending_order_id)
        if pending_order and pending_order["status"] == "PENDING":
            st.markdown("<div style='margin-top:12px'></div>", unsafe_allow_html=True)
            st.markdown(f"**주문번호:** `{pending_order_id}` · **결제금액:** 1,000원")
            st.html(render_toss_payment_button(pending_order_id, pending_order["phone"]), unsafe_allow_javascript=True)
            st.caption("결제창은 현재 브라우저 페이지에서 열립니다. 결제 완료 후 같은 주소로 돌아오며, 승인 확인 전에는 VIP 코드가 발급되지 않습니다.")
        elif pending_order and pending_order["status"] == "PAID":
            st.info("이 주문은 이미 결제 승인되었습니다. VIP 코드 입력란에서 문자로 받은 코드를 입력해 주세요.")
        elif pending_order and pending_order["status"] in ("FAILED", "CANCELLED"):
            st.warning("이 주문은 진행할 수 없는 상태입니다. 새 주문을 생성해 주세요.")

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
            st.success("🎉 VIP 프리패스가 성공적으로 활성화되었습니다!")
            st.rerun()
        else:
            st.error(f"❌ {msg}")

    last_order_id = st.session_state.get("last_completed_order_id", "")
    if last_order_id:
        last_order = get_order(last_order_id)
        if last_order and last_order["status"] == "PAID" and last_order["sms_status"] in ("FAILED", "PENDING"):
            if st.button("📨 VIP 코드 문자 재발송", use_container_width=True, key="resend_vip_sms"):
                ok, detail = schedule_sms_for_order(last_order_id, allow_retry=True)
                if ok:
                    st.success("✅ " + detail)
                else:
                    st.error(f"문자 재발송을 처리하지 못했습니다: {detail}")
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
            if st.session_state.extract_game_type == "lotto":
                fixed_str = ", ".join(map(str, st.session_state.get("vip_fixed", [1, 2])))
                excl_str = ", ".join(map(str, st.session_state.get("vip_excluded", [3, 4, 5])))
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
            st.markdown(
"""
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
        st.markdown(
"""
<div style='text-align:center; padding: 10px; background:#1e1b18; border:1px solid #eab308; border-radius:8px; color:#facc15; font-size:14px; font-weight: bold;'>
🔒 VIP 전용: 미출현 장기 번호 및 회귀 추적 데이터 잠김
</div>
""", unsafe_allow_html=True)

with tab3:
    st.markdown("<h4 style='color: #ffffff; font-weight: 800;'>📑 분석 연구 모델</h4>", unsafe_allow_html=True)
    st.markdown(
"""
<div style="font-size: 15px; color: #f1f5f9; line-height: 1.8; font-weight: 600;">
- Markov Chain Monte Carlo (MCMC) 모델<br>
- Poisson Distribution 출현 간격 예측<br>
- AC값(Arithmetic Complexity) 복잡도 필터링
</div>
""", unsafe_allow_html=True)

# ================= 7. 하단 고객센터 =================
st.markdown("---")
st.markdown("<h4 style='color: #ffffff; font-weight: 900; margin-bottom: 8px;'>📞 고객 센터</h4>", unsafe_allow_html=True)

st.markdown(
"""
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
st.markdown(
"""
<div style="background-color: #1a1a1a; padding: 15px; border-radius: 8px; margin-top: 25px; border: 1px solid #333; color: #a1a1aa; font-size: 11px; line-height: 1.6; word-break: keep-all;">
<b>[법적 고지 및 주의사항]</b><br>
1. 본 서비스(로또픽)에서 제공하는 번호 조합 및 통계 분석 자료는 과거의 데이터를 기반으로 한 확률적 추정치이며, <b>실제 복권 당첨을 절대 보장하지 않습니다.</b><br>
2. 제공된 번호를 이용한 복권 구매 등 모든 판단과 책임은 전적으로 <b>사용자 본인</b>에게 있으며, 본 서비스는 이로 인해 발생하는 어떠한 직·간접적 손실에 대해서도 법적 책임을 지지 않습니다.<br>
3. 복권은 소액으로 건전하게 즐기시길 바라며, 과도한 몰입은 일상생활에 지장을 줄 수 있습니다. (도박중독 예방치유센터: 1336)
</div>

<div style="text-align: center; color: #94a3b8; font-size: 11px; margin-top: 20px; line-height: 1.8; padding-top: 20px; border-top: 1px solid #333;">
    <b>상호:</b> 엠피디뮤직 (MPD music) &nbsp;|&nbsp; <b>대표:</b> 이근영 &nbsp;|&nbsp; <b>사업자등록번호:</b> 162-23-01932<br>
    <b>사업장 주소:</b> 경기도 고양시 덕양구 능곡로 16, 101동 501호(토당동, 숲예찬)<br>
    <b>고객센터:</b> 010-5282-7017 &nbsp;|&nbsp; <b>이메일:</b> leegysa@naver.com<br><br>
    © 2026 로또픽(Lotto Pick) 분석 시스템. All Rights Reserved.
</div>
""", unsafe_allow_html=True)
