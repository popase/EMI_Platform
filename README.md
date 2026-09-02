# EMI Platform — Reproducibility Repository

This repository contains the software, experimental data, analysis scripts, and derived datasets supporting the research article on the **EMI Platform**, a modular embedded architecture for intelligent measurement instruments.

The repository is intended to support **experimental reproducibility and data traceability** for the reported results.

The scientific contribution of the work is the EMI Platform architecture, which separates application-specific measurement functionality from reusable platform services. The smart pyranometer is used as the experimental application through which the architecture is instantiated and validated. It is not the primary contribution of the work.

---

## 1. Repository scope

The repository covers the complete experimental data path:

```text
raw acquisition
      ↓
offline synchronization
      ↓
validity screening / segmentation
      ↓
calibration and validation datasets
      ↓
application-specific model fitting
      ↓
frozen model
      ↓
independent validation
      ↓
reported results
```

Raw experimental measurements are preserved unchanged. Screening, segmentation, and exclusion are applied only to derived analytical datasets.

---

## 2. Repository structure

```text
EMI_Platform/
│
├── raw_series/
│   └── <experimental measurement series>
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
└── README.md
```

The repository may also contain `.gitignore` and `.gitkeep` files used to preserve the intended directory structure without committing local or intermediate content.

---

## 3. Experimental platform

The experimental implementation consists of:

- **EMI Node:** Arduino Uno-based embedded measurement node.
- **EMI Gateway:** Raspberry Pi-based gateway.
- **Communication:** RS485 using Modbus RTU.
- **Supervisory environment:** Node-RED and Grafana.
- **Persistent storage:** SQLite.
- **Application:** prototype smart pyranometer.
- **Reference instrument:** SPM72 reference pyranometer.

The reference pyranometer is used exclusively for application-level measurement validation and is not part of the EMI Platform architecture.

The platform provides the common acquisition, communication, gateway, storage, and supervisory infrastructure, while the irradiance measurement relationship belongs to the application-specific functionality of the instrument.

---

## 4. Raw experimental data

The `raw_series/` directory contains the experimental measurement series retained for the article.

The repository contains the following 13 raw series:

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

Raw data must not be modified during analytical processing.

Two series are excluded from the final calibration/validation datasets:

- `20260825_163306` — excluded according to the predefined analytical decisions.
- `20260825_173650` — excluded as a duplicate of `20260820_091508`.

The excluded raw series remain archived so that the original experimental record is preserved.

---

## 5. Calibration and validation datasets

The final analytical split is fixed before model fitting.

### Calibration

Calibration uses seven valid analytical sessions:

```text
S01
S02
S03
S04
S05
S06
S07
```

These sessions were acquired during **20–22 August 2026**.

Total:

```text
N = 1044 synchronized observations
```

### Independent validation

Validation uses the following valid sessions or temporal segments:

```text
S08-A
S08-B
S09
S10
S11
```

These data were acquired on **24 August 2026**, which is a separate measurement day from calibration.

Total:

```text
N = 583 synchronized observations
```

The validation observations were not used for model estimation or model selection.

For `20260824_093823`, the analytical segmentation is:

```text
S08-A   VALID
S08-B   VALID / dynamic
S08-C   EXCLUDED
```

Excluded observations are not repaired or reintroduced into the analytical datasets.

---

## 6. Synchronization procedure

Reference measurements from the SPM72 were acquired using the Raspberry Pi USB UVC microscope/OCR subsystem at approximately 30 s intervals.

The EMI Node generated timestamped measurement records in UTC.

The two data streams were synchronized offline using **nearest-neighbour temporal matching** with a maximum permitted difference of:

```text
±15 s
```

Only valid OCR observations satisfying the synchronization criterion were retained.

The synchronization procedure is implemented in:

```text
gateway/FSM/sync_series.py
```

The synchronization process preserves the original timestamps and records the temporal difference between the matched observations.

---

## 7. Gateway/FSM software

The `gateway/FSM/` directory contains the software used to orchestrate the experimental acquisition workflow.

### `spm72_ocr.py`

Standalone OCR acquisition utility for the SPM72 display.

Its processing path is:

```text
USB UVC microscope
   ↓
image capture on Raspberry Pi
   ↓
image preprocessing
   ↓
ssocr
   ↓
SPM72 irradiance value
```

The acquisition interval used in the experiment was approximately 30 s.

### `spm72_control.py`

Finite-state-machine controller for the experimental measurement workflow.

The principal states are:

```text
IDLE
OCR CHECK
EMI NODE CHECK
MEASUREMENT
STOP
```

The EMI Node check verifies end-to-end data-path availability through the operational SQLite database. It should not be interpreted as a direct Modbus protocol test.

### `sync_series.py`

Offline synchronization utility implementing the nearest-neighbour matching procedure described above.

---

## 8. EMI Node firmware

The `firmware/EMI_Node/` directory contains the Arduino firmware used by the experimental EMI Node.

The firmware is provided as the experimental implementation rather than as a reconstructed or simplified example.

