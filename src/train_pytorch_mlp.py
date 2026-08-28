from pathlib import Path

from torch import nn
from torch.utils.data import DataLoader, TensorDataset
import numpy as np
import pandas as pd
import torch
import copy


project = Path(
    r"D:\Michael\Interesting Project\Madison Bus Delay Prediction"
)

train_path = project / "data" / "processed" / "baseline_train.csv"

validation_path = (
    project
    / "data"
    / "processed"
    / "baseline_validation.csv"
)

target_column = "actual_delay_seconds"

numeric_feature_columns = [
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
]

categorical_feature_columns = [
    "stop_name",
    "weather_code",
]

train_data = pd.read_csv(train_path)

validation_data = pd.read_csv(validation_path)

numeric_means = train_data[
    numeric_feature_columns
].mean()

numeric_stds = train_data[
    numeric_feature_columns
].std()

numeric_stds = numeric_stds.replace(0, 1)

category_levels = {
    column: sorted(
        train_data[column]
        .dropna()
        .astype("string")
        .unique()
        .tolist()
    )
    for column in categorical_feature_columns
}

def make_feature_table(
    data,
    numeric_means,
    numeric_stds,
    category_levels,
):
    numeric_features = data[
        numeric_feature_columns
    ].astype("float32").copy()

    numeric_features = (
        numeric_features - numeric_means
    ) / numeric_stds

    categorical_parts = []

    for column in categorical_feature_columns:
        category_values = pd.Categorical(
            data[column].astype("string"),
            categories=category_levels[column],
        )

        one_hot_features = pd.get_dummies(
            category_values,
            prefix=column,
            dtype="float32",
        )

        categorical_parts.append(one_hot_features)

    categorical_features = pd.concat(
        categorical_parts,
        axis=1,
    )

    feature_table = pd.concat(
        [
            numeric_features,
            categorical_features,
        ],
        axis=1,
    )

    return feature_table

train_features = make_feature_table(
    data=train_data,
    numeric_means=numeric_means,
    numeric_stds=numeric_stds,
    category_levels=category_levels,
)

validation_features = make_feature_table(
    data=validation_data,
    numeric_means=numeric_means,
    numeric_stds=numeric_stds,
    category_levels=category_levels,
)

feature_columns = train_features.columns.tolist()

validation_features = validation_features.reindex(
    columns=feature_columns,
    fill_value=0,
)

if train_features.isna().any().any():
    raise ValueError("Training features contain missing values.")

if validation_features.isna().any().any():
    raise ValueError("Validation features contain missing values.")

train_targets = train_data[
    target_column
].astype("float32")

validation_targets = validation_data[
    target_column
].astype("float32")

target_mean = train_targets.mean()

target_std = train_targets.std()

if target_std == 0:
    raise ValueError("Training target has zero standard deviation.")

train_targets_scaled = (
    train_targets - target_mean
) / target_std

validation_targets_scaled = (
    validation_targets - target_mean
) / target_std

X_train = torch.tensor(
    train_features.to_numpy(),
    dtype=torch.float32,
)

y_train = torch.tensor(
    train_targets_scaled.to_numpy(),
    dtype=torch.float32,
)

X_validation = torch.tensor(
    validation_features.to_numpy(),
    dtype=torch.float32,
)

y_validation = torch.tensor(
    validation_targets_scaled.to_numpy(),
    dtype=torch.float32,
)


# print("PyTorch version:", torch.__version__)
# print("Training feature shape:", tuple(X_train.shape))
# print("Validation feature shape:", tuple(X_validation.shape))
# print("Training target shape:", tuple(y_train.shape))
# print("Feature columns:", feature_columns)
# print("Target mean:", target_mean)
# print("Target standard deviation:", target_std)

random_seed = 42
batch_size = 256

torch.manual_seed(random_seed)


training_dataset = TensorDataset(
    X_train,
    y_train,
)

training_loader = DataLoader(
    training_dataset,
    batch_size=batch_size,
    shuffle=True,
)

class DelayMLP(nn.Module):
    def __init__(self, input_size):
        super().__init__()

        self.network = nn.Sequential(
            nn.Linear(input_size, 64),
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
        )

    def forward(self, features):
        return self.network(features).squeeze(1)

device = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

model = DelayMLP(
    input_size=X_train.shape[1]
).to(device)


first_feature_batch, first_target_batch = next(
    iter(training_loader)
)

first_predictions = model(
    first_feature_batch.to(device)
)

# print("Device:", device)
# print("One feature batch shape:", tuple(first_feature_batch.shape))
# print("One target batch shape:", tuple(first_target_batch.shape))
# print("One prediction batch shape:", tuple(first_predictions.shape))
# print("Model:")
# print(model)

learning_rate = 0.001
max_epochs = 200
early_stopping_patience = 20

loss_function = nn.L1Loss()

optimizer = torch.optim.AdamW(
    model.parameters(),
    lr=learning_rate,
    weight_decay=0.0001,
)

