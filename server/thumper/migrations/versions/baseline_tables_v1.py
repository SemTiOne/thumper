"""Baseline: create all tables and indexes.

Revision ID: baseline_tables_v1
Revises:
Create Date: 2026-06-11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "baseline_tables_v1"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tripwires",
        sa.Column("id", sa.String(255), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("token_type", sa.String(255), nullable=False),
        sa.Column("path", sa.String(255), nullable=False),
        sa.Column("source", sa.String(255), nullable=False, server_default="template"),
        sa.Column("custom_content", sa.Text()),
        sa.Column("token", sa.Text()),
        sa.Column("created_at", sa.String(255), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_table(
        "endpoints",
        sa.Column("id", sa.String(255), primary_key=True),
        sa.Column("hostname", sa.String(255), nullable=False),
        sa.Column("platform", sa.String(255)),
        sa.Column("machine_id", sa.String(255), unique=True),
        sa.Column("agent_token", sa.String(255), nullable=False),
        sa.Column("enrolled_at", sa.String(255), nullable=False),
        sa.Column("last_seen", sa.String(255)),
    )
    op.create_table(
        "deployments",
        sa.Column("id", sa.String(255), primary_key=True),
        sa.Column("tripwire_id", sa.String(255), sa.ForeignKey("tripwires.id"), nullable=False),
        sa.Column("endpoint_id", sa.String(255), sa.ForeignKey("endpoints.id"), nullable=False),
        sa.Column("path", sa.String(255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("hmac_secret", sa.String(255), nullable=False),
        sa.Column("state", sa.String(255), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.String(255), nullable=False),
        sa.Column("last_triggered", sa.String(255)),
        sa.UniqueConstraint("tripwire_id", "endpoint_id"),
    )
    op.create_index("ix_deploy_tripwire", "deployments", ["tripwire_id"])
    op.create_index("ix_deploy_endpoint", "deployments", ["endpoint_id"])

    op.create_table(
        "alerts",
        sa.Column("id", sa.String(255), primary_key=True),
        sa.Column("deployment_id", sa.String(255), nullable=False),
        sa.Column("tripwire_id", sa.String(255), nullable=False),
        sa.Column("endpoint_id", sa.String(255), nullable=False),
        sa.Column("tripwire_name", sa.String(255), nullable=False),
        sa.Column("endpoint_hostname", sa.String(255), nullable=False),
        sa.Column("token_type", sa.String(255), nullable=False),
        sa.Column("accessed_path", sa.String(255)),
        sa.Column("process", sa.String(255)),
        sa.Column("pid", sa.Integer()),
        sa.Column("os_user", sa.String(255)),
        sa.Column("event_type", sa.String(255)),
        sa.Column("timestamp", sa.String(255), nullable=False),
        sa.Column("triggered_by", sa.String(255)),
    )
    op.create_index("ix_alert_deployment", "alerts", ["deployment_id"])
    op.create_index("ix_alert_tripwire", "alerts", ["tripwire_id"])

    op.create_table(
        "integrations",
        sa.Column("plugin", sa.String(255), primary_key=True),
        sa.Column("kind", sa.String(255), nullable=False),
        sa.Column("configured", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("config_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("last_test_status", sa.String(255)),
        sa.Column("last_test_at", sa.String(255)),
        sa.Column("last_test_error", sa.String(255)),
    )

    op.create_table(
        "delivery_attempts",
        sa.Column("id", sa.String(255), primary_key=True),
        sa.Column("alert_id", sa.String(255), nullable=False),
        sa.Column("plugin", sa.String(255), nullable=False),
        sa.Column("status", sa.String(255), nullable=False),
        sa.Column("error", sa.String(255)),
        sa.Column("created_at", sa.String(255), nullable=False),
    )
    op.create_index("ix_delivery_alert", "delivery_attempts", ["alert_id"])


def downgrade() -> None:
    op.drop_table("delivery_attempts")
    op.drop_table("integrations")
    op.drop_table("alerts")
    op.drop_table("deployments")
    op.drop_table("endpoints")
    op.drop_table("tripwires")
