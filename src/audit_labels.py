from pathlib import Path
import pandas as pd

project = Path(r"D:\Michael\Interesting Project\Madison Bus Delay Prediction")

labels_path = (
    project /
    "data" /
    "interim" /
    "arrival_labels_20260110_to_20260827.csv")

scheduled_path = (
    project /
    "data" /
    "interim" /
    "scheduled_data.csv"
)

output_path = (
    project /
    "data" /
    "interim" /
    "label_audit_20260110_to_20260827.csv"
)

time_zone = "America/Chicago"
delay_threshold_seconds = 60 * 30

key_columns = [
    "service_date",
    "trip_id",
    "stop_id",
]

labels = pd.read_csv(labels_path, dtype = {
    "service_date": "string",
    "trip_id": "string",
    "stop_id": "string"
})

scheduled_data = pd.read_csv(scheduled_path, dtype = {
    "service_date": "string",
    "trip_id": "string",
    "stop_id": "string"
})

schedule_context = scheduled_data[
    key_columns
    + [
        "arrival_time",
        "stop_sequence",
        "static_gtfs_file",
        "static_gtfs_version",
    ]
].copy()

audit_data = labels.merge(
    schedule_context,
    on=key_columns,
    how = "left",
    validate = "one_to_one",
)

# print(audit_data.head())

exceptions_path = (
    project
    / "data"
    / "interim"
    / "label_exceptions_20260110_to_20260827.csv"
)

clean_labels_path = (
    project
    / "data"
    / "interim"
    / "clean_labels_20260110_to_20260827.csv"
)

audit_data["has_label"] = (
    audit_data["estimated_actual_arrival"].notna()
    & audit_data["actual_delay_seconds"].notna()
)

audit_data["abs_delay_seconds"] = (
    audit_data["actual_delay_seconds"].abs()
)

audit_data["is_extreme_delay"] = (
    audit_data["has_label"]
    & (
        audit_data["abs_delay_seconds"]
        > delay_threshold_seconds
    )
)

exceptions = audit_data.loc[audit_data["is_extreme_delay"]].copy()

exceptions["exception_reason"] = (
    "absolute_delay_over_30_minutes"
)

exceptions.to_csv(
    exceptions_path,
    index=False,
)

clean_labels = audit_data.loc[
    audit_data["has_label"]
    & ~audit_data["is_extreme_delay"]
].copy()

clean_labels.to_csv(
    clean_labels_path,
    index=False,
)

audit_data.to_csv(
    output_path,
    index=False,
)

# print("All rows:", len(audit_data))
# print("Rows without labels:", (~audit_data["has_label"]).sum())
# print("Extreme-delay exceptions:", len(exceptions))
# print("Clean labels for training:", len(clean_labels))
