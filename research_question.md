# Research definition: Madison Metro Route A arrival-delay prediction

## 1. Research question

For eastbound Metro Rapid Route A trips, can data available **ten minutes before a scheduled arrival** improve the prediction of arrival deviation at Capitol Square Eastbound beyond schedule-only, historical, and agency real-time baselines?

## 2. Scope for the first study

| Item | Fixed first-study choice |
|---|---|
| Agency | Madison Metro Transit |
| Route | Rapid Route A (`route_id` confirmed during intake) |
| Direction | Eastbound (`direction_id` confirmed against static GTFS) |
| Target stop | Capitol Square Eastbound (`stop_id` and `stop_sequence` confirmed during intake) |
| Prediction horizon | 10 minutes before scheduled arrival |
| Unit of analysis | One scheduled Route A trip arriving at the target stop on one service date |
| Model type | Regression: predicted early/late arrival in seconds |

The study intentionally excludes additional routes, other stops, a dashboard, and event-calendar features until the first analysis is complete.

## 3. Prediction time and allowed information

For a scheduled trip-stop arrival at `scheduled_arrival_time`, define the model issue time as:

```text
T = scheduled_arrival_time − 10 minutes
```

Every feature used for that row must have a timestamp at or before `T`. This rule includes Metro GTFS-Realtime records, weather observations, and every derived feature. A record created after `T` is future information and must not be used.

## 4. Outcome / label

```text
actual_delay_seconds = estimated_actual_arrival − scheduled_arrival_time
```

- Positive value: bus arrived late.
- Negative value: bus arrived early.
- Zero: bus arrived on schedule.

`estimated_actual_arrival` is not a GTFS-RT prediction. It is estimated from archived **Vehicle Positions**: the first credible time a vehicle on the matching trip enters a defined geofence around the target stop while approaching in the expected route direction.

### Label-quality rules to decide during data audit

- Test a geofence radius of 50 m, 60 m, and 75 m.
- Require nearby GPS observations before and after the inferred arrival; gaps over 90 seconds are low confidence.
- Flag impossible or extreme values for review rather than silently treating them as valid.
- Randomly audit at least 20 labels by plotting GPS distance-to-stop against time.
- Retain an explicit `label_confidence` or `label_status` column.

The report must state that these are GPS-derived arrival estimates, not agency-certified actual arrivals.

## 5. Candidate feature sets

### Calendar and schedule features

- scheduled hour and minute
- weekday
- weekend flag
- public-holiday flag
- scheduled travel time from the preceding stop

### Weather features

- temperature
- precipitation
- wind speed

### Real-time features, only when timestamped at or before T

- latest known vehicle latitude and longitude
- distance from the target stop
- vehicle speed, when available
- Metro’s most recent predicted arrival deviation, when available

No “nearby event” feature belongs in version 1. It needs a separate, documented definition and source-quality review.

## 6. Required comparisons

The learned model must be compared with all applicable baselines:

| Method | Prediction |
|---|---|
| Schedule baseline | 0 seconds of delay |
| Historical baseline | Median training-set delay for the relevant weekday × hour bucket |
| Agency baseline | Most recent Metro GTFS-RT prediction available at or before `T` |
| Learned model | A scikit-learn regression model using only allowed features |

The first learned model should be `HistGradientBoostingRegressor`; deep learning is explicitly out of scope.

## 7. Evaluation protocol

Split by time, never by randomly shuffled rows:

```text
Training period   → earliest contiguous dates
Validation period → following contiguous dates
Test period       → final held-out contiguous dates
```

Primary metrics:

- Mean Absolute Error (MAE), reported in minutes
- Median Absolute Error, reported in minutes
- Percentage of predictions within ±2 minutes

Diagnostics:

- Mean signed error (systematically early vs. late predictions)
- Results by weekday/weekend
- Results by rainfall/no rainfall, if enough cases exist
- Results with and without an agency real-time prediction
- Number of valid examples at every filtering step

## 8. Data sources and provenance

| Data | Purpose | Local destination |
|---|---|---|
| Metro static GTFS | Planned trips, stops, stop times, calendar | `data/raw/gtfs/` |
| Archived GTFS-RT Vehicle Positions | GPS-derived arrival labels and real-time features | `data/raw/vehicle_positions/` |
| Archived GTFS-RT Trip Updates | Agency prediction baseline | `data/raw/trip_updates/` |
| Historical weather | Weather features | `data/raw/weather/` |
| Holiday calendar | Calendar feature | Derived in analysis; source/version documented |

For each input, record URL, date range, fetch date, static GTFS feed version, and any manual decisions in a future `data/manifest.csv`.

## 9. Success criterion

The project is successful if it produces a reproducible, leakage-free comparison and an honest error analysis. Beating Metro’s own prediction is **not** required. A valid result may show that the agency forecast is stronger, or that added features help only when the agency prediction is missing.

