from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    conversation_id: Optional[int] = None
    customer_name: str = Field(default="Pelanggan GlowMart", min_length=1, max_length=120)


class ChatResponse(BaseModel):
    conversation_id: int
    answer: str
    intent: str
    confidence: float
    requires_human: bool
    sources: list[str]
    response_mode: Literal["groq", "deterministic", "fallback_error"]
    conversation_status: Literal["ai_active", "waiting_admin", "admin_active", "resolved"] = "ai_active"
    stored_for_support: bool = False
    customer_message_id: Optional[int] = None
    assistant_message_id: Optional[int] = None


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    category: str
    description: str
    skin_type: str
    price: float
    stock: int
    usage: str


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    order_number: str
    customer_name: str
    product_name: str
    status: str
    courier: str
    tracking_number: str
    estimated_arrival: str


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    sender: str
    content: str
    intent: str
    created_at: datetime


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    customer_name: str
    started_at: datetime
    status: str
    requires_human: bool
    messages: list[MessageResponse] = Field(default_factory=list)


class HandoffRequest(BaseModel):
    requires_human: bool = True


class AdminMessageRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    sender: Literal["admin"]
    content: str = Field(min_length=1, max_length=2000)


class DashboardStats(BaseModel):
    total_conversations: int
    resolved_by_ai: int
    requires_human: int
    automation_rate: float
    average_response_seconds: float
    intent_distribution: dict[str, int]
