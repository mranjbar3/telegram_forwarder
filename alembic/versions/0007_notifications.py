"""notifications system"""
from alembic import op
import sqlalchemy as sa

revision = "0007"
down_revision = "0006"


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id SERIAL PRIMARY KEY,
            title VARCHAR(200) NOT NULL,
            body TEXT NOT NULL,
            level VARCHAR(20) DEFAULT 'info' NOT NULL,
            target_role VARCHAR(60) DEFAULT '' NOT NULL,
            created_by VARCHAR(80) DEFAULT '' NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
        )
    """)
    op.execute("""
        CREATE TABLE IF NOT EXISTS notification_reads (
            id SERIAL PRIMARY KEY,
            notification_id INTEGER NOT NULL REFERENCES notifications(id) ON DELETE CASCADE,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            read_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
            CONSTRAINT uq_notif_user UNIQUE (notification_id, user_id)
        )
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS notification_reads")
    op.execute("DROP TABLE IF EXISTS notifications")
