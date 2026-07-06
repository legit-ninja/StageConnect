"""friend invites

Revision ID: 006_promoter_connections
Revises: 005_admin_audit_offering
Create Date: 2026-07-01

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "006_promoter_connections"
down_revision: Union[str, None] = "005_admin_audit_offering"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

promoter_connection_status = postgresql.ENUM(
    "pending",
    "accepted",
    "declined",
    "cancelled",
    name="promoter_connection_status",
    create_type=True,
)


def upgrade() -> None:
    bind = op.get_bind()
    promoter_connection_status.create(bind, checkfirst=True)

    op.create_table(
        "promoter_connections",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("act_owner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("booker_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("invitee_email", sa.String(length=255), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(
                "pending",
                "accepted",
                "declined",
                "cancelled",
                name="promoter_connection_status",
                create_type=False,
            ),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "invited_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["act_owner_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["booker_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_promoter_connections_act_owner_id", "promoter_connections", ["act_owner_id"])
    op.create_index("ix_promoter_connections_booker_id", "promoter_connections", ["booker_id"])
    op.create_index(
        "ix_promoter_connections_invitee_email", "promoter_connections", ["invitee_email"]
    )


def downgrade() -> None:
    op.drop_index("ix_promoter_connections_invitee_email", table_name="promoter_connections")
    op.drop_index("ix_promoter_connections_booker_id", table_name="promoter_connections")
    op.drop_index("ix_promoter_connections_act_owner_id", table_name="promoter_connections")
    op.drop_table("promoter_connections")
    op.execute("DROP TYPE IF EXISTS promoter_connection_status")
