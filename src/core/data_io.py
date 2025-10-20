import os
import shutil
from dataclasses import dataclass
from datetime import datetime, date
from zoneinfo import ZoneInfo
from typing import Dict, Optional

import pandas as pd
import yaml


DEFAULT_TZ = "Asia/Shanghai"


@dataclass
class Paths:
    root: str
    data_raw: str
    data_processed: str
    data_ref: str
    reports_daily: str
    reports_backtest: str


def load_config(path: str = "config.yaml") -> Dict:
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
    else:
        cfg = {}
    return cfg


def tz_now(tz_name: Optional[str]) -> datetime:
    tz = ZoneInfo(tz_name or DEFAULT_TZ)
    return datetime.now(tz)


def today_str(tz_name: Optional[str] = None) -> str:
    return tz_now(tz_name).date().isoformat()


def get_paths(root: str = ".") -> Paths:
    root = os.path.abspath(root)
    return Paths(
        root=root,
        data_raw=os.path.join(root, "data", "raw"),
        data_processed=os.path.join(root, "data", "processed"),
        data_ref=os.path.join(root, "data", "ref"),
        reports_daily=os.path.join(root, "reports", "daily"),
        reports_backtest=os.path.join(root, "reports", "backtest"),
    )


def ensure_dirs(paths: Paths) -> None:
    for p in [
        paths.data_raw,
        paths.data_processed,
        paths.data_ref,
        paths.reports_daily,
        paths.reports_backtest,
    ]:
        os.makedirs(p, exist_ok=True)


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def write_csv(df: pd.DataFrame, path: str) -> None:
    ensure_dir(os.path.dirname(path))
    df.to_csv(path, index=False)


def read_csv(path: str) -> pd.DataFrame:
    return pd.read_csv(path)


def copytree(src: str, dst: str) -> None:
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def get_daily_report_dir(paths: Paths, day: date | str) -> str:
    d = day if isinstance(day, str) else day.isoformat()
    out = os.path.join(paths.reports_daily, d)
    ensure_dir(out)
    return out


def log(msg: str) -> None:
    ts = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    print(f"[{ts}] {msg}")
