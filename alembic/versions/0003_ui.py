"""ui features: users, roles, logs, settings, bookmarks, categories"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"

def upgrade() -> None:
    op.create_table("users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("username", sa.String(80), unique=True, index=True, nullable=False),
        sa.Column("full_name", sa.String(120), default=""),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(60), default="viewer"),
        sa.Column("is_active", sa.Boolean, default=True, nullable=False),
        sa.Column("last_login", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table("role_permissions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("role", sa.String(60), index=True, nullable=False),
        sa.Column("page", sa.String(60), nullable=False),
        sa.UniqueConstraint("role", "page", name="uq_role_page"),
    )
    op.create_table("activity_logs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user", sa.String(80), default="system"),
        sa.Column("action", sa.String(120), nullable=False),
        sa.Column("detail", sa.Text, default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), index=True),
    )
    op.create_table("settings",
        sa.Column("key", sa.String(80), primary_key=True),
        sa.Column("value", sa.Text, default=""),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.add_column("source_channels", sa.Column("category", sa.String(60), server_default="عمومی"))
    op.add_column("message_queue", sa.Column("is_bookmarked", sa.Boolean, server_default=sa.text("false")))
    op.add_column("message_queue", sa.Column("manual_source", sa.Boolean, server_default=sa.text("false")))

    # نقش‌های پیش‌فرض
    for role, pages in {
        "admin": ["dashboard","publish","channels","categories","templates","bookmarks",
                  "queue","rules","prompts","reports","users","roles","logs","health","settings"],
        "operator": ["dashboard","publish","bookmarks","queue"],
        "editor": ["dashboard","channels","categories","templates","rules","prompts"],
        "viewer": ["dashboard","bookmarks","reports"],
    }.items():
        for p in pages:
            op.execute(
                f"INSERT INTO role_permissions (role, page) VALUES ('{role}', '{p}') "
                f"ON CONFLICT DO NOTHING"
            )

def downgrade() -> None:
    op.drop_column("message_queue", "manual_source")
    op.drop_column("message_queue", "is_bookmarked")
    op.drop_column("source_channels", "category")
    op.drop_table("settings")
    op.drop_table("activity_logs")
    op.drop_table("role_permissions")
    op.drop_table("users")
