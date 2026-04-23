"""
app.py — Streamlit UI for the Binance Futures Demo Trading Bot.
Run with: streamlit run app.py
"""

import os
import re
import sys

# ── Ensure project root is on the path ───────────────────────────────────────
_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from bot.client import BinanceFuturesClient, BinanceClientError  # noqa: E402
import streamlit as st

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Binance Futures Trading Bot",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background: linear-gradient(135deg, #0d0d1a 0%, #0a1628 50%, #0d0d1a 100%); }

.hero-banner {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    border: 1px solid rgba(99,102,241,0.3);
    border-radius: 16px; padding: 2rem 2.5rem; margin-bottom: 2rem;
    box-shadow: 0 8px 32px rgba(99,102,241,0.15);
}
.hero-banner h1 { color: #e0e7ff; font-size: 2rem; font-weight: 700; margin: 0; }
.hero-banner p  { color: #94a3b8; font-size: 1rem; margin: 0.5rem 0 0; }

.metric-box {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 10px; padding: 1rem 1.2rem; text-align: center;
}
.metric-box .label { color: #94a3b8; font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.08em; }
.metric-box .value { color: #e0e7ff; font-size: 1.3rem; font-weight: 700; margin-top: 0.3rem; }

.result-card-success {
    background: linear-gradient(135deg, rgba(34,197,94,0.1), rgba(16,185,129,0.05));
    border: 1px solid rgba(34,197,94,0.3); border-radius: 12px; padding: 1.5rem;
}
.result-card-fail {
    background: linear-gradient(135deg, rgba(239,68,68,0.1), rgba(220,38,38,0.05));
    border: 1px solid rgba(239,68,68,0.3); border-radius: 12px; padding: 1.5rem;
}
.log-box {
    background: #0d1117; border: 1px solid rgba(99,102,241,0.2);
    border-radius: 8px; padding: 1rem 1.2rem;
    font-family: 'Courier New', monospace; font-size: 0.78rem; color: #94a3b8;
    max-height: 400px; overflow-y: auto; white-space: pre-wrap;
}
.notice-info {
    background: rgba(99,102,241,0.08); border: 1px solid rgba(99,102,241,0.25);
    border-radius: 8px; padding: 0.75rem 1rem;
    color: #a5b4fc; font-size: 0.85rem; margin-bottom: 1rem;
}
.notice-warn {
    background: rgba(251,191,36,0.1); border: 1px solid rgba(251,191,36,0.35);
    border-radius: 10px; padding: 1rem 1.2rem; margin-bottom: 0.75rem;
}
.notice-error {
    background: rgba(239,68,68,0.1); border: 1px solid rgba(239,68,68,0.35);
    border-radius: 10px; padding: 1rem 1.2rem; margin-bottom: 0.75rem;
}
div[data-testid="stSidebar"] {
    background: rgba(15,15,35,0.95) !important;
    border-right: 1px solid rgba(99,102,241,0.2);
}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR — Credentials
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### ⚙️ Configuration")
    st.markdown("---")

    if "api_key"      not in st.session_state:
        st.session_state["api_key"]      = os.environ.get("BINANCE_API_KEY", "")
    if "api_secret"   not in st.session_state:
        st.session_state["api_secret"]   = os.environ.get("BINANCE_API_SECRET", "")
    if "is_connected" not in st.session_state:
        st.session_state["is_connected"] = bool(
            st.session_state["api_key"] and st.session_state["api_secret"]
        )

    # ── Not connected: show input fields ──────────────────────────────
    if not st.session_state["is_connected"]:
        temp_key    = st.text_input("Binance API Key",    value=st.session_state["api_key"],
                                    type="password", placeholder="64-character API key",
                                    help="Binance API keys are exactly 64 characters")
        temp_secret = st.text_input("Binance API Secret", value=st.session_state["api_secret"],
                                    type="password", placeholder="64-character secret key",
                                    help="Binance API secrets are exactly 64 characters")

        # Live length validation
        clean_key    = re.sub(r'[^\x20-\x7E]', '', temp_key).strip()
        clean_secret = re.sub(r'[^\x20-\x7E]', '', temp_secret).strip()
        key_len      = len(clean_key)
        secret_len   = len(clean_secret)

        if temp_key:
            if key_len == 64:
                st.caption(f"✅ API Key: {key_len} chars (correct)")
            else:
                st.error(f"⚠️ Key is {key_len} chars — must be **64**. Re-copy the full key.")

        if temp_secret:
            if secret_len == 64:
                st.caption(f"✅ API Secret: {secret_len} chars (correct)")
            else:
                st.error(f"⚠️ Secret is {secret_len} chars — must be **64**. Re-copy the full secret.")

        connect_ok = (key_len == 64 and secret_len == 64)

        if st.button("🔗 Connect", type="primary", use_container_width=True,
                     disabled=not connect_ok):
            st.session_state["api_key"]      = clean_key
            st.session_state["api_secret"]   = clean_secret
            st.session_state["is_connected"] = True
            st.rerun()

        if not connect_ok and (temp_key or temp_secret):
            st.caption("💡 Copy keys directly from Binance API Management page — don't select manually.")

    # ── Connected: show status ─────────────────────────────────────────
    else:
        stored_key    = st.session_state["api_key"]
        stored_secret = st.session_state["api_secret"]
        kl = len(stored_key)
        sl = len(stored_secret)

        if kl == 64 and sl == 64:
            st.success("✅ Connected to Binance API")
            st.caption(f"Key: {kl} chars ✓  |  Secret: {sl} chars ✓")
        else:
            st.warning("⚠️ Connected — but key lengths are wrong!")
            st.caption(f"Key: {kl} chars  |  Secret: {sl} chars  (need 64 each)")
            st.error("Disconnect and re-enter your full keys.")

        if st.button("🔌 Disconnect", use_container_width=True):
            st.session_state["api_key"]      = ""
            st.session_state["api_secret"]   = ""
            st.session_state["is_connected"] = False
            st.rerun()

    api_key    = st.session_state["api_key"]
    api_secret = st.session_state["api_secret"]

    st.markdown("---")
    st.markdown("**Base Endpoint**")
    st.code("https://demo-fapi.binance.com", language=None)
    st.markdown("---")
    st.markdown("### 📋 Quick Links")
    st.markdown("- [Binance Demo Futures](https://testnet.binancefuture.com)")
    st.markdown("- [Claim Demo Assets](https://testnet.binancefuture.com)")
    st.markdown("- [API Docs](https://developers.binance.com/docs/derivatives/)")

# ══════════════════════════════════════════════════════════════════════════════
# HERO BANNER
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="hero-banner">
  <h1>⚡ Binance Futures Demo Trading Bot</h1>
  <p>Place MARKET &amp; LIMIT orders on the Binance Futures Demo environment</p>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# STATUS ROW
# ══════════════════════════════════════════════════════════════════════════════
col_ping, col_test, col_cred = st.columns(3)

with col_ping:
    if st.button("🔌 Check Connectivity", use_container_width=True):
        try:
            import requests as _req
            r = _req.get("https://demo-fapi.binance.com/fapi/v1/ping", timeout=5)
            st.success("✅ Demo API is reachable") if r.ok else st.error(f"❌ HTTP {r.status_code}")
        except Exception as e:
            st.error(f"❌ {e}")

with col_test:
    if st.button("🔑 Test Credentials", use_container_width=True):
        if not api_key or not api_secret:
            st.error("❌ No credentials set")
        else:
            with st.spinner("Verifying keys..."):
                try:
                    _c    = BinanceFuturesClient(api_key=api_key, api_secret=api_secret)
                    _acct = _c.get_account_info()
                    avail = _acct.get("availableBalance", "N/A")
                    st.success(f"✅ Keys valid! Balance: {avail} USDT")
                except BinanceClientError as _e:
                    err = str(_e)
                    st.error(f"❌ {_e}")
                    if "-2015" in err:
                        st.warning("Invalid API key or missing Futures permission.")
                    elif "-1022" in err:
                        st.warning("Signature error — disconnect and re-enter full 64-char keys.")
                except Exception as _e:
                    st.error(f"❌ {_e}")

with col_cred:
    if api_key and api_secret:
        st.success("✅ Credentials set")
    else:
        st.warning("⚠️ No credentials")

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════════════════════════════
tab_place, tab_logs = st.tabs(["📤 Place Order", "📋 View Logs"])

# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 — Place Order
# ─────────────────────────────────────────────────────────────────────────────
with tab_place:
    st.markdown("### New Order")

    # ── Demo limitations notice ────────────────────────────────────────
    st.markdown("""
    <div class="notice-info">
      ℹ️ <b>Demo API supports:</b> ✅ MARKET &nbsp;|&nbsp; ✅ LIMIT &nbsp;|&nbsp;
      🚫 STOP_MARKET (blocked by Binance Demo — error -4120, works on live API only)<br/>
      If you see <b>-2019 Margin insufficient</b> →
      <a href="https://testnet.binancefuture.com" target="_blank" style="color:#818cf8;font-weight:600;">
      testnet.binancefuture.com</a> → click <b>"Claim demo assets"</b>.
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    # ── Left column: symbol / side / type / qty ────────────────────────
    with col1:
        symbol = st.text_input(
            "Symbol", value="BTCUSDT",
            placeholder="e.g. BTCUSDT, ETHUSDT"
        ).strip().upper()

        side = st.selectbox("Side", ["BUY", "SELL"])

        order_type = st.selectbox(
            "Order Type",
            ["MARKET", "LIMIT", "STOP_MARKET"],
            help=(
                "MARKET ✅ — fill immediately at market price\n"
                "LIMIT ✅ — fill at your price or better\n"
                "STOP_MARKET 🚫 — NOT supported on demo API (error -4120)"
            ),
        )

        # Text input for quantity — avoids float step-snap issues
        qty_raw = st.text_input(
            "Quantity",
            value="0.01",
            placeholder="e.g. 0.05, 0.019, 0.001",
            help="Exact quantity. Min for BTCUSDT: 0.001. Min order value: 50 USDT.",
        )

        quantity  = None
        qty_error = None
        try:
            quantity = float(qty_raw.strip())
            if quantity <= 0:
                qty_error = "Quantity must be greater than 0"
            elif quantity < 0.001:
                qty_error = "Minimum quantity for BTCUSDT is 0.001"
        except ValueError:
            qty_error = f"'{qty_raw}' is not a valid number"

        if qty_error:
            st.error(f"❌ {qty_error}")
        elif quantity is not None:
            st.caption(
                f"✅ Quantity: {quantity}  →  sent as: "
                f"`{BinanceFuturesClient._fmt_qty(quantity)}`"
            )

    # ── Right column: price / stop inputs ─────────────────────────────
    with col2:
        price      = None
        stop_price = None
        tif        = "GTC"

        if order_type == "LIMIT":
            price = st.number_input(
                "Limit Price (USDT)",
                min_value=0.01, value=60000.0, step=100.0, format="%.2f",
                help="Your limit price — order fills at this price or better",
            )
            tif = st.selectbox("Time in Force", ["GTC", "IOC", "FOK"])

        elif order_type == "STOP_MARKET":
            stop_price = st.number_input(
                "Stop Trigger Price (USDT)",
                min_value=0.01, value=59000.0, step=100.0, format="%.2f",
            )
            direction = "above" if side == "BUY" else "below"
            st.markdown(
                f'<div class="notice-info">💡 Stop price must be '
                f'<b>{direction}</b> the current market price.</div>',
                unsafe_allow_html=True,
            )

        st.markdown("<br/>", unsafe_allow_html=True)

    # ── STOP_MARKET blocked banner ─────────────────────────────────────
    STOP_NOT_SUPPORTED = (order_type == "STOP_MARKET")
    if STOP_NOT_SUPPORTED:
        st.markdown("""
        <div class="notice-error">
          <b style="color:#f87171;">🚫 STOP_MARKET cannot be placed on the Binance Demo API</b><br/>
          <span style="color:#fca5a5;font-size:0.9rem;">
            <code>demo-fapi.binance.com</code> returns error <code>-4120</code> for all STOP order types —
            this is a <b>Binance limitation on their demo environment</b>, not a bug in this app.<br/>
            <b>Use MARKET or LIMIT</b> to trade on demo.
            Stop orders are available on the live Binance Futures API.
          </span>
        </div>
        """, unsafe_allow_html=True)

    # ── Order preview cards ────────────────────────────────────────────
    st.markdown("#### Order Preview")
    qty_display = str(quantity) if quantity is not None else "⚠️ Invalid"
    for col, (lbl, val) in zip(st.columns(4), [
        ("Symbol", symbol or "—"), ("Side", side),
        ("Type", order_type),      ("Qty", qty_display),
    ]):
        with col:
            st.markdown(
                f'<div class="metric-box">'
                f'<div class="label">{lbl}</div>'
                f'<div class="value">{val}</div></div>',
                unsafe_allow_html=True,
            )

    if price is not None:
        st.markdown(f"**Limit Price:** `{price:,.2f} USDT`")
    if stop_price is not None:
        st.markdown(f"**Stop Trigger:** `{stop_price:,.2f} USDT`")

    st.markdown("<br/>", unsafe_allow_html=True)

    # ── Submit ─────────────────────────────────────────────────────────
    btn_label       = f"🚀 Place {side} {order_type} Order"
    submit_disabled = bool(qty_error or quantity is None or STOP_NOT_SUPPORTED)

    if st.button(btn_label, type="primary", use_container_width=True,
                 disabled=submit_disabled):

        if not api_key or not api_secret:
            st.error("❌ Connect your API keys in the sidebar first.")
            st.stop()
        if not symbol:
            st.error("❌ Symbol cannot be empty.")
            st.stop()
        if quantity is None or quantity <= 0:
            st.error("❌ Quantity must be a positive number.")
            st.stop()
        if order_type == "LIMIT" and (price is None or price <= 0):
            st.error("❌ A valid limit price is required for LIMIT orders.")
            st.stop()

        with st.spinner("Placing order on Binance Demo..."):
            try:
                client   = BinanceFuturesClient(api_key=api_key, api_secret=api_secret)
                response = client.place_order(
                    symbol=symbol,
                    side=side,
                    order_type=order_type,
                    quantity=quantity,
                    price=price if order_type == "LIMIT" else None,
                    stop_price=stop_price,
                    time_in_force=tif,
                )

                # ── Success ────────────────────────────────────────────
                st.markdown(
                    '<div class="result-card-success">'
                    '<h3 style="color:#22c55e;margin:0 0 1rem;">✅ Order Placed Successfully!</h3>'
                    '</div>', unsafe_allow_html=True
                )
                st.success(
                    f"**Order ID:** `{response.get('orderId')}` | "
                    f"**Status:** `{response.get('status')}` | "
                    f"**Symbol:** `{response.get('symbol')}`"
                )

                orig_qty     = response.get("origQty", "N/A")
                exec_qty     = response.get("executedQty", "0")
                order_status = response.get("status", "N/A")

                for col, (lbl, val) in zip(st.columns(4), [
                    ("Order ID",   str(response.get("orderId", "N/A"))),
                    ("Status",     order_status),
                    ("Order Qty",  orig_qty),
                    ("Filled Qty", exec_qty),
                ]):
                    with col:
                        st.markdown(
                            f'<div class="metric-box">'
                            f'<div class="label">{lbl}</div>'
                            f'<div class="value">{val}</div></div>',
                            unsafe_allow_html=True,
                        )

                st.markdown("<br/>", unsafe_allow_html=True)

                if exec_qty in ("0", "0.0", "0.00", "0.000", "0.0000", "0.00000000"):
                    st.info(
                        f"ℹ️ **Filled Qty = 0 is normal** for a newly placed order. "
                        f"Your order of **{orig_qty} {symbol[:3]}** is live on the "
                        f"exchange and awaiting execution."
                    )

                with st.expander("📄 Full API Response"):
                    st.json(response)

            except BinanceClientError as e:
                err_msg = str(e)
                st.markdown(
                    f'<div class="result-card-fail">'
                    f'<h3 style="color:#ef4444;margin:0 0 0.5rem;">❌ Order Failed</h3>'
                    f'<p style="color:#fca5a5;margin:0;">{err_msg}</p></div>',
                    unsafe_allow_html=True,
                )
                if "-2019" in err_msg:
                    st.warning(
                        "💡 **Insufficient demo margin** — your demo balance is too low.\n\n"
                        "**Fix:** Open [testnet.binancefuture.com](https://testnet.binancefuture.com) "
                        "→ click **'Claim demo assets'** to top up your USDT balance, then retry."
                    )
                elif "-1022" in err_msg:
                    st.warning(
                        "💡 **Signature invalid** — your API Secret is probably truncated.\n\n"
                        "Disconnect → re-enter both keys (each must be exactly 64 characters)."
                    )
                elif "-4164" in err_msg:
                    st.warning(
                        "💡 **Order too small** — minimum order notional is **50 USDT**. "
                        "Increase your quantity."
                    )
                elif "-4120" in err_msg:
                    st.error(
                        "🚫 **STOP orders are not supported on the Binance Demo API** (error -4120). "
                        "Use MARKET or LIMIT instead."
                    )
                elif "-2015" in err_msg:
                    st.warning(
                        "💡 **Invalid API key** — check it on Binance and ensure it has "
                        "**Futures trading** permission enabled."
                    )
                elif "-1111" in err_msg or "-1013" in err_msg:
                    st.warning(
                        "💡 **Invalid precision** — the quantity or price does not match "
                        "the exchange's step size rules."
                    )

            except ValueError as e:
                st.error(f"❌ Validation error: {e}")
            except Exception as e:
                st.error(f"❌ Unexpected error: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 — View Logs
# ─────────────────────────────────────────────────────────────────────────────
with tab_logs:
    st.markdown("### 📋 Log Viewer")

    log_dir   = os.path.join(os.path.dirname(__file__), "logs")
    log_files = []
    if os.path.isdir(log_dir):
        log_files = sorted(
            [f for f in os.listdir(log_dir) if f.endswith(".log")],
            reverse=True,
        )

    if not log_files:
        st.info("No log files found yet. Place an order to generate logs.")
    else:
        selected_log = st.selectbox("Select Log File", log_files)
        log_path     = os.path.join(log_dir, selected_log)

        col_r, col_dl = st.columns(2)
        with col_r:
            st.button("🔄 Refresh", use_container_width=True)
        with col_dl:
            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                log_content = f.read()
            st.download_button(
                "⬇️ Download Log", data=log_content,
                file_name=selected_log, mime="text/plain",
                use_container_width=True,
            )

        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        st.markdown(f"**{len(lines)} log entries** in `{selected_log}`")

        level_filter = st.multiselect(
            "Filter by level", ["INFO", "DEBUG", "ERROR", "WARNING"],
            default=["INFO", "ERROR"],
        )
        keyword = st.text_input("Search keyword", placeholder="e.g. orderId, MARKET, BTCUSDT")

        def colorize(line: str) -> str:
            line = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            if "| ERROR"   in line: return f'<span style="color:#f87171">{line}</span>'
            if "| INFO"    in line: return f'<span style="color:#60a5fa">{line}</span>'
            if "| DEBUG"   in line: return f'<span style="color:#94a3b8">{line}</span>'
            if "| WARNING" in line: return f'<span style="color:#fbbf24">{line}</span>'
            return f'<span style="color:#e2e8f0">{line}</span>'

        filtered = [
            line.rstrip() for line in lines
            if (any(f"| {lv}" in line for lv in level_filter) if level_filter else True)
            and ((keyword.lower() in line.lower()) if keyword else True)
        ]

        html = ("<br/>".join(colorize(l) for l in filtered)
                if filtered else "<span style='color:#64748b'>No entries match the filter.</span>")
        st.markdown(f'<div class="log-box">{html}</div>', unsafe_allow_html=True)
        st.caption(f"Showing {len(filtered)} of {len(lines)} total lines")
