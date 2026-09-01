from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent


def load_config() -> dict:
    with open(BASE_DIR / "config.json", "r", encoding="utf-8") as f:
        return json.load(f)


def resolve_path(value: str) -> Path:
    p = Path(value)
    return p if p.is_absolute() else BASE_DIR / p


def load_metadata() -> pd.DataFrame:
    path = BASE_DIR / "series_metadata.csv"
    df = pd.read_csv(path, comment="#", dtype=str).fillna("")
    required = {"series_id", "category"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing metadata columns: {sorted(missing)}")

    allowed = {"stable", "dynamic_C1", "local_shading", "unknown"}
    bad = sorted(set(df["category"]) - allowed)
    if bad:
        raise ValueError(
            f"Unknown category values: {bad}. "
            f"Allowed: {sorted(allowed)}"
        )

    return df


def find_column(df: pd.DataFrame, aliases: Iterable[str], logical_name: str) -> str:
    lower = {str(c).strip().lower(): c for c in df.columns}
    for alias in aliases:
        key = str(alias).strip().lower()
        if key in lower:
            return lower[key]

    raise KeyError(
        f"Could not find column for '{logical_name}'. "
        f"Available columns: {list(df.columns)}"
    )


def parse_time(series: pd.Series) -> pd.Series:
    # utc=True safely normalizes both +03:00 and Z timestamps.
    return pd.to_datetime(series, errors="coerce", utc=True)


def load_one_series(path: Path, config: dict, metadata: pd.DataFrame) -> pd.DataFrame:
    raw = pd.read_csv(path)

    c = config["columns"]
    timestamp_col = find_column(raw, c["timestamp"], "timestamp")
    spm_col = find_column(raw, c["spm72"], "SPM72")
    pv_col = find_column(raw, c["pv_rear"], "PV_Rear")

    out = pd.DataFrame({
        "series_id": path.parent.name,
        "source_file": str(path),
        "source_row": np.arange(len(raw)) + 2,
        "timestamp": parse_time(raw[timestamp_col]),
        "SPM72_Wm2": pd.to_numeric(raw[spm_col], errors="coerce"),
        "PV_Rear": pd.to_numeric(raw[pv_col], errors="coerce"),
    })

    # Preserve useful synchronization information if present.
    sync_col = None
    for alias in c.get("sync_difference", []):
        if alias.lower() in {str(x).lower() for x in raw.columns}:
            sync_col = next(x for x in raw.columns if str(x).lower() == alias.lower())
            break
    if sync_col:
        out["sync_difference_s"] = pd.to_numeric(raw[sync_col], errors="coerce")
    else:
        out["sync_difference_s"] = np.nan

    status_col = None
    for alias in c.get("sync_status", []):
        matches = [x for x in raw.columns if str(x).lower() == alias.lower()]
        if matches:
            status_col = matches[0]
            break
    out["source_status"] = raw[status_col].astype(str) if status_col else ""

    meta = metadata[metadata["series_id"].astype(str) == path.parent.name]
    if len(meta):
        row = meta.iloc[0]
        out["category"] = row["category"]
        out["condition_code"] = row.get("condition_code", "")
        out["notes"] = row.get("notes", "")
    else:
        out["category"] = "unknown"
        out["condition_code"] = ""
        out["notes"] = "No metadata entry"

    return out


def discover_series(config: dict, metadata: pd.DataFrame) -> pd.DataFrame:
    root = resolve_path(config["input_root"])
    file_name = config["file_name"]

    paths = sorted(root.glob(f"*/{file_name}"))
    if not paths:
        raise FileNotFoundError(
            f"No '{file_name}' files found below {root}"
        )

    frames = []
    errors = []

    for path in paths:
        try:
            frames.append(load_one_series(path, config, metadata))
        except Exception as exc:
            errors.append(f"{path}: {exc}")

    if errors:
        message = "\n".join(errors)
        raise RuntimeError("Input errors:\n" + message)

    df = pd.concat(frames, ignore_index=True)
    return df


def add_qc_columns(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    tol = float(config["analysis"]["sync_tolerance_seconds"])

    df = df.copy()
    df["valid_pair"] = (
        df["timestamp"].notna()
        & df["SPM72_Wm2"].notna()
        & df["PV_Rear"].notna()
    )

    df["sync_within_tolerance"] = np.where(
        df["sync_difference_s"].notna(),
        df["sync_difference_s"].abs() <= tol,
        True
    )

    df["analysis_eligible"] = (
        df["valid_pair"] & df["sync_within_tolerance"]
    )

    return df


def load_analysis_dataset(config: dict) -> pd.DataFrame:
    path = resolve_path(
        str(Path(config["output_root"]) / "dataset" / "analysis_dataset.csv")
    )
    if not path.exists():
        raise FileNotFoundError(
            f"{path} does not exist. Run 01_prepare_dataset.py first."
        )

    df = pd.read_csv(path)
    df["timestamp"] = parse_time(df["timestamp"])
    return df


def safe_corr(x: pd.Series, y: pd.Series, method: str = "pearson"):
    tmp = pd.DataFrame({"x": x, "y": y}).dropna()
    if len(tmp) < 3:
        return np.nan

    if tmp["x"].nunique() < 2 or tmp["y"].nunique() < 2:
        return np.nan

    return tmp["x"].corr(tmp["y"], method=method)


def continuity_metrics(group: pd.DataFrame) -> dict:
    g = group.sort_values("timestamp").copy()
    t = g["timestamp"].dropna()

    if len(t) < 2:
        return {
            "duration_s": np.nan,
            "median_interval_s": np.nan,
            "max_gap_s": np.nan,
            "n_gaps_over_60s": np.nan,
        }

    diffs = t.diff().dt.total_seconds().dropna()

    return {
        "duration_s": (t.iloc[-1] - t.iloc[0]).total_seconds(),
        "median_interval_s": diffs.median(),
        "max_gap_s": diffs.max(),
        "n_gaps_over_60s": int((diffs > 60).sum()),
    }


def ensure_output_dirs(config: dict):
    root = resolve_path(config["output_root"])
    for name in ["dataset", "figures", "reports"]:
        (root / name).mkdir(parents=True, exist_ok=True)


def save_markdown(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
