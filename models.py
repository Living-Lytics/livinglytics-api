from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Date, JSON, Numeric, Text, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import UUID, BIGINT
import uuid

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(Text, unique=True)
    org_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())

class DataSource(Base):
    __tablename__ = "data_sources"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    source_name: Mapped[str] = mapped_column(Text, index=True)
    account_ref: Mapped[str | None] = mapped_column(Text)
    access_token: Mapped[str | None] = mapped_column(Text)
    refresh_token: Mapped[str | None] = mapped_column(Text)
    expires_at: Mapped = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    created_at: Mapped = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

class Metric(Base):
    __tablename__ = "metrics"
    id: Mapped[int] = mapped_column(BIGINT, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    source_name: Mapped[str] = mapped_column(Text, index=True)
    metric_date: Mapped = mapped_column(Date, index=True)
    metric_name: Mapped[str] = mapped_column(Text)
    metric_value: Mapped = mapped_column(Numeric)
    meta: Mapped = mapped_column(JSON, default={})
    created_at: Mapped = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
