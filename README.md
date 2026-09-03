# EMI Platform

Repository accompanying the research article:

**EMI Platform: A Modular Embedded Measurement Architecture for Industrial SCADA Systems**

## 1. Overview

This repository contains the software, experimental data, analysis workflow, and firmware associated with the experimental evaluation of the **EMI Platform**, a modular embedded architecture for intelligent measurement instruments.

The repository supports the reproducibility of the experimental results reported in the article. The smart pyranometer is used as an application-specific experimental implementation of the platform; it is not the primary contribution of the work.

The demonstrated system integrates:

- an Arduino Uno-based EMI Node;
- RS485/Modbus RTU industrial communication;
- a Raspberry Pi-based EMI Gateway;
- Node-RED-based data acquisition and storage;
- SQLite data storage;
- Grafana-based supervisory visualization.

---

## 2. Repository structure

```text
EMI_Platform/
├── README.md
├── series/
├── gateway/
│   └── FSM/
├── analysis/
│   └── EMI_Dataset/
└── firmware/
```

### `series/`

Contains the 13 experimental measurement series retained for the article.

Each experimental series contains the recorded image data and associated measurement files used in the data-processing chain.

### `gateway/FSM/`

Contains the Raspberry Pi gateway-side measurement-control and data-processing scripts used during the experimental campaign:

- `spm72_control.py`
- `spm72_ocr.py`
- `sync_series.py`

### `analysis/EMI_Dataset/`

Contains the reproducible data-analysis environment, including configuration, common utilities, analysis scripts, input data, and generated outputs.

The internal directory structure is preserved so that the relative paths used by the analysis scripts remain valid.

### `firmware/`

Contains the firmware used by the experimental EMI Node.

---

## 3. Experimental data provenance

The raw experimental data are preserved before correction, screening, synchronization, or model fitting.

The data-processing provenance is:

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
analytical datasets
      │
      ├── calibration_dataset.csv
      └── validation_dataset.csv
      │
      ▼
model fitting and independent validation
```

Raw measurements are not modified during analytical processing. Screening and segmentation are applied only to derived analytical datasets.

---

## 4. Calibration and validation

The analytical datasets are frozen.

### Calibration dataset

- Series: S01–S07
- Measurement dates: 20–22 August 2026
- Observations: **1044**

### Independent validation dataset

- Series: S08-A, S08-B, S09, S10, S11
- Measurement date: 24 August 2026
- Observations: **583**

The validation day was kept independent from model estimation. Validation observations were not used for fitting or model selection.

---

## 5. Frozen measurement model

The application-specific irradiance model uses PV current as predictor and the SPM72 reference measurement as response.

The selected model is linear:

```text
G = 6.550 I − 37.577
```

where:

- `I` is the PV current in mA;
- `G` is the estimated irradiance in W/m².

The model was estimated by ordinary least squares using the calibration dataset only and was frozen before independent validation.

Model identifier:

```text
EMI-LIN-2026-08-26
```

The complete frozen coefficients are preserved in the model artifact.

---

## 6. Independent validation result

For the independent validation dataset (`N = 583`):

| Metric | Result |
|---|---:|
| MAE | 25.67 W/m² |
| RMSE | 36.07 W/m² |
| MBE | 4.44 W/m² |
| Pearson r | 0.990 |
| R² | 0.979 |

These values correspond to the frozen model and dataset versions included in the repository.

---

## 7. Reproduction workflow

A clean reproduction of the analytical results should follow this order:

1. Clone the repository.
2. Preserve the repository directory structure.
3. Enter `analysis/EMI_Dataset/`.
4. Verify the paths defined in `config.json`.
5. Ensure the required Python dependencies are installed.
6. Run the analysis scripts in their documented order.
7. Verify the generated datasets and reports.
8. Verify the frozen calibration/validation split.
9. Verify the frozen model coefficients.
10. Compare the generated validation metrics with the reported results.

The analysis scripts use the repository-relative data structure defined by `config.json` and the shared utilities in `common.py`.

---

## 8. Reproducibility boundary

The repository provides the data and software required to reproduce the reported analytical results and to inspect the experimental data-processing chain.

The repository does not claim that the platform has been experimentally demonstrated across multiple independent instrument types, alternative MCU families, or multi-node deployments. These are architectural objectives and future extensions of the EMI Platform.

Remote device configuration is not part of the implemented experimental prototype.

---

## 9. Experimental implementation

The experimental platform consists of:

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
Grafana supervisory visualization
```

The SPM72 reference pyranometer and the associated OCR processing belong to the application-specific experimental validation layer.

The Raspberry Pi OCR system uses a **USB UVC microscope** for image acquisition.

---

## 10. Scope

This repository is intended to provide transparent access to the implementation and data supporting the research article.

The scientific contribution is the **EMI Platform architecture and its separation of application-specific measurement functionality from reusable platform services**. The smart pyranometer is the experimental validation application.