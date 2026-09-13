import { useEffect, useRef, useState } from "react";
import { useChat } from "../hooks/useChat";
import { useConversations } from "../hooks/useConversations";
import { useAuth } from "../context/AuthContext";
import Sidebar from "../components/common/Sidebar";
import ChatMessage from "../components/chat/ChatMessage";
import ChatInput from "../components/chat/ChatInput";
import ErrorState from "../components/common/ErrorState";
import { ThinkingIndicator } from "../components/common/Skeletons";

function SidebarAccountFooter({ email, onSignOut }) {
  return (
    <div className="flex items-center justify-between gap-2">
      <div className="min-w-0">
        <p className="truncate text-xs text-bark-500">Signed in as</p>
        <p className="truncate text-sm text-soil-900">{email}</p>
      </div>
      <button
        type="button"
        onClick={onSignOut}
        className="shrink-0 rounded-md border border-bark-500/20 px-2.5 py-1.5 text-xs font-medium text-bark-700 hover:bg-bark-500/10"
      >
        Sign out
      </button>
    </div>
  );
}

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
  const { user, signOut } = useAuth();
  const scrollRef = useRef(null);

  // Sidebar is `fixed` now (see Sidebar.jsx's file-level comment), so it no
  // longer reserves space as a flex sibling — the content pane below has to
  // reserve matching space itself. Lifting `collapsed` here (via
  // onCollapsedChange) is what lets that space track the rail's actual
  // width instead of guessing one fixed value.
  const [sidebarCollapsed, setSidebarCollapsed] = useState(
    () => typeof window !== "undefined" && window.localStorage.getItem("sidebar:collapsed") === "1",
  );

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

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

  // Wipes this browser's visible chat state on sign-out so the next person
  // to use it doesn't land on the previous user's conversation — the
  // conversations list itself belongs to the signed-out account and simply
  // won't be fetchable once the token is gone, but the in-memory message
  // pane needs an explicit reset since it isn't re-derived from that list.
  const handleSignOut = async () => {
    await signOut();
    startNewChat();
    setActiveConversationId(null);
  };

  return (
    // No more flex-row wrapper around Sidebar — it isn't a flow participant
    // anymore. `pt-14 md:pt-0` clears the fixed mobile top bar; the
    // `md:pl-*` swap clears the fixed desktop rail at whichever width it's
    // currently at.
    <div className={`h-full pt-14 transition-[padding] duration-200 ease-in-out md:pt-0 ${sidebarCollapsed ? "md:pl-16" : "md:pl-72"}`}>
      <Sidebar
        conversations={conversations}
        activeConversationId={activeConversationId}
        onSelectConversation={handleSelectConversation}
        onNewChat={handleNewChat}
        onRenameConversation={renameConversation}
        onDeleteConversation={deleteConversation}
        onCollapsedChange={setSidebarCollapsed}
        loading={conversationsLoading}
        error={conversationsError}
        footer={<SidebarAccountFooter email={user?.email} onSignOut={handleSignOut} />}
      />

      <div className="flex h-full flex-col overflow-hidden">
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