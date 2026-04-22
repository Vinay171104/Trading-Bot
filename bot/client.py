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
    Thin wrapper around the Binance Futures Testnet REST API.
    Handles request signing, sending, and basic error surfacing.
    """

    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.session = requests.Session()
        self.session.headers.update({"X-MBX-APIKEY": self.api_key})

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _sign(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Append HMAC-SHA256 signature to params dict."""
        query_string = urlencode(params)
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        params["signature"] = signature
        return params

    def _get(self, path: str, params: Optional[Dict] = None, signed: bool = False) -> Any:
        params = params or {}
        if signed:
            params["timestamp"] = int(time.time() * 1000)
            params["recvWindow"] = 5000
            params = self._sign(params)

        url = BASE_URL + path
        logger.debug("GET %s params=%s", url, {k: v for k, v in params.items() if k != "signature"})

        try:
            resp = self.session.get(url, params=params, timeout=10)
        except requests.exceptions.RequestException as exc:
            logger.error("Network error on GET %s: %s", url, exc)
            raise BinanceClientError(f"Network error: {exc}") from exc

        return self._handle_response(resp)

    def _post(self, path: str, params: Dict[str, Any]) -> Any:
        params["timestamp"] = int(time.time() * 1000)
        params["recvWindow"] = 5000
        params = self._sign(params)

        url = BASE_URL + path
        logger.debug(
            "POST %s params=%s",
            url,
            {k: v for k, v in params.items() if k != "signature"},
        )

        try:
            resp = self.session.post(url, params=params, timeout=10)
        except requests.exceptions.RequestException as exc:
            logger.error("Network error on POST %s: %s", url, exc)
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
        """Return True if the testnet is reachable."""
        try:
            self._get("/fapi/v1/ping")
            return True
        except BinanceClientError:
            return False

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
        Place a MARKET, LIMIT, or STOP order on Binance Futures Testnet.

        Args:
            symbol:        Trading pair (e.g. BTCUSDT).
            side:          BUY or SELL.
            order_type:    MARKET, LIMIT, or STOP.
            quantity:      Order quantity.
            price:         Required for LIMIT and STOP orders.
            stop_price:    Required for STOP orders (trigger price).
            time_in_force: Time-in-force policy (default GTC).

        Returns:
            dict: Binance API order response.
        """
        params: Dict[str, Any] = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": quantity,
        }

        if order_type == "LIMIT":
            if price is None:
                raise ValueError("Price must be provided for LIMIT orders.")
            params["price"] = price
            params["timeInForce"] = time_in_force

        if order_type == "STOP":
            if price is None:
                raise ValueError("Price must be provided for STOP (Stop-Limit) orders.")
            if stop_price is None:
                raise ValueError("Stop price must be provided for STOP (Stop-Limit) orders.")
            params["price"] = price
            params["stopPrice"] = stop_price
            params["timeInForce"] = time_in_force

        logger.info(
            "Placing %s %s order | symbol=%s qty=%s price=%s stop=%s",
            side,
            order_type,
            symbol,
            quantity,
            price or "MARKET",
            stop_price or "N/A",
        )

        response = self._post("/fapi/v1/order", params)
        logger.debug("Order response: %s", response)
        return response
