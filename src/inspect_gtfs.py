from pathlib import Path
from zipfile import ZipFile
import pandas as pd

project = Path(r"D:\Michael\Interesting Project\Medicine Bus Delay Prediction")
gtfs_zip = project / r"data/raw/gtfs/mmt_gtfs_2026-05-10_to_2026-08-15.zip"

#route id
with ZipFile(gtfs_zip) as archive:
    with archive.open("routes.txt") as file:
        routes = pd.read_csv(file, dtype = "string")

# print(routes.columns.tolist())
# print(routes.head())
# print(routes.shape)
# print(routes.dtypes)

# routes.info(
#     verbose=None,
#     show_counts=None,
#     memory_usage=None,
# )

route_names = routes["route_short_name"]

route_A = routes.loc[routes["route_short_name"] == "A"].copy()
route_A_id = route_A.iloc[0]["route_id"]

#trip id with simplized colomns
with ZipFile(gtfs_zip) as archive:
    with archive.open("trips.txt") as file:
        trips = pd.read_csv(file, dtype = "string")
Atrips = trips.loc[trips["route_id"] == route_A_id].copy()

junctions = Atrips.loc[Atrips["trip_headsign"] == "JUNCTION"].copy()
trip_ids = junctions["trip_id"].tolist()
junctions = junctions[[
        "trip_id",
        "service_id"
    ]].copy()

#stop information with simplized colomns
with ZipFile(gtfs_zip) as archive:
    with archive.open("stop_times.txt") as file:
        stop_times = pd.read_csv(file, dtype = "string")
# print(stop_times.columns.tolist())
a_stop_times = stop_times.loc[stop_times["trip_id"].isin(trip_ids)].copy()
a_stop_times = a_stop_times[[
        "trip_id",
        "arrival_time",
        "stop_id",
        "stop_sequence",
    ]].copy()

#station information with simplized colomns
with ZipFile(gtfs_zip) as archive:
    with archive.open("stops.txt") as file:
        stops = pd.read_csv(file, dtype = "string")
a_stops = stops.loc[stops["stop_id"].isin(a_stop_times["stop_id"])]
# print(a_stops.columns.tolist())
a_stops = a_stops[[
        "stop_id",
        "stop_name",
        "stop_lat",
        "stop_lon",
        "cardinal_direction"
]].copy()

junction_stop_data = a_stop_times.merge(a_stops, on="stop_id", how="left")
stops_count = junction_stop_data.groupby(["stop_id", "stop_name"])["trip_id"].nunique().reset_index(name="trip_count").sort_values("trip_count", ascending=False)
# print(stops_count.head(20))
target_stops = stops_count.loc[stops_count["stop_name"].isin(["Shorewood", "Blair", "Eau Claire"])].copy()
print(target_stops.head(20))

with ZipFile(gtfs_zip) as archive:
    with archive.open("calendar.txt") as file:
        calendar = pd.read_csv(file, dtype = "string")
with ZipFile(gtfs_zip) as archive:
    with archive.open("calendar_dates.txt") as file:
        calendar_dates = pd.read_csv(file, dtype = "string")

