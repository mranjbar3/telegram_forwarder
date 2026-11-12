from datetime import datetime
from enum import Enum
from typing import Optional
from sqlalchemy import (
    BigInteger, Boolean, DateTime, ForeignKey, Integer, String, Text,
    UniqueConstraint, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


# ──────── کاربران و نقش‌ها ────────
class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(120), default="")
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(60), default="viewer")  # admin|operator|editor|viewer
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RolePermission(Base):
    __tablename__ = "role_permissions"
    __table_args__ = (UniqueConstraint("role", "page", name="uq_role_page"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    role: Mapped[str] = mapped_column(String(60), index=True)
    page: Mapped[str] = mapped_column(String(60))


class ActivityLog(Base):
    __tablename__ = "activity_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user: Mapped[str] = mapped_column(String(80), default="system")
    action: Mapped[str] = mapped_column(String(120))
    detail: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class Setting(Base):
    __tablename__ = "settings"
    key: Mapped[str] = mapped_column(String(80), primary_key=True)
    value: Mapped[str] = mapped_column(Text, default="")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class MessageStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    UNKNOWN = "unknown"
    FILTERED = "filtered"
    SPAM = "spam"  # ← وضعیت جدید


class SourceChannel(Base):
    __tablename__ = "source_channels"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # حالا String است — هم "@farsna" هم "-1001234567890" می‌پذیرد
    chat_id: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), default="")
    code: Mapped[str] = mapped_column(String(50), unique=True, default="")
    chat_username: Mapped[str] = mapped_column(String(120), default="")
    category: Mapped[str] = mapped_column(String(60), default="عمومی")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    destinations: Mapped[list["Destination"]] = relationship(back_populates="source", cascade="all, delete-orphan", lazy="selectin")
    last_message_id: Mapped[int] = mapped_column(BigInteger, default=0, server_default="0")
    country: Mapped[str] = mapped_column(String(10), default="ir", index=True)


class Destination(Base):
    __tablename__ = "destinations"
    __table_args__ = (UniqueConstraint("source_id", "chat_id", name="uq_source_dest"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("source_channels.id", ondelete="CASCADE"))
    chat_id: Mapped[str] = mapped_column(String(120), index=True, nullable=False)  # String
    chat_username: Mapped[str] = mapped_column(String(120), default="")
    title: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    source: Mapped[SourceChannel] = relationship(back_populates="destinations")


class MessageQueue(Base):
    __tablename__ = "message_queue"
    __table_args__ = (
        UniqueConstraint("source_chat_id", "source_message_id", "dest_chat_id", name="uq_idempotency"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_chat_id: Mapped[str] = mapped_column(String(120), index=True)   # String
    source_message_id: Mapped[int] = mapped_column(BigInteger)
    dest_chat_id: Mapped[str] = mapped_column(String(120), index=True)     # String
    source_chat_title: Mapped[str] = mapped_column(String(255), default="")
    dest_chat_title: Mapped[str] = mapped_column(String(255), default="")
    content_preview: Mapped[str] = mapped_column(Text, default="")
    cleaned_text: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default=MessageStatus.PENDING.value, index=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str] = mapped_column(Text, default="")
    llm_reason: Mapped[str] = mapped_column(Text, default="")
    sent_message_id: Mapped[int] = mapped_column(BigInteger, nullable=True)
    is_bookmarked: Mapped[bool] = mapped_column(Boolean, default=False)
    manual_source: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    media_path: Mapped[str] = mapped_column(String(500), default="")
    media_type: Mapped[str] = mapped_column(String(30), default="")


class FilterRule(Base):
    __tablename__ = "filter_rules"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    rule_type: Mapped[str] = mapped_column(String(30))  # keyword | regex | header | footer
    pattern: Mapped[str] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class LLMPrompt(Base):
    __tablename__ = "llm_prompts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    prompt_type: Mapped[str] = mapped_column(String(30), index=True)  # classify | clean | translate
    prompt: Mapped[str] = mapped_column(Text)
    applies_to_chat_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)  # NULL → همه
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class Notification(Base):
    __tablename__ = "notifications"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text)
    level: Mapped[str] = mapped_column(String(20), default="info")  # info/warning/error/success
    target_role: Mapped[str] = mapped_column(String(60), default="")  # "" = همه
    created_by: Mapped[str] = mapped_column(String(80), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class NotificationRead(Base):
    __tablename__ = "notification_reads"
    __table_args__ = (UniqueConstraint("notification_id", "user_id", name="uq_notif_user"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    notification_id: Mapped[int] = mapped_column(ForeignKey("notifications.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    read_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

