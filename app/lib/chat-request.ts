// Keep these outside React so timing/history behavior can be tested directly.
export const PROXY_TIMEOUT_MS = 60000;
export const BROWSER_TIMEOUT_MS = 70000;
export const RETRY_MESSAGE = 'Ask LichenLens could not generate a response right now. Please try again shortly.';
export function thinkingLabel(slow: boolean) {
  return slow ? 'Thinking… This is taking a little longer.' : 'Thinking…';
}
export function conversationHistory(turns: {id:string; question:string; reply?:{answer:string}; error?:string}[], retryId?:string) {
  const before = retryId ? turns.slice(0, turns.findIndex(t => t.id === retryId)) : turns;
  return before.filter(t => t.reply && !t.error).slice(-3).flatMap(t => [
    {role:'user' as const,content:t.question.slice(0,1200)},
    {role:'assistant' as const,content:t.reply!.answer.slice(0,1200)},
  ]);
}
export function requestHistory(body: Record<string, unknown>) {
  const raw = body.conversation_history;
  if (raw !== undefined) {
    if (!Array.isArray(raw) || raw.length > 6 || raw.some(m => !m ||
        !['user','assistant'].includes(m.role) || typeof m.content !== 'string' ||
        !m.content.trim() || m.content.length > 1200)) throw Error('Invalid conversation history');
    return raw.map(m => ({role:m.role as 'user'|'assistant',content:m.content.trim()}));
  }
  // Compatibility with older clients which sent question/answer pairs.
  return (Array.isArray(body.history) ? body.history : []).slice(-3).flatMap(h => {
    if (!h || typeof h.question !== 'string' || !h.question.trim()) return [];
    const messages = [{role:'user' as 'user'|'assistant',content:h.question.slice(0,1200)}];
    if (typeof h.answer === 'string' && h.answer.trim()) messages.push({role:'assistant',content:h.answer.slice(0,1200)});
    return messages;
  });
}

// Cloud previews can use HTTP, where randomUUID is absent even though secure
// random bytes are available. These IDs identify chats, not authentication.
export function createChatId(){
 if(typeof crypto.randomUUID==='function')return crypto.randomUUID();
 const bytes=crypto.getRandomValues(new Uint8Array(16));bytes[6]=(bytes[6]&15)|64;bytes[8]=(bytes[8]&63)|128;
 const hex=Array.from(bytes,b=>b.toString(16).padStart(2,'0')).join('');return `${hex.slice(0,8)}-${hex.slice(8,12)}-${hex.slice(12,16)}-${hex.slice(16,20)}-${hex.slice(20)}`;
}
