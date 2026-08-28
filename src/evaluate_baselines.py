from pathlib import Path

import pandas as pd


project = Path(
    r"D:\Michael\Interesting Project\Madison Bus Delay Prediction"
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

predictions_path = (
    project
    / "data"
    / "processed"
    / "baseline_validation_predictions.csv"
)

metrics_path = (
    project
    / "data"
    / "processed"
    / "baseline_validation_metrics.csv"
)

target_column = "actual_delay_seconds"

train_data = pd.read_csv(train_path)

validation_data = pd.read_csv(validation_path)

global_median_delay = train_data[
    target_column
].median()

stop_medians = (
    train_data
    .groupby("stop_name")[target_column]
    .median()
    .reset_index(
        name="prediction_stop_median"
    )
)

stop_hour_medians = (
    train_data
    .groupby(
        [
            "stop_name",
            "hour",
        ]
    )[target_column]
    .median()
    .reset_index(
        name="prediction_stop_hour_median"
    )
)

validation_predictions = validation_data.copy()

validation_predictions[
    "prediction_global_median"
] = global_median_delay

validation_predictions = validation_predictions.merge(
    stop_medians,
    on="stop_name",
    how="left",
    validate="many_to_one",
)

validation_predictions = validation_predictions.merge(
    stop_hour_medians,
    on=[
        "stop_name",
        "hour",
    ],
    how="left",
    validate="many_to_one",
)

validation_predictions[
    "prediction_stop_median"
] = validation_predictions[
    "prediction_stop_median"
].fillna(
    global_median_delay
)

validation_predictions[
    "prediction_stop_hour_median"
] = validation_predictions[
    "prediction_stop_hour_median"
].fillna(
    validation_predictions[
        "prediction_stop_median"
    ]
)

def evaluate_prediction(data, prediction_column):
    absolute_error = (
        data[target_column] - data[prediction_column]
    ).abs()

    return {
        "model": prediction_column,
        "mae_seconds": absolute_error.mean(),
        "mae_minutes": absolute_error.mean() / 60,
        "within_2_minutes": (absolute_error <= 120).mean(),
    }

metrics = pd.DataFrame([
    evaluate_prediction(
        validation_predictions,
        "prediction_global_median",
    ),
    evaluate_prediction(
        validation_predictions,
        "prediction_stop_median",
    ),
    evaluate_prediction(
        validation_predictions,
        "prediction_stop_hour_median",
    ),
])

metrics = metrics.sort_values(
    "mae_seconds"
).reset_index(drop=True)

validation_predictions.to_csv(
    predictions_path,
    index=False,
)

metrics.to_csv(
    metrics_path,
    index=False,
)

print("Global training median delay:", global_median_delay)
print("\nValidation metrics:")
print(metrics)
