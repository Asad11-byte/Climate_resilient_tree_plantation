import { useCallback, useEffect, useState } from "react";
import {
  createSession,
  deleteSession,
  fetchSessionMessages,
  fetchSessions,
  renameSession,
} from "../api/sessions";
import { normalizeApiError } from "../api/client";

/**
 * Manages the sidebar's session list against the FastAPI /api/sessions
 * endpoints (backed by the chat_sessions / chat_messages tables), via the
 * same apiClient postChat uses — so it picks up the same VITE_API_BASE_URL,
 * timeout, and error shape instead of guessing its own base URL.
 */
export function useConversations() {
  const [conversations, setConversations] = useState([]);
  const [activeConversationId, setActiveConversationId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setConversations(await fetchSessions());
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const createConversation = useCallback(async () => {
    const created = await createSession();
    setConversations((prev) => [created, ...prev]);
    setActiveConversationId(created.id);
    return created;
  }, []);

  const renameConversation = useCallback(
    async (id, title) => {
      setConversations((prev) => prev.map((c) => (c.id === id ? { ...c, title } : c)));
      try {
        await renameSession(id, title);
      } catch (err) {
        refresh(); // roll back to server truth on failure
        throw err;
      }
    },
    [refresh]
  );

  const deleteConversation = useCallback(
    async (id) => {
      const prev = conversations;
      setConversations((cur) => cur.filter((c) => c.id !== id));
      if (activeConversationId === id) setActiveConversationId(null);
      try {
        await deleteSession(id);
      } catch (err) {
        setConversations(prev);
        throw err;
      }
    },
    [conversations, activeConversationId]
  );

  // Fetch full message history for a session — called when the user clicks
  // a conversation in the sidebar, then fed into useChat.loadConversation.
  const loadMessages = useCallback((id) => fetchSessionMessages(id), []);

  return {
    conversations,
    activeConversationId,
    setActiveConversationId,
    loading,
    error,
    createConversation,
    renameConversation,
    deleteConversation,
    loadMessages,
    refresh,
  };
}