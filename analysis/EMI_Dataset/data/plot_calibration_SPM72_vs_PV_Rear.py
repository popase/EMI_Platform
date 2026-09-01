"""
EMI Platform — Calibration Figure
SPM72 irradiance vs PV_Rear current

Reproducible figure generation from the frozen calibration dataset.
This script does NOT use the validation dataset and does NOT fit the
final calibration model. The linear regression shown in the figure
is diagnostic only.
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------

DATASET = Path("calibration_dataset.csv")
OUTPUT_FIGURE = Path("calibration_SPM72_vs_PV_Rear.png")
OUTPUT_DPI = 300


# ---------------------------------------------------------------------
# Load frozen calibration dataset
# ---------------------------------------------------------------------

df = pd.read_csv(DATASET)

required_columns = [
    "timestamp",
    "spm72_wm2",
    "current_rear",
    "series_id",
]

missing = [c for c in required_columns if c not in df.columns]
if missing:
    raise ValueError(f"Missing required columns: {missing}")

df["spm72_wm2"] = pd.to_numeric(df["spm72_wm2"], errors="coerce")
df["current_rear"] = pd.to_numeric(df["current_rear"], errors="coerce")

df = df.dropna(subset=["spm72_wm2", "current_rear", "series_id"])


# ---------------------------------------------------------------------
# Diagnostic linear regression
#
# IMPORTANT:
# This is only a diagnostic relationship for the exploratory figure.
# It is NOT the final calibration model.
# ---------------------------------------------------------------------

x = df["current_rear"].to_numpy()
y = df["spm72_wm2"].to_numpy()

slope, intercept = np.polyfit(x, y, 1)

y_pred = slope * x + intercept

ss_res = np.sum((y - y_pred) ** 2)
ss_tot = np.sum((y - np.mean(y)) ** 2)
r2 = 1.0 - ss_res / ss_tot


# ---------------------------------------------------------------------
# Figure
# ---------------------------------------------------------------------

fig, ax = plt.subplots(figsize=(8, 6))

series_ids = sorted(df["series_id"].unique())

for series_id in series_ids:
    subset = df[df["series_id"] == series_id]

    ax.scatter(
        subset["current_rear"],
        subset["spm72_wm2"],
        s=18,
        alpha=0.65,
        label=series_id,
    )


# Diagnostic linear fit
x_line = np.linspace(x.min(), x.max(), 200)
y_line = slope * x_line + intercept

ax.plot(
    x_line,
    y_line,
    linewidth=2,
    label="Linear diagnostic fit",
)


# ---------------------------------------------------------------------
# Labels and layout
# ---------------------------------------------------------------------

ax.set_xlabel("PV_Rear current [mA]")
ax.set_ylabel("SPM72 irradiance [W/m²]")
ax.set_title("Calibration dataset: SPM72 vs PV_Rear")

ax.grid(True, alpha=0.25)
ax.legend(ncol=2, fontsize=8)

fig.tight_layout()


# ---------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------

fig.savefig(
    OUTPUT_FIGURE,
    dpi=OUTPUT_DPI,
    bbox_inches="tight",
)

plt.show()


# ---------------------------------------------------------------------
# Console output for reproducibility
# ---------------------------------------------------------------------

pearson = df["spm72_wm2"].corr(df["current_rear"], method="pearson")
spearman = df["spm72_wm2"].corr(df["current_rear"], method="spearman")

print("EMI Platform — Calibration Figure")
print("---------------------------------")
print(f"Dataset:       {DATASET}")
print(f"Observations:  {len(df)}")
print(f"Series:        {', '.join(series_ids)}")
print()
print(f"Pearson r:     {pearson:.6f}")
print(f"Spearman rho:  {spearman:.6f}")
print()
print("Diagnostic linear relationship:")
print(f"G = {slope:.6f} * I + {intercept:.6f}")
print(f"R² = {r2:.6f}")
print()
print(f"Figure saved:  {OUTPUT_FIGURE}")
