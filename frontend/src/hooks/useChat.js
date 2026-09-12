import { useCallback, useState } from "react";
import { postChat } from "../api/chat";
import { normalizeApiError } from "../api/client";

/**
 * Owns the AI Assistant's conversation state. Each entry in `messages` is
 * either { role: "user", text } or { role: "assistant", response } where
 * `response` is the raw /chat response (so the UI can render
 * evidence_available, sources, etc. distinctly).
 *
 * Also owns `sessionId`: null means "no session yet, the next sendMessage
 * will create one on the backend." Once a response comes back, sessionId is
 * set from it so every subsequent message in this chat continues the same
 * backend session instead of creating a new one each turn.
 */
export function useChat() {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [lastQuery, setLastQuery] = useState(null);
  const [sessionId, setSessionId] = useState(null);

  const sendMessage = useCallback(
    async (query, { latitude = null, longitude = null } = {}) => {
      if (!query?.trim()) return;

      setMessages((prev) => [...prev, { role: "user", text: query }]);
      setLoading(true);
      setError(null);
      setLastQuery({ query, latitude, longitude });

      try {
        const response = await postChat({ query, latitude, longitude, sessionId });
        setMessages((prev) => [...prev, { role: "assistant", response }]);
        // Always sync from the response: on the first message this is where
        // sessionId goes from null -> a real id; on later messages it just
        // confirms we're still on the same session.
        if (response.session_id) setSessionId(response.session_id);
      } catch (err) {
        setError(normalizeApiError(err));
      } finally {
        setLoading(false);
      }
    },
    [sessionId]
  );

  const retryLast = useCallback(() => {
    if (lastQuery) {
      setError(null);
      sendMessage(lastQuery.query, { latitude: lastQuery.latitude, longitude: lastQuery.longitude });
    }
  }, [lastQuery, sendMessage]);

  // Clears the pane for a fresh conversation. Deliberately does NOT create a
  // backend session — that happens lazily on the first sendMessage, so
  // clicking "New chat" repeatedly doesn't litter the sidebar with empty
  // untitled sessions.
  const startNewChat = useCallback(() => {
    setMessages([]);
    setSessionId(null);
    setError(null);
    setLastQuery(null);
  }, []);

  // Replaces the pane with a previously-saved conversation. `rawMessages` is
  // whatever GET /api/sessions/{id}/messages returns (MessageSchema[],
  // camelCase) — mapped here into the same { role, text | response } shape
  // sendMessage produces, so ChatMessage doesn't need to know the source.
  const loadConversation = useCallback((id, rawMessages) => {
    const mapped = rawMessages.map((m) =>
      m.role === "user"
        ? { role: "user", text: m.content }
        : {
            role: "assistant",
            response: {
              query_category: m.queryCategory,
              evidence_available: m.evidenceAvailable,
              answer: m.content,
              sources: m.sources ?? [],
              model: null,
              session_id: id,
            },
          }
    );
    setMessages(mapped);
    setSessionId(id);
    setError(null);
    setLastQuery(null);
  }, []);

  return {
    messages,
    loading,
    error,
    sendMessage,
    retryLast,
    sessionId,
    startNewChat,
    loadConversation,
  };
}