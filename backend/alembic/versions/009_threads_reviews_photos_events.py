"""threads, messages, reviews, offering photos, events

Revision ID: 009_threads_reviews
Revises: 008_user_names_flags
Create Date: 2026-07-01

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "009_threads_reviews_photos_events"
down_revision: Union[str, None] = "008_user_names_flags_notifications"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    moderation_status = postgresql.ENUM(
        "pending", "approved", "rejected", name="moderation_status", create_type=True
    )
    moderation_status.create(bind, checkfirst=True)

    op.create_table(
        "threads",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("gig_request_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("promoter_connection_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "(gig_request_id IS NULL) <> (promoter_connection_id IS NULL)",
            name="ck_threads_exactly_one_parent",
        ),
        sa.ForeignKeyConstraint(["gig_request_id"], ["gig_requests.id"]),
        sa.ForeignKeyConstraint(["promoter_connection_id"], ["promoter_connections.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "uq_threads_gig_request_id",
        "threads",
        ["gig_request_id"],
        unique=True,
        postgresql_where=sa.text("gig_request_id IS NOT NULL"),
    )
    op.create_index(
        "uq_threads_promoter_connection_id",
        "threads",
        ["promoter_connection_id"],
        unique=True,
        postgresql_where=sa.text("promoter_connection_id IS NOT NULL"),
    )

    op.create_table(
        "messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("thread_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sender_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column(
            "sent_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["thread_id"], ["threads.id"]),
        sa.ForeignKeyConstraint(["sender_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_messages_thread_id", "messages", ["thread_id"])

    op.create_table(
        "reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("gig_request_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reviewer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reviewee_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column(
            "moderation_status",
            postgresql.ENUM(
                "pending", "approved", "rejected", name="moderation_status", create_type=False
            ),
            server_default="approved",
            nullable=False,
        ),
        sa.Column("is_friend_ride", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["gig_request_id"], ["gig_requests.id"]),
        sa.ForeignKeyConstraint(["reviewer_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["reviewee_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "gig_request_id", "reviewer_id", name="uq_review_booking_reviewer"
        ),
    )

    op.create_table(
        "offering_photos",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("offering_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("storage_key", sa.String(length=512), nullable=False),
        sa.Column("thumbnail_key", sa.String(length=512), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_primary", sa.Boolean(), server_default="false", nullable=False),
        sa.Column(
            "moderation_status",
            postgresql.ENUM(
                "pending", "approved", "rejected", name="moderation_status", create_type=False
            ),
            server_default="approved",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["offering_id"], ["offerings.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_offering_photos_offering_id", "offering_photos", ["offering_id"])

    op.create_table(
        "events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("src", sa.String(length=64), nullable=True),
        sa.Column("offering_slug", sa.String(length=128), nullable=True),
        sa.Column("invite_token", sa.String(length=64), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_events_event_type", "events", ["event_type"])


def downgrade() -> None:
    op.drop_index("ix_events_event_type", table_name="events")
    op.drop_table("events")
    op.drop_index("ix_offering_photos_offering_id", table_name="offering_photos")
    op.drop_table("offering_photos")
    op.drop_table("reviews")
    op.drop_index("ix_messages_thread_id", table_name="messages")
    op.drop_table("messages")
    op.drop_index("uq_threads_promoter_connection_id", table_name="threads")
    op.drop_index("uq_threads_gig_request_id", table_name="threads")
    op.drop_table("threads")
    op.execute("DROP TYPE IF EXISTS moderation_status")
