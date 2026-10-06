from database import Base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, DateTime, Text,ForeignKey
from datetime import datetime, timezone


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key = True)
    account: Mapped[str] = mapped_column(
        String(50),
        unique = True,
        index = True,
        nullable = False
        )
    username: Mapped[str] = mapped_column(
        String(50),
        nullable = False
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable = False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone = True),
        default = lambda: datetime.now(timezone.utc),
        nullable = False
    )
    last_seen_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone = True),
        default = None,
        nullable = True
    )

class Message(Base):
    __tablename__ = "messages"
    id: Mapped[int] = mapped_column(primary_key = True)
    sender_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable = False,
        index = True
    )
    receiver_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable = False,
        index = True
    )
    content: Mapped[str] = mapped_column(
        Text(),
        nullable = False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone = True),
        default = lambda: datetime.now(timezone.utc),
        nullable = False
    )