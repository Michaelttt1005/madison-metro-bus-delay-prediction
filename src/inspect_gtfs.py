from pathlib import Path
from zipfile import ZipFile

import pandas as pd


project = Path(r"D:\Michael\Interesting Project\Madison Bus Delay Prediction")
gtfs_dir = project / "data" / "raw" / "gtfs"
vehicle_positions_dir = project / "data" / "raw" / "vehicle_positions"

target_stop_names = ["Shorewood", "Blair", "Eau Claire"]


def read_gtfs_table(gtfs_zip, filename):
    """Read one CSV table from an immutable GTFS zip as strings."""
    with ZipFile(gtfs_zip) as archive:
        with archive.open(filename) as file:
            return pd.read_csv(file, dtype="string")


def build_schedule_for_static_feed(gtfs_zip, service_dates):
    """Create Route A / JUNCTION planned arrivals for one GTFS service period."""
    routes = read_gtfs_table(gtfs_zip, "routes.txt")
    route_a = routes.loc[routes["route_short_name"] == "A"].copy()

    if route_a.empty:
        raise ValueError(f"Route A is missing from {gtfs_zip.name}.")

    route_a_id = route_a.iloc[0]["route_id"]
    trips = read_gtfs_table(gtfs_zip, "trips.txt")
    a_trips = trips.loc[trips["route_id"] == route_a_id].copy()
    junctions = a_trips.loc[
        a_trips["trip_headsign"] == "JUNCTION",
        ["trip_id", "service_id"],
    ].copy()

    stop_times = read_gtfs_table(gtfs_zip, "stop_times.txt")
    a_stop_times = stop_times.loc[
        stop_times["trip_id"].isin(junctions["trip_id"]),
        ["trip_id", "arrival_time", "stop_id", "stop_sequence"],
    ].copy()

    stops = read_gtfs_table(gtfs_zip, "stops.txt")
    a_stops = stops.loc[
        stops["stop_id"].isin(a_stop_times["stop_id"]),
        [
            "stop_id",
            "stop_name",
            "stop_lat",
            "stop_lon",
            "cardinal_direction",
        ],
    ].copy()

    junction_stop_data = a_stop_times.merge(a_stops, on="stop_id", how="left")
    target_stop_data = junction_stop_data.loc[
        junction_stop_data["stop_name"].isin(target_stop_names)
    ].copy()

    found_stop_names = set(target_stop_data["stop_name"].dropna())
    missing_stop_names = set(target_stop_names) - found_stop_names
    if missing_stop_names:
        raise ValueError(
            f"{gtfs_zip.name} is missing target stops: {sorted(missing_stop_names)}"
        )

    calendar = read_gtfs_table(gtfs_zip, "calendar.txt")
    calendar_dates = read_gtfs_table(gtfs_zip, "calendar_dates.txt")
    feed_info = read_gtfs_table(gtfs_zip, "feed_info.txt").iloc[0]
    feed_version = feed_info["feed_version"]

    junction_calendar = calendar.loc[
        calendar["service_id"].isin(junctions["service_id"])
    ].copy()

    scheduled_tables = []

    for service_date in service_dates:
        day_name = pd.Timestamp(service_date).day_name().lower()

        active_services = junction_calendar.loc[
            (junction_calendar[day_name] == "1")
            & (service_date >= junction_calendar["start_date"])
            & (service_date <= junction_calendar["end_date"])
        ].copy()

        date_exceptions = calendar_dates.loc[
            calendar_dates["date"] == service_date
        ].copy()

        added_service_ids = date_exceptions.loc[
            date_exceptions["exception_type"] == "1",
            "service_id",
        ].tolist()

        removed_service_ids = date_exceptions.loc[
            date_exceptions["exception_type"] == "2",
            "service_id",
        ].tolist()

        active_service_ids = active_services["service_id"].tolist()
        final_active_service_ids = list(
            set(active_service_ids + added_service_ids)
            - set(removed_service_ids)
        )

        active_junctions = junctions.loc[
            junctions["service_id"].isin(final_active_service_ids)
        ].copy()

        scheduled_for_date = target_stop_data.loc[
            target_stop_data["trip_id"].isin(active_junctions["trip_id"])
        ].copy()

        scheduled_for_date["service_date"] = service_date
        scheduled_for_date["static_gtfs_file"] = gtfs_zip.name
        scheduled_for_date["static_gtfs_version"] = feed_version
        scheduled_tables.append(scheduled_for_date)

    return pd.concat(scheduled_tables, ignore_index=True)


service_dates = sorted(
    vehicle_path.stem.replace("-", "")
    for vehicle_path in vehicle_positions_dir.glob("*.parquet")
)

static_gtfs_files = sorted(gtfs_dir.glob("mmt_gtfs_*.zip"))
if not static_gtfs_files:
    raise FileNotFoundError("No archived GTFS zip files were found.")

scheduled_tables = []

for gtfs_zip in static_gtfs_files:
    feed_info = read_gtfs_table(gtfs_zip, "feed_info.txt").iloc[0]
    feed_start_date = feed_info["feed_start_date"]
    feed_end_date = feed_info["feed_end_date"]

    dates_for_feed = [
        service_date
        for service_date in service_dates
        if feed_start_date <= service_date <= feed_end_date
    ]

    if not dates_for_feed:
        continue

    scheduled_tables.append(
        build_schedule_for_static_feed(gtfs_zip, dates_for_feed)
    )

scheduled_data = pd.concat(scheduled_tables, ignore_index=True)

output_path = project / "data" / "interim" / "scheduled_data.csv"
scheduled_data.to_csv(output_path, index=False)

# print("Scheduled-table shape:", scheduled_data.shape)
# print("Covered service dates:", scheduled_data["service_date"].nunique())
# print(
#     "Static GTFS versions:",
#     scheduled_data["static_gtfs_version"].nunique(),
# )
# print(
#     "Duplicate date-trip-stop keys:",
#     scheduled_data.duplicated(
#         ["service_date", "trip_id", "stop_id"]
#     ).sum(),
# )
