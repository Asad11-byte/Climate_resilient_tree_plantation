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
    // h-full, not a guessed viewport-minus-pixels value — Layout's <main>
    // is now the one true scroll container, so this only needs to fill
    // whatever height main actually gives it. That's what fixes the
    // double-scrollbar bug: previously this page's own guessed height
    // didn't quite match main's real available height, so both this
    // page's inner list AND the outer page could end up scrollable at
    // once.
    <div className="flex h-full flex-col">
      <div className="mx-auto flex w-full max-w-3xl flex-1 flex-col overflow-hidden">
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
          <div className="flex-1 space-y-4 overflow-y-auto px-4 pb-6 pt-6 sm:px-2">
            {messages.map((message, i) => (
              <ChatMessage key={i} message={message} />
            ))}
            {loading && <ThinkingIndicator />}
            {error && <ErrorState error={error} onRetry={retryLast} />}
            <div ref={scrollRef} />
          </div>
        )}

        <div className="sticky bottom-0 bg-gradient-to-t from-page from-65% to-transparent px-4 pb-4 pt-6 sm:px-2">
          <ChatInput
            onSend={handleSend}
            disabled={loading}
            locationLabel={locationLabel}
            onClearLocation={onClearMapSelection}
          />
        </div>
      </div>
    </div>
  );
}