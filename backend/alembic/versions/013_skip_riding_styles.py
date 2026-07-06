"""Skip riding_styles migration — genres JSON folded into 004.

Revision ID: 013_skip_riding_styles
Revises: 012_offering_availability_slots
"""

from typing import Union

revision: str = "013_skip_riding_styles"
down_revision: Union[str, None] = "012_offering_availability_slots"
branch_labels: Union[str, tuple[str, ...], None] = None
depends_on: Union[str, tuple[str, ...], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
