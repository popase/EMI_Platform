from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from common import (
    ensure_output_dirs,
    load_analysis_dataset,
    load_config,
    resolve_path,
    safe_corr,
)


def robust_stats(series: pd.Series) -> dict:
    x = pd.to_numeric(series, errors="coerce").dropna()
    if len(x) == 0:
        return {"min": np.nan, "max": np.nan, "median": np.nan,
                "mean": np.nan, "std": np.nan, "p05": np.nan, "p95": np.nan}
    return {"min": x.min(), "max": x.max(), "median": x.median(),
            "mean": x.mean(), "std": x.std(), "p05": x.quantile(.05),
            "p95": x.quantile(.95)}


def change_stats(series: pd.Series) -> dict:
    d = pd.to_numeric(series, errors="coerce").diff().dropna().abs()
    if len(d) == 0:
        return {"delta_median_abs": np.nan, "delta_p90_abs": np.nan,
                "delta_p95_abs": np.nan, "delta_max_abs": np.nan}
    return {"delta_median_abs": d.median(), "delta_p90_abs": d.quantile(.90),
            "delta_p95_abs": d.quantile(.95), "delta_max_abs": d.max()}


def temporal_stats(g: pd.DataFrame) -> dict:
    t = g.sort_values("timestamp")["timestamp"].dropna()
    out = {"start_utc": pd.NaT, "end_utc": pd.NaT, "duration_min": np.nan,
           "median_sampling_interval_s": np.nan, "max_gap_s": np.nan,
           "n_gaps_over_60s": np.nan}
    if len(t):
        out["start_utc"], out["end_utc"] = t.iloc[0], t.iloc[-1]
    if len(t) >= 2:
        dt = t.diff().dt.total_seconds().dropna()
        out["duration_min"] = (t.iloc[-1] - t.iloc[0]).total_seconds() / 60
        out["median_sampling_interval_s"] = dt.median()
        out["max_gap_s"] = dt.max()
        out["n_gaps_over_60s"] = int((dt > 60).sum())
    return out


def analyze_series(g: pd.DataFrame, config: dict) -> dict:
    sid = str(g["series_id"].iloc[0])
    category = str(g["category"].iloc[0])
    e = g[g["analysis_eligible"]].copy()
    s, p = robust_stats(e["SPM72_Wm2"]), robust_stats(e["PV_Rear"])
    sd, pd_ = change_stats(e["SPM72_Wm2"]), change_stats(e["PV_Rear"])
    out = {"series_id": sid, "category": category, "n_raw": len(g),
           "n_eligible": len(e), "eligible_pct": 100*len(e)/len(g) if len(g) else np.nan,
           "SPM72_min_Wm2": s["min"], "SPM72_max_Wm2": s["max"],
           "SPM72_median_Wm2": s["median"], "SPM72_std_Wm2": s["std"],
           "SPM72_p05_Wm2": s["p05"], "SPM72_p95_Wm2": s["p95"],
           "SPM72_delta_median_abs": sd["delta_median_abs"],
           "SPM72_delta_p90_abs": sd["delta_p90_abs"],
           "SPM72_delta_p95_abs": sd["delta_p95_abs"],
           "SPM72_delta_max_abs": sd["delta_max_abs"],
           "PV_Rear_min_mA": p["min"], "PV_Rear_max_mA": p["max"],
           "PV_Rear_median_mA": p["median"], "PV_Rear_std_mA": p["std"],
           "PV_Rear_delta_median_abs_mA": pd_["delta_median_abs"],
           "PV_Rear_delta_p90_abs_mA": pd_["delta_p90_abs"],
           "PV_Rear_delta_p95_abs_mA": pd_["delta_p95_abs"],
           "PV_Rear_delta_max_abs_mA": pd_["delta_max_abs"],
           "pearson_r": safe_corr(e["SPM72_Wm2"], e["PV_Rear"], "pearson"),
           "spearman_rho": safe_corr(e["SPM72_Wm2"], e["PV_Rear"], "spearman")}
    out.update(temporal_stats(g))
    sync = pd.to_numeric(g["sync_difference_s"], errors="coerce").dropna()
    tol = float(config["analysis"]["sync_tolerance_seconds"])
    out["sync_abs_median_s"] = sync.abs().median() if len(sync) else np.nan
    out["sync_abs_p95_s"] = sync.abs().quantile(.95) if len(sync) else np.nan
    out["sync_abs_max_s"] = sync.abs().max() if len(sync) else np.nan
    out["sync_within_tolerance_pct"] = 100*(sync.abs() <= tol).mean() if len(sync) else np.nan
    return out


def plot_diagnostic(g, out_dir, config):
    sid = str(g["series_id"].iloc[0])
    cat = str(g["category"].iloc[0])
    g = g.sort_values("timestamp")
    fig, ax = plt.subplots(figsize=(config["plot"]["figure_width"], config["plot"]["figure_height"]))

    ax.plot(g["timestamp"], g["SPM72_Wm2"], linewidth=1.2, linestyle="-", color="tab:blue",label="SPM72 [W/m²]",)
    ax2 = ax.twinx()
    ax2.plot(
    g["timestamp"],
    g["PV_Rear"],
    linewidth=1.2,
    linestyle="--",
    color="tab:orange",
    label="PV_Rear [mA]",)

    ax.set_xlabel("Time (UTC)"); ax.set_ylabel("SPM72 irradiance [W/m²]")
    ax2.set_ylabel("PV_Rear current [mA]")
    ax.set_title(f"{sid} — preliminary series diagnostic — {cat}")
    ax.grid(True, alpha=.25)
    h1,l1=ax.get_legend_handles_labels(); h2,l2=ax2.get_legend_handles_labels()
    ax.legend(h1+h2,l1+l2,loc="best")
    fig.autofmt_xdate(); fig.tight_layout()
    path=out_dir/f"diagnostic_{sid}.png"
    fig.savefig(path,dpi=config["plot"]["dpi"],bbox_inches="tight"); plt.close(fig)


def main():
    config=load_config(); ensure_output_dirs(config)
    df=load_analysis_dataset(config)
    figures=resolve_path(str(resolve_path(config["output_root"])/"figures"/"diagnostics"))
    reports=resolve_path(str(resolve_path(config["output_root"])/"reports"))
    figures.mkdir(parents=True,exist_ok=True); reports.mkdir(parents=True,exist_ok=True)
    rows=[]
    for sid,g in df.groupby("series_id",sort=True):
        rows.append(analyze_series(g,config)); plot_diagnostic(g,figures,config)
    report=pd.DataFrame(rows)
    report.to_csv(reports/"series_diagnostics.csv",index=False,encoding="utf-8-sig")
    cols=["series_id","category","n_raw","duration_min","SPM72_min_Wm2","SPM72_max_Wm2","SPM72_delta_p95_abs","PV_Rear_min_mA","PV_Rear_max_mA","pearson_r","spearman_rho","max_gap_s"]
    with (reports/"series_diagnostics_summary.txt").open("w",encoding="utf-8") as f:
        f.write("EMI Platform — preliminary series diagnostics\n")
        f.write("These diagnostics are descriptive; no automatic classification or calibration model is applied.\n\n")
        f.write(report[cols].to_string(index=False)); f.write("\n")
    print(f"Series analyzed: {len(report)}")
    print(f"Diagnostic figures: {figures}")
    print(f"CSV report: {reports/'series_diagnostics.csv'}")
    print(f"Text summary: {reports/'series_diagnostics_summary.txt'}")
    print("\nQuick diagnostic table:")
    print(report[cols].to_string(index=False))

if __name__ == "__main__":
    main()
