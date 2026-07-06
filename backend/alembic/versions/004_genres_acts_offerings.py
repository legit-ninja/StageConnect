"""genres acts offerings

Revision ID: 004_genres_acts_offerings
Revises: 003_admin_audit_log
Create Date: 2026-07-01

"""

from typing import Sequence, Union
import uuid

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "004_genres_acts_offerings"
down_revision: Union[str, None] = "003_admin_audit_log"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

activity_type = postgresql.ENUM(
    "private_gig",
    "corporate",
    "wedding",
    "festival",
    name="activity_type",
    create_type=True,
)

GENRE_SEED = [
    ("jazz", True),
    ("rock", True),
    ("pop", True),
    ("country", True),
    ("classical", True),
]


def upgrade() -> None:
    bind = op.get_bind()
    activity_type.create(bind, checkfirst=True)

    op.create_table(
        "genres",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("active_in_ui", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    genres_table = sa.table(
        "genres",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("name", sa.String()),
        sa.column("active_in_ui", sa.Boolean()),
    )
    op.bulk_insert(
        genres_table,
        [
            {"id": uuid.uuid4(), "name": name, "active_in_ui": active}
            for name, active in GENRE_SEED
        ],
    )

    op.create_table(
        "acts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("act_owner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("genre_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("act_type", sa.String(length=128), nullable=True),
        sa.Column("years_active", sa.Integer(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("lat", sa.Float(), nullable=False),
        sa.Column("lng", sa.Float(), nullable=False),
        sa.Column("address", sa.String(length=512), nullable=False),
        sa.Column("photo_urls", postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column("genres", postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["act_owner_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["genre_id"], ["genres.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_acts_act_owner_id", "acts", ["act_owner_id"], unique=False)
    op.create_index("ix_acts_genre_id", "acts", ["genre_id"], unique=False)

    op.create_table(
        "offerings",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("act_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("act_owner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "activity_type",
            postgresql.ENUM(
                "private_gig",
                "corporate",
                "wedding",
                "festival",
                name="activity_type",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("price", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("availability", sa.Text(), nullable=True),
        sa.Column(
            "promoter_only_allowed",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["act_id"], ["acts.id"]),
        sa.ForeignKeyConstraint(["act_owner_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_offerings_act_id", "offerings", ["act_id"], unique=False)
    op.create_index("ix_offerings_act_owner_id", "offerings", ["act_owner_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_offerings_act_owner_id", table_name="offerings")
    op.drop_index("ix_offerings_act_id", table_name="offerings")
    op.drop_table("offerings")
    op.drop_index("ix_acts_genre_id", table_name="acts")
    op.drop_index("ix_acts_act_owner_id", table_name="acts")
    op.drop_table("acts")
    op.drop_table("genres")
    activity_type.drop(op.get_bind(), checkfirst=True)
