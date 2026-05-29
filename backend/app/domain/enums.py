from enum import Enum


class BloodType(str, Enum):
    A_POSITIVE = "A+"
    A_NEGATIVE = "A-"
    B_POSITIVE = "B+"
    B_NEGATIVE = "B-"
    AB_POSITIVE = "AB+"
    AB_NEGATIVE = "AB-"
    O_POSITIVE = "O+"
    O_NEGATIVE = "O-"


class InventoryStatus(str, Enum):
    ADEQUATE = "adequate"
    LOW = "low"
    CRITICAL = "critical"
    SURPLUS = "surplus"


class CampaignStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ForecastHorizon(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class WastageReason(str, Enum):
    EXPIRED = "expired"
    CONTAMINATED = "contaminated"
    ADMINISTRATIVE = "administrative"
    OTHER = "other"
