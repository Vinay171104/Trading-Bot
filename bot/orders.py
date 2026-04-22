"""
orders.py — Order placement orchestration with rich, formatted output.
"""

from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .client import BinanceFuturesClient, BinanceClientError
from .logging_config import get_logger

logger = get_logger(__name__)
console = Console()

# Map Binance API order types back to friendly names for display
DISPLAY_TYPE = {
    "MARKET": "MARKET",
    "LIMIT": "LIMIT",
    "STOP": "STOP-LIMIT",
}


def _build_request_table(
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: Optional[float],
    stop_price: Optional[float],
) -> Table:
    """Build a rich Table summarizing the order request."""
    table = Table(
        title="Order Request Summary",
        title_style="bold cyan",
        show_header=True,
        header_style="bold magenta",
        border_style="bright_blue",
        padding=(0, 2),
    )
    table.add_column("Parameter", style="bold white", min_width=14)
    table.add_column("Value", style="green")

    display_type = DISPLAY_TYPE.get(order_type, order_type)
    side_color = "green" if side == "BUY" else "red"

    table.add_row("Symbol", symbol)
    table.add_row("Side", Text(side, style=f"bold {side_color}"))
    table.add_row("Order Type", Text(display_type, style="bold yellow"))
    table.add_row("Quantity", str(quantity))

    if order_type in ("LIMIT", "STOP"):
        table.add_row("Price", str(price))

    if order_type == "STOP" and stop_price is not None:
        table.add_row("Stop Price", str(stop_price))

    return table


def _build_response_table(response: dict) -> Table:
    """Build a rich Table showing the order response details."""
    table = Table(
        title="Order Response Details",
        title_style="bold cyan",
        show_header=True,
        header_style="bold magenta",
        border_style="bright_green",
        padding=(0, 2),
    )
    table.add_column("Field", style="bold white", min_width=16)
    table.add_column("Value", style="green")

    status = response.get("status", "N/A")
    status_color = "bold green" if status == "FILLED" else "bold yellow"
    side = response.get("side", "N/A")
    side_color = "green" if side == "BUY" else "red"

    table.add_row("Order ID", str(response.get("orderId", "N/A")))
    table.add_row("Client Order ID", str(response.get("clientOrderId", "N/A")))
    table.add_row("Symbol", str(response.get("symbol", "N/A")))
    table.add_row("Status", Text(status, style=status_color))
    table.add_row("Side", Text(side, style=f"bold {side_color}"))

    resp_type = response.get("type", "N/A")
    table.add_row("Type", DISPLAY_TYPE.get(resp_type, resp_type))
    table.add_row("Orig Qty", str(response.get("origQty", "N/A")))
    table.add_row("Executed Qty", str(response.get("executedQty", "N/A")))

    avg_price = response.get("avgPrice") or response.get("price")
    if avg_price and float(avg_price) > 0:
        table.add_row("Avg Price", str(avg_price))

    stop_price = response.get("stopPrice")
    if stop_price and float(stop_price) > 0:
        table.add_row("Stop Price", str(stop_price))

    return table


def place_order(
    client: BinanceFuturesClient,
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: Optional[float] = None,
    stop_price: Optional[float] = None,
) -> None:
    """
    Orchestrates order placement and prints a human-readable summary.

    Args:
        client:     Authenticated BinanceFuturesClient instance.
        symbol:     E.g. 'BTCUSDT'
        side:       'BUY' or 'SELL'
        order_type: 'MARKET', 'LIMIT', or 'STOP'
        quantity:   Order quantity
        price:      Required for LIMIT and STOP orders
        stop_price: Required for STOP (Stop-Limit) orders
    """

    # ── Request summary ───────────────────────────────────────────────
    console.print()
    console.print(_build_request_table(symbol, side, order_type, quantity, price, stop_price))
    console.print()

    # ── Send order ────────────────────────────────────────────────────
    try:
        response = client.place_order(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            stop_price=stop_price,
        )
    except BinanceClientError as exc:
        logger.error("Order placement failed: %s", exc)
        console.print(
            Panel(
                f"[bold red]FAILED:[/bold red] {exc}",
                title="❌ Order Failed",
                title_align="left",
                border_style="red",
                padding=(1, 2),
            )
        )
        return
    except Exception as exc:
        logger.exception("Unexpected error during order placement: %s", exc)
        console.print(
            Panel(
                f"[bold red]UNEXPECTED ERROR:[/bold red] {exc}",
                title="❌ Error",
                title_align="left",
                border_style="red",
                padding=(1, 2),
            )
        )
        return

    # ── Response details ──────────────────────────────────────────────
    console.print(_build_response_table(response))
    console.print()
    console.print(
        Panel(
            "[bold green]Order placed successfully![/bold green]",
            title="✅ Success",
            title_align="left",
            border_style="green",
            padding=(0, 2),
        )
    )
    console.print()

    logger.info(
        "Order SUCCESS | orderId=%s status=%s executedQty=%s",
        response.get("orderId"),
        response.get("status"),
        response.get("executedQty"),
    )
