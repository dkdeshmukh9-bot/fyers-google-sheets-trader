from __future__ import annotations

import datetime as dt
from typing import Any

from app.config import get_settings
from app.fyers_client import FyersClient
from app.google_sheets import GoogleSheetsClient


class TradeManager:
    def __init__(self, fyers_client: FyersClient | None = None, sheets_client: GoogleSheetsClient | None = None):
        self.settings = get_settings()
        self.fyers = fyers_client or FyersClient()
        self.sheets = sheets_client or GoogleSheetsClient()

    def initialize_dashboard(self):
        self.sheets.setup_dashboard()

    def sync_live_market_data(self, symbols: list[str] | None = None):
        watchlist = symbols or self.settings.watchlist
        if not watchlist:
            raise ValueError("No symbols configured in WATCHLIST")

        quote_response = self.fyers.get_quote(watchlist)
        quote_data = quote_response.get("d", {})

        for symbol, payload in quote_data.items():
            normalized = payload
            market_row = {
                "lastPrice": normalized.get("lastPrice"),
                "netChange": normalized.get("netChange"),
                "percentChange": normalized.get("percentChange"),
                "volume": normalized.get("volume"),
                "timestamp": dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            }
            self.sheets.write_live_market_row(symbol, market_row)

    def place_trade(
        self,
        symbol: str,
        side: str,
        qty: int,
        product_type: str = "CNC",
        order_type: str = "MARKET",
        limit_price: float = 0.0,
        stop_loss: float | None = None,
        target: float | None = None,
    ) -> dict[str, Any]:
        result = self.fyers.place_order(
            symbol=symbol,
            qty=qty,
            side=side,
            product_type=product_type,
            order_type=order_type,
            limit_price=limit_price,
            stop_loss=stop_loss,
            target=target,
        )

        order_payload = {
            "id": result.get("id") or result.get("order_id") or "",
            "symbol": symbol,
            "side": side.upper(),
            "qty": qty,
            "price": limit_price if order_type.upper() == "LIMIT" else "MARKET",
            "status": result.get("status") or "placed",
            "entry_time": dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "stop_loss": stop_loss,
            "target": target,
        }
        self.sheets.record_trade(order_payload)
        return result

    def update_stop_loss(self, order_id: str, stop_loss_value: float):
        result = self.fyers.add_stop_loss(order_id, stop_loss_value)
        self.sheets.update_trade_row(order_id, "Stop Loss", stop_loss_value)
        return result

    def update_target(self, order_id: str, target_value: float):
        result = self.fyers.add_target(order_id, target_value)
        self.sheets.update_trade_row(order_id, "Target", target_value)
        return result

    def fetch_and_write_pnl(self):
        positions = self.fyers.get_positions()
        pnl_rows = []

        for item in positions.get("data", []):
            pnl_rows.append(
                {
                    "symbol": item.get("symbol"),
                    "netPnl": item.get("pnl"),
                    "unrealizedPnl": item.get("unrealizedPnl"),
                    "realizedPnl": item.get("realizedPnl"),
                    "position": item.get("quantity"),
                    "avgPrice": item.get("averagePrice"),
                }
            )

        self.sheets.write_pnl(pnl_rows)
        return pnl_rows
