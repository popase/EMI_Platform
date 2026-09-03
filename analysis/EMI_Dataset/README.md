# EMI Platform — Dataset Analysis

This directory contains the reproducible Python analysis pipeline used for processing and diagnosing the experimental measurement dataset of the EMI Platform.

The analysis supports the experimental validation of the EMI Platform. The smart pyranometer is the application-specific validation instrument; the analysis pipeline does not constitute a metrological characterization workflow.

## 1. Purpose

The analysis package is used to:

- load and validate the synchronized experimental measurements;
- preserve the original synchronized CSV files unchanged;
- associate each measurement series with its experimental metadata;
- generate the complete derived analysis dataset;
- generate series-level diagnostic statistics;
- generate scatter and temporal plots;
- generate descriptive reports;
- support reproducibility of the experimental data-processing workflow.

The pipeline does **not** automatically determine the calibration/validation split and does **not** refit the frozen model.

---

## 2. Experimental dataset

The final experimental dataset contains **13 measurement series** acquired between 20 and 25 August 2026.

The definitive experimental series directory is:

```text
series/
```

Each series contains:

```text
series/
  YYYYMMDD_HHMMSS/
    spm72_readings_raw.csv
    spm72_readings.csv
    emi_measurements.csv
    synchronized_measurements.csv
```

The data provenance is:

```text
Raw JPEG / OCR acquisition
        ↓
spm72_readings_raw.csv
        ↓
manual / visual OCR correction
        ↓
spm72_readings.csv
        ↓
synchronization with EMI measurements
        ↓
synchronized_measurements.csv
        ↓
analysis_dataset.csv
```

The raw OCR output is preserved unchanged. Corrected OCR values are used for the synchronized analytical data.

---

## 3. Directory structure

The analysis package is organized as follows:

```text
EMI_Dataset/
│
├── config.json
├── series_metadata.csv
├── requirements.txt
├── common.py
│
├── 01_prepare_dataset.py
├── 02_scatter_spm72_pvrear.py
├── 03_timeseries.py
├── 04_descriptive_report.py
├── 05_make_all.py
├── 06_check_input.py
├── 07_series_diagnostics.py
│
├── data/
│   ├── 20260820_091508/
│   ├── 20260820_114939/
│   ├── 20260820_151336/
│   ├── 20260821_100631/
│   ├── 20260821_115655/
│   ├── 20260821_154849/
│   ├── 20260822_163702/
│   ├── 20260824_093823/
│   ├── 20260824_120328/
│   ├── 20260824_163924/
│   ├── 20260824_174119/
│   ├── 20260825_163306/
│   ├── 20260825_173650/
│   │
│   ├── CALIBRATION/
│   │   └── S01–S07
│   │
│   └── VALIDATION/
│       └── S08-A, S08-B, S09, S10, S11
│
└── output/
    ├── dataset/
    ├── figures/
    └── reports/
```

The `data/` directory contains the complete experimental series used by the general analysis pipeline.

`CALIBRATION/` and `VALIDATION/` contain the **frozen analytical datasets established on 26 August 2026**. They must not be regenerated or modified merely because the complete experimental dataset is subsequently reprocessed.

---

## 4. Backup data

The series:

```text
20260825_173650
```

was recovered from the Raspberry Pi after an earlier repository-placement problem was identified and corrected.

The recovered files were verified against the corresponding experimental series.

This series is retained for provenance and backup purposes but is **not part of the frozen calibration or validation datasets**.

If a backup copy is retained in the repository, it should be stored outside the analysis input tree, for example:

```text
backup/
  20260825_173650/
```

It must not be placed inside a directory automatically scanned by the analysis scripts.

The frozen calibration and validation datasets remain unchanged.

---

## 5. Experimental metadata

`series_metadata.csv` associates each experimental series with:

- analytical category;
- experimental condition code;
- optional notes.

The current metadata are:

```csv
series_id,category,condition_code,notes
20260820_091508,unknown,C0,
20260820_114939,dynamic_C1,C1,isolated clouds
20260820_151336,unknown,C1,
20260821_100631,unknown,C0,
20260821_115655,unknown,C0,
20260821_154849,unknown,C0,
20260822_163702,unknown,C3,
20260824_093823,unknown,C4->C3,
20260824_120328,unknown,C0->C2,
20260824_163924,unknown,C1,
20260824_174119,unknown,,umbra
20260825_163306,local_shading,C0,local shading event
20260825_173650,unknown,C0,apus / umbra totala
```

The analytical `category` is not automatically inferred from the condition code. It represents the classification used for analysis.

Allowed categories are:

```text
stable
dynamic_C1
local_shading
unknown
```

---

## 6. Calibration and validation datasets

The frozen datasets used in the article are:

```text
data/CALIBRATION/
data/VALIDATION/
```

The corresponding frozen aggregate files are:

```text
data/calibration_dataset.csv
data/validation_dataset.csv
```

Their sizes are:

```text
Calibration: 1044 observations
Validation:   583 observations
```

The calibration dataset contains seven valid sessions:

```text
S01–S07
```

The independent validation dataset contains five valid sessions or temporal segments:

