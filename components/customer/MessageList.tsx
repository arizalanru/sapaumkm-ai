"use client";

import { AlertCircle, Bot, CheckCircle, Clock, Headphones } from "lucide-react";
import { useEffect, useRef } from "react";
import { cleanMessageText } from "../../lib/text";
import type { ChatMessage, ConversationStatus } from "../../lib/types";
import { SuggestionActions } from "./SuggestionActions";

const statusCopy: Partial<Record<ConversationStatus, { title: string; body: string }>> = {
  waiting_admin: { title: "Menunggu tim GlowMart", body: "Permintaan Anda sudah masuk ke antrean tim GlowMart." },
  admin_active: { title: "Terhubung dengan admin", body: "Anda sedang terhubung dengan tim GlowMart." },
  resolved: { title: "Percakapan selesai", body: "Percakapan telah diselesaikan." },
};

export function MessageList({ messages, loading, status, onSuggestion }: { messages: ChatMessage[]; loading: boolean; status: ConversationStatus; onSuggestion: (message: string) => void }) {
  const endRef = useRef<HTMLDivElement>(null);
  useEffect(() => { endRef.current?.scrollIntoView({ block: "end" }); }, [messages, loading, status]);

  return <div className="customer-messages" aria-live="polite">
    <div className="message-column">
      {messages.map((message, index) => {
        const isSupport = message.sender === "assistant" || message.sender === "admin";
        const showAvatar = isSupport && (index === 0 || messages[index - 1]?.sender !== message.sender);
        const senderLabel = message.sender === "assistant" ? "Sapa" : message.sender === "admin" ? "Tim GlowMart" : "Pelanggan";
        return <article className={`message-row message-${message.sender}`} key={message.id}>
          {isSupport && <span className={`${message.sender === "admin" ? "admin-avatar" : "assistant-avatar"} ${showAvatar ? "" : "avatar-hidden"}`}>{message.sender === "admin" ? <Headphones size={16} aria-hidden="true"/> : <Bot size={16} aria-hidden="true"/>}</span>}
          <div className="message-content"><span className="message-sender-label">{senderLabel}</span><p>{cleanMessageText(message.content)}</p><time>{message.time}</time></div>
        </article>;
      })}
      {messages.length <= 1 && <SuggestionActions onSelect={onSuggestion} disabled={loading}/>} 
      {statusCopy[status] && <div className={`support-notice support-${status}`} role="status">{status === "resolved" ? <CheckCircle size={18} aria-hidden="true"/> : <AlertCircle size={18} aria-hidden="true"/>}<div><strong>{statusCopy[status]?.title}</strong><p>{statusCopy[status]?.body}</p></div></div>}
      {loading && status === "ai_active" && <div className="typing-row" role="status"><span className="assistant-avatar"><Bot size={16} aria-hidden="true"/></span><div><Clock size={14} aria-hidden="true"/>Sapa sedang menulis</div></div>}
      <div ref={endRef}/>
    </div>
  </div>;
}
