"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-06-23

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=100), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "agencies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "snmp_profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("version", sa.String(length=10), nullable=False),
        sa.Column("community", sa.String(length=64), nullable=True),
        sa.Column("username", sa.String(length=64), nullable=True),
        sa.Column("auth_protocol", sa.String(length=20), nullable=True),
        sa.Column("auth_password_enc", sa.Text(), nullable=True),
        sa.Column("priv_protocol", sa.String(length=20), nullable=True),
        sa.Column("priv_password_enc", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "subnets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("cidr", sa.String(length=18), nullable=False),
        sa.Column("description", sa.String(length=100), nullable=True),
        sa.Column("agency_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["agency_id"], ["agencies.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("cidr"),
    )
    op.create_index("ix_subnets_cidr", "subnets", ["cidr"])

    op.create_table(
        "routers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("ip_address", sa.String(length=45), nullable=False),
        sa.Column("description", sa.String(length=100), nullable=True),
        sa.Column("snmp_profile_id", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["snmp_profile_id"], ["snmp_profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ip_address"),
    )
    op.create_index("ix_routers_ip_address", "routers", ["ip_address"])

    op.create_table(
        "assets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("mac_address", sa.String(length=17), nullable=False),
        sa.Column("ip_address", sa.String(length=45), nullable=False),
        sa.Column("hostname", sa.String(length=255), nullable=True),
        sa.Column("os_name", sa.String(length=100), nullable=True),
        sa.Column("sys_descr", sa.Text(), nullable=True),
        sa.Column("device_type", sa.String(length=50), nullable=True),
        sa.Column("subnet_id", sa.Integer(), nullable=True),
        sa.Column("first_seen", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("last_seen", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["subnet_id"], ["subnets.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("mac_address"),
    )
    op.create_index("ix_assets_mac_address", "assets", ["mac_address"])
    op.create_index("ix_assets_ip_address", "assets", ["ip_address"])

    op.create_table(
        "discovery_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("run_type", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("router_id", sa.Integer(), nullable=True),
        sa.Column("assets_found", sa.Integer(), nullable=False),
        sa.Column("assets_updated", sa.Integer(), nullable=False),
        sa.Column("assets_new", sa.Integer(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["router_id"], ["routers.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("discovery_runs")
    op.drop_table("assets")
    op.drop_table("routers")
    op.drop_table("subnets")
    op.drop_table("snmp_profiles")
    op.drop_table("agencies")
    op.drop_table("users")