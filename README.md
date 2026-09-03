# EMI Platform

Repository accompanying the research article:

**EMI Platform: A Modular Embedded Measurement Architecture for Industrial SCADA Systems**

## 1. Purpose and scope

This repository contains the implementation, experimental data, and analysis software supporting the experimental evaluation of the **EMI Platform**.

The EMI Platform is the primary contribution of the associated study. The smart pyranometer is an application-specific implementation used to validate the platform; it is not the primary architectural contribution.

The demonstrated experimental system integrates:

- an Arduino Uno-based EMI Node;
- RS485 / Modbus RTU communication;
- a Raspberry Pi-based EMI Gateway;
- Node-RED for data acquisition and supervisory integration;
- SQLite data storage;
- Grafana visualization.

## 2. Repository structure

The current repository is organized as follows:

```text
EMI_Platform/
├── README.md
├── .gitattributes
├── series/
│   └── 13 experimental measurement series
├── gateway/
│   └── FSM/
│       ├── spm72_control.py
│       ├── spm72_ocr.py
│       └── sync_series.py
├── analysis/
│   └── EMI_Dataset/
│       ├── config.json
│       ├── series_metadata.csv
│       ├── requirements.txt
│       ├── common.py
│       ├── 01_prepare_dataset.py
│       ├── 02_scatter_spm72_pvrear.py
│       ├── 03_timeseries.py
│       ├── 04_descriptive_report.py
│       ├── 05_make_all.py
│       ├── 06_check_input.py
│       ├── 07_series_diagnostics.py
│       ├── data/
│       └── output/
└── firmware/
    └── EMI_Node/
        └── EMI_Node.ino
```

### `series/`

Contains the 13 experimental measurement series used for the article. The series preserve the measurement files generated and processed during the experimental campaign.

Each final series follows the established structure:

```text
series/YYYYMMDD_HHMMSS/
├── spm72_readings_raw.csv
├── spm72_readings.csv
├── emi_measurements.csv
└── synchronized_measurements.csv
```

The final series correspond to the experimental campaign conducted between 20 and 25 August 2026.

### `gateway/FSM/`

Contains the Raspberry Pi-side scripts used for the experimental acquisition workflow:

- `spm72_control.py` — measurement control and series generation;
- `spm72_ocr.py` — SPM72 OCR acquisition;
- `sync_series.py` — synchronization of SPM72 and EMI measurements.

### `analysis/EMI_Dataset/`

Contains the Python analysis environment used to process and diagnose the experimental dataset. Its internal directory structure is part of the reproducibility setup and should be preserved.

The detailed analysis-specific instructions are provided in:

```text
analysis/EMI_Dataset/README.md
```

### `firmware/EMI_Node/`

Contains the Arduino firmware used by the experimental EMI Node:

```text
firmware/EMI_Node/EMI_Node.ino
```

The firmware implements sensor acquisition and exposure of measurement values through RS485 / Modbus RTU.

## 3. Experimental data provenance

The repository preserves the experimental data-processing chain from acquisition to synchronized measurements:

```text
Raw JPEG images
      │
      ▼
spm72_readings_raw.csv
      │
      │ visual/manual OCR verification
      ▼
spm72_readings.csv
      │
      │ synchronization with EMI measurements
      ▼
synchronized_measurements.csv
      │
      ▼
analysis dataset
      │
      ├── calibration dataset
      └── validation dataset
```

The raw OCR files are retained as acquired. Corrected OCR values are stored separately and are used for the synchronized analytical data.

## 4. Frozen experimental datasets

The final analytical datasets used by the article are frozen research artifacts.

### Calibration

- Series: **S01–S07**
- Observations: **1044**
- Measurement period: **20–22 August 2026**

### Independent validation

- Series/segments: **S08-A, S08-B, S09, S10, S11**
- Observations: **583**
- Measurement date: **24 August 2026**

The validation observations were not used for model estimation or model selection.

The analysis package contains both the complete experimental-series input data and the frozen calibration/validation datasets. The frozen datasets must not be silently regenerated or replaced.

## 5. Application-specific measurement model

For the smart-pyranometer validation application, PV current is used as the predictor and the SPM72 measurement as the reference response.

The selected model is linear:

```text
G = 6.5501833853 × I − 37.5771821527
```

where:

- `I` is PV current in mA;
- `G` is estimated irradiance in W/m².

The coefficients were estimated by ordinary least squares using the calibration dataset only and were frozen before independent validation.

Model identifier:

```text
EMI-LIN-2026-08-26
```

The model is application-specific; it is not part of the reusable core EMI Platform services.

## 6. Independent validation result

For the frozen independent validation dataset (`N = 583`):

| Metric | Result |
|---|---:|
| MAE | 25.67 W/m² |
| RMSE | 36.07 W/m² |
| MBE | 4.44 W/m² |
| Pearson r | 0.9904 |
| R² | 0.9791 |

These values are the frozen validation results reported in the article.

## 7. Reproduction workflow

For reproduction of the general data-analysis workflow:

1. Clone the repository.
2. Preserve the repository directory structure.
3. Enter `analysis/EMI_Dataset/`.
4. Create the Python environment described in `analysis/EMI_Dataset/README.md`.
5. Verify `config.json` and the configured input/output paths.
6. Run the input check.
7. Run the analysis pipeline and series diagnostics.
8. Compare the resulting derived data and diagnostics with the repository contents and frozen research datasets.

The main analysis sequence is:

```powershell
python 06_check_input.py
python 01_prepare_dataset.py
python 02_scatter_spm72_pvrear.py
python 03_timeseries.py
python 04_descriptive_report.py
python 07_series_diagnostics.py
```

Alternatively:

```powershell
python 05_make_all.py
python 07_series_diagnostics.py
```

The analysis scripts use repository-relative paths defined through `config.json`; they do not modify the source synchronized measurement files.

The final application-specific model is treated as a frozen research result rather than being automatically refitted by the generic analysis pipeline.

## 8. Reproducibility boundary

The repository provides the implementation and experimental data required to inspect and reproduce the reported data-processing workflow and to verify the frozen analytical datasets and validation results.

The repository does **not** claim experimental validation of the EMI Platform across multiple independent instrument types, alternative MCU families, or multi-node deployments. Such extensions are outside the present experimental validation scope.

Remote device configuration is not part of the implemented experimental prototype and is outside the scope of the present implementation.

## 9. Experimental architecture

The demonstrated system follows this data path:

```text
EMI Node
   │
   │ RS485 / Modbus RTU
   ▼
EMI Gateway
   │
   ▼
Node-RED / SQLite
   │
   ▼
Grafana
```

The SPM72 reference instrument, USB UVC microscope, and OCR processing belong to the application-specific validation layer.

The reusable platform services are therefore distinguishable from the application-specific measurement and validation functionality.

## 10. Traceability

The repository distinguishes four levels of research artifacts:

1. **Raw experimental evidence** — acquired images and raw OCR output;
2. **Corrected and synchronized measurements** — processed measurement files associated with each experimental series;
3. **Frozen analytical datasets** — calibration and independent validation datasets used for the reported model and validation;
4. **Derived analytical results** — diagnostics, figures, reports, and validation metrics.

This separation is intended to preserve traceability between the experimental campaign, the data-processing workflow, and the results reported in the article.

## 11. Scientific scope

The associated study evaluates the **EMI Platform architecture** and its separation of reusable platform services from application-specific measurement functionality.

The smart pyranometer provides the experimental validation case through which the architecture is demonstrated and quantitatively evaluated. The repository should therefore be interpreted primarily as a reproducibility package for the EMI Platform study, not as a standalone pyranometer or metrological-characterization project.