from __future__ import annotations

from pathlib import Path
from typing import Any

import gspread
from google.oauth2 import service_account

from app.config import get_settings


class GoogleSheetsClient:
    """Google Sheets wrapper for live market data and trade logs."""

    def __init__(self, service_account_json_path: str | None = None):
        settings = get_settings()
        self.service_account_json_path = service_account_json_path or settings.google_service_account_json
        self.sheet_name = settings.google_sheet_name
        self.live_sheet_name = settings.live_sheet_name
        self.trades_sheet_name = settings.trades_sheet_name
        self.pnl_sheet_name = settings.pnl_sheet_name
        self.client = self._connect()

    def _connect(self):
        file_path = Path(self.service_account_json_path).resolve()
        if not file_path.exists():
            raise FileNotFoundError(
                f"Google service account JSON not found: {file_path}. "
                "Create a service account and point GOOGLE_SERVICE_ACCOUNT_JSON to the JSON file."
            )

        credentials = service_account.Credentials.from_service_account_file(
            str(file_path),
            scopes=["https://www.googleapis.com/auth/spreadsheets"],
        )
        return gspread.authorize(credentials)

    def get_or_create_workbook(self):
        workbook = self.client.open(self.sheet_name)
        return workbook

    def _ensure_sheet(self, workbook, sheet_name: str, headers: list[str]):
        try:
            worksheet = workbook.worksheet(sheet_name)
        except gspread.exceptions.WorksheetNotFound:
            worksheet = workbook.add_worksheet(title=sheet_name, rows="1000", cols="20")
            worksheet.append_row(headers)
        else:
            existing = worksheet.get_all_values()
            if not existing or existing[0] != headers:
                worksheet.insert_row(headers, 1)
        return worksheet

    def setup_dashboard(self):
        workbook = self.get_or_create_workbook()
        live_headers = ["Symbol", "LTP", "Change", "%Change", "Volume", "Timestamp"]
        trade_headers = ["Order ID", "Symbol", "Side", "Qty", "Price", "Status", "Entry Time", "Stop Loss", "Target"]
        pnl_headers = ["Symbol", "Net PnL", "Unrealized PnL", "Realized PnL", "Position", "Avg Price"]

        self._ensure_sheet(workbook, self.live_sheet_name, live_headers)
        self._ensure_sheet(workbook, self.trades_sheet_name, trade_headers)
        self._ensure_sheet(workbook, self.pnl_sheet_name, pnl_headers)
        return workbook

    def write_live_market_row(self, symbol: str, quote: dict[str, Any]):
        workbook = self.get_or_create_workbook()
        worksheet = self._ensure_sheet(
            workbook,
            self.live_sheet_name,
            ["Symbol", "LTP", "Change", "%Change", "Volume", "Timestamp"],
        )

        row = [
            symbol,
            quote.get("lastPrice", ""),
            quote.get("netChange", ""),
            quote.get("percentChange", ""),
            quote.get("volume", ""),
            quote.get("timestamp", ""),
        ]

        rows = worksheet.get_all_values()
        for index, existing in enumerate(rows[1:], start=2):
            if existing and existing[0] == symbol:
                worksheet.update(f"A{index}:F{index}", [row])
                return

        worksheet.append_row(row)

    def record_trade(self, order_result: dict[str, Any]):
        workbook = self.get_or_create_workbook()
        worksheet = self._ensure_sheet(
            workbook,
            self.trades_sheet_name,
            ["Order ID", "Symbol", "Side", "Qty", "Price", "Status", "Entry Time", "Stop Loss", "Target"],
        )

        order_id = str(order_result.get("id") or order_result.get("order_id") or "")
        symbol = order_result.get("symbol") or ""
        side = order_result.get("side") or ""
        qty = order_result.get("qty") or ""
        price = order_result.get("price") or ""
        status = order_result.get("status") or "placed"
        entry_time = order_result.get("entry_time") or order_result.get("timestamp") or ""
        stop_loss = order_result.get("stop_loss") or ""
        target = order_result.get("target") or ""

        worksheet.append_row([order_id, symbol, side, qty, price, status, entry_time, stop_loss, target])

    def update_trade_row(self, order_id: str, field_name: str, value: Any):
        workbook = self.get_or_create_workbook()
        worksheet = self._ensure_sheet(
            workbook,
            self.trades_sheet_name,
            ["Order ID", "Symbol", "Side", "Qty", "Price", "Status", "Entry Time", "Stop Loss", "Target"],
        )

        rows = worksheet.get_all_values()
        headers = rows[0]
        field_index = headers.index(field_name) + 1

        for row_idx, row in enumerate(rows[1:], start=2):
            if row and row[0] == str(order_id):
                worksheet.update_cell(row_idx, field_index, str(value))
                return

        raise ValueError(f"Order ID {order_id} not found in sheet")

    def write_pnl(self, pnl_rows: list[dict[str, Any]]):
        workbook = self.get_or_create_workbook()
        worksheet = self._ensure_sheet(
            workbook,
            self.pnl_sheet_name,
            ["Symbol", "Net PnL", "Unrealized PnL", "Realized PnL", "Position", "Avg Price"],
        )

        worksheet.clear()
        worksheet.append_row(["Symbol", "Net PnL", "Unrealized PnL", "Realized PnL", "Position", "Avg Price"])
        for row in pnl_rows:
            worksheet.append_row(
                [
                    row.get("symbol"),
                    row.get("netPnl"),
                    row.get("unrealizedPnl"),
                    row.get("realizedPnl"),
                    row.get("position"),
                    row.get("avgPrice"),
                ]
            )
