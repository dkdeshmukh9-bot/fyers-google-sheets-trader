from __future__ import annotations

import argparse
import time

from app.config import get_settings
from app.fyers_client import FyersClient
from app.google_sheets import GoogleSheetsClient
from app.trade_manager import TradeManager


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fyers + Google Sheets Trading Dashboard")
    subparsers = parser.add_subparsers(dest="action", required=True)

    subparsers.add_parser("auth-url", help="Print the Fyers authorization URL")

    token_parser = subparsers.add_parser("generate-token", help="Generate access token from auth code")
    token_parser.add_argument("--auth-code", required=True, help="Fyers auth code returned by the login flow")

    sync_parser = subparsers.add_parser("sync-live", help="Fetch live prices and write to Google Sheets")
    sync_parser.add_argument("--symbols", help="Optional comma separated symbol list")

    order_parser = subparsers.add_parser("place-order", help="Place a Fyers order")
    order_parser.add_argument("--symbol", required=True)
    order_parser.add_argument("--side", required=True, choices=["BUY", "SELL"])
    order_parser.add_argument("--qty", required=True, type=int)
    order_parser.add_argument("--product-type", default="CNC")
    order_parser.add_argument("--order-type", default="MARKET")
    order_parser.add_argument("--limit-price", type=float, default=0.0)
    order_parser.add_argument("--stop-loss", type=float, default=None)
    order_parser.add_argument("--target", type=float, default=None)

    stop_parser = subparsers.add_parser("update-stop-loss", help="Update the stop-loss of an order")
    stop_parser.add_argument("--order-id", required=True)
    stop_parser.add_argument("--stop-loss", required=True, type=float)

    target_parser = subparsers.add_parser("update-target", help="Update the target of an order")
    target_parser.add_argument("--order-id", required=True)
    target_parser.add_argument("--target", required=True, type=float)

    pnl_parser = subparsers.add_parser("pnl", help="Fetch PnL and write to Google Sheets")

    dashboard_parser = subparsers.add_parser("run-dashboard", help="Run continual dashboard updates")
    dashboard_parser.add_argument("--interval", type=int, default=15, help="Refresh interval in seconds")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    settings = get_settings()

    if args.action == "auth-url":
        client = FyersClient()
        print(client.auth_url())
        return

    if args.action == "generate-token":
        client = FyersClient()
        result = client.generate_session_from_auth_code(args.auth_code)
        print(result)
        return

    manager = TradeManager()
    manager.initialize_dashboard()

    if args.action == "sync-live":
        symbols = None
        if args.symbols:
            symbols = [symbol.strip() for symbol in args.symbols.split(",") if symbol.strip()]
        result = manager.sync_live_market_data(symbols)
        print(result)
        return

    if args.action == "place-order":
        result = manager.place_trade(
            symbol=args.symbol,
            side=args.side,
            qty=args.qty,
            product_type=args.product_type,
            order_type=args.order_type,
            limit_price=args.limit_price,
            stop_loss=args.stop_loss,
            target=args.target,
        )
        print(result)
        return

    if args.action == "update-stop-loss":
        result = manager.update_stop_loss(args.order_id, args.stop_loss)
        print(result)
        return

    if args.action == "update-target":
        result = manager.update_target(args.order_id, args.target)
        print(result)
        return

    if args.action == "pnl":
        pnl = manager.fetch_and_write_pnl()
        print(pnl)
        return

    if args.action == "run-dashboard":
        while True:
            manager.sync_live_market_data()
            manager.fetch_and_write_pnl()
            print(f"Dashboard refreshed at {__import__('datetime').datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
            time.sleep(args.interval)

    parser.error(f"Unsupported action: {args.action}")


if __name__ == "__main__":
    main()
