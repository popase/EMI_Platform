from pathlib import Path

import numpy as np
import pandas as pd

from common import (
    continuity_metrics,
    ensure_output_dirs,
    load_analysis_dataset,
    load_config,
    resolve_path,
    safe_corr,
)


def summarize_group(g: pd.DataFrame, group_name: str, group_value: str, config: dict):
    all_n = len(g)
    eligible = g[g["analysis_eligible"]].copy()
    n = len(eligible)

    cont = continuity_metrics(g)

    if n:
        spm_min = eligible["SPM72_Wm2"].min()
        spm_max = eligible["SPM72_Wm2"].max()
        pv_min = eligible["PV_Rear"].min()
        pv_max = eligible["PV_Rear"].max()
        pearson = safe_corr(eligible["SPM72_Wm2"], eligible["PV_Rear"], "pearson")
        spearman = safe_corr(eligible["SPM72_Wm2"], eligible["PV_Rear"], "spearman")
    else:
        spm_min = spm_max = pv_min = pv_max = np.nan
        pearson = spearman = np.nan

    sync = g["sync_difference_s"].dropna()
    if len(sync):
        sync_abs_median = sync.abs().median()
        sync_abs_max = sync.abs().max()
        sync_within = (sync.abs() <= float(
            config["analysis"]["sync_tolerance_seconds"]
        )).mean() * 100
    else:
        sync_abs_median = sync_abs_max = np.nan
        sync_within = np.nan

    return {
        group_name: group_value,
        "n_raw_rows": all_n,
        "n_eligible_pairs": n,
        "pair_fraction_pct": (100 * n / all_n) if all_n else np.nan,
        "SPM72_min_Wm2": spm_min,
        "SPM72_max_Wm2": spm_max,
        "PV_Rear_min": pv_min,
        "PV_Rear_max": pv_max,
        "pearson_r": pearson,
        "spearman_rho": spearman,
        "sync_abs_median_s": sync_abs_median,
        "sync_abs_max_s": sync_abs_max,
        "sync_within_tolerance_pct": sync_within,
        **cont,
    }


def main():
    config = load_config()
    ensure_output_dirs(config)
    df = load_analysis_dataset(config)

    reports = resolve_path(
        str(resolve_path(config["output_root"]) / "reports")
    )
    reports.mkdir(parents=True, exist_ok=True)

    by_category = pd.DataFrame([
        summarize_group(g, "category", category, config)
        for category, g in df.groupby("category", sort=True)
    ])

    by_series = pd.DataFrame([
        summarize_group(g, "series_id", series_id, config)
        for series_id, g in df.groupby("series_id", sort=True)
    ])

    by_category.to_csv(
        reports / "descriptive_by_category.csv",
        index=False,
        encoding="utf-8-sig",
    )
    by_series.to_csv(
        reports / "descriptive_by_series.csv",
        index=False,
        encoding="utf-8-sig",
    )

    lines = [
        "# EMI Platform — descriptive dataset report",
        "",
        "This report is descriptive only. No calibration model is fitted.",
        "",
        "## By category",
        "",
        by_category.to_markdown(index=False),
        "",
        "## By series",
        "",
        by_series.to_markdown(index=False),
        "",
        "## Interpretation notes",
        "",
        "- `n_raw_rows` counts rows imported from synchronized CSV files.",
        "- `n_eligible_pairs` counts observations with valid timestamp, SPM72 and PV_Rear and within the configured synchronization tolerance.",
        "- Pearson and Spearman coefficients are descriptive correlations, not calibration models.",
        "- Continuity metrics describe temporal coverage and gaps.",
        "- Raw synchronized files are not modified.",
    ]

    (reports / "descriptive_report.md").write_text(
        "\n".join(lines),
        encoding="utf-8",
    )

    print(f"Saved: {reports / 'descriptive_by_category.csv'}")
    print(f"Saved: {reports / 'descriptive_by_series.csv'}")
    print(f"Saved: {reports / 'descriptive_report.md'}")


if __name__ == "__main__":
    main()
