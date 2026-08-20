"use client";

import { MessageCircle, RefreshCw } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { getConversation, getConversationMessages, sendChat } from "../../lib/api";
import { clearStoredConversationId, readStoredConversationId, stableReturnedConversationId, storeConversationId } from "../../lib/customer-conversation";
import { formatShortTime, localTime } from "../../lib/text";
import type { ChatMessage, ConversationStatus, StoredMessage } from "../../lib/types";
import { ChatComposer } from "./ChatComposer";
import { CustomerHeader } from "./CustomerHeader";
import { MessageList } from "./MessageList";

function messageId() { return `${Date.now()}-${Math.random().toString(36).slice(2)}`; }
function welcomeMessage(): ChatMessage { return { id: messageId(), sender: "assistant", content: "Halo, selamat datang di GlowMart. Saya Sapa, siap membantu soal produk, pembayaran, dan pesanan Anda.", time: localTime() }; }
function storedToChat(message: StoredMessage): ChatMessage {
  return { id: `db-${message.id}`, sender: message.sender as ChatMessage["sender"], content: message.content, time: formatShortTime(message.created_at) };
}

export function ChatShell() {
  const [messages, setMessages] = useState<ChatMessage[]>(() => [welcomeMessage()]);
  const [input, setInput] = useState("");
  const [conversationId, setConversationId] = useState<number>();
  const conversationIdRef = useRef<number>();
  const submittingRef = useRef(false);
  const [sessionReady, setSessionReady] = useState(false);
  const [loading, setLoading] = useState(false);
  const [conversationStatus, setConversationStatus] = useState<ConversationStatus>("ai_active");
  const [offlineError, setOfflineError] = useState("");

  useEffect(() => {
    const storedConversationId = readStoredConversationId(window.localStorage);
    conversationIdRef.current = storedConversationId;
    setConversationId(storedConversationId);
    setSessionReady(true);
  }, []);

  useEffect(() => {
    if (!conversationId) return;
    const pollingConversationId = conversationId;
    let active = true;
    let polling = false;
    const poll = async () => {
      if (document.hidden || polling) return;
      polling = true;
      try {
        const [storedMessages, conversation] = await Promise.all([
          getConversationMessages(pollingConversationId),
          getConversation(pollingConversationId),
        ]);
        if (!active || conversationIdRef.current !== pollingConversationId) return;
        setConversationStatus(conversation.status);
        setMessages((current) => {
          const welcome = current.filter((message) => !message.id.startsWith("db-") && message.sender === "assistant").slice(0, 1);
          const pending = current.filter((message) => message.id.startsWith("local-"));
          return [...welcome, ...storedMessages.map(storedToChat), ...pending];
        });
      } catch {
        // Sending errors remain visible; a transient polling failure should not interrupt the chat.
      } finally { polling = false; }
    };
    void poll();
    const timer = window.setInterval(poll, 2000);
    const resume = () => { if (!document.hidden) void poll(); };
    document.addEventListener("visibilitychange", resume);
    return () => { active = false; window.clearInterval(timer); document.removeEventListener("visibilitychange", resume); };
  }, [conversationId]);

  async function submit(value = input) {
    const content = value.trim();
    if (!content || !sessionReady || submittingRef.current || conversationStatus === "resolved") return;
    const requestedConversationId = conversationIdRef.current;
    submittingRef.current = true;
    const localId = `local-${messageId()}`;
    setMessages((current) => [...current, { id: localId, sender: "customer", content, time: localTime() }]);
    setInput("");
    setLoading(true);
    setOfflineError("");
    try {
      const result = await sendChat(content, requestedConversationId);
      const activeConversationId = stableReturnedConversationId(requestedConversationId, result.conversation_id);
      conversationIdRef.current = activeConversationId;
      setConversationId(activeConversationId);
      storeConversationId(window.localStorage, activeConversationId);
      setConversationStatus(result.conversation_status);
      setMessages((current) => {
        const replaced = current.map((message) => message.id === localId && result.customer_message_id ? { ...message, id: `db-${result.customer_message_id}` } : message);
        if (!result.answer || !result.assistant_message_id || result.stored_for_support) return replaced;
        if (replaced.some((message) => message.id === `db-${result.assistant_message_id}`)) return replaced;
        return [...replaced, { id: `db-${result.assistant_message_id}`, sender: "assistant", content: result.answer, time: localTime() }];
      });
    } catch {
      setOfflineError("Layanan sedang tidak dapat dihubungi. Periksa koneksi atau coba kembali beberapa saat lagi.");
      setMessages((current) => current.filter((message) => message.id !== localId));
    } finally {
      submittingRef.current = false;
      setLoading(false);
    }
  }

  function resetConversation() {
    if (loading || !sessionReady) return;
    conversationIdRef.current = undefined;
    clearStoredConversationId(window.localStorage);
    setMessages([welcomeMessage()]);
    setConversationId(undefined);
    setInput("");
    setConversationStatus("ai_active");
    setOfflineError("");
  }

  return <main className="customer-page">
    <CustomerHeader/>
    <div className="customer-stage"><section className="chat-shell" aria-label="Percakapan dengan GlowMart">
      <header className="chat-shell-header"><div className="sapa-identity"><span className="sapa-avatar"><MessageCircle size={24} aria-hidden="true"/></span><div><strong>Sapa</strong><span>Asisten GlowMart <i aria-hidden="true"/> Daring</span></div></div><button type="button" className="button button-quiet" onClick={resetConversation} disabled={loading || !sessionReady}><RefreshCw size={16} aria-hidden="true"/>Percakapan baru</button></header>
      {offlineError && <div className="offline-banner" role="alert">{offlineError}</div>}
      <MessageList messages={messages} loading={loading} status={conversationStatus} onSuggestion={submit}/>
      <ChatComposer value={input} onChange={setInput} onSend={() => submit()} loading={loading || !sessionReady} disabled={conversationStatus === "resolved"}/>
    </section></div>
  </main>;
}
