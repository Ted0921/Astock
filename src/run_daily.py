#!/usr/bin/env python3
import argparse
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S %Z")


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def write_file(path: Path, content: str) -> None:
    ensure_dir(path.parent)
    path.write_text(content, encoding="utf-8")


def pick_columns(df):
    # Try to locate common columns across AkShare variants (Chinese/English)
    cols = df.columns.tolist()
    def find(names):
        for n in names:
            for c in cols:
                if c == n or n in str(c):
                    return c
        return None

    sym = find(["代码", "symbol", "证券代码", "股票代码"]) or cols[0]
    name = find(["名称", "name", "股票名称"]) or cols[1] if len(cols) > 1 else None
    price = find(["最新", "现价", "close", "最新价", "当前价", "最新价格", "最新价(元)"]) or None
    change_pct = find(["涨跌幅", "涨幅", "change", "%", "涨跌幅(%)"]) or None
    amount = find(["成交额", "amount", "成交额(元)", "金额"]) or None
    volume = find(["成交量", "volume", "成交量(手)"]) or None
    return {"symbol": sym, "name": name, "price": price, "change_pct": change_pct, "amount": amount, "volume": volume}


def df_to_table(df, max_rows: int) -> str:
    if df is None or df.empty:
        return "<p>No data to display.</p>"
    cols = pick_columns(df)
    # Sort by amount/volume if available
    sort_key = cols["amount"] or cols["volume"] or cols["change_pct"] or cols["price"] or cols["symbol"]
    try:
        sdf = df.sort_values(by=sort_key, ascending=False)
    except Exception:
        sdf = df
    sdf = sdf.head(max_rows).reset_index(drop=True)

    headers = [c for c in [cols["symbol"], cols["name"], cols["price"], cols["change_pct"], cols["amount"], cols["volume"]] if c]
    # Fallback to first up-to-6 columns if nothing could be mapped
    if not headers:
        headers = list(df.columns[:6])
        sdf = df[headers].head(max_rows)

    # Build HTML table
    ths = "".join(f"<th>{h}</th>" for h in headers)
    rows = []
    for _, r in sdf.iterrows():
        tds = "".join(f"<td>{r.get(h, '')}</td>" for h in headers)
        rows.append(f"<tr>{tds}</tr>")
    tbody = "".join(rows)
    return f"""
    <div class=table-wrap>
      <table>
        <thead><tr>{ths}</tr></thead>
        <tbody>
          {tbody}
        </tbody>
      </table>
    </div>
    """


