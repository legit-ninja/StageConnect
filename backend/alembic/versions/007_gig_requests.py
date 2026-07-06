"""booking requests

Revision ID: 007_gig_requests
Revises: 006_promoter_connections
Create Date: 2026-07-01

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "007_gig_requests"
down_revision: Union[str, None] = "006_promoter_connections"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

GIG_STATUS_VALUES = (
    "pending_payment",
    "pending_act_owner",
    "counter_offered",
    "approved",
    "declined",
    "cancelled",
)


def upgrade() -> None:
    bind = op.get_bind()
    payment_type = postgresql.ENUM("paid", "free", name="payment_type", create_type=True)
    gig_status = postgresql.ENUM(*GIG_STATUS_VALUES, name="gig_status", create_type=True)
    transaction_direction = postgresql.ENUM(
        "booker_to_platform_deposit", name="transaction_direction", create_type=True
    )
    payment_type.create(bind, checkfirst=True)
    gig_status.create(bind, checkfirst=True)
    transaction_direction.create(bind, checkfirst=True)

    op.create_table(
        "gig_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("offering_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("booker_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("act_owner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("promoter_connection_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "payment_type",
            postgresql.ENUM("paid", "free", name="payment_type", create_type=False),
            nullable=False,
        ),
        sa.Column(
            "status",
            postgresql.ENUM(*GIG_STATUS_VALUES, name="gig_status", create_type=False),
            nullable=False,
        ),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("counter_offer_price", sa.Numeric(10, 2), nullable=True),
        sa.Column("counter_offer_scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("counter_offer_note", sa.Text(), nullable=True),
        sa.Column("confirmed_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "requested_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["offering_id"], ["offerings.id"]),
        sa.ForeignKeyConstraint(["booker_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["act_owner_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["promoter_connection_id"], ["promoter_connections.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_gig_requests_offering_id", "gig_requests", ["offering_id"])
    op.create_index("ix_gig_requests_booker_id", "gig_requests", ["booker_id"])
    op.create_index("ix_gig_requests_act_owner_id", "gig_requests", ["act_owner_id"])

    op.create_table(
        "payment_transactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("gig_request_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("booker_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "direction",
            postgresql.ENUM(
                "booker_to_platform_deposit",
                name="transaction_direction",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("stripe_payment_intent_id", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["booker_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["gig_request_id"], ["gig_requests.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_payment_transactions_gig_request_id", "payment_transactions", ["gig_request_id"])
    op.create_index("ix_payment_transactions_booker_id", "payment_transactions", ["booker_id"])


def downgrade() -> None:
    op.drop_index("ix_payment_transactions_booker_id", table_name="payment_transactions")
    op.drop_index("ix_payment_transactions_gig_request_id", table_name="payment_transactions")
    op.drop_table("payment_transactions")
    op.drop_index("ix_gig_requests_act_owner_id", table_name="gig_requests")
    op.drop_index("ix_gig_requests_booker_id", table_name="gig_requests")
    op.drop_index("ix_gig_requests_offering_id", table_name="gig_requests")
    op.drop_table("gig_requests")
    op.execute("DROP TYPE IF EXISTS transaction_direction")
    op.execute("DROP TYPE IF EXISTS gig_status")
    op.execute("DROP TYPE IF EXISTS payment_type")
