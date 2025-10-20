from __future__ import annotations

import math
from datetime import datetime, timedelta
from typing import Optional, List

import pandas as pd

from .data_io import log


def _try_import_akshare():
    try:
        import akshare as ak  # type: ignore
        return ak
    except Exception as e:  # pragma: no cover - best effort to import
        log(f"AkShare import failed: {e}")
        return None


def _fetch_codes_akshare(ak, max_symbols: int) -> List[str]:
    try:
        spot = ak.stock_zh_a_spot_em()
        # Use top by amount to pick more liquid names
        spot = spot.sort_values(by="成交额", ascending=False)
        codes = spot["代码"].astype(str).head(max_symbols).tolist()
        return codes
    except Exception as e:
        log(f"Fetching A-share list failed: {e}")
        return []


def fetch_akshare_daily(max_symbols: int = 30, lookback_days: int = 260) -> Optional[pd.DataFrame]:
    """
    Fetch daily qfq data via AkShare for up to max_symbols tickers.
    Returns a DataFrame with columns: date, symbol, open, high, low, close, volume.
    """
    ak = _try_import_akshare()
    if ak is None:
        return None

    codes = _fetch_codes_akshare(ak, max_symbols=max_symbols)
    if not codes:
        return None

    start_date = (datetime.utcnow() - timedelta(days=lookback_days * 2)).strftime("%Y%m%d")

    frames = []
    for code in codes:
        try:
            # qfq daily
            hist = ak.stock_zh_a_hist(symbol=code, period="daily", start_date=start_date, adjust="qfq")
            if hist is None or hist.empty:
                continue
            # Normalize columns
            rename_map = {
                "日期": "date",
                "开盘": "open",
                "最高": "high",
                "最低": "low",
                "收盘": "close",
                "成交量": "volume",
            }
            for col in rename_map:
                if col not in hist.columns:
                    # Some akshare versions use slightly different names; try English fallbacks
                    english_map = {
                        "日期": "date",
                        "开盘": "open",
                        "最高": "high",
                        "最低": "low",
                        "收盘": "close",
                        "成交量": "volume",
                    }
                    # If English already present, continue
                    pass
            hist = hist.rename(columns=rename_map)
            cols_needed = ["date", "open", "high", "low", "close", "volume"]
            if not set(cols_needed).issubset(hist.columns):
                # Try alternative AkShare column names
                alt_map = {
                    "日期": "date",
                    "开盘价": "open",
                    "最高价": "high",
                    "最低价": "low",
                    "收盘价": "close",
                    "成交量(手)": "volume",
                }
                hist = hist.rename(columns=alt_map)
            hist = hist[[c for c in ["date", "open", "high", "low", "close", "volume"] if c in hist.columns]].copy()
            if hist.empty:
                continue
            hist["date"] = pd.to_datetime(hist["date"]).dt.date
            hist["symbol"] = code
            frames.append(hist)
        except Exception as e:
            log(f"Fetch failed for {code}: {e}")
            continue

    if not frames:
        return None

    df = pd.concat(frames, ignore_index=True)
    df = df.dropna(subset=["close"]).sort_values(["symbol", "date"]).reset_index(drop=True)
    # Try to coerce numeric
    for c in ["open", "high", "low", "close", "volume"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    # Some AkShare endpoints return volume in hands; scale to shares not strictly needed
    return df
