from datetime import date, datetime, timedelta
from uuid import uuid4

import pytest

from app.domain.enums import BloodType, ForecastHorizon
from app.domain.forecasting.models import ForecastResult
from app.infrastructure.repositories.forecasting import SQLForecastRepository


@pytest.mark.asyncio
async def test_get_latest_returns_only_most_recent_batch(db_session):
    repo = SQLForecastRepository(db_session)
    hospital_id = uuid4()
    blood_type = BloodType.O_POSITIVE
    horizon = ForecastHorizon.DAILY

    old_batch = datetime.utcnow() - timedelta(hours=1)
    new_batch = datetime.utcnow()

    for forecast_date, predicted_units in [(date.today(), 10.0), (date.today() + timedelta(days=1), 11.0)]:
        forecast = ForecastResult.create(
            hospital_id=hospital_id,
            blood_type=blood_type,
            horizon=horizon,
            forecast_date=forecast_date,
            predicted_units=predicted_units,
            lower_bound=predicted_units - 1,
            upper_bound=predicted_units + 1,
            model_name="ensemble",
            confidence=0.9,
        )
        forecast.created_at = old_batch
        await repo.save(forecast)

    for forecast_date, predicted_units in [(date.today(), 20.0), (date.today() + timedelta(days=1), 21.0)]:
        forecast = ForecastResult.create(
            hospital_id=hospital_id,
            blood_type=blood_type,
            horizon=horizon,
            forecast_date=forecast_date,
            predicted_units=predicted_units,
            lower_bound=predicted_units - 1,
            upper_bound=predicted_units + 1,
            model_name="ensemble",
            confidence=0.9,
        )
        forecast.created_at = new_batch
        await repo.save(forecast)

    await db_session.commit()

    latest = await repo.get_latest(hospital_id, blood_type, horizon)

    assert len(latest) == 2
    assert [item.predicted_units for item in latest] == [20.0, 21.0]
    assert all(item.created_at == new_batch for item in latest)