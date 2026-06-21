"""initial migration.

Revision ID: 0001
Create Date: 2026-06-20 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial tables: api_keys, flows, flow_runs."""

    op.create_table(
        "api_keys",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("key_prefix", sa.String(length=8), nullable=False),
        sa.Column("encrypted_key", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider"),
    )
    op.create_index("ix_api_keys_provider", "api_keys", ["provider"])

    op.create_table(
        "flows",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=256), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("nodes", sa.JSON(), nullable=True),
        sa.Column("edges", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "flow_runs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("flow_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=True),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["flow_id"], ["flows.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_flow_runs_flow_id", "flow_runs", ["flow_id"])


def downgrade() -> None:
    """Drop all tables in reverse order."""

    op.drop_index("ix_flow_runs_flow_id", table_name="flow_runs")
    op.drop_table("flow_runs")
    op.drop_table("flows")
    op.drop_index("ix_api_keys_provider", table_name="api_keys")
    op.drop_table("api_keys")
