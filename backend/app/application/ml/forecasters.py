from __future__ import annotations

from datetime import date, timedelta
from typing import Protocol

import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder


class ForecastOutput:
    def __init__(
        self,
        dates: list[date],
        predicted: list[float],
        lower: list[float],
        upper: list[float],
        model_name: str,
        confidence: float,
    ) -> None:
        self.dates = dates
        self.predicted = predicted
        self.lower = lower
        self.upper = upper
        self.model_name = model_name
        self.confidence = confidence


class BaseForecaster(Protocol):
    def fit(self, df: pd.DataFrame) -> None: ...
    def predict(self, horizon: int) -> ForecastOutput: ...


class ProphetForecaster:
    MODEL_NAME = "prophet"

    def __init__(self) -> None:
        self._model = None
        self._last_date: date | None = None

    def fit(self, df: pd.DataFrame) -> None:
        from prophet import Prophet  # type: ignore

        train = df.rename(columns={"ds": "ds", "y": "y"})[["ds", "y"]]
        self._model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=True,
            daily_seasonality=False,
            interval_width=0.95,
            changepoint_prior_scale=0.05,
        )
        self._model.fit(train)
        self._last_date = train["ds"].max().date()

    def predict(self, horizon: int) -> ForecastOutput:
        if self._model is None:
            raise RuntimeError("Model not fitted yet")
        future = self._model.make_future_dataframe(periods=horizon, freq="D")
        forecast = self._model.predict(future)
        tail = forecast.tail(horizon)

        dates = [pd.Timestamp(d).date() for d in tail["ds"]]
        predicted = [max(0.0, float(v)) for v in tail["yhat"]]
        lower = [max(0.0, float(v)) for v in tail["yhat_lower"]]
        upper = [max(0.0, float(v)) for v in tail["yhat_upper"]]

        return ForecastOutput(
            dates=dates,
            predicted=predicted,
            lower=lower,
            upper=upper,
            model_name=self.MODEL_NAME,
            confidence=0.95,
        )


class XGBoostForecaster:
    MODEL_NAME = "xgboost"
    LAG_DAYS = [1, 7, 14, 21, 28]
    WINDOW_SIZES = [7, 14, 28]

    def __init__(self) -> None:
        self._model = None
        self._last_date: date | None = None
        self._history: pd.DataFrame | None = None

    def _create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["dayofweek"] = df["ds"].dt.dayofweek
        df["month"] = df["ds"].dt.month
        df["quarter"] = df["ds"].dt.quarter
        df["dayofyear"] = df["ds"].dt.dayofyear
        for lag in self.LAG_DAYS:
            df[f"lag_{lag}"] = df["y"].shift(lag)
        for w in self.WINDOW_SIZES:
            df[f"rolling_mean_{w}"] = df["y"].shift(1).rolling(w).mean()
            df[f"rolling_std_{w}"] = df["y"].shift(1).rolling(w).std()
        return df.dropna()

    def fit(self, df: pd.DataFrame) -> None:
        import xgboost as xgb  # type: ignore

        self._history = df.copy()
        featured = self._create_features(df)
        feature_cols = [c for c in featured.columns if c not in ["ds", "y"]]
        X = featured[feature_cols].values
        y = featured["y"].values

        self._model = xgb.XGBRegressor(
            n_estimators=200,
            max_depth=5,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
        )
        self._model.fit(X, y)
        self._last_date = df["ds"].max().date()
        self._feature_cols = feature_cols

    def predict(self, horizon: int) -> ForecastOutput:
        if self._model is None or self._history is None:
            raise RuntimeError("Model not fitted yet")

        history = self._history.copy()
        preds: list[float] = []
        future_dates: list[date] = []

        for i in range(horizon):
            next_date = history["ds"].max() + pd.Timedelta(days=1)
            new_row = pd.DataFrame({"ds": [next_date], "y": [np.nan]})
            history = pd.concat([history, new_row], ignore_index=True)
            featured = self._create_features(history)
            last_row = featured.iloc[[-1]][self._feature_cols]
            pred = float(self._model.predict(last_row.values)[0])
            pred = max(0.0, pred)
            history.iloc[-1, history.columns.get_loc("y")] = pred
            preds.append(pred)
            future_dates.append(next_date.date())

        # Confidence intervals using rolling std
        std_dev = float(self._history["y"].std()) or 1.0
        lower = [max(0.0, p - 1.96 * std_dev) for p in preds]
        upper = [p + 1.96 * std_dev for p in preds]

        return ForecastOutput(
            dates=future_dates,
            predicted=preds,
            lower=lower,
            upper=upper,
            model_name=self.MODEL_NAME,
            confidence=0.80,
        )


class EnsembleForecaster:
    MODEL_NAME = "ensemble"

    def __init__(self) -> None:
        self._prophet = ProphetForecaster()
        self._xgb = XGBoostForecaster()

    def fit(self, df: pd.DataFrame) -> None:
        try:
            self._prophet.fit(df)
            self._prophet_ok = True
        except Exception:
            self._prophet_ok = False

        try:
            self._xgb.fit(df)
            self._xgb_ok = True
        except Exception:
            self._xgb_ok = False

    def predict(self, horizon: int) -> ForecastOutput:
        outputs: list[ForecastOutput] = []
        if self._prophet_ok:
            outputs.append(self._prophet.predict(horizon))
        if self._xgb_ok:
            outputs.append(self._xgb.predict(horizon))

        if not outputs:
            raise RuntimeError("All forecasters failed")

        if len(outputs) == 1:
            return outputs[0]

        # Average predictions
        dates = outputs[0].dates
        predicted = [
            float(np.mean([o.predicted[i] for o in outputs])) for i in range(horizon)
        ]
        lower = [
            float(np.min([o.lower[i] for o in outputs])) for i in range(horizon)
        ]
        upper = [
            float(np.max([o.upper[i] for o in outputs])) for i in range(horizon)
        ]

        return ForecastOutput(
            dates=dates,
            predicted=predicted,
            lower=lower,
            upper=upper,
            model_name=self.MODEL_NAME,
            confidence=0.90,
        )
