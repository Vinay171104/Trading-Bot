"""
cli.py — Command-line entry point for the Binance Futures Trading Bot.

Usage examples:
  # Market buy
  python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01

  # Limit sell
  python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.01 --price 70000

  # Stop-Limit buy
  python cli.py --symbol BTCUSDT --side BUY --type STOP_LIMIT --quantity 0.01 --price 60000 --stop-price 59500

Environment variables (required):
  BINANCE_API_KEY      — Your Binance Futures Testnet API key
  BINANCE_API_SECRET   — Your Binance Futures Testnet API secret
"""

import argparse
import os
import sys

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from bot.client import BinanceFuturesClient
from bot.logging_config import get_logger
from bot.orders import place_order
from bot.validators import (
    ValidationError,
    validate_order_type,
    validate_price,
    validate_quantity,
    validate_side,
    validate_stop_price,
    validate_symbol,
)

logger = get_logger("cli")
console = Console(highlight=False)


def show_banner() -> None:
    """Display a colorized startup banner."""
    banner_text = (
        "\n"
        "  +----------------------------------------------------------+\n"
        "  |   Binance Futures Testnet -- Trading Bot                 |\n"
        "  |                                                          |\n"
        "  |   MARKET  |  LIMIT  |  STOP-LIMIT                       |\n"
        "  |   Powered by direct REST API calls                       |\n"
        "  +----------------------------------------------------------+\n"
    )
    console.print(banner_text, style="bold cyan")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="trading_bot",
        description="Simplified Binance Futures Testnet Trading Bot",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument(
        "--symbol",
        required=True,
        help="Trading pair symbol (e.g. BTCUSDT)",
    )
    parser.add_argument(
        "--side",
        required=True,
        choices=["BUY", "SELL"],
        help="Order side: BUY or SELL",
    )
    parser.add_argument(
        "--type",
        dest="order_type",
        required=True,
        choices=["MARKET", "LIMIT", "STOP_LIMIT"],
        help="Order type: MARKET, LIMIT, or STOP_LIMIT",
    )
    parser.add_argument(
        "--quantity",
        required=True,
        help="Order quantity (e.g. 0.01)",
    )
    parser.add_argument(
        "--price",
        default=None,
        help="Limit price — required when --type is LIMIT or STOP_LIMIT",
    )
    parser.add_argument(
        "--stop-price",
        default=None,
        help="Stop trigger price — required when --type is STOP_LIMIT",
    )

    return parser.parse_args()


def load_credentials() -> tuple[str, str]:
    """Load API credentials from environment variables."""
    api_key = os.environ.get("BINANCE_API_KEY", "").strip()
    api_secret = os.environ.get("BINANCE_API_SECRET", "").strip()

    if not api_key or not api_secret:
        logger.error("BINANCE_API_KEY and BINANCE_API_SECRET must be set.")
        console.print(
            Panel(
                "[bold red]Please set the environment variables:[/bold red]\n"
                "  • BINANCE_API_KEY\n"
                "  • BINANCE_API_SECRET",
                title="❌ Missing Credentials",
                title_align="left",
                border_style="red",
                padding=(1, 2),
            )
        )
        sys.exit(1)

    return api_key, api_secret


def main() -> None:
    show_banner()
    args = parse_args()

    # ── Validate inputs ───────────────────────────────────────────────
    try:
        symbol = validate_symbol(args.symbol)
        side = validate_side(args.side)
        order_type = validate_order_type(args.order_type)
        quantity = validate_quantity(args.quantity)
        price = validate_price(args.price, order_type)
        stop_price = validate_stop_price(args.stop_price, order_type)
    except ValidationError as exc:
        logger.error("Input validation error: %s", exc)
        console.print(
            Panel(
                f"[bold red]{exc}[/bold red]",
                title="⚠️  Validation Error",
                title_align="left",
                border_style="yellow",
                padding=(1, 2),
            )
        )
        sys.exit(1)

    # ── Build client ──────────────────────────────────────────────────
    api_key, api_secret = load_credentials()
    client = BinanceFuturesClient(api_key=api_key, api_secret=api_secret)

    logger.info(
        "Bot started | symbol=%s side=%s type=%s qty=%s price=%s stop=%s",
        symbol, side, order_type, quantity, price, stop_price,
    )

    # ── Connectivity check ────────────────────────────────────────────
    console.print("[dim]Checking testnet connectivity...[/dim]", end=" ")
    if not client.ping():
        console.print("[bold red]FAILED[/bold red]")
        logger.error("Cannot reach Binance Testnet. Check your internet connection.")
        console.print(
            Panel(
                "[bold red]Cannot reach Binance Futures Testnet.[/bold red]\n"
                "Check your internet connection and try again.",
                title="❌ Connection Error",
                title_align="left",
                border_style="red",
                padding=(1, 2),
            )
        )
        sys.exit(1)
    console.print("[bold green]OK[/bold green]")

    # ── Place order ───────────────────────────────────────────────────
    place_order(
        client=client,
        symbol=symbol,
        side=side,
        order_type=order_type,
        quantity=quantity,
        price=price,
        stop_price=stop_price,
    )


if __name__ == "__main__":
    main()
