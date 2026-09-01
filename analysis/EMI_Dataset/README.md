# EMI Platform — Dataset Analysis (Windows)

Purpose:
- preserve raw synchronized CSV files unchanged;
- classify measurement series as `stable`, `dynamic_C1`, or `local_shading`;
- generate two diagnostics:
  1. SPM72 vs PV_Rear scatter;
  2. temporal evolution for dynamic/stable/shading series;
- generate descriptive CSV/Markdown reports;
- keep every analysis independent so one plot can be changed without regenerating the rest.

## 1. Folder structure

Put the package next to your data:

```text
emi_dataset_analysis_windows/
  config.json
  series_metadata.csv
  requirements.txt
  common.py
  01_prepare_dataset.py
  02_scatter_spm72_pvrear.py
  03_timeseries.py
  04_descriptive_report.py
  05_make_all.py
  data/
    20260819_152149/
      synchronized_measurements.csv
    20260820_114939/
      synchronized_measurements.csv
    20260825_163306/
      synchronized_measurements.csv
```

The scripts also accept a different input directory through `config.json`.

## 2. Install Python packages

Open PowerShell in this directory:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 3. Configure

Edit only:

- `config.json` for column names, input/output directories and plotting defaults;
- `series_metadata.csv` for the experimental classification.

The raw CSV files are never edited.

## 4. Classification metadata

Example:

```csv
series_id,category,condition_code,notes
20260825_163306,local_shading,,local shading event
20260820_114939,dynamic_C1,C1,isolated clouds
20260824_120000,dynamic_C1,C2,rapid cloud variability
```

Allowed categories:

- `stable`
- `dynamic_C1`
- `local_shading`
- `unknown`

Do not use `unknown` in final article figures unless deliberately retained as an unclassified dataset.

## 5. Run independently

Prepare a clean analysis dataset:

```powershell
python 01_prepare_dataset.py
```

Scatter only:

```powershell
python 02_scatter_spm72_pvrear.py
```

Temporal plots only:

```powershell
python 03_timeseries.py
```

Descriptive report only:

```powershell
python 04_descriptive_report.py
```

Everything:

```powershell
python 05_make_all.py
```

## 6. Important methodological rule

`01_prepare_dataset.py` creates a derived analysis table. It does NOT modify the original synchronized files.

The derived table contains:

- original series;
- category;
- source row;
- timestamps;
- SPM72;
- PV_Rear;
- available synchronization information;
- QC flags.

No calibration model is fitted by these scripts.

## 7. Flexible CSV input

The loader searches for:

```text
synchronized_measurements.csv
```

inside each series directory.

If your actual column names differ, change only `config.json`.

The loader is intentionally tolerant of common names such as:

- `spm72_wm2`, `SPM72`, `SPM72_Wm2`
- `pv_rear`, `PV_Rear`, `PVRear`
- `timestamp`, `timestamp_utc`

For exact/unknown formats, add aliases in `config.json`.

## 8. Outputs

```text
output/
  dataset/
    analysis_dataset.csv
  figures/
    scatter_spm72_pv_rear.png
    timeseries_*.png
  reports/
    descriptive_by_category.csv
    descriptive_by_series.csv
    descriptive_report.md
```

The figures are saved as high-resolution PNG (300 dpi) and can be regenerated individually.

## 9. Design choice

The scripts intentionally do NOT:
- fit a calibration equation;
- remove dynamic data automatically;
- replace OCR errors with estimates;
- smooth PV_Rear;
- discard a series because it is variable.

Those are later methodological decisions.
