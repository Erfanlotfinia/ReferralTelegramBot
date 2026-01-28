"""create users and referrals tables

Revision ID: 0001_create_users_referrals
Revises: 
Create Date: 2024-01-01 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "0001_create_users_referrals"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("telegram_id", sa.BigInteger, nullable=False, unique=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_table(
        "referrals",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("referrer_telegram_id", sa.BigInteger, nullable=False),
        sa.Column("referred_telegram_id", sa.BigInteger, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("referred_telegram_id", name="uq_referrals_referred"),
    )
    op.create_index("ix_referrals_referrer", "referrals", ["referrer_telegram_id"])
    op.create_index("ix_referrals_referred", "referrals", ["referred_telegram_id"])


def downgrade() -> None:
    op.drop_index("ix_referrals_referred", table_name="referrals")
    op.drop_index("ix_referrals_referrer", table_name="referrals")
    op.drop_table("referrals")
    op.drop_table("users")
    op.drop_table("alembic_version")