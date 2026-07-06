"""offering availability slots

Revision ID: 012_offering_availability_slots
Revises: 011_user_profile_photo
Create Date: 2026-07-04

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "012_offering_availability_slots"
down_revision: Union[str, None] = "011_user_profile_photo"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    slot_status = postgresql.ENUM(
        "open", "held", "booked", "blocked", name="slot_status", create_type=True
    )
    slot_status.create(bind, checkfirst=True)

    op.create_table(
        "offering_availability_slots",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("offering_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(
                "open",
                "held",
                "booked",
                "blocked",
                name="slot_status",
                create_type=False,
            ),
            nullable=False,
            server_default="open",
        ),
        sa.Column("capacity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["offering_id"], ["offerings.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_offering_availability_slots_offering_id",
        "offering_availability_slots",
        ["offering_id"],
    )
    op.create_index(
        "ix_offering_availability_slots_start_at",
        "offering_availability_slots",
        ["start_at"],
    )

    op.add_column(
        "gig_requests",
        sa.Column("availability_slot_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_gig_requests_availability_slot_id",
        "gig_requests",
        "offering_availability_slots",
        ["availability_slot_id"],
        ["id"],
    )
    op.create_index(
        "ix_gig_requests_availability_slot_id",
        "gig_requests",
        ["availability_slot_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_gig_requests_availability_slot_id", table_name="gig_requests")
    op.drop_constraint(
        "fk_gig_requests_availability_slot_id", "gig_requests", type_="foreignkey"
    )
    op.drop_column("gig_requests", "availability_slot_id")
    op.drop_index("ix_offering_availability_slots_start_at", table_name="offering_availability_slots")
    op.drop_index(
        "ix_offering_availability_slots_offering_id", table_name="offering_availability_slots"
    )
    op.drop_table("offering_availability_slots")
    op.execute("DROP TYPE IF EXISTS slot_status")