```text
S08-A
S08-B
S09
S10
S11
```

The calibration and validation split is performed by measurement day. Validation observations were not used for model estimation or model selection.

These datasets are frozen research artifacts and should not be silently regenerated or replaced.

---

## 7. Python environment

Create a virtual environment in the analysis directory:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
```

Install the required packages:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

The virtual environment is local and must not be committed to the repository.

---

## 8. Configuration

The main configuration file is:

```text
config.json
```

It defines input/output paths, column mappings, synchronization parameters, and analysis settings used by the scripts.

Series classification is maintained separately in:

```text
series_metadata.csv
```

The original measurement CSV files should not be edited by the analysis scripts.

---

## 9. Analysis scripts

### 9.1 Input check

```powershell
python 06_check_input.py
```

Checks the configured input directory, metadata and available measurement series.

### 9.2 Prepare analysis dataset

```powershell
python 01_prepare_dataset.py
```

Creates:

```text
output/dataset/analysis_dataset.csv
```

The derived dataset contains the measurement variables together with metadata and quality-control fields.

The script does not modify the source synchronized CSV files.

### 9.3 Scatter analysis

```powershell
python 02_scatter_spm72_pvrear.py
```

Generates the SPM72 versus PV-current scatter figure.

### 9.4 Temporal analysis

```powershell
python 03_timeseries.py
```

Generates temporal plots for the experimental series.

### 9.5 Descriptive analysis

```powershell
python 04_descriptive_report.py
```

Generates descriptive statistics and reports.

### 9.6 Complete basic analysis

```powershell
python 05_make_all.py
```

Runs scripts 01–04 sequentially.

### 9.7 Series diagnostics

```powershell
python 07_series_diagnostics.py
```

Generates series-level diagnostics, including:

- sample counts;
- ranges;
- temporal characteristics;
- correlation statistics;
- synchronization information;
- diagnostic figures and reports.

---

## 10. Output structure

Generated results are stored under:

```text
output/
├── dataset/
│   └── analysis_dataset.csv
│
├── figures/
│   ├── scatter_spm72_pv_rear.png
│   └── timeseries_*.png
│
└── reports/
    ├── descriptive_by_category.csv
    ├── descriptive_by_series.csv
    ├── descriptive_report.md
    └── series_diagnostics.csv
```

Generated outputs are derived artifacts. The original experimental data remain unchanged.

---

## 11. Frozen application-specific model

The analysis pipeline does not refit the article's final model automatically.

The frozen linear model identified from the calibration dataset is:

```text
G = 6.5501833853 × I − 37.5771821527
```

where:

- `G` is irradiance in W/m²;
- `I` is PV current in mA.

The coefficients were estimated using the calibration dataset only and frozen before independent validation.

The model identifier is:

```text
EMI-LIN-2026-08-26
```

---

## 12. Frozen validation results

The independent validation dataset contains:

```text
N = 583
```

The frozen validation results reported in the article are:

```text
MAE      = 25.67 W/m²
RMSE     = 36.07 W/m²
MBE      =  4.44 W/m²
R²       =  0.9791
Pearson r = 0.9904
```

These values constitute frozen article results and should be treated as reference values when auditing reproducibility.

---

## 13. Methodological boundaries

The scripts intentionally do **not**:

- fit a new calibration model automatically;
- change the frozen calibration/validation split;
- modify original measurement files;
- replace OCR values with estimated values;
- smooth the PV-current measurements;
- automatically exclude variable measurement series;
- interpret experimental condition codes as analytical categories.

Decisions concerning session validity, calibration/validation selection, model selection and model freezing are methodological research decisions and are maintained separately from the generic data-processing scripts.

---

## 14. Reproducibility principle

The intended reproducibility chain is:

```text
Experimental acquisition
        ↓
Raw OCR data
        ↓
Corrected OCR data
        ↓
Synchronized measurements
        ↓
Derived analysis dataset
        ↓
Series diagnostics / descriptive analysis
        ↓
Frozen calibration and validation datasets
        ↓
Application-specific model
        ↓
Independent validation
```

The repository distinguishes between:

1. **raw experimental evidence**;
2. **derived analysis data**;
3. **frozen research datasets**;
4. **derived analytical results**.

This separation is maintained to preserve traceability and prevent accidental modification of the datasets underlying the reported results.

---

## 15. Reproduction sequence

For a clean reproduction of the general analysis pipeline:

```powershell
python 06_check_input.py
python 01_prepare_dataset.py
python 02_scatter_spm72_pvrear.py
python 03_timeseries.py
python 04_descriptive_report.py
python 07_series_diagnostics.py
```

or:

```powershell
python 05_make_all.py
python 07_series_diagnostics.py
```

The frozen calibration and validation datasets are then used for reproduction of the reported application-specific model and validation results.

---

## 16. Scope

This package documents the data-processing workflow supporting the experimental validation of the EMI Platform.

The primary scientific contribution of the associated study is the EMI Platform architecture and its separation of application-specific measurement functionality from reusable platform services. The smart pyranometer and its calibration model constitute the application-specific experimental validation of that architecture.