X_validation_on_device = X_validation.to(device)

validation_targets_array = (
    validation_targets
    .to_numpy()
)

best_validation_mae_seconds = np.inf
best_epoch = 0
best_model_state = None
epochs_without_improvement = 0

training_history_rows = []

for epoch in range(1, max_epochs + 1):
    model.train()

    total_training_loss = 0.0
    total_training_rows = 0

    for feature_batch, target_batch in training_loader:
        feature_batch = feature_batch.to(device)
        target_batch = target_batch.to(device)

        optimizer.zero_grad()

        prediction_batch = model(feature_batch)

        loss = loss_function(
            prediction_batch,
            target_batch,
        )

        loss.backward()

        optimizer.step()

        total_training_loss += (
            loss.item()
            * feature_batch.size(0)
        )

        total_training_rows += feature_batch.size(0)

    training_loss = (
        total_training_loss
        / total_training_rows
    )

    model.eval()

    with torch.no_grad():
        validation_predictions_scaled = model(
            X_validation_on_device
        ).cpu().numpy()

    validation_predictions_seconds = (
        validation_predictions_scaled
        * target_std
        + target_mean
    )

    validation_absolute_errors = np.abs(
        validation_targets_array
        - validation_predictions_seconds
    )

    validation_mae_seconds = (
        validation_absolute_errors.mean()
    )

    training_history_rows.append(
        {
            "epoch": epoch,
            "training_l1_loss_scaled": training_loss,
            "validation_mae_seconds": validation_mae_seconds,
        }
    )

    if validation_mae_seconds < best_validation_mae_seconds:
        best_validation_mae_seconds = validation_mae_seconds
        best_epoch = epoch

        best_model_state = copy.deepcopy(
            model.state_dict()
        )

        epochs_without_improvement = 0

    else:
        epochs_without_improvement += 1

    if epoch == 1 or epoch % 10 == 0:
        print(
            f"Epoch {epoch:03d} | "
            f"train L1 loss: {training_loss:.4f} | "
            f"validation MAE: "
            f"{validation_mae_seconds / 60:.3f} minutes"
        )

    if epochs_without_improvement >= early_stopping_patience:
        print(
            "Early stopping at epoch:",
            epoch,
        )

        break

model.load_state_dict(best_model_state)

model.eval()

with torch.no_grad():
    best_validation_predictions_scaled = model(
        X_validation_on_device
    ).cpu().numpy()

best_validation_predictions_seconds = (
    best_validation_predictions_scaled
    * target_std
    + target_mean
)

best_validation_absolute_errors = np.abs(
    validation_targets_array
    - best_validation_predictions_seconds
)

best_validation_within_2_minutes = (
    best_validation_absolute_errors <= 120
).mean()

history_path = (
    project
    / "data"
    / "processed"
    / "pytorch_mlp_training_history.csv"
)

predictions_path = (
    project
    / "data"
    / "processed"
    / "pytorch_mlp_validation_predictions.csv"
)

metrics_path = (
    project
    / "data"
    / "processed"
    / "pytorch_mlp_validation_metrics.csv"
)

model_path = (
    project
    / "data"
    / "processed"
    / "pytorch_mlp_best.pt"
)

training_history = pd.DataFrame(
    training_history_rows
)

training_history.to_csv(
    history_path,
    index=False,
)

validation_predictions_table = validation_data[
    [
        "service_date",
        "trip_id",
        "stop_id",
        "stop_name",
        "prediction_time",
        "actual_delay_seconds",
    ]
].copy()

validation_predictions_table[
    "prediction_pytorch_mlp_seconds"
] = best_validation_predictions_seconds

validation_predictions_table[
    "absolute_error_seconds"
] = best_validation_absolute_errors

validation_predictions_table.to_csv(
    predictions_path,
    index=False,
)

metrics = pd.DataFrame(
    [
        {
            "model": "pytorch_mlp_no_gps",
            "best_epoch": best_epoch,
            "mae_seconds": best_validation_mae_seconds,
            "mae_minutes": (
                best_validation_mae_seconds / 60
            ),
            "within_2_minutes": (
                best_validation_within_2_minutes
            ),
        }
    ]
)

metrics.to_csv(
    metrics_path,
    index=False,
)


torch.save(
    {
        "model_state_dict": model.state_dict(),
        "feature_columns": feature_columns,
        "numeric_means": numeric_means.to_dict(),
        "numeric_stds": numeric_stds.to_dict(),
        "category_levels": category_levels,
        "target_mean": float(target_mean),
        "target_std": float(target_std),
    },
    model_path,
)


print("\nBest epoch:", best_epoch)

print(
    "Best validation MAE:",
    f"{best_validation_mae_seconds:.2f} seconds",
    f"({best_validation_mae_seconds / 60:.3f} minutes)",
)

print(
    "Validation predictions within 2 minutes:",
    f"{best_validation_within_2_minutes:.2%}",
)

print(
    "Baseline MAE:",
    "2.183 minutes",
)
