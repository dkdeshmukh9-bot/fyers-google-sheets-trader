from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


@dataclass(frozen=True)
class Settings:
    fyers_app_id: str
    fyers_secret_key: str
    fyers_redirect_url: str
    fyers_access_token: str | None
    fyers_refresh_token: str | None
    fyers_totp_secret: str | None
    google_service_account_json: str
    google_sheet_name: str
    live_sheet_name: str
    trades_sheet_name: str
    pnl_sheet_name: str
    watchlist: list[str]


def get_settings() -> Settings:
    required = [
        "FYERS_APP_ID",
        "FYERS_SECRET_KEY",
        "FYERS_REDIRECT_URL",
    ]

    missing = [key for key in required if not os.getenv(key)]
    if missing:
        raise ValueError(f"Missing required env vars: {', '.join(missing)}")

    watchlist_raw = os.getenv("WATCHLIST", "")
    watchlist = [item.strip() for item in watchlist_raw.split(",") if item.strip()]

    return Settings(
        fyers_app_id=os.getenv("FYERS_APP_ID"),
        fyers_secret_key=os.getenv("FYERS_SECRET_KEY"),
        fyers_redirect_url=os.getenv("FYERS_REDIRECT_URL"),
        fyers_access_token=os.getenv("FYERS_ACCESS_TOKEN"),
        fyers_refresh_token=os.getenv("FYERS_REFRESH_TOKEN"),
        fyers_totp_secret=os.getenv("FYERS_TOTP_SECRET"),
        google_service_account_json=os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "service_account.json"),
        google_sheet_name=os.getenv("GOOGLE_SHEET_NAME", "FyersTradeDashboard"),
        live_sheet_name=os.getenv("LIVE_SHEET_NAME", "LiveMarketData"),
        trades_sheet_name=os.getenv("TRADES_SHEET_NAME", "Trades"),
        pnl_sheet_name=os.getenv("PNL_SHEET_NAME", "Pnl"),
        watchlist=watchlist,
    )
