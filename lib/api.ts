import type { ChatResponse, Conversation, DashboardStats, Product, StoredMessage } from "./types";

export const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, options);
  if (!response.ok) throw new Error(`API request failed with status ${response.status}`);
  return response.json() as Promise<T>;
}

export function sendChat(message: string, conversationId?: number) {
  return request<ChatResponse>("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message,
      conversation_id: conversationId,
      customer_name: "Pelanggan GlowMart",
    }),
  });
}

export const getDashboardStats = () => request<DashboardStats>("/api/dashboard/stats");
export const getConversations = () => request<Conversation[]>("/api/conversations");
export const getConversation = (conversationId: number) => request<Conversation>(`/api/conversations/${conversationId}`);
export const getConversationMessages = (conversationId: number) => request<StoredMessage[]>(`/api/conversations/${conversationId}/messages`);
export const getProducts = () => request<Product[]>("/api/products");

export function takeOverConversation(conversationId: number) {
  return request<Conversation>(`/api/conversations/${conversationId}/takeover`, {
    method: "PATCH",
  });
}

export function resolveConversation(conversationId: number) {
  return request<Conversation>(`/api/conversations/${conversationId}/resolve`, { method: "PATCH" });
}

export function returnConversationToAI(conversationId: number) {
  return request<Conversation>(`/api/conversations/${conversationId}/return-to-ai`, { method: "PATCH" });
}

export function sendAdminMessage(conversationId: number, content: string) {
  return request<StoredMessage>(`/api/conversations/${conversationId}/messages`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ sender: "admin", content }),
  });
}
