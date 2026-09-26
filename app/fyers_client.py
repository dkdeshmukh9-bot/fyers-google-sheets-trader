from __future__ import annotations

import datetime as dt
import json
from typing import Any

import requests

from app.config import get_settings


class FyersClient:
    """Thin wrapper for Fyers REST calls."""

    def __init__(self, access_token: str | None = None, refresh_token: str | None = None):
        settings = get_settings()
        self.app_id = settings.fyers_app_id
        self.secret_key = settings.fyers_secret_key
        self.redirect_url = settings.fyers_redirect_url
        self.access_token = access_token or settings.fyers_access_token
        self.refresh_token = refresh_token or settings.fyers_refresh_token
        self.base_url = "https://api.fyers.in/api/v2"

    @property
    def auth_headers(self) -> dict[str, str]:
        if not self.access_token:
            raise ValueError("Access token is missing. Generate one from Fyers auth flow first.")
        return {"Authorization": f"Bearer {self.access_token}"}

    def auth_url(self) -> str:
        return (
            "https://api.fyers.in/api/v2/authorize?"
            f"response_type=code&client_id={self.app_id}&redirect_uri={self.redirect_url}"
        )

    def generate_session_from_auth_code(self, auth_code: str) -> dict[str, Any]:
        payload = {
            "grant_type": "authorization_code",
            "appId": self.app_id,
            "secretKey": self.secret_key,
            "code": auth_code,
        }
        response = requests.post(f"{self.base_url}/token", data=payload, timeout=30)
        response.raise_for_status()
        result = response.json()

        if result.get("s": "") == "ok":
            self.access_token = result.get("access_token")
            self.refresh_token = result.get("refresh_token")
        return result

    def refresh_session(self) -> dict[str, Any]:
        if not self.refresh_token:
            raise ValueError("Refresh token is missing.")

        payload = {
            "grant_type": "refresh_token",
            "appId": self.app_id,
            "secretKey": self.secret_key,
            "refresh_token": self.refresh_token,
        }
        response = requests.post(f"{self.base_url}/token", data=payload, timeout=30)
        response.raise_for_status()
        result = response.json()

        if result.get("s") == "ok":
            self.access_token = result.get("access_token")
            self.refresh_token = result.get("refresh_token")
        return result

    def _request(self, method: str, endpoint: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        response = requests.request(
            method=method.upper(),
            url=url,
            headers=self.auth_headers,
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        if data.get("s") == "error":
            raise RuntimeError(f"Fyers API error: {data}")
        return data

    def get_profile(self) -> dict[str, Any]:
        return self._request("GET", "/profile")

    def get_quote(self, symbols: list[str]) -> dict[str, Any]:
        return self._request("POST", "/quotes", {"symbols": symbols})

    def get_positions(self) -> dict[str, Any]:
        return self._request("GET", "/positions")

    def get_pnl(self) -> dict[str, Any]:
        return self._request("GET", "/pnl")

    def place_order(
        self,
        symbol: str,
        qty: int,
        side: str,
        product_type: str = "CNC",
        order_type: str = "MARKET",
        limit_price: float = 0.0,
        stop_loss: float | None = None,
        target: float | None = None,
        validity: str = "DAY",
    ) -> dict[str, Any]:
        payload = {
            "symbol": symbol,
            "qty": qty,
            "type": self._order_type_mapper(order_type),
            "side": side.upper(),
            "productType": product_type.upper(),
            "limitPrice": limit_price,
            "stopPrice": 0,
            "validity": validity.upper(),
            "disclosedQuantity": 0,
            "offlineOrder": False,
        }

        if stop_loss is not None:
            payload["stopLoss"] = stop_loss
        if target is not None:
            payload["takeProfit"] = target

        return self._request("POST", "/orders", payload)

    def modify_order(self, order_id: str, **kwargs) -> dict[str, Any]:
        payload = {"id": order_id}
        payload.update(kwargs)
        return self._request("PUT", "/orders", payload)

    def cancel_order(self, order_id: str) -> dict[str, Any]:
        return self._request("DELETE", "/orders", {"id": order_id})

    def add_stop_loss(self, order_id: str, stop_loss_value: float) -> dict[str, Any]:
        return self.modify_order(order_id, stopLoss=stop_loss_value)

    def add_target(self, order_id: str, target_value: float) -> dict[str, Any]:
        return self.modify_order(order_id, takeProfit=target_value)

    @staticmethod
    def _order_type_mapper(order_type: str) -> int:
        mapping = {
            "MARKET": 2,
            "LIMIT": 1,
            "STOPLOSS_LIMIT": 3,
            "STOPLOSS_MARKET": 4,
        }
        normalized = order_type.upper()
        if normalized not in mapping:
            raise ValueError(f"Unsupported order type: {order_type}")
        return mapping[normalized]

    @staticmethod
    def get_current_timestamp() -> str:
        return dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
