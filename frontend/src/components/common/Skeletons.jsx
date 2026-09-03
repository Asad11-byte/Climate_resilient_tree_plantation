export function SpeciesGridSkeleton({ count = 6 }) {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3" aria-hidden="true">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="animate-pulse rounded-lg border border-bark-500/15 p-4">
          <div className="h-4 w-2/3 rounded bg-bark-500/15" />
          <div className="mt-2 h-3 w-1/2 rounded bg-bark-500/10" />
          <div className="mt-4 space-y-2">
            <div className="h-3 w-full rounded bg-bark-500/10" />
            <div className="h-3 w-5/6 rounded bg-bark-500/10" />
          </div>
        </div>
      ))}
    </div>
  );
}

export function SourceListSkeleton({ count = 4 }) {
  return (
    <div className="space-y-3" aria-hidden="true">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="animate-pulse rounded-lg border border-bark-500/15 p-4">
          <div className="h-4 w-3/4 rounded bg-bark-500/15" />
          <div className="mt-2 h-3 w-1/3 rounded bg-bark-500/10" />
        </div>
      ))}
    </div>
  );
}

/**
 * Chat's loading state needs context, not just a spinner — Groq calls can
 * take several seconds and a bare spinner reads as broken past ~2s.
 */
export function ThinkingIndicator() {
  return (
    <div className="flex items-center gap-3 rounded-lg border border-leaf-600/20 bg-leaf-100/40 px-4 py-3 text-sm text-bark-700">
      <span className="flex gap-1" aria-hidden="true">
        <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-leaf-600 [animation-delay:-0.3s]" />
        <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-leaf-600 [animation-delay:-0.15s]" />
        <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-leaf-600" />
      </span>
      Weighing this against the evidence…
    </div>
  );
}
