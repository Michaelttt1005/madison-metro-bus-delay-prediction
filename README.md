# Madison Metro Bus Delay Prediction

> Local folder name: `Madison Bus Delay Prediction`.

An independent, data-centric machine-learning study of short-horizon arrival-delay prediction for Madison Metro Rapid Route A. The first milestone is deliberately narrow: predict the arrival deviation at **Capitol Square Eastbound**, ten minutes before a scheduled arrival.

## Research focus

The project asks whether calendar, weather, vehicle-position, and agency real-time context improve short-horizon arrival-delay prediction compared with simple, transparent baselines.

The detailed study definition is in [research_question.md](research_question.md).

## Project layout

```text
Madison Bus Delay Prediction/
├── data/                 # Data already acquired and placed locally; not committed to Git
│   ├── raw/              # Original GTFS, GTFS-RT, and weather files
│   ├── interim/          # Cleaned intermediate tables
│   └── processed/        # Modeling-ready tables
├── notebooks/            # Manual exploration and label-audit notebooks
├── reports/figures/      # Charts used in the report
├── src/                  # Analysis, feature, modeling, and evaluation code only
├── tests/                # Small validation tests added as the pipeline grows
├── research_question.md  # Pre-registered project definition
├── requirements.txt
└── .gitignore
```

Data-acquisition scripts are intentionally **outside** this project, at:

```text
D:\Michael\Interesting Project\_external_data_tools\madison_bus_delay
```

That keeps the research repository focused on the data you have already placed under `data/`, plus the analysis that turns it into labels, features, models, and results.

The initial pilot's exact public sources and service dates are documented in
[data/SOURCES.md](data/SOURCES.md). Raw files and the local checksum manifest
are deliberately excluded from Git.

## Local setup

The project uses Python 3.11+. From this folder, run:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If you do not already have JupyterLab available, install it as an optional notebook interface:

```powershell
python -m pip install jupyterlab
python -m jupyter lab
```

## First milestone

Before fitting any model, complete the data audit in this order:

1. Match each service date to the correct static GTFS version.
2. Identify the exact GTFS `stop_id` and `stop_sequence` for Capitol Square Eastbound on Route A eastbound trips.
3. Construct estimated actual arrivals from archived Vehicle Positions.
4. Manually audit 20 GPS-derived arrival labels.
5. Only then construct features and compare baselines.

## Data attribution

Metro data should retain the required attribution: “Data provided under license granted by City of Madison, WI, Metro Transit.”
