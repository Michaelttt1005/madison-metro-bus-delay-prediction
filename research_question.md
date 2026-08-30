# Research definition: Madison Metro Route A arrival-delay prediction

## Research question

For eastbound Madison Metro Rapid Route A trips at Shorewood, Blair, and Eau Claire, can calendar and weather information available **ten minutes before a scheduled arrival** improve predicted arrival deviation beyond transparent historical-delay baselines?

## Scope of the current workflow

| Item | Current choice |
| --- | --- |
| Agency | Madison Metro Transit |
| Route | Rapid Route A (`route_id = A`) |
| Direction and trip subset | Junction eastbound trips |
| Target stops | Shorewood, Blair, and Eau Claire |
| Service dates | 2026-01-10 through 2026-08-27, excluding unavailable archive dates |
| Prediction horizon | 10 minutes before scheduled arrival |
| Unit of analysis | One scheduled trip-stop arrival on one service date |
| Prediction target | Arrival deviation in seconds |
| Current feature set | Calendar/time, stop identity, and hourly weather; no GPS input features |

The first version deliberately stays small. GPS observations are used to construct labels, but no real-time vehicle position is used as a model feature yet.

## Prediction-time rule

For a scheduled trip-stop arrival at `scheduled_arrival`, the issue time is:

```text
prediction_time = scheduled_arrival - 10 minutes
```

Every model feature must be known at or before `prediction_time`. The no-GPS v1 table uses only schedule-derived time fields and weather values aligned to that time. Future vehicle-position features will require a timestamped snapshot at or before this cutoff.

## Outcome and label construction

```text
actual_delay_seconds = estimated_actual_arrival - scheduled_arrival
```

`estimated_actual_arrival` is a GPS-derived proxy, not an agency-certified door-open timestamp. For each scheduled trip and stop, the label builder detects the vehicle's first entry from outside to inside a 60 m geofence around the stop. Positive values mean late arrival; negative values mean early arrival.

The completed label audit keeps raw labels unchanged, stores observed delays above 30 minutes in a separate exceptions file, and excludes those extreme observations from the clean modeling table. Missing GPS labels are not treated as zero delay.

## Data and feature pipeline

1. Match each service date to the corresponding archived static GTFS feed version.
2. Extract Route A / Junction scheduled arrivals for the three target stops.
3. Join matching archived Vehicle Positions by trip identifier and filter observations back to the service date.
4. Construct 60 m geofence arrival labels and audit extreme observed delays.
5. Create no-GPS features: month, weekday, hour, minute, weekend flag, stop identity, temperature, precipitation, rain, snowfall, wind speed, and weather category.
6. Split rows chronologically by service date: 70% train, 15% validation, 15% held-out test.

The current split contains 18,885 training rows, 4,023 validation rows, and 4,546 test rows. The test split remains locked during model development.

## Models and validation results

All baseline statistics and preprocessing parameters are fit on the training period only.

| Model | Validation MAE | Within +/- 2 minutes |
| --- | ---: | ---: |
| Global median delay | 2.366 min | 54.86% |
| Stop median delay | 2.277 min | 57.17% |
| Stop + hour median delay | 2.183 min | 59.71% |
| PyTorch MLP, no GPS | **2.074 min** | **62.49%** |

The PyTorch MLP accepts 26 processed features, uses two hidden layers (64 and 32 units), ReLU activations, L1 loss, AdamW optimization, and validation-based early stopping. Its best validation checkpoint occurred at epoch 4.

## Validation diagnostics

The diagnostic script merges baseline and MLP validation predictions on `service_date`, `trip_id`, and `stop_id`, then writes overall, by-stop, by-hour, and worst-case outputs. The MLP reduced overall validation MAE by 6.53 seconds. It improved MAE at every target stop: Shorewood by 9.62 seconds, Eau Claire by 9.60 seconds, and Blair by 1.13 seconds.

At 8:00, the MLP produced the largest observed hourly improvement: MAE fell by 23.27 seconds and the within-two-minute rate increased from 54.95% to 73.04%. These are diagnostic observations from the validation set, not final held-out-test results.

## Evaluation protocol

Rows are never randomly shuffled into train, validation, and test. The chronological split simulates the realistic situation in which a model trained on earlier service dates is used on later dates.

The primary metric is mean absolute error (MAE) in seconds and minutes. The secondary metric is the percentage of predictions within +/- 120 seconds. Model selection uses validation performance only; the held-out test period is reserved for one final evaluation after the configuration is fixed.

## Planned extensions

- Use the completed validation diagnostics to tune model capacity and learning rate on the validation period only.
- Add leakage-safe Vehicle Positions snapshots that occurred at or before prediction time.
- Evaluate one selected final model on the held-out test period and write a concise result report.

## Data sources and provenance

| Data | Purpose | Local destination |
| --- | --- | --- |
| Metro static GTFS | Planned trips, stops, stop times, and service calendar | `data/raw/gtfs/` |
| Archived GTFS-RT Vehicle Positions | GPS-derived arrival labels | `data/raw/vehicle_positions/` |
| Open-Meteo historical weather | Hourly weather features | `data/raw/weather/` |

Raw data, local checksum manifests, model checkpoints, and generated modeling tables are excluded from Git. Metro data should retain the attribution: "Data provided under license granted by City of Madison, WI, Metro Transit."
