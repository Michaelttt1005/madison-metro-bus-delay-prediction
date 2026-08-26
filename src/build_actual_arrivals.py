from pathlib import Path
import pandas as pd
import duckdb
import numpy as np

project = Path(
    r"D:\Michael\Interesting Project\Madison Bus Delay Prediction"
)

scheduled_data = pd.read_csv(
    project / "data" / "interim" / "scheduled_data.csv",
    dtype={
        "trip_id": "string",
        "stop_id": "string",
        "service_date": "string",
    }
)

vehicle_path_1 = (
    project
    / "data"
    / "raw"
    / "vehicle_positions"
    / "2026-08-10.parquet"
)

con = duckdb.connect()

vehicle_sample = con.execute(
    """
    select *
    FROM read_parquet(?)
    LIMIT 10
    """,
    [str(vehicle_path_1)]
).fetchdf()

scheduled_data_1 = scheduled_data.loc[
    scheduled_data["service_date"] == "20260810"
].copy()

trip_ids_1 = (
    scheduled_data_1["trip_id"]
    .drop_duplicates()
    .tolist()
)

target_trips_1 = pd.DataFrame({
    "trip_id": trip_ids_1
})

con.register(
    "target_trips_1",
    target_trips_1
)

vehicle_positions_1 = con.execute(
    """
    SELECT
        v.trip_id,
        v.route_id,
        v.direction_id,
        v.vehicle_id,
        v.latitude,
        v.longitude,
        v.speed,
        v.current_stop_sequence,
        v.stop_id,
        v.current_status,
        v.timestamp,
        v.fetch_timestamp
    FROM read_parquet(?) AS v
    INNER JOIN target_trips_1 AS t
        ON v.trip_id = t.trip_id
    WHERE v.route_id = 'A'
    """,
    [str(vehicle_path_1)]
).fetchdf()

vehicle_positions_1["vehicle_time"] = (
    pd.to_datetime(
        vehicle_positions_1["timestamp"],
        unit="s",
        utc=True
    )
    .dt.tz_convert("America/Chicago")
)

vehicle_positions_1 = vehicle_positions_1.drop_duplicates(
    subset=[
        "trip_id",
        "vehicle_time",
        "latitude",
        "longitude"
    ]
).copy()

# print("Scheduled trips:", len(trip_ids_1))
# print(
#     "GPS trips:",
#     vehicle_positions_1["trip_id"].nunique()
# )
# print("GPS rows:", len(vehicle_positions_1))
# print(vehicle_positions_1.head())

test_trip_id = trip_ids_1[0]

test_trip = vehicle_positions_1.loc[
    vehicle_positions_1["trip_id"] == test_trip_id
].copy()

test_trip = test_trip.sort_values("vehicle_time")

# print(
#     test_trip.loc[
#         test_trip["vehicle_time"]
#         == pd.Timestamp("2026-08-10 11:24:36", tz="America/Chicago"),
#         [
#             "vehicle_id",
#             "latitude",
#             "longitude",
#             "fetch_timestamp"
#         ]
#     ]
# )

# print(test_trip.shape)

test_schedule = scheduled_data_1.loc[
    scheduled_data_1["trip_id"] == test_trip_id
].copy()

# print(
#     test_schedule[
#         [
#             "trip_id",
#             "stop_id",
#             "stop_name",
#             "arrival_time",
#             "stop_lat",
#             "stop_lon",
#             "stop_sequence"
#         ]
#     ]
# )

blair = test_schedule.loc[
    test_schedule["stop_name"] == "Blair"
].iloc[0]

def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371000

    lat1 = np.radians(lat1)
    lon1 = np.radians(lon1)
    lat2 = np.radians(lat2)
    lon2 = np.radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        np.sin(dlat / 2) ** 2
        + np.cos(lat1)
        * np.cos(lat2)
        * np.sin(dlon / 2) ** 2
    )

    c = 2 * np.arctan2(
        np.sqrt(a),
        np.sqrt(1 - a)
    )

    return R * c

test_trip["distance_to_blair_m"] = haversine_distance(
    test_trip["latitude"],
    test_trip["longitude"],
    float(blair["stop_lat"]),
    float(blair["stop_lon"])
)

# print(
#     test_trip[
#         [
#             "vehicle_time",
#             "latitude",
#             "longitude",
#             "distance_to_blair_m"
#         ]
#     ]
#     .sort_values("distance_to_blair_m")
#     .head(20)
# )

near_blair = test_trip.loc[
    test_trip["distance_to_blair_m"] <= 500
].copy()

near_blair = near_blair.sort_values("vehicle_time")

# print(
#     near_blair[
#         [
#             "vehicle_time",
#             "distance_to_blair_m",
#             "speed"
#         ]
#     ]
# )

inside_blair = test_trip.loc[
    test_trip["distance_to_blair_m"] <= 60
].copy()

inside_blair = inside_blair.sort_values("vehicle_time")

print(
    inside_blair[
        [
            "vehicle_time",
            "distance_to_blair_m",
            "speed"
        ]
    ]
)

if inside_blair.empty:
    estimated_actual_arrival = pd.NaT
    print("No GPS point entered the 60 m geofence.")
else:
    estimated_actual_arrival = inside_blair.iloc[0]["vehicle_time"]
    print("Estimated actual arrival:", estimated_actual_arrival)

print(
    near_blair[
        [
            "vehicle_time",
            "distance_to_blair_m",
            "speed"
        ]
    ]
)

service_date = blair["service_date"]

scheduled_arrival = pd.Timestamp(
    f"{service_date[:4]}-{service_date[4:6]}-{service_date[6:]} {blair['arrival_time']}",
    tz="America/Chicago"
)

if pd.isna(estimated_actual_arrival):
    actual_delay_seconds = np.nan
else:
    actual_delay_seconds = (
        estimated_actual_arrival - scheduled_arrival
    ).total_seconds()

print("Scheduled arrival:", scheduled_arrival)
print("Estimated actual arrival:", estimated_actual_arrival)
print("Actual delay seconds:", actual_delay_seconds)

def estimate_actual_arrival(
    trip_positions,
    stop_lat,
    stop_lon,
    geofence_m=60
):
    trip_positions = trip_positions.sort_values("vehicle_time").copy()

    trip_positions["distance_to_stop_m"] = haversine_distance(
        trip_positions["latitude"],
        trip_positions["longitude"],
        float(stop_lat),
        float(stop_lon)
    )

    trip_positions["previous_distance_m"] = (
        trip_positions["distance_to_stop_m"].shift(1)
    )

    entered_stop = trip_positions.loc[
        (trip_positions["previous_distance_m"] > geofence_m)
        & (trip_positions["distance_to_stop_m"] <= geofence_m)
    ].copy()

    if entered_stop.empty:
        return pd.NaT

    return entered_stop.iloc[0]["vehicle_time"]

def build_scheduled_arrival(service_date, arrival_time):
    return pd.Timestamp(
        f"{service_date[:4]}-{service_date[4:6]}-{service_date[6:]} {arrival_time}",
        tz="America/Chicago"
    )

# print(vehicle_sample)
# print(vehicle_sample.dtypes)
# vehicle_positions_1 = pd.read_parquet(vehicle_path_1)

# print(vehicle_positions_1.columns.tolist())
# print(vehicle_positions_1.head())
# print(vehicle_positions_1.shape)
# print(vehicle_positions_1.dtypes)

