from __future__ import annotations

import numpy as np
import pandas as pd


def compute_features(
    df: pd.DataFrame,
    lookback: int = 60,
    vol_win: int = 20,
    vol_lb: int = 120,
) -> pd.DataFrame:
    """
    Compute features on a long-format OHLCV DataFrame with columns:
    ['date', 'symbol', 'open', 'high', 'low', 'close', 'volume', optional 'concept'].

    Features:
    - log_ret: log returns
    - vol: rolling std of log_ret (vol_win)
    - vol_z: z-score of vol over a longer baseline (vol_lb)
    - stock_mom: momentum via exp(sum of log_ret over lookback) - 1
    - concept_mom: same but aggregated at concept level if available
    """
    out = df.copy()
    out = out.sort_values(["symbol", "date"]).reset_index(drop=True)

    # Compute per-symbol log returns
    out["log_ret"] = (
        np.log(out.groupby("symbol")["close"].transform(lambda s: s.shift(0)))
        - np.log(out.groupby("symbol")["close"].transform(lambda s: s.shift(1)))
    )

    # Rolling vol and vol z-score
    def _rolling_std(x, win):
        return x.rolling(win, min_periods=max(2, win // 2)).std()

    out["vol"] = out.groupby("symbol")["log_ret"].transform(lambda s: _rolling_std(s, vol_win))
    base_mean = out.groupby("symbol")["vol"].transform(lambda s: s.rolling(vol_lb, min_periods=max(5, vol_lb // 4)).mean())
    base_std = out.groupby("symbol")["vol"].transform(lambda s: s.rolling(vol_lb, min_periods=max(5, vol_lb // 4)).std())
    out["vol_z"] = (out["vol"] - base_mean) / base_std.replace(0, np.nan)

    # Momentum on stock level
    roll_sum = out.groupby("symbol")["log_ret"].transform(lambda s: s.rolling(lookback, min_periods=max(5, lookback // 4)).sum())
    out["stock_mom"] = np.exp(roll_sum) - 1.0

    # Concept aggregation if available
    if "concept" in out.columns:
        concept_daily = (
            out.dropna(subset=["log_ret"]).groupby(["date", "concept"])['log_ret'].mean().reset_index(name='concept_log_ret')
        )
        concept_daily["concept_mom"] = (
            concept_daily.groupby("concept")["concept_log_ret"].transform(
                lambda s: s.rolling(lookback, min_periods=max(5, lookback // 4)).sum()
            )
        )
        concept_daily["concept_mom"] = np.exp(concept_daily["concept_mom"]) - 1.0
        out = out.merge(concept_daily[["date", "concept", "concept_mom"]], on=["date", "concept"], how="left")
    else:
        out["concept_mom"] = np.nan

    return out
