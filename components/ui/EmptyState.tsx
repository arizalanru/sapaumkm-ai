import type { LucideIcon } from "lucide-react";

export function EmptyState({ icon: Icon, title, description }: { icon: LucideIcon; title: string; description: string }) {
  return <div className="empty-state"><Icon size={24} aria-hidden="true"/><strong>{title}</strong><p>{description}</p></div>;
}
