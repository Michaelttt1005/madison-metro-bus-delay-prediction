# Madison Metro Bus Delay Prediction

An independent, data-centric machine-learning study of **short-horizon arrival-delay prediction for Madison Metro Rapid Route A**. The current reproducible workflow predicts the arrival deviation at three Route A / Junction eastbound stops - **Shorewood, Blair, and Eau Claire** - ten minutes before each scheduled arrival.

## Why this project

The project asks whether time and weather context can improve arrival-delay predictions beyond simple, transparent historical baselines. It is intentionally a small research-style project: all feature transformations are learned from the training period only, the validation period is later in time, and the final test period remains held out.

## Current workflow status

The first no-GPS modeling workflow is complete locally:

1. Archived static GTFS schedules from four feed versions were matched to 229 available Vehicle Positions service dates (2026-01-10 through 2026-08-27).
2. Route A / Junction scheduled arrivals were extracted for Shorewood, Blair, and Eau Claire.
3. GPS-based proxy arrival labels were constructed by detecting a vehicle's first entry into a 60 m stop geofence. These are estimated arrivals, not agency door-open timestamps.
4. Labels were audited, and observed delays greater than 30 minutes were retained in a separate exceptions file and excluded from the clean modeling table.
5. Calendar/time and hourly Open-Meteo weather features were joined at a fixed prediction horizon of ten minutes before scheduled arrival.
6. The data was split chronologically into train, validation, and held-out test periods. No random split is used.
7. Transparent median baselines and a PyTorch multilayer perceptron (MLP) were trained and evaluated on the validation period only.

### Validation results

| Model | Validation MAE | Within 2 minutes |
| --- | ---: | ---: |
| Global median delay | 2.366 min | 54.86% |
| Stop median delay | 2.277 min | 57.17% |
| Stop + hour median delay | 2.183 min | 59.71% |
| PyTorch MLP, no GPS | **2.074 min** | **62.49%** |

The MLP used 26 features: normalized calendar/weather values plus one-hot stop and weather-condition categories. It used AdamW optimization, L1 loss, and validation-based early stopping; the best validation epoch was 4. The final test period has deliberately not been used yet.

## Project layout

```text
Madison Bus Delay Prediction/
├── data/                 # Local data; excluded from Git
│   ├── raw/              # Original GTFS, GTFS-RT, and weather files
│   ├── interim/          # Labels and audited intermediate tables
│   └── processed/        # Modeling tables, splits, and local outputs
├── notebooks/            # Manual exploration and label-audit notebooks
├── reports/figures/      # Charts used in the project report
├── src/                  # Reproducible analysis, modeling, and evaluation code
├── tests/                # Small validation tests added as the pipeline grows
├── research_question.md  # Study definition and scope
├── requirements.txt
└── .gitignore
```

Data-acquisition scripts are intentionally kept outside this repository at:

```text
D:\Michael\Interesting Project\_external_data_tools\madison_bus_delay
```

This repository therefore contains only analysis and modeling code; raw GTFS, GTFS-Realtime, weather data, model checkpoints, and generated tables remain local.

## Local setup

The project currently runs with Python 3.10 and CPU PyTorch. From this folder:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Reproducing the current workflow

Run these scripts in order after the local data has been placed in `data/`:

```powershell
python src\inspect_gtfs.py
python src\build_actual_arrivals.py
python src\audit_labels.py
python src\build_baseline_features.py
python src\create_time_splits.py
python src\evaluate_baselines.py
python src\train_pytorch_mlp.py
```

## Next steps

- Diagnose validation errors by stop, time of day, and weather condition.
- Tune the no-GPS MLP using the validation period only.
- Add leakage-safe real-time vehicle-position snapshot features.
- Select one final configuration, evaluate it once on the held-out test period, and publish a concise results report.

## Data attribution

Metro data should retain the required attribution: "Data provided under license granted by City of Madison, WI, Metro Transit."
