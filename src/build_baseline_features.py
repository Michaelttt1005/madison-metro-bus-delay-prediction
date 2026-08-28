from pathlib import Path
import json

import pandas as pd

project = Path(
    r"D:\Michael\Interesting Project\Madison Bus Delay Prediction"
)

clean_labels_path = (
    project
    / "data"
    / "interim"
    / "clean_labels_20260110_to_20260827.csv"
)

weather_path = (
    project
    / "data"
    / "raw"
    / "weather"
    / "open_meteo_madison_2026-01-10_2026-08-27.json"
)

output_path = (
    project
    / "data"
    / "processed"
    / "baseline_modeling_table.csv"
)

timezone = "America/Chicago"
prediction_horizon_minutes = 10

clean_labels = pd.read_csv(
    clean_labels_path,
    dtype={
        "service_date": "string",
        "trip_id": "string",
        "stop_id": "string",
    },
)

clean_labels["scheduled_arrival"] = (
    pd.to_datetime(
        clean_labels["scheduled_arrival"],
        utc=True,
        errors="raise",
    )
    .dt.tz_convert(timezone)
)

clean_labels["prediction_time"] = (
    clean_labels["scheduled_arrival"]
    - pd.Timedelta(
        minutes = prediction_horizon_minutes
    )
)

clean_labels["month"] = (
    clean_labels["prediction_time"]
    .dt.month
)

clean_labels["weekday"] = (
    clean_labels["prediction_time"]
    .dt.dayofweek
)

clean_labels["hour"] = (
    clean_labels["prediction_time"]
    .dt.hour
)

clean_labels["minute"] = (
    clean_labels["prediction_time"]
    .dt.minute
)

clean_labels["is_weekend"] = (
    clean_labels["weekday"] >= 5
).astype("int8")

clean_labels["weather_time"] = (
    clean_labels["prediction_time"]
    .dt.floor("h")
    .dt.tz_localize(None)
)

with weather_path.open(
    "r",
    encoding = "utf-8",
) as file:
    weather_json = json.load(file)

weather_data = pd.DataFrame(
    weather_json["hourly"]
)

# print("shape:", clean_labels.shape)
# print("columns:", clean_labels.columns.tolist())
# print(clean_labels.head())

# print(weather_json.keys())
# print(type(weather_json["hourly"]))
# print(weather_json["hourly"].keys())

weather_data = weather_data.rename(
    columns={
        "time":"weather_time"
    }
)

weather_data["weather_time"] = pd.to_datetime(
    weather_data["weather_time"],
    errors="raise",
)

weather_columns = [
    "weather_time",
    "temperature_2m",
    "precipitation",
    "rain",
    "snowfall",
    "wind_speed_10m",
    "weather_code",
]

weather_data = weather_data[
    weather_columns
].copy()

# print("Weather-table shape:", weather_data.shape)
# print("Duplicate weather hours:")
# print(weather_data["weather_time"].duplicated().sum())

# print("Weather missing values:")
# print(weather_data.isna().sum())

# print(weather_json["hourly_units"])
# print(weather_data.head())

modeling_table = clean_labels.merge(
    weather_data,
    on="weather_time",
    how="left",
    validate="many_to_one",
)

weather_feature_columns = [
    "temperature_2m",
    "precipitation",
    "rain",
    "snowfall",
    "wind_speed_10m",
    "weather_code",
]

if modeling_table[weather_feature_columns].isna().any().any():
    raise ValueError(
        "Some clean labels could not be matched to hourly weather."
    )

# print("Modeling-table shape:", modeling_table.shape)

# print("Weather missing values:")
# print(
#     modeling_table[
#         weather_feature_columns
#     ].isna().sum()
# )

# print(
#     modeling_table[
#         [
#             "stop_name",
#             "prediction_time",
#             "weather_time",
#             "temperature_2m",
#             "precipitation",
#             "wind_speed_10m",
#             "actual_delay_seconds",
#         ]
#     ].head(10)
# )

modeling_columns = [
    "service_date",
    "trip_id",
    "stop_id",
    "stop_name",
    "scheduled_arrival",
    "prediction_time",
    "month",
    "weekday",
    "hour",
    "minute",
    "is_weekend",
    "temperature_2m",
    "precipitation",
    "rain",
    "snowfall",
    "wind_speed_10m",
    "weather_code",
    "actual_delay_seconds",
]

modeling_table = modeling_table[
    modeling_columns
].copy()

modeling_table.to_csv(
    output_path,
    index=False,
)

print("Final modeling-table shape:", modeling_table.shape)

print(
    "Duplicate date-trip-stop keys:",
    modeling_table.duplicated(
        [
            "service_date",
            "trip_id",
            "stop_id",
        ]
    ).sum(),
)

print(
    "Missing target values:",
    modeling_table[
        "actual_delay_seconds"
    ].isna().sum(),
)

print(modeling_table.head())
