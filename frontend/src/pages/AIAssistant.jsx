import { useEffect, useRef } from "react";
import { useChat } from "../hooks/useChat";
import ChatMessage from "../components/chat/ChatMessage";
import ChatInput from "../components/chat/ChatInput";
import ErrorState from "../components/common/ErrorState";
import EmptyState from "../components/common/EmptyState";
import { ThinkingIndicator } from "../components/common/Skeletons";

export default function AIAssistant({ mapSelection, onClearMapSelection }) {
  const { messages, loading, error, sendMessage, retryLast } = useChat();
  const scrollRef = useRef(null);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const locationLabel = mapSelection
    ? `${mapSelection.latitude.toFixed(4)}, ${mapSelection.longitude.toFixed(4)}`
    : null;

  const handleSend = (query) => {
    sendMessage(query, mapSelection ? { latitude: mapSelection.latitude, longitude: mapSelection.longitude } : {});
  };

  return (
    <div className="flex h-[calc(100vh-160px)] flex-col">
      <div className="mb-4">
        <h1 className="font-[var(--font-display)] text-2xl font-semibold text-soil-900">AI Assistant</h1>
        <p className="mt-1 text-sm text-bark-700">
          Answers are grounded in retrieved evidence. When the evidence doesn't support a claim, that's stated
          plainly instead of guessed at.
        </p>
      </div>

      <div className="flex-1 space-y-4 overflow-y-auto rounded-lg border border-bark-500/15 bg-parchment-100/40 p-4">
        {messages.length === 0 && (
          <EmptyState
            title="Ask your first question"
            description="Try something like “What tree species tolerate drought in Mandi Bahauddin?”"
          />
        )}
        {messages.map((message, i) => (
          <ChatMessage key={i} message={message} />
        ))}
        {loading && <ThinkingIndicator />}
        {error && <ErrorState error={error} onRetry={retryLast} />}
        <div ref={scrollRef} />
      </div>

      <div className="mt-4">
        <ChatInput
          onSend={handleSend}
          disabled={loading}
          locationLabel={locationLabel}
          onClearLocation={onClearMapSelection}
        />
      </div>
    </div>
  );
}
