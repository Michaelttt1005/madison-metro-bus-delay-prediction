from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


project = Path(
    r"D:\Michael\Interesting Project\Madison Bus Delay Prediction"
)

baseline_predictions_path = (
    project
    / "data"
    / "processed"
    / "baseline_validation_predictions.csv"
)

mlp_predictions_path = (
    project
    / "data"
    / "processed"
    / "pytorch_mlp_validation_predictions.csv"
)

history_path = (
    project
    / "data"
    / "processed"
    / "pytorch_mlp_training_history.csv"
)

comparison_path = (
    project
    / "data"
    / "processed"
    / "pytorch_validation_model_comparison.csv"
)

by_stop_path = (
    project
    / "data"
    / "processed"
    / "pytorch_validation_by_stop.csv"
)

by_hour_path = (
    project
    / "data"
    / "processed"
    / "pytorch_validation_by_hour.csv"
)

worst_cases_path = (
    project
    / "data"
    / "processed"
    / "pytorch_validation_worst_cases.csv"
)

figure_path = (
    project
    / "reports"
    / "figures"
    / "pytorch_validation_learning_curve.png"
)

key_columns = [
    "service_date",
    "trip_id",
    "stop_id",
]

target_column = "actual_delay_seconds"

baseline_prediction_column = (
    "prediction_stop_hour_median"
)

mlp_prediction_column = (
    "prediction_pytorch_mlp_seconds"
)

baseline_predictions = pd.read_csv(
    baseline_predictions_path,
    dtype={
        "service_date": "string",
        "trip_id": "string",
        "stop_id": "string",
    },
)

mlp_predictions = pd.read_csv(
    mlp_predictions_path,
    dtype={
        "service_date": "string",
        "trip_id": "string",
        "stop_id": "string",
    },
)

training_history = pd.read_csv(history_path)

mlp_prediction_data = mlp_predictions[
    key_columns
    + [
        mlp_prediction_column,
    ]
].copy()

diagnostic_data = baseline_predictions.merge(
    mlp_prediction_data,
    on=key_columns,
    how="left",
    validate="one_to_one",
)

if diagnostic_data[mlp_prediction_column].isna().any():
    raise ValueError(
        "Some baseline rows could not be matched "
        "to MLP predictions."
    )

def calculate_metrics(
    data,
    prediction_column,
):
    absolute_error = (
        data[target_column]
        - data[prediction_column]
    ).abs()

    return {
        "mae_seconds": absolute_error.mean(),
        "mae_minutes": absolute_error.mean() / 60,
        "within_2_minutes": (
            absolute_error <= 120
        ).mean(),
    }

def build_group_comparison(
    data,
    group_column,
):
    rows = []

    for group_value, group_data in data.groupby(
        group_column,
        dropna=False,
    ):
        baseline_metrics = calculate_metrics(
            group_data,
            baseline_prediction_column,
        )

        mlp_metrics = calculate_metrics(
            group_data,
            mlp_prediction_column,
        )

        rows.append(
            {
                group_column: group_value,
                "rows": len(group_data),
                "baseline_mae_seconds": (
                    baseline_metrics["mae_seconds"]
                ),
                "mlp_mae_seconds": (
                    mlp_metrics["mae_seconds"]
                ),
                "mlp_improvement_seconds": (
                    baseline_metrics["mae_seconds"]
                    - mlp_metrics["mae_seconds"]
                ),
                "baseline_within_2_minutes": (
                    baseline_metrics["within_2_minutes"]
                ),
                "mlp_within_2_minutes": (
                    mlp_metrics["within_2_minutes"]
                ),
            }
        )
    return pd.DataFrame(rows).sort_values(
        "mlp_improvement_seconds",
        ascending=False,
    ).reset_index(drop=True)

baseline_metrics = calculate_metrics(
    diagnostic_data,
    baseline_prediction_column,
)

mlp_metrics = calculate_metrics(
    diagnostic_data,
    mlp_prediction_column,
)

comparison = pd.DataFrame(
    [
        {
            "model": "stop_hour_median_baseline",
            **baseline_metrics,
        },
        {
            "model": "pytorch_mlp_no_gps",
            **mlp_metrics,
        }
    ]
)

comparison["mae_improvement_vs_baseline_seconds"] = (
    baseline_metrics["mae_seconds"] - comparison["mae_seconds"]
)

by_stop = build_group_comparison(
    diagnostic_data,
    "stop_name",
)

by_hour = build_group_comparison(
    diagnostic_data,
    "hour",
)

diagnostic_data["mlp_absolute_error_seconds"] = (
    diagnostic_data[target_column]
    - diagnostic_data[mlp_prediction_column]
).abs()

diagnostic_data["baseline_absolute_error_seconds"] = (
    diagnostic_data[target_column]
    - diagnostic_data[baseline_prediction_column]
).abs()

diagnostic_data["mlp_error_improvement_seconds"] = (
    diagnostic_data["baseline_absolute_error_seconds"]
    - diagnostic_data["mlp_absolute_error_seconds"]
)

worst_cases = diagnostic_data.sort_values(
    "mlp_absolute_error_seconds",
    ascending=False,
).head(20)

worst_cases = worst_cases[
    key_columns
    + [
        "stop_name",
        "hour",
        target_column,
        baseline_prediction_column,
        mlp_prediction_column,
        "baseline_absolute_error_seconds",
        "mlp_absolute_error_seconds",
        "mlp_error_improvement_seconds",
    ]
].copy()

comparison.to_csv(
    comparison_path,
    index=False,
)

by_stop.to_csv(
    by_stop_path,
    index=False,
)

by_hour.to_csv(
    by_hour_path,
    index=False,
)

worst_cases.to_csv(
    worst_cases_path,
    index=False,
)


figure_path.parent.mkdir(
    parents=True,
    exist_ok=True,
)

best_history_row = training_history.loc[
    training_history[
        "validation_mae_seconds"
    ].idxmin()
]

fig, axis = plt.subplots(
    figsize=(8, 5),
)

axis.plot(
    training_history["epoch"],
    training_history["validation_mae_seconds"] / 60,
    marker="o",
    label="PyTorch MLP validation MAE",
)

axis.axhline(
    baseline_metrics["mae_minutes"],
    color="tab:red",
    linestyle="--",
    label="Stop + hour median baseline",
)

axis.set_xlabel("Epoch")
axis.set_ylabel("Validation MAE (minutes)")
axis.set_title(
    "PyTorch MLP Validation Learning Curve"
)

axis.legend()

fig.tight_layout()

fig.savefig(
    figure_path,
    dpi=160,
)

plt.close(fig)


print("Overall comparison:")
print(comparison)

print("\nPerformance by stop:")
print(by_stop)

print("\nTop 10 hours by MLP improvement:")
print(by_hour.head(10))

print("\nWorst 20 MLP predictions saved to:")
print(worst_cases_path)

print("\nLearning-curve figure saved to:")
print(figure_path)
