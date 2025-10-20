# A-Share Daily Report (AkShare)

This repository publishes a simple daily report to GitHub Pages. The report attempts to fetch live A-share market data via AkShare (online mode). If the online fetch fails or returns no data, the workflow falls back to offline mode and still publishes a report, so your Pages site always has the latest artifact.

## How it works

- GitHub Actions runs daily (schedule), on manual dispatch, and on pushes to the repo.
- The workflow installs dependencies (including `akshare`) and runs:

  ```bash
  python src/run_daily.py --online --max-symbols 120 --lookback 320
  ```

- The script tries to retrieve A-share snapshot data using AkShare. If it succeeds, the generated HTML shows:
  - Mode: online
  - Data source: AkShare function used and a precise timestamp
- If the fetch raises an error or returns empty data, it logs the error and regenerates the report in offline mode so publication continues.

The report is written under `reports/daily/YYYY-MM-DD/report.html`, and `index.html` is updated to redirect to the latest date.

## Online vs Offline

- Online mode: Uses AkShare (e.g., `stock_zh_a_spot_em` or `stock_zh_a_spot`) to fetch a snapshot list of A-share symbols. The HTML displays Mode: online and a data source annotation with timestamp.
- Offline mode (fallback): If online data fails, the HTML explicitly displays Mode: offline with a note indicating the failure and a fallback timestamp.

## Deployment to GitHub Pages (gh-pages)

The workflow deploys the generated site to the `gh-pages` branch using `peaceiris/actions-gh-pages`. Make sure:

- Repository Settings → Pages: source is set to Branch: `gh-pages` and folder: `/ (root)`.
- Actions permissions allow the workflow to push to the repository.

### Required workflow permissions

The workflow sets:

```yaml
permissions:
  contents: write
```

This enables pushing the built site to the `gh-pages` branch via the built-in `GITHUB_TOKEN`.

## Manual run

You can manually trigger a run via the Actions tab using the "Run workflow" button. This will perform the same online-then-offline-fallback logic and deploy to `gh-pages`.

## Troubleshooting

- If the workflow fails on the dependency step, ensure that Actions have internet access and that `akshare` can be installed. The workflow uses Python 3.11.
- If the online step logs an error and the report shows Mode: offline, check network access from Actions runners. This is expected fallback behavior; Pages should still be updated.
- If Pages does not update, verify:
  - Settings → Pages is configured to use the `gh-pages` branch (root).
  - Actions permissions include `contents: write` (either default repo permission or set in the workflow), and that the workflow has not been restricted from creating the `gh-pages` branch.
  - The workflow's deploy step (`peaceiris/actions-gh-pages`) runs after the generation step and reports success.

## Local development

Optionally, you can run the generator locally:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python src/run_daily.py --online --max-symbols 120 --lookback 320
```

This will update `index.html` and create `reports/daily/<today>/report.html` in your working tree.
