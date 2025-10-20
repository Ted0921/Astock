from __future__ import annotations

import math
import random
from dataclasses import dataclass
from datetime import timedelta, datetime
from typing import List, Optional

import numpy as np
import pandas as pd

from .data_io import tz_now, DEFAULT_TZ


@dataclass
class SampleConfig:
    n_symbols: int = 120
    n_days: int = 260
    seed: int = 42
    tz_name: str = DEFAULT_TZ


def _make_trading_days(end_dt: Optional[datetime], n_days: int, tz_name: str) -> List[pd.Timestamp]:
    end_dt = end_dt or tz_now(tz_name)
    # Assume business days, generate backwards
    days = []
    cur = end_dt.date()
    while len(days) < n_days:
        if cur.weekday() < 5:
            days.append(pd.Timestamp(cur))
        cur = cur - timedelta(days=1)
    days = list(reversed(days))
    return days


def generate_offline_sample(cfg: Optional[SampleConfig] = None) -> pd.DataFrame:
    cfg = cfg or SampleConfig()
    rng = np.random.default_rng(cfg.seed)
    random.seed(cfg.seed)

    days = _make_trading_days(end_dt=None, n_days=cfg.n_days, tz_name=cfg.tz_name)

    # Build synthetic symbols and concepts
    n = cfg.n_symbols
    symbols = [f"S{str(i+1).zfill(4)}" for i in range(n)]
    concepts = ["Tech", "Finance", "Industrial"]
    concept_map = {s: concepts[i % len(concepts)] for i, s in enumerate(symbols)}

    # Concept-level drifts and vols
    concept_drift = {c: rng.normal(0.0003, 0.0001) for c in concepts}
    concept_vol = {c: abs(rng.normal(0.015, 0.003)) for c in concepts}

    records = []
    for s in symbols:
        c = concept_map[s]
        price = float(rng.uniform(5.0, 50.0))
        for d in days:
            # Daily return from GBM-like with concept component and idiosyncratic noise
            mu = concept_drift[c] + rng.normal(0.0001, 0.0002)
            sigma = concept_vol[c] * float(abs(rng.normal(1.0, 0.1)))
            r = rng.normal(mu, sigma)
            new_price = max(0.5, price * math.exp(r))
            open_p = price
            close_p = new_price
            high_p = max(open_p, close_p) * (1 + abs(rng.normal(0.001, 0.002)))
            low_p = min(open_p, close_p) * (1 - abs(rng.normal(0.001, 0.002)))
            vol = int(abs(rng.normal(2e6, 5e5)))
            records.append(
                {
                    "date": d,
                    "symbol": s,
                    "open": open_p,
                    "high": high_p,
                    "low": low_p,
                    "close": close_p,
                    "volume": vol,
                    "concept": c,
                }
            )
            price = new_price

    df = pd.DataFrame.from_records(records)
    df.sort_values(["symbol", "date"], inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df
