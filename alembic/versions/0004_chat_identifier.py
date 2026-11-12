"""change chat_id columns to string to allow @username"""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"

def upgrade() -> None:
    # source_channels
    op.alter_column(
        "source_channels", "chat_id",
        type_=sa.String(120),
        existing_type=sa.BigInteger(),
        postgresql_using="chat_id::text",
        nullable=True,
    )
    # destinations
    op.alter_column(
        "destinations", "chat_id",
        type_=sa.String(120),
        existing_type=sa.BigInteger(),
        postgresql_using="chat_id::text",
        nullable=True,
    )
    # message_queue — هر دو ستون
    op.alter_column(
        "message_queue", "source_chat_id",
        type_=sa.String(120),
        existing_type=sa.BigInteger(),
        postgresql_using="source_chat_id::text",
        nullable=True,
    )
    op.alter_column(
        "message_queue", "dest_chat_id",
        type_=sa.String(120),
        existing_type=sa.BigInteger(),
        postgresql_using="dest_chat_id::text",
        nullable=True,
    )

def downgrade() -> None:
    for table, col in [
        ("source_channels", "chat_id"),
        ("destinations", "chat_id"),
        ("message_queue", "source_chat_id"),
        ("message_queue", "dest_chat_id"),
    ]:
        op.alter_column(
            table, col,
            type_=sa.BigInteger(),
            existing_type=sa.String(120),
            postgresql_using=f"NULLIF({col}, '')::bigint",
            nullable=(table == "message_queue"),
        )
