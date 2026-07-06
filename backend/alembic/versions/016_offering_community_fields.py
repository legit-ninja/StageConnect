"""Offering community fields: min booker experience, venue capacity, gear expectations.

Revision ID: 016_offering_community_fields
Revises: 015_act_manager_booker_experience
Create Date: 2026-07-05
"""

from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "016_offering_community_fields"
down_revision: Union[str, None] = "015_act_manager_booker_experience"
branch_labels: Union[str, tuple[str, ...], None] = None
depends_on: Union[str, tuple[str, ...], None] = None

equipment_provided = sa.Enum("provided", "bring_own", "either", name="equipment_provided")


def upgrade() -> None:
    equipment_provided.create(op.get_bind(), checkfirst=True)
    op.add_column("offerings", sa.Column("min_booker_experience", sa.SmallInteger(), nullable=True))
    op.add_column("offerings", sa.Column("max_venue_capacity", sa.Integer(), nullable=True))
    op.add_column(
        "offerings",
        sa.Column(
            "sound_system_required",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )
    op.add_column(
        "offerings",
        sa.Column(
            "equipment_provided",
            equipment_provided,
            nullable=False,
            server_default="either",
        ),
    )
    op.alter_column("offerings", "sound_system_required", server_default=None)
    op.alter_column("offerings", "equipment_provided", server_default=None)
    op.add_column(
        "offerings",
        sa.Column(
            "requires_21_plus",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.alter_column("offerings", "requires_21_plus", server_default=None)


def downgrade() -> None:
    op.drop_column("offerings", "requires_21_plus")
    op.drop_column("offerings", "equipment_provided")
    op.drop_column("offerings", "sound_system_required")
    op.drop_column("offerings", "max_venue_capacity")
    op.drop_column("offerings", "min_booker_experience")
    equipment_provided.drop(op.get_bind(), checkfirst=True)
