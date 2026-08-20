"use client";

import { AlertCircle, CheckCircle, Headphones, Inbox, RotateCcw, Search, Send, User } from "lucide-react";
import { useEffect, useMemo, useRef, useState, type KeyboardEvent } from "react";
import type { Conversation } from "../../lib/types";
import { cleanMessageText, conversationDisplayName, formatDateTime, formatShortTime } from "../../lib/text";
import { EmptyState } from "../ui/EmptyState";
import { StatusBadge } from "../ui/StatusBadge";
import { ConversationDetails } from "./ConversationDetails";

type Filter = "all" | "ai" | "handoff";

type AdminInboxProps = {
  conversations: Conversation[];
  selectedId?: number;
  onSelect: (id: number) => void;
  onTakeover: (id: number) => Promise<void>;
  onResolve: (id: number) => Promise<void>;
  onReturnToAI: (id: number) => Promise<void>;
  onSendMessage: (id: number, content: string) => Promise<void>;
  actionLoading: boolean;
};

const statusLabel = {
  ai_active: "AI aktif",
  waiting_admin: "Menunggu admin",
  admin_active: "Admin aktif",
  resolved: "Selesai",
} as const;

type ThreadSender = "customer" | "sapa" | "admin";

function threadSender(sender: string): ThreadSender {
  const normalized = sender.trim().toLowerCase();
  if (["assistant", "ai", "bot"].includes(normalized)) return "sapa";
  if (["admin", "operator"].includes(normalized)) return "admin";
  return "customer";
}

