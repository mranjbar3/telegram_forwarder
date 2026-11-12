"""add last_message_id to source_channels for polling (idempotent)"""
from alembic import op

revision = "0006"
down_revision = "0005"


def upgrade() -> None:
    # PostgreSQL: IF NOT EXISTS کل مشکل را حل می‌کند
    op.execute("""
        ALTER TABLE source_channels
        ADD COLUMN IF NOT EXISTS last_message_id BIGINT DEFAULT 0 NOT NULL
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE source_channels DROP COLUMN IF EXISTS last_message_id")
