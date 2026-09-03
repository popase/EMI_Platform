# EMI Platform — Reproducibility Repository

This repository contains the software, experimental data, analysis scripts, and derived datasets supporting the research article on the **EMI Platform**, a modular embedded architecture for intelligent measurement instruments.

The repository is intended to support **experimental reproducibility, data provenance, and traceability** of the reported results.

The primary scientific contribution is the **EMI Platform architecture**, which separates reusable platform services from application-specific measurement functionality. The smart pyranometer is used as the experimental application through which the platform is instantiated and validated.

---

## 1. Repository scope

The repository covers the experimental data and software path supporting the study:

```text
experimental acquisition
        ↓
raw measurement data
        ↓
OCR correction / data preparation
        ↓
offline temporal synchronization
        ↓
analytical screening and segmentation
        ↓
calibration / validation datasets
        ↓
application-specific model fitting
        ↓
frozen model
        ↓
independent validation
        ↓
reported results
```

Raw experimental data are preserved separately from derived analytical datasets.

The repository distinguishes between:

- experimental source data;
- platform and gateway software;
- firmware;
- analytical scripts;
- frozen calibration and validation datasets;
- derived analytical results.

---

## 2. Repository structure

```text
EMI_Platform/
│
├── series/
│   └── final experimental measurement series
│
├── gateway/
│   └── FSM/
│       ├── spm72_control.py
│       ├── spm72_ocr.py
│       └── sync_series.py
│
├── firmware/
│   └── EMI_Node/
│       └── EMI_Node.ino
│
├── analysis/
│   └── EMI_Dataset/
│       ├── 01_prepare_dataset.py
│       ├── 02_scatter_spm72_pvrear.py
│       ├── 03_timeseries.py
│       ├── 04_descriptive_report.py
│       ├── 05_make_all.py
│       ├── 06_check_input.py
│       ├── 07_series_diagnostics.py
│       ├── common.py
│       ├── config.json
│       ├── series_metadata.csv
│       ├── requirements.txt
│       ├── README.md
│       ├── data/
│       └── output/
│
├── supplementary/
│
├── backup/
│   └── archived experimental data not used by the analysis pipeline
│
└── README.md
```

The local Python virtual environment (`.venv/`) is not part of the repository and must not be committed.

---

## 3. Experimental platform

The experimental implementation consists of:

- **EMI Node:** Arduino Uno-based embedded measurement node;
- **EMI Gateway:** Raspberry Pi-based gateway;
- **Communication:** RS485 using Modbus RTU;
- **Supervisory environment:** Node-RED and Grafana;
- **Persistent storage:** SQLite;
- **Application:** prototype smart pyranometer;
- **Reference instrument:** SPM72 reference pyranometer.

The EMI Node, gateway, communication, storage, and supervisory components form the platform infrastructure.

The irradiance measurement relationship is application-specific and is used to validate the platform through the smart-pyranometer application.

The SPM72 is a reference instrument used for this application-level validation.

---

## 4. Experimental series

The final experimental dataset contains **13 measurement series**, acquired between 20 and 25 August 2026:

```text
20260820_091508
20260820_114939
20260820_151336
20260821_100631
20260821_115655
20260821_154849
20260822_163702
20260824_093823
20260824_120328
20260824_163924
20260824_174119
20260825_163306
20260825_173650
```

Each final series contains:

```text
series/
  YYYYMMDD_HHMMSS/
    spm72_readings_raw.csv
    spm72_readings.csv
    emi_measurements.csv
    synchronized_measurements.csv
```

The four files represent different stages of the experimental data path:

- `spm72_readings_raw.csv` — direct OCR output, preserved unchanged;
- `spm72_readings.csv` — corrected OCR data;
- `emi_measurements.csv` — EMI Node measurements;
- `synchronized_measurements.csv` — temporally synchronized measurements used by the analysis pipeline.

The original experimental files are not modified by the analytical scripts.

