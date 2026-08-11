"""Initial SaaS schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-08-06
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enums
    userrole = postgresql.ENUM("user", "admin", name="userrole", create_type=False)
    subscriptionstatus = postgresql.ENUM(
        "active", "canceled", "past_due", "trialing", "incomplete", name="subscriptionstatus", create_type=False
    )
    propertytype = postgresql.ENUM(
        "apartment",
        "house",
        "villa",
        "cabin",
        "room",
        "hotel",
        "hostel",
        "tiny_house",
        "farm_stay",
        "boat",
        name="propertytype",
        create_type=False,
    )
    predictionstatus = postgresql.ENUM(
        "pending", "running", "completed", "failed", name="predictionstatus", create_type=False
    )
    plantier = postgresql.ENUM("free", "pro", "business", name="plantier", create_type=False)

    for e in (userrole, subscriptionstatus, propertytype, predictionstatus, plantier):
        e.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255)),
        sa.Column("role", postgresql.ENUM(name="userrole", create_type=False), server_default="user"),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("is_verified", sa.Boolean(), server_default="false"),
        sa.Column("stripe_customer_id", sa.String(255)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", postgresql.ENUM(name="plantier", create_type=False), nullable=False, unique=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("property_limit", sa.Integer()),
        sa.Column("price_monthly_cents", sa.Integer(), server_default="0"),
        sa.Column("stripe_price_id", sa.String(255)),
        sa.Column("features", postgresql.JSONB(), server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "amenities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(100), nullable=False, unique=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("category", sa.String(100), server_default="general"),
    )

    op.create_table(
        "email_verification_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("token", sa.String(255), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used", sa.Boolean(), server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "password_reset_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("token", sa.String(255), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used", sa.Boolean(), server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("jti", sa.String(64), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean(), server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), unique=True),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("plans.id")),
        sa.Column(
            "status",
            postgresql.ENUM(name="subscriptionstatus", create_type=False),
            server_default="active",
        ),
        sa.Column("stripe_subscription_id", sa.String(255)),
        sa.Column("current_period_end", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "payments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("stripe_payment_intent_id", sa.String(255)),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(10), server_default="usd"),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("meta", postgresql.JSONB(), server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "user_settings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), unique=True),
        sa.Column("preferences", postgresql.JSONB(), server_default="{}"),
        sa.Column("notification_email", sa.Boolean(), server_default="true"),
        sa.Column("notification_in_app", sa.Boolean(), server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "properties",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("property_type", postgresql.ENUM(name="propertytype", create_type=False), nullable=False),
        sa.Column("building_type", sa.String(100)),
        sa.Column("floor_number", sa.Integer()),
        sa.Column("country", sa.String(100)),
        sa.Column("state", sa.String(100)),
        sa.Column("city", sa.String(100)),
        sa.Column("area", sa.String(150)),
        sa.Column("neighborhood", sa.String(150)),
        sa.Column("postal_code", sa.String(30)),
        sa.Column("latitude", sa.Float()),
        sa.Column("longitude", sa.Float()),
        sa.Column("bedrooms", sa.Integer()),
        sa.Column("bathrooms", sa.Float()),
        sa.Column("beds", sa.Integer()),
        sa.Column("guests", sa.Integer()),
        sa.Column("square_feet", sa.Float()),
        sa.Column("square_meters", sa.Float()),
        sa.Column("cleaning_fee", sa.Float()),
        sa.Column("extra_guest_fee", sa.Float()),
        sa.Column("minimum_nights", sa.Integer()),
        sa.Column("maximum_nights", sa.Integer()),
        sa.Column("current_price", sa.Float()),
        sa.Column("availability_notes", sa.Text()),
        sa.Column("features", postgresql.JSONB(), server_default="{}"),
        sa.Column("onboarding_step", sa.Integer(), server_default="1"),
        sa.Column("onboarding_complete", sa.Boolean(), server_default="false"),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_properties_city", "properties", ["city"])
    op.create_index("ix_properties_user_id", "properties", ["user_id"])

    op.create_table(
        "property_photos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("property_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("properties.id", ondelete="CASCADE")),
        sa.Column("s3_key", sa.String(512), nullable=False),
        sa.Column("url", sa.String(1024), nullable=False),
        sa.Column("content_type", sa.String(100)),
        sa.Column("sort_order", sa.Integer(), server_default="0"),
        sa.Column("room_tag", sa.String(50)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "property_amenities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("property_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("properties.id", ondelete="CASCADE")),
        sa.Column("amenity_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("amenities.id", ondelete="CASCADE")),
        sa.UniqueConstraint("property_id", "amenity_id"),
    )

    op.create_table(
        "market_listings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("external_listing_id", sa.String(100), nullable=False),
        sa.Column("source", sa.String(50), server_default="airbnb"),
        sa.Column("title", sa.String(255)),
        sa.Column("url", sa.String(1024)),
        sa.Column("property_type", sa.String(100)),
        sa.Column("city", sa.String(100)),
        sa.Column("region", sa.String(100)),
        sa.Column("neighborhood", sa.String(150)),
        sa.Column("latitude", sa.Float()),
        sa.Column("longitude", sa.Float()),
        sa.Column("bedrooms", sa.Integer()),
        sa.Column("bathrooms", sa.Float()),
        sa.Column("beds", sa.Integer()),
        sa.Column("guests", sa.Integer()),
        sa.Column("amenities", postgresql.JSONB(), server_default="{}"),
        sa.Column("rating", sa.Float()),
        sa.Column("review_count", sa.Integer()),
        sa.Column("current_price", sa.Float()),
        sa.Column("currency", sa.String(10), server_default="USD"),
        sa.Column("raw", postgresql.JSONB(), server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("external_listing_id", "source"),
    )

    op.create_table(
        "market_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("listing_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("market_listings.id", ondelete="CASCADE")),
        sa.Column("price", sa.Float()),
        sa.Column("available", sa.Boolean()),
        sa.Column("rating", sa.Float()),
        sa.Column("review_count", sa.Integer()),
        sa.Column("scraped_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("meta", postgresql.JSONB(), server_default="{}"),
    )

    op.create_table(
        "predictions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("property_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("properties.id", ondelete="CASCADE")),
        sa.Column(
            "status",
            postgresql.ENUM(name="predictionstatus", create_type=False),
            server_default="pending",
        ),
        sa.Column("suggested_price", sa.Float()),
        sa.Column("min_price", sa.Float()),
        sa.Column("max_price", sa.Float()),
        sa.Column("expected_occupancy", sa.Float()),
        sa.Column("monthly_revenue", sa.Float()),
        sa.Column("annual_revenue", sa.Float()),
        sa.Column("confidence_score", sa.Float()),
        sa.Column("model_version", sa.String(100)),
        sa.Column("features", postgresql.JSONB(), server_default="{}"),
        sa.Column("strengths", postgresql.JSONB(), server_default="[]"),
        sa.Column("weaknesses", postgresql.JSONB(), server_default="[]"),
        sa.Column("recommendations", postgresql.JSONB(), server_default="[]"),
        sa.Column("explanation", sa.Text()),
        sa.Column("error_message", sa.Text()),
        sa.Column("agent_traces", postgresql.JSONB(), server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "comp_sets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("property_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("properties.id", ondelete="CASCADE")),
        sa.Column("prediction_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("predictions.id", ondelete="SET NULL")),
        sa.Column("summary", postgresql.JSONB(), server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "comp_set_members",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("comp_set_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("comp_sets.id", ondelete="CASCADE")),
        sa.Column(
            "market_listing_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("market_listings.id", ondelete="CASCADE"),
        ),
        sa.Column("similarity_score", sa.Float(), server_default="0"),
        sa.Column("distance_km", sa.Float()),
    )

    op.create_table(
        "vision_analyses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("prediction_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("predictions.id", ondelete="CASCADE"), unique=True),
        sa.Column("quality_score", sa.Float()),
        sa.Column("luxury_score", sa.Float()),
        sa.Column("cleanliness_score", sa.Float()),
        sa.Column("lighting_score", sa.Float()),
        sa.Column("furniture_score", sa.Float()),
        sa.Column("overall_score", sa.Float()),
        sa.Column("details", postgresql.JSONB(), server_default="{}"),
        sa.Column("missing_amenities", postgresql.JSONB(), server_default="[]"),
        sa.Column("suggestions", postgresql.JSONB(), server_default="[]"),
        sa.Column("estimated_revenue_impact", sa.Float()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("prediction_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("predictions.id", ondelete="CASCADE"), unique=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("summary", sa.Text()),
        sa.Column("s3_key", sa.String(512)),
        sa.Column("url", sa.String(1024)),
        sa.Column("status", sa.String(50), server_default="pending"),
        sa.Column("content_markdown", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "ai_conversations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("property_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("properties.id", ondelete="CASCADE")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("title", sa.String(255)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "conversation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("ai_conversations.id", ondelete="CASCADE"),
        ),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("meta", postgresql.JSONB(), server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("type", sa.String(50), server_default="info"),
        sa.Column("is_read", sa.Boolean(), server_default="false"),
        sa.Column("link", sa.String(512)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "activity_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(50)),
        sa.Column("resource_id", sa.String(64)),
        sa.Column("ip_address", sa.String(50)),
        sa.Column("meta", postgresql.JSONB(), server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "model_registry",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("version", sa.String(50), nullable=False),
        sa.Column("algorithm", sa.String(50), server_default="catboost"),
        sa.Column("artifact_path", sa.String(512), nullable=False),
        sa.Column("metrics", postgresql.JSONB(), server_default="{}"),
        sa.Column("is_active", sa.Boolean(), server_default="false"),
        sa.Column("feature_schema", postgresql.JSONB(), server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "holiday_calendars",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("country", sa.String(10), nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("multiplier", sa.Float(), server_default="1.15"),
    )

    op.create_table(
        "seasonality_indexes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("city", sa.String(100), nullable=False),
        sa.Column("month", sa.Integer(), nullable=False),
        sa.Column("day_of_week", sa.Integer(), nullable=False),
        sa.Column("multiplier", sa.Float(), server_default="1.0"),
        sa.UniqueConstraint("city", "month", "day_of_week"),
    )


def downgrade() -> None:
    for table in [
        "seasonality_indexes",
        "holiday_calendars",
        "model_registry",
        "activity_logs",
        "notifications",
        "messages",
        "ai_conversations",
        "reports",
        "vision_analyses",
        "comp_set_members",
        "comp_sets",
        "predictions",
        "market_snapshots",
        "market_listings",
        "property_amenities",
        "property_photos",
        "properties",
        "user_settings",
        "payments",
        "subscriptions",
        "refresh_tokens",
        "password_reset_tokens",
        "email_verification_tokens",
        "amenities",
        "plans",
        "users",
    ]:
        op.drop_table(table)
    for name in ["plantier", "predictionstatus", "propertytype", "subscriptionstatus", "userrole"]:
        postgresql.ENUM(name=name).drop(op.get_bind(), checkfirst=True)
