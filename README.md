Astock: A-share Analyzer (Daily Pipeline, Reports, GitHub Pages)

Overview
This repository contains a lightweight Python 3.11 project that generates daily A-share analysis reports. It supports both offline sample data (fast and deterministic) and online data via AkShare (前复权, 日频). A scheduled GitHub Actions workflow publishes the latest report to GitHub Pages.

Quick start
- Python: 3.11
- Install dependencies:
  pip install -r requirements.txt

Offline daily run (default)
Generates a synthetic universe and produces a report for today under reports/daily/YYYY-MM-DD/.
  python src/run_daily.py --offline

Online daily run (AkShare)
Fetches a subset of A-shares, computes features/signals, and produces the daily report. If the online fetch fails, use the offline mode.
  python src/run_daily.py --online
Useful flags:
  --max-symbols INT   Limit universe size (default read from config.yaml)
  --lookback INT      Momentum lookback for strength
  --vol-win INT       Rolling volatility window
  --vol-lb INT        Volatility baseline lookback for z-score

Backtest demo
Runs a simple top-N rotation on the synthetic dataset and writes a minimal report under reports/backtest/.
  python src/run_backtest.py

What gets produced
- reports/daily/YYYY-MM-DD/
  - picks.csv: Top-N symbols for the day with strength and volatility stats
  - universe.csv: Snapshot of universe with features for the day
  - report.html: Minimal HTML report linking to the CSVs
- reports/daily/latest/ mirrors the latest report folder for GitHub Pages deployment

GitHub Pages and Workflow
- GitHub Actions workflow: .github/workflows/daily.yml
  - Trigger: schedule "40 8 * * 1-5" (UTC), i.e. 16:40 Asia/Shanghai
  - Steps: checkout → setup Python 3.11 → pip cache + install → run online mode with fallback to offline
  - Deployment: publishes reports/daily/latest/ to gh-pages branch root via peaceiris/actions-gh-pages@v3.
  - The workflow sets permissions: contents: write and initializes gh-pages if it doesn’t exist (force_orphan on first publish).
- Published site: https://<your-username>.github.io/Astock/ (replace <your-username>)
  The site always serves the latest daily report.

Configuration
- config.yaml controls defaults:
  - lookback: momentum/strength lookback window
  - vol_win: rolling window for volatility
  - vol_lb: lookback for volatility baseline (z-score)
  - max_symbols: limit for online fetch
  - topN: number of top picks
  - ab_vol_threshold: z-score threshold for abnormal volatility
  - timezone: timestamping for daily reports (default Asia/Shanghai)

Notes about AkShare
- Online mode relies on AkShare endpoints and may be subject to rate limits or upstream instability.
- The workflow uses --online by default but gracefully falls back to --offline if fetching fails or times out.
- On fresh runners, extra time may be needed for the first dependency installation and any upstream responses.

Repository layout
- src/
  - run_daily.py: End-to-end daily pipeline
  - run_backtest.py: Demo rotation backtest
  - core/
    - data_io.py: I/O utilities, config, path helpers
    - sample.py: Offline sample universe generator
    - fetchers.py: AkShare online fetchers (qfq, daily)
    - features.py: Log returns, concept aggregation, volatility z-score
    - signals.py: Strength and abnormal volatility signals
    - backtest.py: Top-N rotation
    - report.py: CSV exports + minimal HTML report
- data/
  - raw/, processed/, ref/ (gitignored except data/ref if you want to place static mappings)
- reports/
  - daily/, backtest/
- .github/workflows/daily.yml: Scheduled GitHub Pages publishing

License
MIT License (see LICENSE)
