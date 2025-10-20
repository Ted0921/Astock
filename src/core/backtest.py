from __future__ import annotations

import numpy as np
import pandas as pd

from .signals import rank_pct


def rotation_backtest(
    df_feat: pd.DataFrame,
    topN: int = 15,
    rebalance_every: int = 5,
) -> pd.DataFrame:
    """
    Simple top-N rotation backtest using strength score computed from stock_mom and concept_mom.
    Rebalance every N trading days; hold equal-weighted portfolio.

    Returns a DataFrame with columns: date, portfolio_log_ret, equity.
    """
    if df_feat.empty:
        return pd.DataFrame(columns=["date", "portfolio_log_ret", "equity"])  # empty

    df = df_feat.sort_values(["date", "symbol"]).copy()
    # Precompute per-date strength score
    def compute_strength(group: pd.DataFrame) -> pd.Series:
        stock_r = rank_pct(group["stock_mom"]).fillna(0)
        concept_r = rank_pct(group["concept_mom"]).fillna(0) if "concept_mom" in group.columns else 0
        return 0.5 * stock_r + 0.5 * concept_r

    df["strength_score"] = df.groupby("date", group_keys=False).apply(lambda g: compute_strength(g))

    dates = sorted(df["date"].unique())
    if not dates:
        return pd.DataFrame(columns=["date", "portfolio_log_ret", "equity"])  # empty

    portfolio_log_rets = []
    equity = 1.0

    for i, d in enumerate(dates):
        daily = df[df["date"] == d]
        if i % rebalance_every == 0:
            picks = (
                daily.sort_values(by=["strength_score", "close"], ascending=[False, False])
                .head(topN)[["symbol"]]
                .copy()
            )
            universe_today = picks["symbol"].tolist()
        # Compute next-day return on the chosen names
        next_idx = i + 1
        if next_idx >= len(dates):
            break
        next_d = dates[next_idx]
        next_day = df[(df["date"] == next_d) & (df["symbol"].isin(universe_today))]
        # Portfolio log return is mean of constituent log rets
        port_lr = next_day["log_ret"].mean()
        if pd.isna(port_lr):
            port_lr = 0.0
        equity *= float(np.exp(port_lr))
        portfolio_log_rets.append({"date": next_d, "portfolio_log_ret": port_lr, "equity": equity})

    res = pd.DataFrame(portfolio_log_rets)
    return res
