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
        "stop_id": "string"
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

print(vehicle_sample.columns.tolist())
print(vehicle_sample)
print(vehicle_sample.dtypes)
# vehicle_positions_1 = pd.read_parquet(vehicle_path_1)

# print(vehicle_positions_1.columns.tolist())
# print(vehicle_positions_1.head())
# print(vehicle_positions_1.shape)
# print(vehicle_positions_1.dtypes)

