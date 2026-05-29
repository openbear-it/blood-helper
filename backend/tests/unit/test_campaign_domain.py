import pytest
from datetime import date, timedelta
from uuid import uuid4

from app.domain.enums import BloodType, CampaignStatus
from app.domain.forecasting.models import DonationCampaign


class TestDonationCampaign:
    def _make_campaign(self, **kwargs) -> DonationCampaign:
        defaults = dict(
            hospital_id=uuid4(),
            title="Test Campaign",
            description="desc",
            target_blood_types=[BloodType.O_POSITIVE],
            target_units=100,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
        )
        defaults.update(kwargs)
        return DonationCampaign.create(**defaults)

    def test_create_campaign(self):
        c = self._make_campaign()
        assert c.status == CampaignStatus.DRAFT
        assert c.collected_units == 0
        assert c.progress_percentage == 0.0

    def test_activate(self):
        c = self._make_campaign()
        c.activate()
        assert c.status == CampaignStatus.ACTIVE

    def test_activate_non_draft_raises(self):
        c = self._make_campaign()
        c.activate()
        with pytest.raises(ValueError):
            c.activate()

    def test_record_donation(self):
        c = self._make_campaign()
        c.activate()
        c.record_donation(50)
        assert c.collected_units == 50
        assert c.progress_percentage == 50.0

    def test_auto_complete_on_goal(self):
        c = self._make_campaign(target_units=10)
        c.activate()
        c.record_donation(10)
        assert c.status == CampaignStatus.COMPLETED

    def test_cancel(self):
        c = self._make_campaign()
        c.cancel()
        assert c.status == CampaignStatus.CANCELLED

    def test_cancel_completed_raises(self):
        c = self._make_campaign(target_units=1)
        c.activate()
        c.record_donation(1)
        with pytest.raises(ValueError):
            c.cancel()

    def test_donate_inactive_raises(self):
        c = self._make_campaign()
        with pytest.raises(ValueError):
            c.record_donation(5)
