"""extend admin_audit_action for offering moderation

Revision ID: 005_admin_audit_offering
Revises: 004_act_categories_acts_offerings
Create Date: 2026-07-01

"""

from typing import Sequence, Union

from alembic import op

revision: str = "005_admin_audit_offering"
down_revision: Union[str, None] = "004_genres_acts_offerings"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TYPE admin_audit_action ADD VALUE IF NOT EXISTS 'offering_deactivated'"
    )
    op.execute(
        "ALTER TYPE admin_audit_action ADD VALUE IF NOT EXISTS 'offering_reactivated'"
    )


def downgrade() -> None:
    pass
