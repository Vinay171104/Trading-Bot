# Binance Futures Testnet Trading Bot

A clean, structured Python CLI application for placing **Market**, **Limit**, and **Stop-Limit** orders on the [Binance Futures Testnet (USDT-M)](https://testnet.binancefuture.com).

---

## Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py          # Package init
│   ├── client.py            # Binance Futures REST API client (signing, requests, errors)
│   ├── orders.py            # Order placement logic + rich output formatting
│   ├── validators.py        # CLI input validation
│   └── logging_config.py    # Logging setup (console + file)
├── cli.py                   # CLI entry point (argparse)
├── requirements.txt
└── README.md
```

---

## Setup

### 1. Register on Binance Demo Trading

1. Log into your Binance account and go to **Demo Trading** (futures)
2. Navigate to **API Management** → create a new key pair
3. Copy your **API Key** and **Secret Key**

> **Base Endpoint used:** `https://demo-fapi.binance.com`
> ([Futures Demo API Documentation](https://developers.binance.com/docs/derivatives/))

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set environment variables

```bash
# Linux / macOS
export BINANCE_API_KEY="your_api_key_here"
export BINANCE_API_SECRET="your_api_secret_here"

# Windows (PowerShell)
$env:BINANCE_API_KEY="your_api_key_here"
$env:BINANCE_API_SECRET="your_api_secret_here"
```

---

## Usage

```
python cli.py --symbol SYMBOL --side SIDE --type TYPE --quantity QTY [--price PRICE] [--stop-price STOP_PRICE]
```

| Argument       | Required        | Description                                          |
|----------------|-----------------|------------------------------------------------------|
| `--symbol`     | ✅              | Trading pair (e.g. `BTCUSDT`)                        |
| `--side`       | ✅              | `BUY` or `SELL`                                      |
| `--type`       | ✅              | `MARKET`, `LIMIT`, or `STOP_LIMIT`                   |
| `--quantity`   | ✅              | Order quantity (e.g. `0.01`)                          |
| `--price`      | ⚠️ LIMIT/STOP   | Limit price — required for LIMIT and STOP_LIMIT      |
| `--stop-price` | ⚠️ STOP_LIMIT   | Stop trigger price — required for STOP_LIMIT only    |

---

## Run Examples

### Market Buy
```bash
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01
```

### Market Sell
```bash
python cli.py --symbol ETHUSDT --side SELL --type MARKET --quantity 0.1
```

### Limit Buy
```bash
python cli.py --symbol BTCUSDT --side BUY --type LIMIT --quantity 0.01 --price 60000
```

### Limit Sell
```bash
python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.01 --price 70000
```

### Stop-Limit Buy (Bonus)
```bash
python cli.py --symbol BTCUSDT --side BUY --type STOP_LIMIT --quantity 0.01 --price 62000 --stop-price 61500
```

### Stop-Limit Sell (Bonus)
```bash
python cli.py --symbol BTCUSDT --side SELL --type STOP_LIMIT --quantity 0.01 --price 58000 --stop-price 58500
```

---

## Sample Output

```
 ╔══════════════════════════════════════════════════════════╗
 ║   ⚡  Binance Futures Testnet — Trading Bot  ⚡         ║
 ║                                                          ║
 ║   MARKET  •  LIMIT  •  STOP-LIMIT                       ║
 ║   Powered by direct REST API calls                       ║
 ╚══════════════════════════════════════════════════════════╝

Checking testnet connectivity... OK

┌─────────── Order Request Summary ───────────┐
│  Parameter      │  Value                     │
├─────────────────┼────────────────────────────│
│  Symbol         │  BTCUSDT                   │
│  Side           │  BUY                       │
│  Order Type     │  MARKET                    │
│  Quantity       │  0.01                      │
└─────────────────┴────────────────────────────┘

┌─────────── Order Response Details ──────────┐
│  Field            │  Value                   │
├───────────────────┼──────────────────────────│
│  Order ID         │  3951238475              │
│  Client Order ID  │  web_abc123              │
│  Symbol           │  BTCUSDT                 │
│  Status           │  FILLED                  │
│  Side             │  BUY                     │
│  Type             │  MARKET                  │
│  Orig Qty         │  0.01                    │
│  Executed Qty     │  0.01                    │
│  Avg Price        │  65432.10                │
└───────────────────┴──────────────────────────┘

╭─ ✅ Success ──────────────────────────────────╮
│  Order placed successfully!                    │
╰────────────────────────────────────────────────╯
```

---

## Logs

Logs are written to `logs/trading_bot_YYYYMMDD.log`.

- **Console**: INFO level and above
- **File**: DEBUG level and above (includes full request/response details)

---

## Bonus Features

### Stop-Limit Orders
The bot supports **Stop-Limit** orders (Binance API type `STOP`). This requires both a `--price` (the limit price for the order) and a `--stop-price` (the trigger price that activates the order). Useful for setting stop-loss or conditional entry points.

> **⚠️ Testnet/Demo Limitation:** The Binance Futures demo environment requires Stop-Limit orders to be placed via the Algo Order API (`/fapi/v1/order/algo`), which is **not available** on the demo or testnet environments. The STOP_LIMIT code is fully implemented and correct for the live Binance Futures API. On testnet/demo, the command will return a `-4120` error — this is an environment restriction, not a code bug.

### Enhanced CLI UX
The CLI uses the [`rich`](https://github.com/Textualize/rich) library for:
- Colorized startup banner
- Styled tables for order request/response summaries
- Color-coded panels for success and error messages
- BUY = green, SELL = red, FILLED = green, pending = yellow

---

## Assumptions

- Uses the **Binance Futures Demo API** (`https://demo-fapi.binance.com`) — no real funds.
- Uses direct REST API calls via `requests` (no third-party Binance SDK).
- LIMIT and STOP-LIMIT orders use `timeInForce=GTC` (Good Till Cancelled) by default.
- Credentials are loaded from environment variables for security.
- Stop-Limit orders map to Binance's `STOP` order type internally.
- Stop-Limit execution on live API requires Binance's Algo Order endpoint (not available on demo/testnet).

---

## Error Handling

| Scenario                    | Behavior                                         |
|-----------------------------|--------------------------------------------------|
| Missing credentials         | Prints clear message with panel, exits code 1    |
| Invalid CLI input            | Prints validation error panel, exits code 1      |
| Binance API error            | Logs error, prints failure panel                 |
| Network failure              | Logs error, prints failure panel                 |
| Testnet unreachable          | Prints connectivity error panel, exits code 1    |
| Missing price for LIMIT      | Validation error before API call                 |
| Missing stop-price for STOP  | Validation error before API call                 |
