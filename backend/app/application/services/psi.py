"""
PSI (Pressure Supply Index) service.

PSI = (Stock Netto Valido + Ingressi Netti Previsti) / Domanda Prevista

PSI >= 1  →  supply sufficient
PSI < 1   →  shortfall risk

Components:
- Stock Netto Valido: units that will NOT expire within the forecast horizon
  (expired and reserved units are excluded)
- Domanda Prevista: statistical estimate based on historical consumption,
  using a configurable percentile (50 = normal, 95 = stress)
  with static (full history) or EWMA (recent-weighted) approach
- Ingressi Netti Previsti: conservative median of historical inflows,
  discounted by a friction factor δ (default 5%)
"""
from __future__ import annotations

import math
import uuid
from dataclasses import dataclass
from datetime import date, timedelta
from enum import Enum
from typing import Literal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import BloodType
from app.infrastructure.database.models import BloodConsumptionORM, BloodUnitORM


class ScenarioMethod(str, Enum):
    STATIC = "static"   # full history percentile
    EWMA = "ewma"       # exponentially-weighted moving average


@dataclass(frozen=True)
class PSIBloodTypeResult:
    blood_type: BloodType
    psi: float
    stock_total: float
    stock_net_valid: float
    expected_demand: float
    expected_inflows: float
    horizon_days: int
    percentile: int
    method: ScenarioMethod
    at_risk_units: float           # stock_total - stock_net_valid


@dataclass(frozen=True)
class PSIHospitalResult:
    hospital_id: uuid.UUID
    horizon_days: int
    percentile: int
    method: ScenarioMethod
    by_blood_type: list[PSIBloodTypeResult]
    overall_psi: float             # weighted average by demand
    critical_types: list[BloodType]  # PSI < 1.0


