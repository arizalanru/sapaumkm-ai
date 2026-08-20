import { Clock } from "lucide-react";

export function LoadingState({ label = "Memuat data" }: { label?: string }) {
  return <div className="loading-state" role="status"><Clock size={16} aria-hidden="true"/><span>{label}</span></div>;
}
