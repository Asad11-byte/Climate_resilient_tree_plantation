import { useCallback, useState } from "react";
import { postChat } from "../api/chat";
import { normalizeApiError } from "../api/client";

/**
 * Owns the AI Assistant's conversation state. Each entry in `messages` is
 * either { role: "user", text } or { role: "assistant", response } where
 * `response` is the raw /chat response (so the UI can render
 * evidence_available, sources, etc. distinctly).
 */
export function useChat() {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [lastQuery, setLastQuery] = useState(null);

  const sendMessage = useCallback(async (query, { latitude = null, longitude = null } = {}) => {
    if (!query?.trim()) return;

    setMessages((prev) => [...prev, { role: "user", text: query }]);
    setLoading(true);
    setError(null);
    setLastQuery({ query, latitude, longitude });

    try {
      const response = await postChat({ query, latitude, longitude });
      setMessages((prev) => [...prev, { role: "assistant", response }]);
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setLoading(false);
    }
  }, []);

  const retryLast = useCallback(() => {
    if (lastQuery) {
      setError(null);
      sendMessage(lastQuery.query, { latitude: lastQuery.latitude, longitude: lastQuery.longitude });
    }
  }, [lastQuery, sendMessage]);

  return { messages, loading, error, sendMessage, retryLast };
}
