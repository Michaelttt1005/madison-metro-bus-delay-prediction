from pathlib import Path
import pandas as pd
from zipfile import ZipFile
import duckdb

project = Path(
    r"D:\Michael\Interesting Project\Madison Bus Delay Prediction"
)

scheduled_data = pd.read_csv(
    project / "data" / "interim" / "scheduled_data.csv",
    dtype={
        "trip_id": "string",
        "stop_id": "string",
        "service_id": "string",
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
# print(vehicle_sample.columns.tolist())
# print(vehicle_sample)
# print(vehicle_sample.dtypes)
# vehicle_positions_1 = pd.read_parquet(vehicle_path_1)

# print(vehicle_positions_1.columns.tolist())
# print(vehicle_positions_1.head())
# print(vehicle_positions_1.shape)
# print(vehicle_positions_1.dtypes)

