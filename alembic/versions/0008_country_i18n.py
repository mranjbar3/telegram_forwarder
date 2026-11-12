"""add country to source_channels; default title_en/title_ar in settings"""
from alembic import op

revision = "0008"
down_revision = "0007"


def upgrade() -> None:
    op.execute("ALTER TABLE source_channels ADD COLUMN IF NOT EXISTS country VARCHAR(10) DEFAULT 'ir' NOT NULL")
    op.execute("CREATE INDEX IF NOT EXISTS ix_source_channels_country ON source_channels(country)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_source_channels_country")
    op.execute("ALTER TABLE source_channels DROP COLUMN IF EXISTS country")
