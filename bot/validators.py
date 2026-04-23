from typing import Optional


VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT", "STOP_LIMIT", "STOP_MARKET"}

# Map user-facing type names to Binance API type values
ORDER_TYPE_MAP = {
    "MARKET":      "MARKET",
    "LIMIT":       "LIMIT",
    "STOP_LIMIT":  "STOP",         # Stop-Limit (not supported on demo API)
    "STOP_MARKET": "STOP_MARKET",  # Stop-Market (supported on demo API)
}


class ValidationError(ValueError):
    """Raised when user input fails validation."""


def validate_symbol(symbol: str) -> str:
    """Validate and normalize the trading pair symbol."""
    symbol = symbol.strip().upper()
    if not symbol.isalnum():
        raise ValidationError(
            f"Invalid symbol '{symbol}'. Must be alphanumeric (e.g. BTCUSDT)."
        )
    return symbol


def validate_side(side: str) -> str:
    """Validate order side (BUY or SELL)."""
    side = side.strip().upper()
    if side not in VALID_SIDES:
        raise ValidationError(
            f"Invalid side '{side}'. Must be one of: {', '.join(sorted(VALID_SIDES))}."
        )
    return side


def validate_order_type(order_type: str) -> str:
    """Validate and map order type to Binance API value."""
    order_type = order_type.strip().upper()
    if order_type not in VALID_ORDER_TYPES:
        raise ValidationError(
            f"Invalid order type '{order_type}'. "
            f"Must be one of: {', '.join(sorted(VALID_ORDER_TYPES))}."
        )
    return ORDER_TYPE_MAP[order_type]


def validate_quantity(quantity: str) -> float:
    """Validate that quantity is a positive number with sufficient precision."""
    try:
        qty = float(str(quantity).strip())
    except (TypeError, ValueError):
        raise ValidationError(f"Invalid quantity '{quantity}'. Must be a positive number.")
    if qty <= 0:
        raise ValidationError(f"Quantity must be greater than 0, got {qty}.")
    return qty


def validate_price(price: Optional[str], order_type: str) -> Optional[float]:
    """Price is required for LIMIT and STOP (stop-limit) orders, ignored for others."""
    if order_type in ("LIMIT", "STOP"):
        if price is None:
            label = "LIMIT" if order_type == "LIMIT" else "STOP_LIMIT"
            raise ValidationError(f"Price is required for {label} orders.")
        try:
            p = float(price)
        except (TypeError, ValueError):
            raise ValidationError(f"Invalid price '{price}'. Must be a positive number.")
        if p <= 0:
            raise ValidationError(f"Price must be greater than 0, got {p}.")
        return p
    return None  # MARKET and STOP_MARKET orders don't use a limit price


def validate_stop_price(stop_price: Optional[str], order_type: str) -> Optional[float]:
    """Stop price is required for STOP and STOP_MARKET orders, ignored for others."""
    if order_type in ("STOP", "STOP_MARKET"):
        label = "STOP_LIMIT" if order_type == "STOP" else "STOP_MARKET"
        if stop_price is None:
            raise ValidationError(f"Stop price (--stop-price) is required for {label} orders.")
        try:
            sp = float(stop_price)
        except (TypeError, ValueError):
            raise ValidationError(f"Invalid stop price '{stop_price}'. Must be a positive number.")
        if sp <= 0:
            raise ValidationError(f"Stop price must be greater than 0, got {sp}.")
        return sp
    return None  # MARKET and LIMIT orders don't need a stop price
