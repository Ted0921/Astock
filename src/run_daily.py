from __future__ import annotations

import argparse
import os
import shutil
from typing import Optional

import pandas as pd

from core.data_io import (
    get_paths,
    ensure_dirs,
    load_config,
    today_str,
    get_daily_report_dir,
    copytree,
    log,
)
from core.sample import generate_offline_sample, SampleConfig
from core.fetchers import fetch_akshare_daily
from core.features import compute_features
from core.signals import compute_signals
from core.report import save_daily_report


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="A-share daily analysis pipeline")
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--offline", action="store_true", help="Use offline sample data (default)")
    mode.add_argument("--online", action="store_true", help="Use online AkShare data")
    p.add_argument("--max-symbols", type=int, help="Maximum number of symbols to use")
    p.add_argument("--lookback", type=int, help="Lookback window for strength")
    p.add_argument("--vol-win", type=int, help="Volatility rolling window")
    p.add_argument("--vol-lb", type=int, help="Volatility baseline lookback for z-score")
    return p.parse_args()


def main() -> int:
    cfg = load_config("config.yaml")
    tz_name = cfg.get("timezone", "Asia/Shanghai")

    args = parse_args()
    offline = True if args.offline or not args.online else False

    lookback = args.lookback or int(cfg.get("lookback", 60))
    vol_win = args.vol_win or int(cfg.get("vol_win", 20))
    vol_lb = args.vol_lb or int(cfg.get("vol_lb", 120))
    max_symbols = args.max_symbols or int(cfg.get("max_symbols", 30))
    topN = int(cfg.get("topN", 15))
    ab_th = float(cfg.get("ab_vol_threshold", 2.0))

    paths = get_paths(".")
    ensure_dirs(paths)

    # Generate or fetch data
    df: Optional[pd.DataFrame] = None
    if not offline:
        log("Running in ONLINE mode: attempting to fetch AkShare data...")
        try:
            df = fetch_akshare_daily(max_symbols=max_symbols, lookback_days=max(lookback * 2, 260))
        except Exception as e:
            log(f"Online fetch failed: {e}")
            df = None
    if df is None:
        log("Falling back to OFFLINE mode: generating synthetic sample data...")
        df = generate_offline_sample(
            SampleConfig(n_symbols=max_symbols, n_days=max(lookback + vol_lb + 10, 260))
        )

    # Feature engineering
    df_feat = compute_features(df, lookback=lookback, vol_win=vol_win, vol_lb=vol_lb)
    # Signals for latest date
    universe_snap, picks = compute_signals(df_feat, topN=topN, ab_vol_threshold=ab_th)

    # Save report
    dstr = today_str(tz_name)
    out_dir = get_daily_report_dir(paths, dstr)
    save_daily_report(universe_snap, picks, out_dir, dstr)

    # Maintain a 'latest' directory for GitHub Pages deployment
    latest_dir = os.path.join(paths.reports_daily, "latest")
    if os.path.exists(latest_dir):
        shutil.rmtree(latest_dir)
    shutil.copytree(out_dir, latest_dir)

    log(f"Report generated at: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