export function AdminInbox({ conversations, selectedId, onSelect, onTakeover, onResolve, onReturnToAI, onSendMessage, actionLoading }: AdminInboxProps) {
  const [filter, setFilter] = useState<Filter>("all");
  const [query, setQuery] = useState("");
  const [draft, setDraft] = useState("");
  const [sendError, setSendError] = useState("");
  const threadEnd = useRef<HTMLDivElement>(null);
  const selected = conversations.find((conversation) => conversation.id === selectedId);

  useEffect(() => { threadEnd.current?.scrollIntoView({ block: "end" }); }, [selectedId, selected?.messages.length]);
  useEffect(() => { setDraft(""); setSendError(""); }, [selectedId]);

  const filtered = useMemo(() => conversations.filter((conversation) => {
    if (filter === "ai" && conversation.status !== "ai_active") return false;
    if (filter === "handoff" && !["waiting_admin", "admin_active"].includes(conversation.status)) return false;
    return conversationDisplayName(conversation).toLowerCase().includes(query.toLowerCase());
  }).sort((a, b) => {
    const priority = (status: Conversation["status"]) => status === "waiting_admin" ? 2 : status === "admin_active" ? 1 : 0;
    return priority(b.status) - priority(a.status);
  }), [conversations, filter, query]);

  async function sendMessage() {
    const content = draft.trim();
    if (!selected || selected.status !== "admin_active" || !content || actionLoading) return;
    setSendError("");
    try {
      await onSendMessage(selected.id, content);
      setDraft("");
    } catch {
      setSendError("Pesan belum dapat dikirim. Periksa koneksi lalu coba kembali.");
    }
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void sendMessage();
    }
  }

  return <div className="admin-inbox">
    <section className="conversation-list">
      <header>
        <div><h1>Kotak Masuk</h1><span>{conversations.length} percakapan</span></div>
        <label><Search size={16} aria-hidden="true"/><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Cari pelanggan" aria-label="Cari pelanggan"/></label>
        <div className="inbox-filters">{([['all','Semua'],['ai','Ditangani AI'],['handoff','Butuh admin']] as [Filter,string][]).map(([id, label]) => <button key={id} className={filter === id ? "active" : ""} onClick={() => setFilter(id)}>{label}</button>)}</div>
      </header>
      <div className="conversation-list-scroll">{filtered.map((conversation) => {
        const last = conversation.messages.at(-1);
        const displayName = conversationDisplayName(conversation);
        const handoffLabel = conversation.status === "waiting_admin" ? "Menunggu admin" : conversation.status === "admin_active" ? "Admin aktif" : "";
        return <button className={`conversation-item ${selectedId === conversation.id ? "selected" : ""} ${conversation.requires_human ? "priority" : ""}`} key={conversation.id} onClick={() => onSelect(conversation.id)}>
          <span className="customer-avatar"><User size={16} aria-hidden="true"/></span>
          <span><strong>{displayName}</strong><small>{last?.content || "Belum ada pesan"}</small><span className="conversation-item-meta"><time>{formatShortTime(last?.created_at || conversation.started_at)}</time>{handoffLabel && <em><i aria-hidden="true"/>{handoffLabel}</em>}</span></span>
          {conversation.status === "waiting_admin" && <AlertCircle size={16} className="warning-icon" aria-label="Belum ditangani"/>}
        </button>;
      })}{!filtered.length && <EmptyState icon={Inbox} title="Tidak ada percakapan" description="Tidak ada data yang cocok dengan filter."/>}</div>
    </section>

    <section className="admin-thread">
      {selected ? <>
        <header>
          <div><strong>{conversationDisplayName(selected)}</strong><span>{selected.messages.length} pesan</span></div>
          <div className="admin-thread-actions">
            <StatusBadge tone={selected.status === "waiting_admin" ? "warning" : selected.status === "resolved" ? "neutral" : "success"}>{statusLabel[selected.status]}</StatusBadge>
            {selected.status === "waiting_admin" && <button className="button button-primary" onClick={() => void onTakeover(selected.id)} disabled={actionLoading}><Headphones size={16} aria-hidden="true"/>Ambil alih</button>}
            {selected.status === "admin_active" && <><button className="button button-quiet" onClick={() => void onReturnToAI(selected.id)} disabled={actionLoading}><RotateCcw size={16} aria-hidden="true"/>Kembalikan ke AI</button><button className="button button-primary" onClick={() => void onResolve(selected.id)} disabled={actionLoading}><CheckCircle size={16} aria-hidden="true"/>Selesaikan</button></>}
            {selected.status === "resolved" && <button className="button button-quiet" onClick={() => void onReturnToAI(selected.id)} disabled={actionLoading}><RotateCcw size={16} aria-hidden="true"/>Kembalikan ke AI</button>}
          </div>
        </header>
        <div className="admin-thread-scroll">{selected.messages.map((message) => {
          const senderKind = threadSender(message.sender);
          const senderLabel = senderKind === "customer" ? conversationDisplayName(selected) : senderKind === "admin" ? "Tim GlowMart" : "Sapa";
          return <article className={`admin-message-row admin-message-row-${senderKind}`} key={message.id}>
            <div className={`admin-message admin-message-${senderKind}`}><span>{senderLabel}</span><p>{cleanMessageText(message.content)}</p><time>{formatDateTime(message.created_at)}</time></div>
          </article>;
        })}<div ref={threadEnd}/></div>
        <div className="admin-composer">
          {sendError && <p className="admin-send-error" role="alert">{sendError}</p>}
          <div><textarea rows={2} value={draft} onChange={(event) => setDraft(event.target.value)} onKeyDown={handleKeyDown} disabled={selected.status !== "admin_active" || actionLoading} placeholder={selected.status === "admin_active" ? "Tulis balasan sebagai tim GlowMart..." : "Ambil alih percakapan untuk membalas"} aria-label="Balasan admin"/><button onClick={() => void sendMessage()} disabled={selected.status !== "admin_active" || actionLoading || !draft.trim()} aria-label="Kirim balasan admin"><Send size={18} aria-hidden="true"/></button></div>
          <small>{selected.status === "admin_active" ? "Tekan Enter untuk mengirim, Shift+Enter untuk baris baru" : "Kolom balasan aktif setelah percakapan diambil alih"}</small>
        </div>
      </> : <EmptyState icon={Inbox} title="Pilih percakapan" description="Riwayat percakapan akan tampil di sini."/>}
    </section>
    <ConversationDetails conversation={selected}/>
  </div>;
}
