# Fyers + Google Sheets Trading Dashboard

This project is a starter Python application that connects:
- Fyers API for live quote retrieval, order placement, and position/PnL checks
- Google Sheets for tracking trade data, live market data, and PnL

It includes:
- login/auth helpers
- live market data snapshot to Google Sheets
- trade logging
- order placement helper
- stop-loss and target update helper
- PnL readout
- command-line runner for automation

## Features

- Fetch live quotes from Fyers for symbols in a watchlist
- Push market data to a Google Sheet
- Place buy/sell orders
- Record order details to a Trades sheet
- Update stop-loss and target values for open trades
- Pull open positions and PnL from Fyers
- Refresh dashboard on a schedule

## Project structure

```text
.
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── fyers_client.py
│   ├── google_sheets.py
│   ├── trade_manager.py
│   └── main.py
├── .env.example
├── requirements.txt
├── README.md
└── .gitignore
```

## Setup

1. Create a Python virtual environment
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Linux/macOS
   .venv\Scripts\activate      # Windows
   ```

2. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

3. Copy environment template
   ```bash
   cp .env.example .env
   ```

4. Fill in your values in `.env`

   Example:
   ```env
   FYERS_APP_ID=YOUR_APP_ID
   FYERS_SECRET_KEY=YOUR_SECRET_KEY
   FYERS_REDIRECT_URL=https://127.0.0.1
   FYERS_ACCESS_TOKEN=
   FYERS_REFRESH_TOKEN=
   FYERS_TOTP_SECRET=

   GOOGLE_SERVICE_ACCOUNT_JSON=service_account.json
   GOOGLE_SHEET_NAME=FyersTradeDashboard
   LIVE_SHEET_NAME=LiveMarketData
   TRADES_SHEET_NAME=Trades
   PNL_SHEET_NAME=Pnl
   WATCHLIST=NSE:RELIANCE-EQ,NSE:TCS-EQ,NSE:INFY-EQ
   ```

5. Create a Google service account and download JSON credentials
   - Go to Google Cloud Console
   - Create a service account
   - Download JSON key
   - Place it in the project folder
   - Share that Google Sheet with the service account email

6. Login to Fyers
   - Use the app to get an auth code or generate token using the method in `app/fyers_client.py`
   - Save the access token and refresh token in `.env`

## Fyers login flow

Use the command below to print the login URL:

```bash
python -m app.main auth-url
```

Then complete the Fyers authorization flow. After that, use the returned auth code to generate the access token:

```bash
python -m app.main generate-token --auth-code YOUR_AUTH_CODE
```

If you already have a valid token, you can skip this step and just set `FYERS_ACCESS_TOKEN` in `.env`.

## Usage

### 1. Sync live market data to Google Sheets

```bash
python -m app.main sync-live
```

### 2. Place an order

```bash
python -m app.main place-order \
  --symbol NSE:RELIANCE-EQ \
  --side BUY \
  --qty 1 \
  --product-type CNC \
  --order-type MARKET
```

### 3. Update stop-loss or target

```bash
python -m app.main update-stop-loss \
  --order-id YOUR_ORDER_ID \
  --stop-loss 2600
```

```bash
python -m app.main update-target \
  --order-id YOUR_ORDER_ID \
  --target 2750
```

### 4. Fetch PnL and positions

```bash
python -m app.main pnl
```

### 5. Run the dashboard loop

```bash
python -m app.main run-dashboard
```

This refreshes market data and PnL at a fixed interval.

## Example Google Sheets layout

### LiveMarketData

| Symbol | LTP | Change | %Change | Volume | Timestamp |
|--------|-----|--------|---------|--------|-----------|

### Trades

| Order ID | Symbol | Side | Qty | Price | Status | Entry Time | Stop Loss | Target |
|----------|--------|------|-----|-------|--------|------------|-----------|--------|

### Pnl

| Symbol | Net PnL | Unrealized PnL | Realized PnL | Position | Avg Price |
|--------|----------|----------------|--------------|----------|-----------|

## Important notes

- Never expose your Fyers secret key or Google service account JSON in public repositories
- Use a dedicated trading account and test environment first
- Make sure the Google Sheet is shared with the service account email
- API endpoints and payload fields can vary slightly by Fyers API version, so validate with their official docs before going live

## Disclaimer

This software is for educational and automation purposes. You are responsible for validating the logic, risk controls, and compliance requirements for your broker account and trading strategy.
