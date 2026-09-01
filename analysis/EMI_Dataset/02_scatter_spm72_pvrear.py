from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from common import (
    ensure_output_dirs,
    load_analysis_dataset,
    load_config,
    resolve_path,
    safe_corr,
)


def main():
    config = load_config()
    ensure_output_dirs(config)
    df = load_analysis_dataset(config)

    df = df[df["analysis_eligible"]].copy()
    if df.empty:
        raise RuntimeError("No eligible paired observations.")

    fig, ax = plt.subplots(
        figsize=(
            config["plot"]["figure_width"],
            config["plot"]["figure_height"],
        )
    )

    categories = ["stable", "dynamic_C1", "local_shading", "unknown"]
    markers = ["o", "^", "s", "x"]

    for category, marker in zip(categories, markers):
        subset = df[df["category"] == category]
        if subset.empty:
            continue

        # Each category is one plotted series; matplotlib assigns colors.
        ax.scatter(
            subset["SPM72_Wm2"],
            subset["PV_Rear"],
            s=config["plot"]["point_size"],
            alpha=config["plot"]["alpha"],
            marker=marker,
            label=f"{category} (n={len(subset)})",
        )

    ax.set_xlabel("SPM72 irradiance [W/m²]")
    ax.set_ylabel("PV_Rear response")
    ax.set_title("SPM72 vs PV_Rear — segmented experimental dataset")
    ax.grid(True, alpha=0.25)
    ax.legend()

    # Descriptive overall Pearson correlation only; no calibration fit.
    r = safe_corr(df["SPM72_Wm2"], df["PV_Rear"])
    ax.text(
        0.02, 0.98,
        f"Pearson r = {r:.4f}" if pd.notna(r) else "Pearson r = n/a",
        transform=ax.transAxes,
        va="top",
        bbox=dict(boxstyle="round", facecolor="white", alpha=0.8),
    )

    fig.tight_layout()

    out = resolve_path(
        str(resolve_path(config["output_root"]) / "figures" / "scatter_spm72_pv_rear.png")
    )
    fig.savefig(out, dpi=config["plot"]["dpi"], bbox_inches="tight")
    plt.close(fig)

    print(f"Saved: {out}")


if __name__ == "__main__":
    main()