---

## 5. Archived backup series

The series:

```text
20260825_173650
```

was initially suspected to be a duplicate of another measurement series.

The original Raspberry Pi files were subsequently recovered and verified. The recovered data correspond to the actual 25 August 2026 measurement session and are therefore retained as a valid experimental record.

The series is **not part of the frozen calibration or validation datasets** and is excluded from the current analytical model workflow.

If archived separately, it should be stored outside the directory automatically scanned by the analysis scripts, for example:

```text
backup/
  20260825_173650/
```

This preserves the experimental record without allowing the archived series to enter the analytical pipeline unintentionally.

---

## 6. Data synchronization

SPM72 readings were acquired through a USB UVC microscope and OCR process running on the Raspberry Pi.

The SPM72 acquisition interval was approximately 30 s.

The EMI Node generated timestamped measurement records in UTC.

The two streams were synchronized offline using nearest-neighbour temporal matching with a maximum permitted difference of:

```text
±15 s
```

The synchronization procedure is implemented in:

```text
gateway/FSM/sync_series.py
```

The synchronized dataset retains the original timestamps and records the temporal difference between matched observations.

---

## 7. Gateway and FSM software

The `gateway/FSM/` directory contains the software used to operate and coordinate the experimental acquisition workflow.

### `spm72_ocr.py`

Acquires images of the SPM72 display and extracts irradiance values using OCR.

Processing path:

```text
USB UVC microscope
        ↓
image acquisition
        ↓
image preprocessing
        ↓
ssocr
        ↓
SPM72 irradiance reading
```

### `spm72_control.py`

Implements the finite-state-machine workflow used during the experimental acquisition.

Principal states:

```text
IDLE
OCR CHECK
EMI NODE CHECK
MEASUREMENT
STOP
```

The EMI Node check verifies availability of the operational measurement data path through the SQLite database.

### `sync_series.py`

Performs offline nearest-neighbour temporal synchronization between the SPM72 and EMI Node measurement streams.

---

## 8. EMI Node firmware

The `firmware/EMI_Node/` directory contains the Arduino firmware used by the experimental EMI Node.

The firmware implements:

- measurement acquisition;
- sensor interfacing;
- local measurement handling;
- RS485 communication;
- Modbus RTU communication with the EMI Gateway.

The application-specific measurement functionality is implemented within the instrument-specific part of the EMI Node, while common communication and platform services remain reusable.

---

## 9. Analysis pipeline

The reproducible analysis pipeline is located in:

```text
analysis/EMI_Dataset/
```

The package provides scripts for:

- input verification;
- dataset preparation;
- descriptive statistics;
- series-level diagnostics;
- scatter analysis;
- temporal analysis;
- generation of derived analytical outputs.

Detailed instructions are provided in:

```text
analysis/EMI_Dataset/README.md
```

The required Python packages are specified in:

```text
analysis/EMI_Dataset/requirements.txt
```

---

## 10. Analytical dataset

The analysis pipeline creates a derived dataset from the synchronized experimental series:

```text
analysis/EMI_Dataset/output/dataset/analysis_dataset.csv
```

The derived dataset contains:

- series identifier;
- source file and row information;
- timestamps;
- SPM72 irradiance;
- PV current;
- synchronization information;
- experimental metadata;
- quality-control flags.

The derived dataset does not modify the original experimental files.

The complete current experimental input comprises the 13 final measurement series.

---

## 11. Calibration and validation

The calibration and validation datasets used for the reported model are frozen analytical artifacts.

### Calibration

```text
N = 1044 observations
```

The calibration data comprise the analytical sessions:

```text
S01
S02
S03
S04
S05
S06
S07
```

### Independent validation

```text
N = 583 observations
```

The independent validation data comprise:

```text
S08-A
S08-B
S09
S10
S11
```

Calibration and validation are separated by measurement day.

Validation observations were not used for model estimation or model selection.

