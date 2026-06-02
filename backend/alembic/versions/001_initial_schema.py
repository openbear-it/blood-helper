"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-05-29

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "hospitals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("code", sa.String(20), nullable=False, unique=True),
        sa.Column("city", sa.String(100), nullable=False),
        sa.Column("region", sa.String(100), nullable=False),
        sa.Column("capacity_beds", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "departments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("hospital_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("hospitals.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("hospital_id", "code", name="uq_dept_hospital_code"),
    )

    blood_type_enum = postgresql.ENUM(
        "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-",
        name="bloodtype",
    )
    blood_type_enum.create(op.get_bind(), checkfirst=True)

    wastage_reason_enum = postgresql.ENUM(
        "expired", "contaminated", "administrative", "other",
        name="wastagEreason",
    )
    wastage_reason_enum.create(op.get_bind(), checkfirst=True)

    forecast_horizon_enum = postgresql.ENUM(
        "daily", "weekly", "monthly",
        name="forecasthorizon",
    )
    forecast_horizon_enum.create(op.get_bind(), checkfirst=True)

    campaign_status_enum = postgresql.ENUM(
        "draft", "active", "completed", "cancelled",
        name="campaignstatus",
    )
    campaign_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "blood_units",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("hospital_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("hospitals.id"), nullable=False),
        sa.Column("blood_type", sa.Enum("A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-", name="bloodtype"), nullable=False),
        sa.Column("units_available", sa.Integer(), nullable=False),
        sa.Column("units_reserved", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("expiry_date", sa.Date(), nullable=False),
        sa.Column("last_updated", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_blood_units_hospital_type", "blood_units", ["hospital_id", "blood_type"])

    op.create_table(
        "blood_consumption_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("hospital_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("hospitals.id"), nullable=False),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("departments.id"), nullable=False),
        sa.Column("blood_type", sa.Enum("A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-", name="bloodtype"), nullable=False),
        sa.Column("units_consumed", sa.Integer(), nullable=False),
        sa.Column("consumption_date", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_consumption_hospital_date", "blood_consumption_records", ["hospital_id", "consumption_date"])

    op.create_table(
        "wastage_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("hospital_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("hospitals.id"), nullable=False),
        sa.Column("blood_type", sa.Enum("A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-", name="bloodtype"), nullable=False),
        sa.Column("units_wasted", sa.Integer(), nullable=False),
        sa.Column("reason", sa.Enum("expired", "contaminated", "administrative", "other", name="wastagEreason"), nullable=False),
        sa.Column("wastage_date", sa.Date(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False, server_default=""),
        sa.Column("estimated_cost", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "forecast_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("hospital_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("hospitals.id"), nullable=False),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("departments.id"), nullable=True),
        sa.Column("blood_type", sa.Enum("A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-", name="bloodtype"), nullable=False),
        sa.Column("horizon", sa.Enum("daily", "weekly", "monthly", name="forecasthorizon"), nullable=False),
        sa.Column("forecast_date", sa.Date(), nullable=False),
        sa.Column("predicted_units", sa.Numeric(10, 2), nullable=False),
        sa.Column("lower_bound", sa.Numeric(10, 2), nullable=False),
        sa.Column("upper_bound", sa.Numeric(10, 2), nullable=False),
        sa.Column("model_name", sa.String(50), nullable=False),
        sa.Column("confidence", sa.Numeric(5, 4), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_forecast_hospital_type_horizon", "forecast_results", ["hospital_id", "blood_type", "horizon"])

    op.create_table(
        "donation_campaigns",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("hospital_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("hospitals.id"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("target_blood_types", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("target_units", sa.Integer(), nullable=False),
        sa.Column("collected_units", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("status", sa.Enum("draft", "active", "completed", "cancelled", name="campaignstatus"), nullable=False, server_default="draft"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("donation_campaigns")
    op.drop_table("forecast_results")
    op.drop_table("wastage_records")
    op.drop_table("blood_consumption_records")
    op.drop_table("blood_units")
    op.drop_table("departments")
    op.drop_table("hospitals")

    op.execute("DROP TYPE IF EXISTS campaignstatus")
    op.execute("DROP TYPE IF EXISTS forecasthorizon")
    op.execute("DROP TYPE IF EXISTS wastagEreason")
    op.execute("DROP TYPE IF EXISTS bloodtype")
