"""Skip is_trainer migration — is_act_manager/is_booking_coordinator in 001.

Revision ID: 014_skip_is_trainer
Revises: 013_skip_riding_styles
"""

from typing import Union

revision: str = "014_skip_is_trainer"
down_revision: Union[str, None] = "013_skip_riding_styles"
branch_labels: Union[str, tuple[str, ...], None] = None
depends_on: Union[str, tuple[str, ...], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