class PSIService:
    """Calculates the PSI for a hospital across all blood types."""

    DEFAULT_HISTORY_DAYS = 90
    DEFAULT_EWMA_SPAN = 30        # decay span in days
    DEFAULT_FRICTION = 0.05       # δ: fraction of inflows to subtract
    PSI_CRITICAL_THRESHOLD = 1.0

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def compute(
        self,
        hospital_id: uuid.UUID,
        horizon_days: int = 7,
        percentile: int = 95,
        method: ScenarioMethod = ScenarioMethod.STATIC,
        history_days: int = DEFAULT_HISTORY_DAYS,
        friction: float = DEFAULT_FRICTION,
        ewma_span: int = DEFAULT_EWMA_SPAN,
    ) -> PSIHospitalResult:
        today = date.today()
        history_start = today - timedelta(days=history_days)

        results: list[PSIBloodTypeResult] = []

        for blood_type in BloodType:
            stock_total, stock_net_valid = await self._compute_stock(
                hospital_id, blood_type, today, horizon_days
            )
            expected_demand = await self._compute_demand(
                hospital_id, blood_type, today, horizon_days,
                history_start, percentile, method, ewma_span
            )
            expected_inflows = await self._compute_inflows(
                hospital_id, blood_type, today, horizon_days,
                history_start, friction
            )

            if expected_demand <= 0:
                psi = float("inf")
            else:
                psi = (stock_net_valid + expected_inflows) / expected_demand

            results.append(PSIBloodTypeResult(
                blood_type=blood_type,
                psi=round(psi, 3),
                stock_total=round(stock_total, 1),
                stock_net_valid=round(stock_net_valid, 1),
                expected_demand=round(expected_demand, 1),
                expected_inflows=round(expected_inflows, 1),
                horizon_days=horizon_days,
                percentile=percentile,
                method=method,
                at_risk_units=round(stock_total - stock_net_valid, 1),
            ))

        # weighted overall PSI (weights = expected_demand per type)
        total_demand = sum(r.expected_demand for r in results)
        if total_demand > 0:
            overall_psi = sum(
                r.psi * r.expected_demand for r in results
                if not math.isinf(r.psi)
            ) / total_demand
        else:
            overall_psi = float("inf")

        critical = [
            r.blood_type for r in results
            if r.psi < self.PSI_CRITICAL_THRESHOLD
        ]

        return PSIHospitalResult(
            hospital_id=hospital_id,
            horizon_days=horizon_days,
            percentile=percentile,
            method=method,
            by_blood_type=results,
            overall_psi=round(overall_psi, 3),
            critical_types=critical,
        )

    # ── Private helpers ───────────────────────────────────────────────────────

    async def _compute_stock(
        self,
        hospital_id: uuid.UUID,
        blood_type: BloodType,
        today: date,
        horizon_days: int,
    ) -> tuple[float, float]:
        """Returns (stock_total, stock_net_valid)."""
        horizon_cutoff = today + timedelta(days=horizon_days)

        stmt = select(BloodUnitORM).where(
            BloodUnitORM.hospital_id == hospital_id,
            BloodUnitORM.blood_type == blood_type,
            BloodUnitORM.expiry_date >= today,
        )
        result = await self._session.execute(stmt)
        units = result.scalars().all()

        stock_total = sum(
            max(0, u.units_available - u.units_reserved) for u in units
        )
        stock_net_valid = sum(
            max(0, u.units_available - u.units_reserved)
            for u in units
            if u.expiry_date > horizon_cutoff
        )
        return float(stock_total), float(stock_net_valid)

    async def _get_daily_consumption_series(
        self,
        hospital_id: uuid.UUID,
        blood_type: BloodType,
        start_date: date,
        end_date: date,
    ) -> list[float]:
        """Returns a list of daily totals (one per day in range)."""
        stmt = (
            select(
                BloodConsumptionORM.consumption_date,
                func.sum(BloodConsumptionORM.units_consumed).label("total"),
            )
            .where(
                BloodConsumptionORM.hospital_id == hospital_id,
                BloodConsumptionORM.blood_type == blood_type,
                BloodConsumptionORM.consumption_date >= start_date,
                BloodConsumptionORM.consumption_date <= end_date,
            )
            .group_by(BloodConsumptionORM.consumption_date)
            .order_by(BloodConsumptionORM.consumption_date)
        )
        result = await self._session.execute(stmt)
        rows = {r.consumption_date: float(r.total) for r in result}

        # fill gaps with 0
        days = (end_date - start_date).days + 1
        return [rows.get(start_date + timedelta(days=i), 0.0) for i in range(days)]

    async def _compute_demand(
        self,
        hospital_id: uuid.UUID,
        blood_type: BloodType,
        today: date,
        horizon_days: int,
        history_start: date,
        percentile: int,
        method: ScenarioMethod,
        ewma_span: int,
    ) -> float:
        """Estimated total demand over horizon_days."""
        history_end = today - timedelta(days=1)
        daily = await self._get_daily_consumption_series(
            hospital_id, blood_type, history_start, history_end
        )

        if not daily or all(v == 0 for v in daily):
            return 0.0

        if method == ScenarioMethod.STATIC:
            daily_estimate = self._percentile(daily, percentile)
        else:
            daily_estimate = self._ewma_stress(daily, ewma_span, percentile)

        return daily_estimate * horizon_days

    async def _compute_inflows(
        self,
        hospital_id: uuid.UUID,
        blood_type: BloodType,
        today: date,
        horizon_days: int,
        history_start: date,
        friction: float,
    ) -> float:
        """
        Conservative inflow estimate over horizon_days.
        Uses the median of daily additions (proxy: units added = new records with expiry > today).
        Discounted by friction factor δ.
        """
        # Proxy: new BloodUnit rows created in the history window represent inflows
        history_end = today - timedelta(days=1)
        date_col = func.date(BloodUnitORM.last_updated).label("day")
        stmt = (
            select(
                date_col,
                func.sum(BloodUnitORM.units_available).label("total"),
            )
            .where(
                BloodUnitORM.hospital_id == hospital_id,
                BloodUnitORM.blood_type == blood_type,
                func.date(BloodUnitORM.last_updated) >= history_start,
                func.date(BloodUnitORM.last_updated) <= history_end,
            )
            .group_by(date_col)
        )
        result = await self._session.execute(stmt)
        rows = result.all()

        if not rows:
            return 0.0

        days = (history_end - history_start).days + 1
        daily_totals = [float(r.total) for r in rows]
        # pad with zeros for days without inflows
        all_days = daily_totals + [0.0] * (days - len(daily_totals))

        median_daily = self._percentile(all_days, 50)
        return median_daily * horizon_days * (1.0 - friction)

    @staticmethod
    def _percentile(data: list[float], p: int) -> float:
        if not data:
            return 0.0
        sorted_data = sorted(data)
        n = len(sorted_data)
        idx = (p / 100) * (n - 1)
        lo = int(idx)
        hi = min(lo + 1, n - 1)
        frac = idx - lo
        return sorted_data[lo] + frac * (sorted_data[hi] - sorted_data[lo])

    @staticmethod
    def _ewma_stress(data: list[float], span: int, percentile: int) -> float:
        """μ_ewma + Z * σ_ewma where Z ≈ norm.ppf(percentile/100)."""
        if not data:
            return 0.0
        alpha = 2.0 / (span + 1)
        mu = data[0]
        variance = 0.0
        for v in data[1:]:
            variance = alpha * (v - mu) ** 2 + (1 - alpha) * variance
            mu = alpha * v + (1 - alpha) * mu
        sigma = math.sqrt(variance)

        # approximate normal quantile (Beasley-Springer-Moro)
        p = percentile / 100.0
        p = max(0.0001, min(0.9999, p))
        if p == 0.5:
            z = 0.0
        else:
            # rational approximation
            sign = 1 if p > 0.5 else -1
            q = p if p > 0.5 else 1 - p
            t = math.sqrt(-2 * math.log(1 - q))
            c0, c1, c2 = 2.515517, 0.802853, 0.010328
            d1, d2, d3 = 1.432788, 0.189269, 0.001308
            z = sign * (t - (c0 + c1 * t + c2 * t**2) / (1 + d1 * t + d2 * t**2 + d3 * t**3))

        return max(0.0, mu + z * sigma)