def build_html(mode: str, generated_at: str, details: str, data_source: str, df=None, max_rows: int = 50) -> str:
    table_html = df_to_table(df, max_rows) if mode == "online" else ""
    return f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
  <title>Daily Report</title>
  <style>
    :root {{ --border:#e1e4e8; --bg:#f6f8fa; --text:#24292e; --muted:#57606a; }}
    body{{font-family:system-ui,-apple-system,Segoe UI,Roboto,Ubuntu,Cantarell,Noto Sans,sans-serif;line-height:1.6;margin:2rem;color:var(--text)}}
    code,pre{{background:var(--bg);border:1px solid var(--border);border-radius:6px;padding:.5rem}}
    .meta{{color:var(--muted)}}
    table{{border-collapse:collapse;width:100%;max-width:1200px}}
    th,td{{border:1px solid var(--border);padding:.4rem .5rem;text-align:left}}
    th{{background:#fafbfc;position:sticky;top:0;}}
    .badge{{display:inline-block;padding:.1rem .4rem;border-radius:.25rem;border:1px solid var(--border);background:var(--bg);}}
  </style>
</head>
<body>
  <h1>Daily Report</h1>
  <p class=\"meta\">Generated at: {generated_at}</p>
  <p>Mode: <strong>{mode}</strong></p>
  <p>Data source: {data_source}</p>
  <p class=\"meta\">{details}</p>
  {table_html}
  <hr />
  <p><a href=\"/\">Back to latest</a></p>
</body>
</html>
"""


def generate_index_html(latest_rel_path: str) -> str:
    return f"""<!doctype html>
<meta charset=\"utf-8\">
<title>Redirecting to latest daily report</title>
<meta http-equiv=\"refresh\" content=\"0; url={latest_rel_path}\">
<link rel=\"canonical\" href=\"{latest_rel_path}\">
<body>
  <p>Redirecting to the <a href=\"{latest_rel_path}\">latest daily report</a>...</p>
</body>
"""


def try_fetch_online(max_symbols: int) -> Tuple[Optional[object], str, str]:
    """Attempt to fetch A-share snapshot data via AkShare.
    Returns (DataFrame or None, used_function_name, error_message)
    """
    try:
        import akshare as ak  # type: ignore
    except Exception as e:
        return None, "akshare-import", f"Failed to import akshare: {e}"

    funcs = [
        ("stock_zh_a_spot_em", "A-share spot (Eastmoney)"),
        ("stock_zh_a_spot", "A-share spot"),
    ]
    last_err = None
    for fname, label in funcs:
        try:
            fn = getattr(ak, fname)
        except Exception:
            last_err = f"Function {fname} not found in akshare"
            continue
        try:
            df = fn()
            if df is None or getattr(df, "empty", False):
                last_err = f"{fname} returned empty"
                continue
            # Downselect columns later; Cap rows here
            if max_symbols and len(df) > max_symbols:
                df = df.head(max_symbols)
            return df, f"AkShare: {fname} ({label})", ""
        except Exception as e:
            last_err = f"{fname} raised: {e}"
            continue
    return None, "AkShare", str(last_err or "unknown error")


def main():
    parser = argparse.ArgumentParser(description="Generate daily A-share report using AkShare (online) with offline fallback.")
    parser.add_argument("--online", action="store_true", help="Force online mode using AkShare; fallback to offline on failure")
    parser.add_argument("--max-symbols", type=int, default=120, help="Max number of symbols to display")
    parser.add_argument("--lookback", type=int, default=320, help="Lookback days for analysis (currently unused)")
    parser.add_argument("--outdir", type=str, default="reports", help="Base output directory for reports")
    args = parser.parse_args()

    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")

    base_out = Path(args.outdir)
    target_dir = base_out / "daily" / date_str
    target_report = target_dir / "report.html"

    print(f"Generating daily report for {date_str} -> {target_report}")

    mode = "offline"
    df = None
    data_source = "Offline fallback"
    details = "Generated without network data."

    if args.online:
        fetched_df, source_label, err = try_fetch_online(args.max_symbols)
        if fetched_df is not None:
            mode = "online"
            df = fetched_df
            data_source = f"{source_label} at {now.strftime('%Y-%m-%d %H:%M:%S')}"
            details = "Fetch succeeded via AkShare."
            print(f"Online fetch succeeded: {source_label} with {len(df)} rows")
        else:
            print(f"Online fetch failed or empty: {err}")
            mode = "offline"
            df = None
            data_source = f"AkShare fallback at {now.strftime('%Y-%m-%d %H:%M:%S')}"
            details = f"Online fetch failed or returned empty: {err}. Generated offline."

    html = build_html(
        mode=mode,
        generated_at=now.strftime("%Y-%m-%d %H:%M:%S %Z"),
        details=details,
        data_source=data_source,
        df=df,
        max_rows=min(args.max_symbols, 200),
    )

    write_file(target_report, html)

    # Update index.html to latest
    latest_rel_path = f"reports/daily/{date_str}/report.html"
    index_html = generate_index_html(latest_rel_path)
    write_file(Path("index.html"), index_html)

    # Ensure nojekyll exists for GitHub Pages
    Path(".nojekyll").touch()

    print(f"Wrote report: {target_report}")
    print(f"Updated index.html -> {latest_rel_path}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # As a last resort, do not fail the CI; write a minimal offline report
        print(f"Fatal error: {e}", file=sys.stderr)
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        target_dir = Path("reports") / "daily" / date_str
        target_report = target_dir / "report.html"
        ensure_dir(target_dir)
        html = build_html(
            mode="offline",
            generated_at=now.strftime("%Y-%m-%d %H:%M:%S %Z"),
            details=f"Fatal error occurred. Generated offline. Error: {e}",
            data_source=f"Offline fallback at {now.strftime('%Y-%m-%d %H:%M:%S')}",
            df=None,
        )
        write_file(target_report, html)
        latest_rel_path = f"reports/daily/{date_str}/report.html"
        write_file(Path("index.html"), generate_index_html(latest_rel_path))
        Path(".nojekyll").touch()
        print(f"Wrote fallback report: {target_report}")
        sys.exit(0)