The firmware is responsible for measurement acquisition and communication of the instrument data through the RS485/Modbus RTU interface.

The application-specific measurement functionality is implemented within the EMI Node, while the common platform services are intended to remain independent of the particular measurement application.

---

## 9. Analysis environment

The main analysis code is located in:

```text
analysis/EMI_Dataset/
```

The analysis environment uses Python and the dependencies specified in:

```text
analysis/EMI_Dataset/requirements.txt
```

The analysis scripts cover:

- input checking;
- dataset preparation;
- descriptive statistics;
- series-level diagnostics;
- time-series inspection;
- reference-versus-PV analysis;
- generation of analysis outputs.

The analysis workflow must use the frozen calibration and validation definitions described in this repository.

---

## 10. Application-specific measurement model

The final application-specific model is a two-parameter linear relationship between PV current and reference irradiance:

```text
G = 6.550 I − 37.577
```

where:

- `I` is the PV sensing current in mA;
- `G` is the estimated irradiance in W/m².

The coefficients were estimated using **ordinary least squares exclusively on the calibration dataset**.

The coefficients were frozen before processing the independent validation dataset.

No validation observation was used for model estimation or model selection.

The frozen model identifier is:

```text
EMI-LIN-2026-08-26
```

The linear model was selected instead of the quadratic candidate because the quadratic formulation provided only a marginal RMSE improvement while requiring an additional parameter.

---

## 11. Frozen validation results

The independent validation dataset contains:

```text
N = 583 observations
```

The frozen linear model achieved:

| Metric | Validation |
|---|---:|
| MAE | 25.67 W/m² |
| RMSE | 36.07 W/m² |
| MBE | 4.44 W/m² |
| R² | 0.9791 |
| Pearson r | 0.9904 |

These results represent **application-level validation** of the implemented measurement function.

They do not constitute a complete metrological characterization of the smart pyranometer or of the SPM72 reference instrument.

---

## 12. Communication endurance result

The implemented RS485/Modbus RTU communication path was evaluated during an approximately three-hour endurance test.

The recorded result was:

```text
Requests:          10,586
Successful:        10,585
Timeouts:               1
Observed CRC errors:    0
Success rate:       99.99%
```

This result demonstrates stable operation of the implemented communication path under the tested experimental conditions. It is not intended as a general reliability characterization of the EMI Platform.

---

## 13. Reproducibility principles

The following rules define the analytical provenance of the reported results:

1. **Raw measurements are immutable.**
2. Analytical screening and segmentation are performed only on derived data.
3. Calibration and validation are separated by measurement day.
4. Validation observations are never used for model fitting or model selection.
5. The final model coefficients are frozen before validation.
6. Excluded observations are not repaired and reintroduced into the analytical datasets.
7. The application-specific measurement model is distinct from the reusable EMI Platform services.
8. Reuse, portability, and scalability are architectural objectives and are not claimed as experimentally demonstrated results in this study.

---

## 14. Reproduction order

For a complete reproduction of the analytical workflow, follow this order:

```text
1. Inspect raw_series/
        ↓
2. Inspect gateway/FSM/
        ↓
3. Install analysis dependencies
        ↓
4. Prepare / verify synchronized datasets
        ↓
5. Apply the frozen calibration/validation split
        ↓
6. Run descriptive and diagnostic analysis
        ↓
7. Reproduce the frozen linear model
        ↓
8. Evaluate the model on validation_dataset.csv
        ↓
9. Compare the reproduced metrics with the frozen results
```

The validation dataset must remain independent throughout the reproduction process.

---

## 15. Traceability

The repository is organized so that the principal evidence chain can be followed as:

```text
Raw experimental series
        │
        ▼
SPM72 OCR + EMI Node acquisition
        │
        ▼
Offline temporal synchronization
        │
        ▼
Validity screening / segmentation
        │
        ├──────────────► Calibration dataset (N=1044)
        │                         │
        │                         ▼
        │                  Model estimation
        │                         │
        │                         ▼
        │                  Frozen coefficients
        │                         │
        │                         ▼
        └──────────────► Validation dataset (N=583)
                                  │
                                  ▼
                           Independent validation
```

This structure separates the **platform-level experimental evidence** from the **application-specific measurement model** used to validate the platform.

---

## 16. Scope and limitations

The repository supports reproduction of the experimental implementation and the reported analytical results.

The present study does not experimentally establish:

- reuse across multiple independent instrument types;
- portability across alternative microcontroller families;
- long-term multi-node scalability;
- general reliability under broader industrial operating conditions;
- complete metrological characterization of the smart pyranometer.

These topics remain outside the demonstrated scope of the present experimental validation.

---

## 17. Relation to the research article

The repository supports the experimental material reported in the manuscript, particularly:

- EMI Platform architecture;
- EMI Node and EMI Gateway implementation;
- experimental measurement workflow;
- calibration procedure;
- SCADA integration;
- communication endurance evaluation;
- application-specific model fitting;
- independent validation.

The smart pyranometer is the experimental validation application. The principal research contribution remains the organization of the EMI Platform into reusable platform services and instrument-specific measurement functionality.