The frozen datasets are retained as:

```text
analysis/EMI_Dataset/data/calibration_dataset.csv
analysis/EMI_Dataset/data/validation_dataset.csv
```

They should not be silently regenerated or replaced during routine repository maintenance.

---

## 12. Application-specific measurement model

The application-specific measurement relationship is a linear model between PV current and reference irradiance:

```text
G = 6.5501833853 × I − 37.5771821527
```

where:

- `I` is PV current in mA;
- `G` is estimated irradiance in W/m².

The coefficients were estimated by ordinary least squares using the calibration dataset only.

The coefficients were frozen before independent validation.

No validation observation was used for model estimation or model selection.

The frozen model identifier is:

```text
EMI-LIN-2026-08-26
```

The linear formulation was retained because the quadratic alternative provided only a marginal improvement while requiring an additional parameter.

---

## 13. Frozen validation results

For the independent validation dataset:

```text
N = 583
```

the frozen model produced:

| Metric | Validation |
|---|---:|
| MAE | 25.67 W/m² |
| RMSE | 36.07 W/m² |
| MBE | 4.44 W/m² |
| R² | 0.9791 |
| Pearson r | 0.9904 |

These results represent application-level validation of the implemented measurement functionality.

They are not intended as a complete metrological characterization of the smart pyranometer or the SPM72 reference instrument.

---

## 14. Communication endurance

The implemented RS485/Modbus RTU communication path was evaluated during an approximately three-hour endurance test.

Recorded result:

```text
Requests:             10,586
Successful:           10,585
Timeouts:                  1
Observed CRC errors:       0
Success rate:          99.99%
```

This result characterizes the implemented communication path under the tested experimental conditions. It is not presented as a general reliability characterization of the EMI Platform.

---

## 15. Reproducibility principles

The repository follows these principles:

1. **Raw experimental measurements are preserved unchanged.**
2. Analytical processing operates on derived data.
3. Calibration and validation are separated before model fitting.
4. Validation data are not used for model estimation or selection.
5. Model coefficients are frozen before validation.
6. Excluded observations are not repaired and silently reintroduced.
7. Archived backup data are kept outside the automatic analysis input path.
8. Application-specific measurement functionality is distinguished from reusable EMI Platform services.
9. Reuse, portability, and scalability are treated as architectural objectives unless experimentally demonstrated.

---

## 16. Reproduction workflow

A complete reproduction should follow this sequence:

```text
1. Inspect the experimental series
        ↓
2. Inspect gateway/FSM software
        ↓
3. Install Python dependencies
        ↓
4. Verify the analysis input
        ↓
5. Generate the derived analysis dataset
        ↓
6. Generate descriptive and diagnostic results
        ↓
7. Use the frozen calibration dataset
        ↓
8. Reproduce the frozen model
        ↓
9. Evaluate the model on the frozen validation dataset
        ↓
10. Compare reproduced metrics with the reported results
```

The validation dataset must remain independent throughout the reproduction process.

---

## 17. Repository limitations

The repository supports reproduction of the reported experimental implementation and analytical results.

The present study does not experimentally establish:

- reuse across multiple independent instrument types;
- portability across alternative microcontroller families;
- long-term multi-node scalability;
- general reliability under broader industrial operating conditions;
- complete metrological characterization of the smart pyranometer.

These topics remain outside the demonstrated experimental scope.

---

## 18. Relation to the research article

The repository supports the experimental material reported in the manuscript, including:

- EMI Platform architecture;
- EMI Node firmware;
- EMI Gateway and FSM;
- RS485/Modbus RTU communication;
- measurement data acquisition;
- synchronization;
- calibration procedure;
- SCADA integration;
- communication endurance;
- application-specific model fitting;
- independent validation.

The smart pyranometer provides the application through which the EMI Platform is experimentally validated.

The principal contribution remains the **EMI Platform architecture and the separation between reusable platform services and application-specific measurement functionality**.