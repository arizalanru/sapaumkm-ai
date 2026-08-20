export const CUSTOMER_CONVERSATION_STORAGE_KEY = "glowmart.activeConversationId";

type ConversationStorage = Pick<Storage, "getItem" | "setItem" | "removeItem">;

export function readStoredConversationId(storage: ConversationStorage): number | undefined {
  try {
    const value = storage.getItem(CUSTOMER_CONVERSATION_STORAGE_KEY);
    if (!value) return undefined;
    const parsed = Number(value);
    return Number.isSafeInteger(parsed) && parsed > 0 ? parsed : undefined;
  } catch {
    return undefined;
  }
}

export function storeConversationId(storage: ConversationStorage, conversationId: number) {
  try {
    storage.setItem(CUSTOMER_CONVERSATION_STORAGE_KEY, String(conversationId));
  } catch {
    // Browsers may disable storage. React state still keeps the active session.
  }
}

export function clearStoredConversationId(storage: ConversationStorage) {
  try {
    storage.removeItem(CUSTOMER_CONVERSATION_STORAGE_KEY);
  } catch {
    // Reset React state even when browser storage is unavailable.
  }
}

export function stableReturnedConversationId(requestedId: number | undefined, returnedId: number) {
  if (requestedId !== undefined && requestedId !== returnedId) {
    throw new Error("Backend returned a different conversation ID for an active conversation");
  }
  return requestedId ?? returnedId;
}
