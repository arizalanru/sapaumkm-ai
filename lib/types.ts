export type ResponseMode = "groq" | "deterministic" | "fallback_error";
export type ConversationStatus = "ai_active" | "waiting_admin" | "admin_active" | "resolved";

export type ChatResponse = {
  conversation_id: number;
  answer: string;
  intent: string;
  confidence: number;
  requires_human: boolean;
  sources: string[];
  response_mode: ResponseMode;
  conversation_status: ConversationStatus;
  stored_for_support: boolean;
  customer_message_id?: number;
  assistant_message_id?: number;
};

export type ChatMessage = {
  id: string;
  sender: "customer" | "assistant" | "admin";
  content: string;
  time: string;
};

export type StoredMessage = {
  id: number;
  sender: string;
  content: string;
  intent: string;
  created_at: string;
};

export type Conversation = {
  id: number;
  customer_name: string;
  started_at: string;
  status: ConversationStatus;
  requires_human: boolean;
  messages: StoredMessage[];
};

export type DashboardStats = {
  total_conversations: number;
  resolved_by_ai: number;
  requires_human: number;
  automation_rate: number;
  average_response_seconds: number;
  intent_distribution: Record<string, number>;
};

export type Product = {
  id: number;
  name: string;
  category: string;
  description: string;
  skin_type: string;
  price: number;
  stock: number;
  usage: string;
};
