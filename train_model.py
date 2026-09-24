"""
Model Training Script.

Trains a Random Forest gesture classifier using normalized landmark features
from data/dataset.csv and saves the model to models/gun_gesture_model.pkl.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split

from hand_tracker import NUM_FEATURES, get_feature_names

DATA_DIR = Path(__file__).resolve().parent / "data"
MODELS_DIR = Path(__file__).resolve().parent / "models"
DEFAULT_DATASET = DATA_DIR / "dataset.csv"
DEFAULT_MODEL_PATH = MODELS_DIR / "gun_gesture_model.pkl"

REQUIRED_CLASSES = {"NO_GUN", "GUN_READY", "SHOOT"}


def load_and_validate_dataset(csv_path: Path):
    """
    Load dataset and validate schema and classes.
    """
    if not csv_path.exists():
        print(f"[ERROR] Dataset file not found at: {csv_path}")
        print("Please run 'python collect_data.py' to record gesture samples first.")
        sys.exit(1)

    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        print(f"[ERROR] Failed to read dataset CSV: {e}")
        sys.exit(1)

    if "label" not in df.columns:
        print("[ERROR] Dataset missing 'label' column.")
        sys.exit(1)

    feature_cols = [col for col in df.columns if col != "label"]
    if len(feature_cols) != NUM_FEATURES:
        print(
            f"[ERROR] Expected {NUM_FEATURES} numerical feature columns, found {len(feature_cols)}."
        )
        sys.exit(1)

    # Check for NaN / nulls
    if df.isnull().values.any():
        print("[Warning] Found NaN values in dataset. Dropping invalid rows...")
        df = df.dropna().reset_index(drop=True)

    present_classes = set(df["label"].unique())
    missing_classes = REQUIRED_CLASSES - present_classes
    if missing_classes:
        print(f"[ERROR] Dataset must contain all 3 classes: {REQUIRED_CLASSES}")
        print(f"Missing classes: {missing_classes}")
        print(f"Classes currently present: {present_classes}")
        print("Please record samples for the missing classes using 'python collect_data.py'.")
        sys.exit(1)

    return df, feature_cols


def main() -> None:
    parser = argparse.ArgumentParser(description="Train Hand Gun gesture recognition model.")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATASET, help="Path to dataset.csv")
    parser.add_argument("--output", type=Path, default=DEFAULT_MODEL_PATH, help="Path for saved model .pkl")
    parser.add_argument("--trees", type=int, default=300, help="Number of trees in Random Forest")
    parser.add_argument("--test-size", type=float, default=0.2, help="Fraction for test evaluation")
    parser.add_argument("--jobs", type=int, default=1, help="Number of parallel jobs (default: 1)")
    args = parser.parse_args()

    print("\n" + "=" * 65)
    print("      HAND GUN GESTURE MODEL TRAINING")
    print("=" * 65)

    df, feature_cols = load_and_validate_dataset(args.data)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    X = df[feature_cols].to_numpy(dtype=np.float32)
    y = df["label"].to_numpy()

    print(f"Total samples: {len(df)}")
    print("Class distribution:")
    for label, count in df["label"].value_counts().items():
        print(f"  - {label:<12}: {count:>5} samples ({count / len(df) * 100:.1f}%)")

    # Check minimum samples per class for stratified splitting
    min_count = df["label"].value_counts().min()
    if min_count < 10:
        print(f"[ERROR] Too few samples in smallest class ({min_count}). Collect at least 10 samples.")
        sys.exit(1)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=args.test_size,
        stratify=y,
        random_state=42,
    )

    print(f"\nTraining set size: {len(X_train)}")
    print(f"Test set size:     {len(X_test)}")
    print(f"Training RandomForestClassifier (n_estimators={args.trees}, n_jobs={args.jobs})...")

    clf = RandomForestClassifier(
        n_estimators=args.trees,
        random_state=42,
        n_jobs=args.jobs,
        class_weight="balanced",
    )
    clf.fit(X_train, y_train)

    train_acc = clf.score(X_train, y_train)
    test_acc = clf.score(X_test, y_test)

    print("\n" + "-" * 65)
    print(f"Training Accuracy:   {train_acc * 100:.2f}%")
    print(f"Test Accuracy:       {test_acc * 100:.2f}%")
    print("-" * 65)

    y_pred = clf.predict(X_test)

    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, digits=4))

    labels_order = sorted(list(REQUIRED_CLASSES))
    print("Confusion Matrix:")
    cm = confusion_matrix(y_test, y_pred, labels=labels_order)
    header = "          " + "".join([f"{l:>12}" for l in labels_order])
    print(header)
    for idx, row_label in enumerate(labels_order):
        row_str = f"{row_label:<10}" + "".join([f"{val:>12}" for val in cm[idx]])
        print(row_str)

    # Save model artifact
    save_payload = {
        "model": clf,
        "classes": clf.classes_.tolist(),
        "feature_names": feature_cols,
        "trained_at": datetime.now().isoformat(),
        "train_accuracy": float(train_acc),
        "test_accuracy": float(test_acc),
    }

    joblib.dump(save_payload, args.output)
    print("\n" + "=" * 65)
    print(f"[SUCCESS] Model successfully saved to: {args.output}")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    main()
