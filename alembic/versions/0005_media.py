"""add media_path/media_type to message_queue (idempotent)"""
from alembic import op

revision = "0005"
down_revision = "0004"


def upgrade() -> None:
    op.execute("""
        ALTER TABLE message_queue
        ADD COLUMN IF NOT EXISTS media_path VARCHAR(500) DEFAULT '' NOT NULL
    """)
    op.execute("""
        ALTER TABLE message_queue
        ADD COLUMN IF NOT EXISTS media_type VARCHAR(30) DEFAULT '' NOT NULL
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE message_queue DROP COLUMN IF EXISTS media_type")
    op.execute("ALTER TABLE message_queue DROP COLUMN IF EXISTS media_path")
