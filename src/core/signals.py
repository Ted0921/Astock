from __future__ import annotations

import numpy as np
import pandas as pd


def rank_pct(s: pd.Series) -> pd.Series:
    return s.rank(pct=True, na_option="keep")


def compute_signals(
    df_feat: pd.DataFrame,
    topN: int = 15,
    ab_vol_threshold: float = 2.0,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Produce two DataFrames for the latest date:
    - universe_latest: all symbols with strength scores and vol info for the latest date
    - picks: topN symbols by strength score
    """
    if df_feat.empty:
        return df_feat.copy(), df_feat.copy()

    # Latest date snapshot
    latest_date = df_feat["date"].max()
    snap = df_feat[df_feat["date"] == latest_date].copy()

    # Strength score combines stock and concept momentum
    stock_r = rank_pct(snap["stock_mom"]) if "stock_mom" in snap.columns else pd.Series(np.nan, index=snap.index)
    concept_r = rank_pct(snap["concept_mom"]) if "concept_mom" in snap.columns else pd.Series(np.nan, index=snap.index)
    strength = 0.5 * stock_r.fillna(0) + 0.5 * concept_r.fillna(0)
    snap["strength_score"] = strength

    # Abnormal vol flag
    snap["ab_vol"] = snap.get("vol_z", pd.Series(np.nan, index=snap.index)) > ab_vol_threshold

    # Rank and pick topN
    snap = snap.sort_values(by=["strength_score", "close"], ascending=[False, False])
    picks = snap.head(topN).copy()

    return snap, picks
