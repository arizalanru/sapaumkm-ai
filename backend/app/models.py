from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Product(Base):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    category: Mapped[str] = mapped_column(String(80), index=True)
    description: Mapped[str] = mapped_column(Text)
    skin_type: Mapped[str] = mapped_column(String(120))
    price: Mapped[float] = mapped_column(Float)
    stock: Mapped[int] = mapped_column(Integer)
    usage: Mapped[str] = mapped_column(Text)


class Order(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_number: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    customer_name: Mapped[str] = mapped_column(String(120))
    product_name: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(120))
    courier: Mapped[str] = mapped_column(String(80))
    tracking_number: Mapped[str] = mapped_column(String(80))
    estimated_arrival: Mapped[str] = mapped_column(String(80))


class FAQ(Base):
    __tablename__ = "faqs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category: Mapped[str] = mapped_column(String(80), index=True)
    question: Mapped[str] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(Text)


class Conversation(Base):
    __tablename__ = "conversations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_name: Mapped[str] = mapped_column(String(120))
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    status: Mapped[str] = mapped_column(String(30), default="ai_active")
    requires_human: Mapped[bool] = mapped_column(Boolean, default=False)
    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan", order_by="Message.id"
    )


class Message(Base):
    __tablename__ = "messages"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"), index=True)
    sender: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    intent: Mapped[str] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    conversation: Mapped[Conversation] = relationship(back_populates="messages")
