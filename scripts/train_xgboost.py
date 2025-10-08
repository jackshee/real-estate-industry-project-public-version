#!/usr/bin/env python3
"""
Utility to train and tune an XGBoost rental price model via cross-validated
hyperparameter search. The script wraps the feature preprocessing pipeline that
was previously explored in the modelling notebook, runs a randomized search
over key XGBoost parameters, evaluates on a held-out test set, and persists
both the trained pipeline and evaluation artefacts for downstream use.
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any, List, Sequence

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    mean_absolute_error,
    mean_absolute_percentage_error,
    mean_squared_error,
    median_absolute_error,
    r2_score,
)
from sklearn.model_selection import RandomizedSearchCV, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from xgboost import XGBRegressor

# Columns mirrored from the exploratory notebook
CAT_COLS: Sequence[str] = (
    "property_type",
    "suburb",
    "postcode",
    "agency_name",
    "agent_name",
    "appointment_only",
    "listing_status",
)

NUM_COLS: Sequence[str] = (
    "bedrooms",
    "bathrooms",
    "car_spaces",
    "land_area",
    "year",
    "quarter",
    "age_0_to_19",
    "age_20_to_39",
    "age_40_to_59",
    "age_60_plus",
    "avg_days_on_market",
    "family_percentage",
    "long_term_resident",
    "median_rent_price",
    "median_sold_price",
    "number_sold",
    "renter_percentage",
    "single_percentage",
)


def _load_dataset(path: Path, target_col: str) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Could not find dataset at {path}")

    df = pd.read_csv(path)
    if target_col not in df.columns:
        raise KeyError(f"Target column '{target_col}' not present in dataset")

    df[target_col] = pd.to_numeric(df[target_col], errors="coerce")
    df = df.dropna(subset=[target_col])

    # Ensure numeric columns are truly numeric for downstream imputers
    for col in NUM_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    missing_cols = set(CAT_COLS + NUM_COLS) - set(df.columns)
    if missing_cols:
        raise KeyError(
            "The following required feature columns are missing from the dataset: "
            f"{sorted(missing_cols)}"
        )

    return df


def _build_preprocessor() -> ColumnTransformer:
    return ColumnTransformer(
        transformers=[
            ("num", SimpleImputer(strategy="median"), list(NUM_COLS)),
            (
                "cat",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("encoder", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                list(CAT_COLS),
            ),
        ],
        remainder="drop",
    )


def _build_model(random_state: int) -> Pipeline:
    preprocessor = _build_preprocessor()

    regressor = XGBRegressor(
        objective="reg:squarederror",
        n_estimators=600,
        learning_rate=0.05,
        max_depth=6,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=1.0,
        reg_alpha=0.0,
        reg_lambda=1.0,
        gamma=0.0,
        n_jobs=-1,
        random_state=random_state,
    )

    return Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("regressor", regressor),
        ]
    )


def _get_search_space() -> dict[str, Sequence[Any]]:
    return {
        "regressor__n_estimators": [200, 400, 600, 800, 1000],
        "regressor__max_depth": [3, 4, 5, 6, 8, 10],
        "regressor__learning_rate": np.round(np.logspace(-2.3, -0.3, 12), 4),
        "regressor__subsample": np.round(np.linspace(0.5, 1.0, 6), 2),
        "regressor__colsample_bytree": np.round(np.linspace(0.5, 1.0, 6), 2),
        "regressor__min_child_weight": [1, 3, 5, 7, 10],
        "regressor__gamma": np.round(np.linspace(0.0, 0.4, 5), 3),
        "regressor__reg_alpha": np.round(np.logspace(-4, 0, 6), 6),
        "regressor__reg_lambda": np.round(np.logspace(-3, 1, 6), 6),
    }


def _evaluate(
    model: Pipeline, X_test: pd.DataFrame, y_test: pd.Series
) -> dict[str, float]:
    preds = model.predict(X_test)

    mse = mean_squared_error(y_test, preds)
    rmse = float(np.sqrt(mse))
    mae = float(mean_absolute_error(y_test, preds))
    medae = float(median_absolute_error(y_test, preds))
    r2 = float(r2_score(y_test, preds))

    try:
        mape = float(mean_absolute_percentage_error(y_test, preds))
    except ZeroDivisionError:
        mape = float("nan")

    smape = float(
        np.mean(
            2.0 * np.abs(preds - y_test) / (np.abs(y_test) + np.abs(preds) + 1e-12)
        )
    )

    return {
        "rmse": rmse,
        "mae": mae,
        "median_ae": medae,
        "r2": r2,
        "mape": mape,
        "smape": smape,
    }


def _top_features(
    model: Pipeline, top_k: int = 20
) -> List[dict[str, float]]:
    preprocessor: ColumnTransformer = model.named_steps["preprocessor"]
    regressor: XGBRegressor = model.named_steps["regressor"]

    feature_names = preprocessor.get_feature_names_out()
    importances = getattr(regressor, "feature_importances_", None)

    if importances is None:
        return []

    order = np.argsort(importances)[::-1][:top_k]
    return [
        {
            "feature": str(feature_names[idx]),
            "importance": float(importances[idx]),
        }
        for idx in order
    ]


def run_training(args: argparse.Namespace) -> None:
    logging.info("Loading dataset from %s", args.data_path)
    df = _load_dataset(Path(args.data_path), args.target)

    X = df[list(NUM_COLS) + list(CAT_COLS)]
    y = df[args.target]

    logging.info(
        "Splitting data with test size %.2f and random_state=%d",
        args.test_size,
        args.random_state,
    )
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=args.test_size,
        random_state=args.random_state,
    )

    pipeline = _build_model(random_state=args.random_state)
    param_distributions = _get_search_space()

    logging.info(
        "Starting randomized hyperparameter search (n_iter=%d, cv=%d, scoring=%s)",
        args.n_iter,
        args.cv,
        args.scoring,
    )
    search = RandomizedSearchCV(
        estimator=pipeline,
        param_distributions=param_distributions,
        n_iter=args.n_iter,
        cv=args.cv,
        scoring=args.scoring,
        n_jobs=args.n_jobs,
        verbose=args.verbose,
        random_state=args.random_state,
        refit=True,
        return_train_score=True,
    )
    search.fit(X_train, y_train)

    best_model: Pipeline = search.best_estimator_
    metrics = _evaluate(best_model, X_test, y_test)
    top_features = _top_features(best_model, top_k=args.top_k_features)

    logging.info("Best CV score: %.4f", search.best_score_)
    logging.info("Test RMSE: %.3f | R^2: %.4f", metrics["rmse"], metrics["r2"])

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    model_path = output_dir / "xgboost_pipeline.joblib"
    joblib.dump(best_model, model_path)
    logging.info("Persisted trained pipeline to %s", model_path)

    metrics_payload = {
        "metrics": metrics,
        "best_params": search.best_params_,
        "best_cv_score": float(search.best_score_),
        "cv_results_path": str(output_dir / "cv_results.csv"),
        "target": args.target,
        "test_size": args.test_size,
        "cv": args.cv,
        "n_iter": args.n_iter,
        "random_state": args.random_state,
        "top_features": top_features,
    }

    with open(output_dir / "metrics.json", "w", encoding="utf-8") as handle:
        json.dump(metrics_payload, handle, indent=2)
    logging.info("Wrote evaluation artefacts to %s", output_dir / "metrics.json")

    cv_results = pd.DataFrame(search.cv_results_)
    cv_results.to_csv(output_dir / "cv_results.csv", index=False)

    logging.info("Hyperparameter search complete.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train and tune an XGBoost model for rental price prediction."
    )
    parser.add_argument(
        "--data-path",
        type=str,
        default="data/curated/rent_features/cleaned_listings.csv",
        help="Path to the prepared feature dataset (CSV).",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="models/xgboost",
        help="Directory where the trained model and artefacts will be written.",
    )
    parser.add_argument(
        "--target",
        type=str,
        default="weekly_rent",
        help="Name of the target column to predict.",
    )
    parser.add_argument(
        "--test-size",
        type=float,
        default=0.2,
        help="Size of the held-out test split (fraction).",
    )
    parser.add_argument(
        "--random-state",
        type=int,
        default=42,
        help="Random seed for reproducibility.",
    )
    parser.add_argument(
        "--cv",
        type=int,
        default=3,
        help="Number of cross-validation folds for hyperparameter search.",
    )
    parser.add_argument(
        "--n-iter",
        type=int,
        default=30,
        help="Number of randomized search iterations.",
    )
    parser.add_argument(
        "--scoring",
        type=str,
        default="neg_root_mean_squared_error",
        help="Scikit-learn scoring metric for cross-validation.",
    )
    parser.add_argument(
        "--n-jobs",
        type=int,
        default=-1,
        help="Number of parallel jobs for the search (-1 uses all cores).",
    )
    parser.add_argument(
        "--verbose",
        type=int,
        default=1,
        help="Verbosity level for scikit-learn's RandomizedSearchCV.",
    )
    parser.add_argument(
        "--top-k-features",
        type=int,
        default=20,
        help="Number of top feature importances to include in the metrics payload.",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level for the script.",
    )
    return parser.parse_args()


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level),
        format="[%(asctime)s] %(levelname)s: %(message)s",
    )


def main() -> None:
    args = parse_args()
    configure_logging(args.log_level)
    run_training(args)


if __name__ == "__main__":
    main()

