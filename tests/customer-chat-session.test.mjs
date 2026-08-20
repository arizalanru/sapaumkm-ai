import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import {
  CUSTOMER_CONVERSATION_STORAGE_KEY,
  clearStoredConversationId,
  readStoredConversationId,
  stableReturnedConversationId,
  storeConversationId,
} from "../lib/customer-conversation.ts";

class MemoryStorage {
  values = new Map();
  getItem(key) { return this.values.get(key) ?? null; }
  setItem(key, value) { this.values.set(key, String(value)); }
  removeItem(key) { this.values.delete(key); }
}

const composerSource = await readFile(new URL("../components/customer/ChatComposer.tsx", import.meta.url), "utf8");
const shellSource = await readFile(new URL("../components/customer/ChatShell.tsx", import.meta.url), "utf8");

test("composer submission prevents navigation and uses an explicit submit button", () => {
  assert.match(composerSource, /<form[^>]*onSubmit=\{handleSubmit\}/);
  assert.match(composerSource, /function handleSubmit[\s\S]*?event\.preventDefault\(\)/);
  assert.match(composerSource, /<button type="submit"/);
  assert.match(composerSource, /event\.currentTarget\.form\?\.requestSubmit\(\)/);
});

test("first response stores its conversation ID", () => {
  const storage = new MemoryStorage();
  const activeId = stableReturnedConversationId(undefined, 41);
  storeConversationId(storage, activeId);
  assert.equal(activeId, 41);
  assert.equal(storage.getItem(CUSTOMER_CONVERSATION_STORAGE_KEY), "41");
});

test("later messages keep the requested conversation ID stable", () => {
  assert.equal(stableReturnedConversationId(41, 41), 41);
  assert.throws(() => stableReturnedConversationId(41, 99), /different conversation ID/);
  assert.match(shellSource, /sendChat\(content, requestedConversationId\)/);
});

test("rerenders and initialization do not POST a new conversation", () => {
  assert.equal(shellSource.match(/sendChat\(/g)?.length, 1);
  assert.match(shellSource, /useEffect\(\(\) => \{[\s\S]*?readStoredConversationId\(window\.localStorage\)/);
});

test("polling cannot replace a newer active conversation ID", () => {
  assert.match(shellSource, /conversationIdRef\.current !== pollingConversationId/);
  assert.match(shellSource, /getConversationMessages\(pollingConversationId\)/);
  assert.match(shellSource, /getConversation\(pollingConversationId\)/);
});

test("browser refresh restores the persisted conversation", () => {
  const storage = new MemoryStorage();
  storeConversationId(storage, 73);
  assert.equal(readStoredConversationId(storage), 73);
});

test("only the explicit new-conversation path clears persisted state", () => {
  const storage = new MemoryStorage();
  storeConversationId(storage, 73);
  clearStoredConversationId(storage);
  assert.equal(readStoredConversationId(storage), undefined);
  assert.equal(shellSource.match(/clearStoredConversationId\(/g)?.length, 1);
  assert.match(shellSource, /function resetConversation\(\)[\s\S]*?clearStoredConversationId\(window\.localStorage\)/);
});
