from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(180), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(160), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="1")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    tickets_created: Mapped[list["TicketModel"]] = relationship(back_populates="creator")


class AnalystModel(Base):
    __tablename__ = "analysts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(180), unique=True, nullable=False)
    level: Mapped[str] = mapped_column(String(8), nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="1")

    tickets: Mapped[list["TicketModel"]] = relationship(back_populates="analyst")


class AdminModel(Base):
    __tablename__ = "admins"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(180), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(160), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="1")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ServiceCategoryModel(Base):
    __tablename__ = "service_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    tickets: Mapped[list["TicketModel"]] = relationship(back_populates="category")


class SLAPolicyModel(Base):
    __tablename__ = "sla_policies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    priority: Mapped[str] = mapped_column(String(8), unique=True, nullable=False)
    resolution_hours: Mapped[int] = mapped_column(Integer, nullable=False)


class TicketModel(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    ticket_type: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    priority: Mapped[str] = mapped_column(String(8), nullable=False)
    analyst_level: Mapped[str] = mapped_column(String(8), nullable=False)
    analyst_id: Mapped[int | None] = mapped_column(ForeignKey("analysts.id"), nullable=True)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("service_categories.id"), nullable=True)
    created_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    sla_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reopened_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    root_cause_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    corrective_actions: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_closure_confirmation: Mapped[str | None] = mapped_column(Text, nullable=True)
    metric_detected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    metric_first_response_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    metric_resolution_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    handover_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_agreement_to_close: Mapped[str | None] = mapped_column(Text, nullable=True)

    analyst: Mapped["AnalystModel | None"] = relationship(back_populates="tickets")
    category: Mapped["ServiceCategoryModel | None"] = relationship(back_populates="tickets")
    creator: Mapped["UserModel | None"] = relationship(back_populates="tickets_created")


class TicketSatisfactionModel(Base):
    __tablename__ = "ticket_satisfaction_surveys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id", ondelete="CASCADE"), unique=True, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SLANotificationModel(Base):
    __tablename__ = "sla_notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id"), nullable=False)
    message: Mapped[str] = mapped_column(String(512), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
