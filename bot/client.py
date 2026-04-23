import hashlib
import hmac
import time
from typing import Any, Dict, Optional
from urllib.parse import urlencode

import requests

from .logging_config import get_logger

logger = get_logger(__name__)

BASE_URL = "https://demo-fapi.binance.com"


class BinanceClientError(Exception):
    """Raised when the Binance API returns an error."""


class BinanceFuturesClient:
    """
    Thin wrapper around the Binance Futures Demo REST API.
    Handles request signing, sending, and basic error surfacing.
    """

    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key.strip()
        self.api_secret = api_secret.strip()
        self.session = requests.Session()
        self.session.headers.update({"X-MBX-APIKEY": self.api_key})
        logger.debug(
            "BinanceFuturesClient created | key_len=%d secret_len=%d key_prefix=%s",
            len(self.api_key), len(self.api_secret),
            self.api_key[:6] + "..." if len(self.api_key) > 6 else "(short!)",
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _fmt_qty(v: float) -> str:
        """Format quantity to avoid float precision issues.
        Uses up to 8 decimal places, strips trailing zeros."""
        # Round to 8 decimal places first to avoid floating point drift
        rounded = round(v, 8)
        # Format with enough precision, strip trailing zeros
        formatted = f"{rounded:.8f}".rstrip("0").rstrip(".")
        return formatted

    @staticmethod
    def _fmt_price(v: float) -> str:
        """Format price values (2 decimal places for USDT pairs)."""
        return f"{round(v, 2):.2f}"

    def _build_signed_query(self, params: Dict[str, Any]) -> str:
        """Build a fully-signed query string that is sent verbatim to Binance.

        Key insight: we must sign *exactly* the string that will be transmitted.
        If we pass a dict to requests it re-encodes the parameters internally,
        which can change ordering or representation and break the HMAC check.
        Instead we build the query string here, sign it, and return the
        complete signed string so the caller can send it as-is.
        """
        # Convert every value to str so urlencode is deterministic
        str_params = [(k, str(v)) for k, v in params.items()]
        query_string = urlencode(str_params)

        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        return query_string + "&signature=" + signature

    def _get(self, path: str, params: Optional[Dict] = None, signed: bool = False) -> Any:
        params = params or {}
        url = BASE_URL + path

        if signed:
            params["timestamp"] = int(time.time() * 1000)
            params["recvWindow"] = 10000
            signed_qs = self._build_signed_query(params)
            # Append pre-built signed query string directly — do NOT pass params dict
            full_url = f"{url}?{signed_qs}"
            logger.debug("GET %s (signed)", url)
            try:
                resp = self.session.get(full_url, timeout=10)
            except requests.exceptions.RequestException as exc:
                logger.error("Network error on GET %s: %s", url, exc)
                raise BinanceClientError(f"Network error: {exc}") from exc
        else:
            logger.debug("GET %s params=%s", url, params)
            try:
                resp = self.session.get(url, params=params, timeout=10)
            except requests.exceptions.RequestException as exc:
                logger.error("Network error on GET %s: %s", url, exc)
                raise BinanceClientError(f"Network error: {exc}") from exc

        return self._handle_response(resp)

    def _get_server_timestamp(self) -> int:
        """Fetch Binance server time to avoid local clock skew issues."""
        try:
            resp = self.session.get(BASE_URL + "/fapi/v1/time", timeout=5)
            data = resp.json()
            return int(data["serverTime"])
        except Exception:
            # Fallback to local time if server time fetch fails
            return int(time.time() * 1000)

    def _post(self, path: str, params: Dict[str, Any]) -> Any:
        # Always use Binance server time — immune to local clock drift
        params["timestamp"] = self._get_server_timestamp()
        params["recvWindow"] = 10000

        # Log params BEFORE signing (exclude sensitive data)
        logger.debug(
            "POST %s params=%s",
            BASE_URL + path,
            {k: v for k, v in params.items() if k not in ("signature",)},
        )

        # Build the complete signed query string and send it verbatim.
        # NEVER pass params as a dict to requests — it will re-encode them
        # and the signature will no longer match what Binance verifies.
        signed_qs = self._build_signed_query(params)
        url = BASE_URL + path + "?" + signed_qs

        try:
            resp = self.session.post(url, timeout=10)
        except requests.exceptions.RequestException as exc:
            logger.error("Network error on POST %s: %s", BASE_URL + path, exc)
            raise BinanceClientError(f"Network error: {exc}") from exc

        return self._handle_response(resp)

    @staticmethod
    def _handle_response(resp: requests.Response) -> Any:
        try:
            data = resp.json()
        except ValueError:
            raise BinanceClientError(
                f"Non-JSON response (HTTP {resp.status_code}): {resp.text[:200]}"
            )

        if resp.ok:
            return data

        code = data.get("code", resp.status_code)
        msg = data.get("msg", "Unknown error")
        logger.error("Binance API error %s: %s", code, msg)
        raise BinanceClientError(f"Binance API error {code}: {msg}")

    # ------------------------------------------------------------------
    # Public API methods
    # ------------------------------------------------------------------

    def ping(self) -> bool:
        """Return True if the demo API is reachable."""
        try:
            self._get("/fapi/v1/ping")
            return True
        except BinanceClientError:
            return False

    def get_account_info(self) -> Dict:
        """Fetch account balance — validates that credentials are correct."""
        return self._get("/fapi/v2/account", signed=True)

    def get_exchange_info(self) -> Dict:
        """Fetch exchange information (symbols, filters, etc.)."""
        return self._get("/fapi/v1/exchangeInfo")

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None,
        stop_price: Optional[float] = None,
        time_in_force: str = "GTC",
    ) -> Dict:
        """
        Place a MARKET, LIMIT, or STOP_MARKET order on Binance Futures Demo.

        Args:
            symbol:        Trading pair (e.g. BTCUSDT).
            side:          BUY or SELL.
            order_type:    MARKET, LIMIT, or STOP_MARKET.
            quantity:      Order quantity (positive float).
            price:         Required for LIMIT orders (limit price).
            stop_price:    Required for STOP_MARKET orders (trigger price).
            time_in_force: Time-in-force policy (default GTC).

        Returns:
            dict: Binance API order response.
        """
        if quantity <= 0:
            raise ValueError(f"Quantity must be positive, got {quantity}")

        qty_str = self._fmt_qty(quantity)

        params: Dict[str, Any] = {
            "symbol": symbol.upper(),
            "side": side.upper(),
            "type": order_type,
            "quantity": qty_str,
        }

        if order_type == "LIMIT":
            if price is None or price <= 0:
                raise ValueError("Price must be provided and positive for LIMIT orders.")
            params["price"] = self._fmt_price(price)
            params["timeInForce"] = time_in_force

        elif order_type == "STOP_MARKET":
            # Stop-Market: triggers a MARKET order at stopPrice
            if stop_price is None or stop_price <= 0:
                raise ValueError("Stop price must be provided for STOP_MARKET orders.")
            params["stopPrice"] = self._fmt_price(stop_price)

        elif order_type == "STOP":
            # Stop-Limit: triggers a LIMIT order at stopPrice, fills at price
            if price is None or price <= 0:
                raise ValueError("Price must be provided for STOP (Stop-Limit) orders.")
            if stop_price is None or stop_price <= 0:
                raise ValueError("Stop price must be provided for STOP (Stop-Limit) orders.")
            params["price"] = self._fmt_price(price)
            params["stopPrice"] = self._fmt_price(stop_price)
            params["timeInForce"] = time_in_force

        logger.info(
            "Placing %s %s order | symbol=%s qty=%s price=%s stop=%s",
            side,
            order_type,
            symbol,
            qty_str,
            price or "MARKET",
            stop_price or "N/A",
        )

        response = self._post("/fapi/v1/order", params)
        logger.debug("Order response: %s", response)
        return response
