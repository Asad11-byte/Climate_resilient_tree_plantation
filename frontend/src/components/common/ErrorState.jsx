/**
 * Retry-able error card. Distinguishes a backend-reported failure (e.g. 503
 * from an upstream provider) from a network failure reaching the server at
 * all — the causes are different, so the messages are too.
 */
export default function ErrorState({ error, onRetry, className = "" }) {
  const isHttp = error?.type === "http";
  const isUpstream = isHttp && error.status === 503;

  const title = isUpstream
    ? "The AI service is temporarily unavailable"
    : isHttp
      ? `Request failed (${error.status})`
      : "Couldn't reach the server";

  const detail = isUpstream
    ? error.detail || "One of the underlying providers (Groq, Jina, Qdrant, or Supabase) isn't responding right now. Try again in a moment."
    : error?.detail || "Something went wrong. Try again.";

  return (
    <div
      role="alert"
      className={`rounded-lg border border-clay-600/30 bg-clay-600/5 px-5 py-4 ${className}`}
    >
      <p className="font-medium text-soil-900">{title}</p>
      <p className="mt-1 text-sm text-bark-700">{detail}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-3 rounded-md border border-soil-800/20 bg-parchment-50 px-3 py-1.5 text-sm font-medium text-soil-900 transition hover:border-soil-800/40 focus-visible:outline focus-visible:outline-2 focus-visible:outline-leaf-600"
        >
          Try again
        </button>
      )}
    </div>
  );
}
