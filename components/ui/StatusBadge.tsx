import type { ReactNode } from "react";

export function StatusBadge({ tone = "neutral", children }: { tone?: "success" | "warning" | "error" | "neutral"; children: ReactNode }) {
  return <span className={`status-badge status-${tone}`}>{children}</span>;
}
