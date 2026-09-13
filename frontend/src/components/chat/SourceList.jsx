import { useState } from "react";

export default function SourceList({ sources }) {
  const [isOpen, setIsOpen] = useState(false);

  if (!sources?.length) return null;

  return (
    <div className="mt-3 border-t border-bark-500/15 pt-3">
      <button
        type="button"
        onClick={() => setIsOpen((v) => !v)}
        aria-expanded={isOpen}
        className="flex w-full items-center gap-1.5 text-xs font-medium uppercase tracking-wide text-bark-500 transition hover:text-soil-900"
      >
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className={`h-3 w-3 shrink-0 transition-transform duration-fast ${isOpen ? "rotate-90" : ""}`}
        >
          <path d="M9 6l6 6-6 6" />
        </svg>
        Sources ({sources.length})
      </button>

      {isOpen && (
        <ul className="mt-2 space-y-1.5">
          {sources.map((source, i) => {
            const label = [source.title, source.year].filter(Boolean).join(" · ");
            const content = (
              <>
                <span className="text-sm text-soil-900">{label || source.document_id}</span>
                {source.source && <span className="ml-1.5 text-xs text-bark-500">({source.source})</span>}
              </>
            );
            return (
              <li key={source.document_id || i}>
                {source.source_url ? (
                  <a
                    href={source.source_url}
                    target="_blank"
                    rel="noreferrer"
                    className="underline decoration-leaf-600/40 underline-offset-2 hover:decoration-leaf-600"
                  >
                    {content}
                  </a>
                ) : (
                  content
                )}
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}