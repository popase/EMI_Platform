from pathlib import Path

import matplotlib.pyplot as plt

from common import (
    ensure_output_dirs,
    load_analysis_dataset,
    load_config,
    resolve_path,
)


def plot_series(df, series_id, category, output_dir, config):
    g = df[df["series_id"].astype(str) == str(series_id)].copy()
    g = g.sort_values("timestamp")

    if g.empty:
        return

    fig, ax = plt.subplots(
        figsize=(
            config["plot"]["figure_width"],
            config["plot"]["figure_height"],
        )
    )

    ax.plot(
        g["timestamp"],
        g["SPM72_Wm2"],
        label="SPM72",
        linewidth=1.2,
    )

    # PV_Rear may have a different physical scale. We intentionally use
    # a second axis for visual diagnosis, not for statistical fitting.
    ax2 = ax.twinx()
    ax2.plot(
        g["timestamp"],
        g["PV_Rear"],
        label="PV_Rear",
        linewidth=1.2,
    )

    ax.set_xlabel("Time")
    ax.set_ylabel("SPM72 irradiance [W/m²]")
    ax2.set_ylabel("PV_Rear response")

    ax.set_title(f"{series_id} — {category}")
    ax.grid(True, alpha=0.25)

    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, loc="best")

    fig.autofmt_xdate()
    fig.tight_layout()

    safe_name = str(series_id).replace("/", "_").replace("\\", "_")
    out = output_dir / f"timeseries_{safe_name}.png"
    fig.savefig(out, dpi=config["plot"]["dpi"], bbox_inches="tight")
    plt.close(fig)

    print(f"Saved: {out}")


def main():
    config = load_config()
    ensure_output_dirs(config)
    df = load_analysis_dataset(config)

    out_dir = resolve_path(
        str(resolve_path(config["output_root"]) / "figures")
    )

    # Plot all classified series. This makes the script reusable when
    # another series is added to metadata.csv.
    for series_id, g in df.groupby("series_id"):
        category = g["category"].iloc[0]
        plot_series(df, series_id, category, out_dir, config)


if __name__ == "__main__":
    main()
