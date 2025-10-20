# Astock

Daily report published to GitHub Pages.

- Actions status: [![Daily Report](https://github.com/Ted0921/Astock/actions/workflows/daily.yml/badge.svg)](https://github.com/Ted0921/Astock/actions/workflows/daily.yml)
- GitHub Pages (latest report): https://Ted0921.github.io/Astock/

How it works
- Runs every day at 16:40 Asia/Shanghai (08:40 UTC)
- Can also be triggered manually from Actions
- A push to `main` that touches `src/**`, `.github/workflows/daily.yml`, or `README.md` will also run the workflow and publish

Manual run
- Go to the repository on GitHub → Actions → Daily Report → Run workflow

Implementation notes
- The workflow attempts to fetch data online first; if that fails, it falls back to an offline mode but still produces a report
- Artifacts are uploaded for each run
- The site is deployed to the `gh-pages` branch root, and `index.html` redirects to the most recent `reports/daily/YYYY-MM-DD/report.html`
