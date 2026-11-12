"""add source code, usernames, llm_prompts, spam status

Revision ID: 0002
Revises: 0001
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column("source_channels", sa.Column("code", sa.String(50), nullable=True))
    op.add_column("source_channels", sa.Column("chat_username", sa.String(120), server_default=""))
    op.create_index("ix_source_channels_code", "source_channels", ["code"], unique=True)
    # پر کردن مقدار اولیه code برای رکوردهای موجود
    op.execute("UPDATE source_channels SET code = CONCAT('SRC-', id) WHERE code IS NULL")
    op.alter_column("source_channels", "code", nullable=False)

    op.add_column("destinations", sa.Column("chat_username", sa.String(120), server_default=""))
    op.create_unique_constraint("uq_source_dest", "destinations", ["source_id", "chat_id"])

    op.add_column("message_queue", sa.Column("cleaned_text", sa.Text, server_default=""))
    op.add_column("message_queue", sa.Column("llm_reason", sa.Text, server_default=""))

    op.create_table(
        "llm_prompts",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("prompt_type", sa.String(30), nullable=False, index=True),
        sa.Column("prompt", sa.Text, nullable=False),
        sa.Column("applies_to_chat_id", sa.BigInteger, nullable=True),
        sa.Column("is_active", sa.Boolean, default=True, nullable=False),
        sa.Column("order", sa.Integer, default=0, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

def downgrade() -> None:
    op.drop_table("llm_prompts")
    op.drop_column("message_queue", "llm_reason")
    op.drop_column("message_queue", "cleaned_text")
    op.drop_constraint("uq_source_dest", "destinations", type_="unique")
    op.drop_column("destinations", "chat_username")
    op.drop_index("ix_source_channels_code")
    op.drop_column("source_channels", "chat_username")
    op.drop_column("source_channels", "code")
