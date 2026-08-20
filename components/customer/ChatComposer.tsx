"use client";

import { Send } from "lucide-react";
import { useEffect, useRef, type ChangeEvent, type FormEvent, type KeyboardEvent } from "react";

export function ChatComposer({ value, onChange, onSend, loading, disabled = false }: { value: string; onChange: (value: string) => void; onSend: () => void; loading: boolean; disabled?: boolean }) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const isDisabled = loading || disabled;
  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;
    textarea.style.height = "auto";
    textarea.style.height = `${Math.min(textarea.scrollHeight, 104)}px`;
  }, [value]);

  function handleChange(event: ChangeEvent<HTMLTextAreaElement>) {
    onChange(event.target.value);
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      event.currentTarget.form?.requestSubmit();
    }
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!isDisabled && value.trim()) onSend();
  }

  return <div className="composer-area"><form className="composer" onSubmit={handleSubmit}><textarea ref={textareaRef} rows={1} value={value} disabled={isDisabled} onChange={handleChange} onKeyDown={handleKeyDown} placeholder={disabled ? "Mulai percakapan baru untuk mengirim pesan" : "Tulis pesan Anda..."} aria-label="Pesan untuk layanan pelanggan"/><button type="submit" className="send-button" disabled={isDisabled || !value.trim()} aria-label="Kirim pesan"><Send size={18} aria-hidden="true"/></button></form><p>Sapa dapat membuat kesalahan. Informasi penting diverifikasi dari data GlowMart.</p></div>;
}
