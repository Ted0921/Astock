from __future__ import annotations

import os
from datetime import datetime

from core.data_io import get_paths, ensure_dirs
from core.sample import generate_offline_sample, SampleConfig
from core.features import compute_features
from core.backtest import rotation_backtest
from core.report import save_daily_report


def main() -> int:
    paths = get_paths(".")
    ensure_dirs(paths)

    # Use offline sample for demo backtest
    df = generate_offline_sample(SampleConfig(n_symbols=100, n_days=300))
    df_feat = compute_features(df, lookback=60, vol_win=20, vol_lb=120)

    res = rotation_backtest(df_feat, topN=15, rebalance_every=5)

    # Save minimal backtest artifacts
    out_dir = os.path.join(paths.reports_backtest, datetime.utcnow().date().isoformat())
    os.makedirs(out_dir, exist_ok=True)

    # Equity curve CSV
    res.to_csv(os.path.join(out_dir, "equity_curve.csv"), index=False)

    # Also produce a simple daily-style report using latest snapshot as proxy
    # Here we reuse the latest available snapshot
    latest_date = df_feat["date"].max()
    snap = df_feat[df_feat["date"] == latest_date].copy()

    from core.signals import compute_signals

    universe_snap, picks = compute_signals(df_feat, topN=15, ab_vol_threshold=2.0)

    from core.data_io import today_str

    save_daily_report(universe_snap, picks, out_dir, today_str())

    print(f"Backtest artifacts written to: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
