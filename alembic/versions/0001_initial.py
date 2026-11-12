"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-01-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "source_channels",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("chat_id", sa.BigInteger, unique=True, index=True, nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean, default=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "destinations",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("source_id", sa.Integer, sa.ForeignKey("source_channels.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chat_id", sa.BigInteger, index=True, nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean, default=True, nullable=False),
    )
    op.create_table(
        "message_queue",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("source_chat_id", sa.BigInteger, index=True, nullable=False),
        sa.Column("source_message_id", sa.BigInteger, nullable=False),
        sa.Column("dest_chat_id", sa.BigInteger, index=True, nullable=False),
        sa.Column("source_chat_title", sa.String(255), default=""),
        sa.Column("dest_chat_title", sa.String(255), default=""),
        sa.Column("content_preview", sa.Text, default=""),
        sa.Column("status", sa.String(20), default="pending", index=True, nullable=False),
        sa.Column("retry_count", sa.Integer, default=0, nullable=False),
        sa.Column("error_message", sa.Text, default=""),
        sa.Column("sent_message_id", sa.BigInteger, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), index=True, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("source_chat_id", "source_message_id", "dest_chat_id", name="uq_idempotency"),
    )
    op.create_table(
        "filter_rules",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("rule_type", sa.String(30), nullable=False),
        sa.Column("pattern", sa.Text, nullable=False),
        sa.Column("is_active", sa.Boolean, default=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

def downgrade() -> None:
    op.drop_table("filter_rules")
    op.drop_table("message_queue")
    op.drop_table("destinations")
    op.drop_table("source_channels")
