"""Act manager flags and booker experience level.

Revision ID: 015_act_manager_booker_experience
Revises: 014_skip_is_trainer
Create Date: 2026-07-05
"""

from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "015_act_manager_booker_experience"
down_revision: Union[str, None] = "014_skip_is_trainer"
branch_labels: Union[str, tuple[str, ...], None] = None
depends_on: Union[str, tuple[str, ...], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "manager_verified",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column("users", sa.Column("booker_experience_level", sa.SmallInteger(), nullable=True))
    op.alter_column("users", "manager_verified", server_default=None)


def downgrade() -> None:
    op.drop_column("users", "booker_experience_level")
    op.drop_column("users", "manager_verified")
