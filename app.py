"""
app.py — Streamlit UI for the Binance Futures Demo Trading Bot.
Run with: streamlit run app.py
"""

import os
import sys

# ── Ensure the project root is on the path so bot package is always found ─────
_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from bot.client import BinanceFuturesClient, BinanceClientError  # noqa: E402

import streamlit as st

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Binance Futures Trading Bot",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Inject custom CSS ─────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.stApp { background: linear-gradient(135deg, #0d0d1a 0%, #0a1628 50%, #0d0d1a 100%); }

.hero-banner {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    border: 1px solid rgba(99,102,241,0.3);
    border-radius: 16px;
    padding: 2rem 2.5rem;
    margin-bottom: 2rem;
    box-shadow: 0 8px 32px rgba(99,102,241,0.15);
}
.hero-banner h1 { color: #e0e7ff; font-size: 2rem; font-weight: 700; margin: 0; }
.hero-banner p  { color: #94a3b8; font-size: 1rem; margin: 0.5rem 0 0; }

.card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1rem;
}

.status-ok  { color: #22c55e; font-weight: 600; }
.status-err { color: #ef4444; font-weight: 600; }

.result-card-success {
    background: linear-gradient(135deg, rgba(34,197,94,0.1), rgba(16,185,129,0.05));
    border: 1px solid rgba(34,197,94,0.3);
    border-radius: 12px;
    padding: 1.5rem;
}
.result-card-fail {
    background: linear-gradient(135deg, rgba(239,68,68,0.1), rgba(220,38,38,0.05));
    border: 1px solid rgba(239,68,68,0.3);
    border-radius: 12px;
    padding: 1.5rem;
}

.metric-box {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 10px;
    padding: 1rem 1.2rem;
    text-align: center;
}
.metric-box .label { color: #94a3b8; font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.08em; }
.metric-box .value { color: #e0e7ff; font-size: 1.3rem; font-weight: 700; margin-top: 0.3rem; }

.log-box {
    background: #0d1117;
    border: 1px solid rgba(99,102,241,0.2);
    border-radius: 8px;
    padding: 1rem 1.2rem;
    font-family: 'Courier New', monospace;
    font-size: 0.78rem;
    color: #94a3b8;
    max-height: 400px;
    overflow-y: auto;
    white-space: pre-wrap;
}
.log-line-info    { color: #60a5fa; }
.log-line-debug   { color: #94a3b8; }
.log-line-error   { color: #f87171; }
.log-line-success { color: #34d399; }

div[data-testid="stSidebar"] { background: rgba(15,15,35,0.95) !important; border-right: 1px solid rgba(99,102,241,0.2); }
</style>
""", unsafe_allow_html=True)

# ── Sidebar — Credentials ────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Configuration")
    st.markdown("---")

    api_key = st.text_input(
        "Binance API Key",
        value=os.environ.get("BINANCE_API_KEY", ""),
        type="password",
        placeholder="Paste your API key here",
        help="From Binance Demo Futures API Management",
    ).strip()  # strip whitespace to prevent -1022 signature errors
    api_secret = st.text_input(
        "Binance API Secret",
        value=os.environ.get("BINANCE_API_SECRET", ""),
        type="password",
        placeholder="Paste your secret key here",
    ).strip()  # strip whitespace to prevent -1022 signature errors

    if api_key and api_secret:
        st.caption("✅ Keys loaded — whitespace auto-trimmed.")

    st.markdown("---")
    st.markdown("**Base Endpoint**")
    st.code("https://demo-fapi.binance.com", language=None)

    st.markdown("---")
    st.markdown("### 📋 Quick Links")
    st.markdown("- [Binance Demo Trading](https://www.binance.com/en/futures/BTCUSDT)")
    st.markdown("- [API Docs](https://developers.binance.com/docs/derivatives/)")

# ── Hero Banner ───────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-banner">
  <h1>⚡ Binance Futures Demo Trading Bot</h1>
  <p>Place MARKET · LIMIT · STOP-LIMIT orders on the Binance Futures Demo environment</p>
</div>
""", unsafe_allow_html=True)

# ── Connectivity check ────────────────────────────────────────────────────────
col_ping, col_cred = st.columns([1, 1])

with col_ping:
    if st.button("🔌 Check Connectivity", use_container_width=True):
        try:
            import requests as req
            r = req.get("https://demo-fapi.binance.com/fapi/v1/ping", timeout=5)
            if r.ok:
                st.success("✅ Demo API is reachable")
            else:
                st.error(f"❌ HTTP {r.status_code}")
        except Exception as e:
            st.error(f"❌ {e}")

with col_cred:
    cred_status = "✅ Credentials set" if (api_key and api_secret) else "⚠️ No credentials"
    cred_color  = "success" if (api_key and api_secret) else "warning"
    if cred_color == "success":
        st.success(cred_status)
    else:
        st.warning(cred_status)

st.markdown("---")

# ── Main tabs ─────────────────────────────────────────────────────────────────
tab_place, tab_logs = st.tabs(["📤 Place Order", "📋 View Logs"])

# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 — Place Order
# ─────────────────────────────────────────────────────────────────────────────
with tab_place:
    st.markdown("### New Order")

    col1, col2 = st.columns(2)

    with col1:
        symbol = st.text_input("Symbol", value="BTCUSDT", placeholder="e.g. BTCUSDT, ETHUSDT").strip().upper()
        side = st.selectbox("Side", ["BUY", "SELL"])
        order_type = st.selectbox("Order Type", ["MARKET", "LIMIT", "STOP_LIMIT"])
        quantity = st.number_input("Quantity", min_value=0.0001, value=0.01, step=0.001, format="%.4f")

    with col2:
        price = None
        stop_price = None

        if order_type in ("LIMIT", "STOP_LIMIT"):
            price = st.number_input("Limit Price (USDT)", min_value=0.01, value=60000.0, step=100.0, format="%.2f")

        if order_type == "STOP_LIMIT":
            stop_price = st.number_input("Stop Trigger Price (USDT)", min_value=0.01, value=59000.0, step=100.0, format="%.2f")

        tif = "GTC"
        if order_type in ("LIMIT", "STOP_LIMIT"):
            tif = st.selectbox("Time in Force", ["GTC", "IOC", "FOK"])

        st.markdown("<br/>", unsafe_allow_html=True)

    # ── Order preview ──────────────────────────────────────────────────────
    st.markdown("#### Order Preview")
    prev_cols = st.columns(4)
    prev_data = [
        ("Symbol", symbol),
        ("Side", side),
        ("Type", order_type),
        ("Qty", f"{quantity:.4f}"),
    ]
    for col, (lbl, val) in zip(prev_cols, prev_data):
        with col:
            st.markdown(f"""
            <div class="metric-box">
              <div class="label">{lbl}</div>
              <div class="value">{val}</div>
            </div>""", unsafe_allow_html=True)

    if price:
        st.markdown(f"**Limit Price:** `{price:,.2f} USDT`")
    if stop_price:
        st.markdown(f"**Stop Trigger:** `{stop_price:,.2f} USDT`")

    st.markdown("<br/>", unsafe_allow_html=True)

    # ── Submit button ──────────────────────────────────────────────────────
    btn_label = f"🚀 Place {side} {order_type} Order"
    side_color = "#22c55e" if side == "BUY" else "#ef4444"

    if st.button(btn_label, type="primary", use_container_width=True):
        # Validate credentials
        if not api_key or not api_secret:
            st.error("❌ Please enter your API Key and Secret in the sidebar.")
            st.stop()

        # Validate inputs
        if not symbol:
            st.error("❌ Symbol cannot be empty.")
            st.stop()

        if quantity <= 0:
            st.error("❌ Quantity must be greater than 0.")
            st.stop()

        if order_type in ("LIMIT", "STOP_LIMIT") and (price is None or price <= 0):
            st.error("❌ A valid price is required for LIMIT and STOP_LIMIT orders.")
            st.stop()

        if order_type == "STOP_LIMIT" and (stop_price is None or stop_price <= 0):
            st.error("❌ A valid stop trigger price is required for STOP_LIMIT orders.")
            st.stop()

        # Map order type for API
        api_type_map = {"MARKET": "MARKET", "LIMIT": "LIMIT", "STOP_LIMIT": "STOP"}
        api_type = api_type_map[order_type]

        with st.spinner("Placing order on Binance Demo..."):
            try:
                # Keys are already stripped at input time
                client = BinanceFuturesClient(api_key=api_key, api_secret=api_secret)
                response = client.place_order(
                    symbol=symbol,
                    side=side,
                    order_type=api_type,
                    quantity=quantity,
                    price=price if order_type != "MARKET" else None,
                    stop_price=stop_price,
                    time_in_force=tif,
                )

                # ── Success display ────────────────────────────────────────
                st.markdown(f"""
                <div class="result-card-success">
                  <h3 style="color:#22c55e; margin:0 0 1rem;">✅ Order Placed Successfully!</h3>
                </div>
                """, unsafe_allow_html=True)

                st.success(f"**Order ID:** `{response.get('orderId')}` | **Status:** `{response.get('status')}`")

                res_cols = st.columns(4)
                res_fields = [
                    ("Order ID",     str(response.get("orderId", "N/A"))),
                    ("Status",       response.get("status", "N/A")),
                    ("Executed Qty", response.get("executedQty", "0")),
                    ("Avg Price",    response.get("avgPrice", "0") or "MARKET"),
                ]
                for col, (lbl, val) in zip(res_cols, res_fields):
                    with col:
                        st.markdown(f"""
                        <div class="metric-box">
                          <div class="label">{lbl}</div>
                          <div class="value">{val}</div>
                        </div>""", unsafe_allow_html=True)

                st.markdown("<br/>", unsafe_allow_html=True)
                with st.expander("📄 Full API Response"):
                    st.json(response)

            except BinanceClientError as e:
                st.markdown(f"""
                <div class="result-card-fail">
                  <h3 style="color:#ef4444; margin:0 0 0.5rem;">❌ Order Failed</h3>
                  <p style="color:#fca5a5; margin:0;">{e}</p>
                </div>""", unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Unexpected error: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 — View Logs
# ─────────────────────────────────────────────────────────────────────────────
with tab_logs:
    st.markdown("### 📋 Log Viewer")

    log_dir = os.path.join(os.path.dirname(__file__), "logs")
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
        log_path = os.path.join(log_dir, selected_log)

        col_refresh, col_dl = st.columns([1, 1])
        with col_refresh:
            refresh = st.button("🔄 Refresh", use_container_width=True)
        with col_dl:
            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                log_content = f.read()
            st.download_button(
                "⬇️ Download Log",
                data=log_content,
                file_name=selected_log,
                mime="text/plain",
                use_container_width=True,
            )

        # Read and display with colored lines
        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        st.markdown(f"**{len(lines)} log entries** in `{selected_log}`")

        # Filter controls
        level_filter = st.multiselect(
            "Filter by level",
            ["INFO", "DEBUG", "ERROR", "WARNING"],
            default=["INFO", "ERROR"],
        )

        keyword = st.text_input("Search keyword", placeholder="e.g. orderId, MARKET, BTCUSDT")

        filtered = []
        for line in lines:
            level_match = any(f"| {lv}" in line or f"|{lv}" in line for lv in level_filter) if level_filter else True
            kw_match = (keyword.lower() in line.lower()) if keyword else True
            if level_match and kw_match:
                filtered.append(line.rstrip())

        # Color-code lines
        def colorize(line: str) -> str:
            if "| ERROR" in line:
                return f'<span style="color:#f87171">{line}</span>'
            elif "| INFO" in line:
                return f'<span style="color:#60a5fa">{line}</span>'
            elif "| DEBUG" in line:
                return f'<span style="color:#94a3b8">{line}</span>'
            elif "| WARNING" in line:
                return f'<span style="color:#fbbf24">{line}</span>'
            return f'<span style="color:#e2e8f0">{line}</span>'

        html_lines = "<br/>".join(colorize(l) for l in filtered) if filtered else "<span style='color:#64748b'>No entries match the filter.</span>"
        st.markdown(f'<div class="log-box">{html_lines}</div>', unsafe_allow_html=True)
        st.caption(f"Showing {len(filtered)} of {len(lines)} total lines")
