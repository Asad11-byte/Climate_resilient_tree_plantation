import { useEffect, useRef } from "react";
import { useChat } from "../hooks/useChat";
import { useConversations } from "../hooks/useConversations";
import Sidebar from "../components/common/Sidebar";
import ThemeToggle from "../components/common/ThemeToggle";
import ChatMessage from "../components/chat/ChatMessage";
import ChatInput from "../components/chat/ChatInput";
import ErrorState from "../components/common/ErrorState";
import { ThinkingIndicator } from "../components/common/Skeletons";

export default function AIAssistant({ mapSelection, onClearMapSelection }) {
  const { messages, loading, error, sendMessage, retryLast, sessionId, startNewChat, loadConversation } =
    useChat();
  const {
    conversations,
    activeConversationId,
    setActiveConversationId,
    loading: conversationsLoading,
    error: conversationsError,
    renameConversation,
    deleteConversation,
    loadMessages,
    refresh,
  } = useConversations();
  const scrollRef = useRef(null);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  // useChat's sessionId is the source of truth for "which backend session is
  // this chat pane on" — it only changes when a message actually creates or
  // confirms one. Whenever it moves to a session the sidebar doesn't know is
  // active yet (typically: first message of a brand-new chat), sync the
  // sidebar's selection and refresh the list so the new/updated session
  // (with its generated title) shows up without a manual reload.
  useEffect(() => {
    if (sessionId && sessionId !== activeConversationId) {
      setActiveConversationId(sessionId);
      refresh();
    }
  }, [sessionId, activeConversationId, setActiveConversationId, refresh]);

  const locationLabel = mapSelection
    ? `${mapSelection.latitude.toFixed(4)}, ${mapSelection.longitude.toFixed(4)}`
    : null;

  const handleSend = (query) => {
    sendMessage(query, mapSelection ? { latitude: mapSelection.latitude, longitude: mapSelection.longitude } : {});
  };

  const handleSelectConversation = async (id) => {
    setActiveConversationId(id);
    try {
      const history = await loadMessages(id);
      loadConversation(id, history);
    } catch {
      // loadMessages already surfaces its own error via whatever calls it;
      // fall back to at least keeping the sidebar selection in sync.
    }
  };

  const handleNewChat = () => {
    startNewChat();
    setActiveConversationId(null);
  };

  return (
    <div className="flex h-full overflow-hidden">
      <Sidebar
        conversations={conversations}
        activeConversationId={activeConversationId}
        onSelectConversation={handleSelectConversation}
        onNewChat={handleNewChat}
        onRenameConversation={renameConversation}
        onDeleteConversation={deleteConversation}
        loading={conversationsLoading}
        error={conversationsError}
        
      />

      <div className="flex h-full flex-1 flex-col overflow-hidden">
        {messages.length === 0 ? (
          <div className="flex flex-1 flex-col items-center justify-center px-4 text-center">
            <h1 className="font-[var(--font-display)] text-2xl font-semibold text-soil-900">AI Assistant</h1>
            <p className="mt-2 max-w-md text-sm text-bark-700">
              Answers are grounded in retrieved evidence. When the evidence doesn't support a claim, that's
              stated plainly instead of guessed at.
            </p>
            <p className="mt-4 text-sm text-bark-500">
              Try: "What tree species tolerate drought in Mandi Bahauddin?"
            </p>
          </div>
        ) : (
          <div className="flex-1 overflow-y-auto">
            <div className="mx-auto max-w-3xl space-y-4 px-4 pb-6 pt-6 sm:px-2">
              {messages.map((message, i) => (
                <ChatMessage key={i} message={message} />
              ))}
              {loading && <ThinkingIndicator />}
              {error && <ErrorState error={error} onRetry={retryLast} />}
              <div ref={scrollRef} />
            </div>
          </div>
        )}

        <div className="bg-gradient-to-t from-page from-65% to-transparent px-4 pb-4 pt-6 sm:px-2">
          <div className="mx-auto max-w-3xl">
            <ChatInput
              onSend={handleSend}
              disabled={loading}
              locationLabel={locationLabel}
              onClearLocation={onClearMapSelection}
            />
          </div>
        </div>
      </div>
    </div>
  );
}