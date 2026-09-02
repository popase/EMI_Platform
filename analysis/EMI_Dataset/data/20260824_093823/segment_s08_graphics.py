import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import spearmanr, pearsonr
from pathlib import Path

# ============================================================
# S08 – analiza segmentelor A/B/C
# SPM72 vs PV_Rear + reziduuri
# ============================================================

INPUT = Path("S08_segmented.csv")
OUTPUT_DIR = Path("plots_S08")
OUTPUT_DIR.mkdir(exist_ok=True)

# ------------------------------------------------------------
# 1. Citire date
# ------------------------------------------------------------

df = pd.read_csv(INPUT)

print("Coloane disponibile:")
print(df.columns.tolist())

# ------------------------------------------------------------
# 2. Verificare coloane
# ------------------------------------------------------------

required = ["timestamp", "series_id", "spm72_wm2", "current_rear"]

missing = [col for col in required if col not in df.columns]

if missing:
    raise ValueError(f"Lipsesc coloanele: {missing}")

df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)

# eliminăm doar rândurile fără valorile necesare analizei
df = df.dropna(subset=["spm72_wm2", "current_rear"])

# ------------------------------------------------------------
# 3. Analiza fiecărui segment
# ------------------------------------------------------------

results = []

for segment in ["S08-A", "S08-B", "S08-C"]:

    d = df[df["series_id"] == segment].copy()

    if len(d) < 3:
        print(f"{segment}: prea puține observații")
        continue

    x = d["spm72_wm2"].to_numpy(dtype=float)
    y = d["current_rear"].to_numpy(dtype=float)

    # Pearson
    pearson_r, pearson_p = pearsonr(x, y)

    # Spearman
    spearman_rho, spearman_p = spearmanr(x, y)

    # regresie liniară
    slope, intercept = np.polyfit(x, y, 1)

    y_pred = slope * x + intercept
    residuals = y - y_pred

    # RMSE
    rmse = np.sqrt(np.mean(residuals ** 2))

    # R²
    ss_res = np.sum(residuals ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r2 = 1 - ss_res / ss_tot

    results.append({
        "segment": segment,
        "N": len(d),
        "SPM72_min": x.min(),
        "SPM72_max": x.max(),
        "SPM72_mean": x.mean(),
        "PV_Rear_min_mA": y.min(),
        "PV_Rear_max_mA": y.max(),
        "PV_Rear_mean_mA": y.mean(),
        "Pearson_r": pearson_r,
        "Pearson_p": pearson_p,
        "Spearman_rho": spearman_rho,
        "Spearman_p": spearman_p,
        "slope": slope,
        "intercept": intercept,
        "R2": r2,
        "RMSE_mA": rmse
    })

    # ========================================================
    # Grafic 1 – SPM72 vs PV_Rear
    # ========================================================

    plt.figure(figsize=(8, 6))

    plt.scatter(x, y, s=25, alpha=0.7)

    x_line = np.linspace(x.min(), x.max(), 200)
    y_line = slope * x_line + intercept

    plt.plot(
        x_line,
        y_line,
        linewidth=2,
        label=f"Linear fit: y = {slope:.4f}x {intercept:+.2f}"
    )

    plt.xlabel("SPM72 irradiance [W/m²]")
    plt.ylabel("PV_Rear current [mA]")
    plt.title(f"{segment}: SPM72 vs PV_Rear")

    plt.grid(True, alpha=0.3)
    plt.legend()

    plt.tight_layout()

    plt.savefig(
        OUTPUT_DIR / f"{segment}_SPM72_vs_PV_Rear.png",
        dpi=300
    )

    plt.close()

    # ========================================================
    # Grafic 2 – Reziduuri
    # ========================================================

    plt.figure(figsize=(8, 5))

    plt.scatter(x, residuals, s=25, alpha=0.7)

    plt.axhline(
        0,
        linewidth=1.5
    )

    plt.xlabel("SPM72 irradiance [W/m²]")
    plt.ylabel("Residual [mA]")
    plt.title(f"{segment}: regression residuals")

    plt.grid(True, alpha=0.3)

    plt.tight_layout()

    plt.savefig(
        OUTPUT_DIR / f"{segment}_residuals.png",
        dpi=300
    )

    plt.close()

    print(
        f"{segment}: "
        f"N={len(d)}, "
        f"Pearson={pearson_r:.4f}, "
        f"Spearman={spearman_rho:.4f}, "
        f"R²={r2:.4f}, "
        f"RMSE={rmse:.3f} mA"
    )

# ------------------------------------------------------------
# 4. Salvare rezultate
# ------------------------------------------------------------

results_df = pd.DataFrame(results)

results_df.to_csv(
    OUTPUT_DIR / "S08_segment_statistics.csv",
    index=False
)

print()
print("Analiza terminată.")
print(f"Rezultatele sunt în: {OUTPUT_DIR.resolve()}")