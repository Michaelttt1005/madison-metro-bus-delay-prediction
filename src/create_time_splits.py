from pathlib import Path

import pandas as pd


project = Path(
    r"D:\Michael\Interesting Project\Madison Bus Delay Prediction"
)

input_path = (
    project
    / "data"
    / "processed"
    / "baseline_modeling_table.csv"
)

train_path = (
    project
    / "data"
    / "processed"
    / "baseline_train.csv"
)

validation_path = (
    project
    / "data"
    / "processed"
    / "baseline_validation.csv"
)

test_path = (
    project
    / "data"
    / "processed"
    / "baseline_test.csv"
)

modeling_table = pd.read_csv(
    input_path,
    dtype={
        "service_date": "string",
        "trip_id": "string",
        "stop_id": "string",
    },
)

service_dates = sorted(
    modeling_table["service_date"]
    .drop_duplicates()
    .tolist()
)

number_of_dates = len(service_dates)

train_end_index = int(number_of_dates * 0.70)

validation_end_index = (
    train_end_index
    + int(number_of_dates * 0.15)
)

train_dates = service_dates[ :train_end_index]

validation_dates = service_dates[train_end_index:validation_end_index]

test_dates = service_dates[validation_end_index:]

train_data = modeling_table.loc[
    modeling_table["service_date"].isin(
        train_dates
    )
].copy()

validation_data = modeling_table.loc[
    modeling_table["service_date"].isin(
        validation_dates
    )
].copy()

test_data = modeling_table.loc[
    modeling_table["service_date"].isin(
        test_dates
    )
].copy()

if set(train_dates) & set(validation_dates):
    raise ValueError("Train and validation dates overlap.")

if set(train_dates) & set(test_dates):
    raise ValueError("Train and test dates overlap.")

if set(validation_dates) & set(test_dates):
    raise ValueError("Validation and test dates overlap.")

if (
    len(train_data)
    + len(validation_data)
    + len(test_data)
    != len(modeling_table)
):
    raise ValueError("Some rows were lost during splitting.")

train_data.to_csv(
    train_path,
    index=False,
)

validation_data.to_csv(
    validation_path,
    index=False,
)

test_data.to_csv(
    test_path,
    index=False,
)

print(
    "Train:",
    train_data.shape,
    train_dates[0],
    "to",
    train_dates[-1],
)

print(
    "Validation:",
    validation_data.shape,
    validation_dates[0],
    "to",
    validation_dates[-1],
)

print(
    "Test:",
    test_data.shape,
    test_dates[0],
    "to",
    test_dates[-1],
)

print(
    "Target medians:",
    {
        "train": train_data[
            "actual_delay_seconds"
        ].median(),
        "validation": validation_data[
            "actual_delay_seconds"
        ].median(),
        "test": test_data[
            "actual_delay_seconds"
        ].median(),
    },
)
