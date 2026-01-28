"""add price samples and referral self-check

Revision ID: 0002_add_price_samples_refchk
Revises: 0001_create_users_referrals
Create Date: 2024-01-02 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_add_price_samples_refchk"
down_revision = "0001_create_users_referrals"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_check_constraint(
        "ck_referrals_no_self_referral",
        "referrals",
        "referrer_telegram_id <> referred_telegram_id",
    )
    op.create_table(
        "price_samples",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("symbol", sa.String(length=32), nullable=False),
        sa.Column("price", sa.Float, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_price_samples_symbol_created",
        "price_samples",
        ["symbol", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_price_samples_symbol_created", table_name="price_samples")
    op.drop_table("price_samples")
    op.drop_constraint("ck_referrals_no_self_referral", "referrals", type_="check")
