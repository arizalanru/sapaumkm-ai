import { Bot, Database, Headphones, User } from "lucide-react";
import type { Conversation } from "../../lib/types";
import { conversationDisplayName, formatDateTime, intentLabel } from "../../lib/text";
import { StatusBadge } from "../ui/StatusBadge";

export function ConversationDetails({ conversation }: { conversation?: Conversation }) {
  if (!conversation) return <aside className="conversation-details"><p className="muted-copy">Pilih percakapan untuk melihat detail.</p></aside>;
  const lastCustomer = [...conversation.messages].reverse().find((message) => message.sender === "customer");
  const state = {
    ai_active: { label: "AI aktif", tone: "success" as const, owner: "Ditangani Sapa" },
    waiting_admin: { label: "Menunggu admin", tone: "warning" as const, owner: "Menunggu operator" },
    admin_active: { label: "Admin aktif", tone: "success" as const, owner: "Ditangani tim GlowMart" },
    resolved: { label: "Selesai", tone: "neutral" as const, owner: "Percakapan selesai" },
  }[conversation.status];
  return <aside className="conversation-details"><div className="details-customer"><span><User size={20} aria-hidden="true"/></span><div><strong>{conversationDisplayName(conversation)}</strong><small>Dimulai {formatDateTime(conversation.started_at)}</small></div></div><dl><div><dt>Status percakapan</dt><dd><StatusBadge tone={state.tone}>{state.label}</StatusBadge></dd></div><div><dt>Topik terakhir</dt><dd>{intentLabel(lastCustomer?.intent)}</dd></div></dl><div className="details-note"><Database size={17} aria-hidden="true"/><p>Mode respons dan sumber data belum disimpan untuk setiap pesan. Detail teknis yang tidak tersedia disembunyikan.</p></div><div className="details-owner"><Headphones size={17} aria-hidden="true"/><span>{state.owner}</span><Bot size={16} aria-hidden="true"/></div></aside>;
}
