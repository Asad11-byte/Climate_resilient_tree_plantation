export default function SourceList({ sources }) {
  if (!sources?.length) return null;

  return (
    <div className="mt-3 border-t border-bark-500/15 pt-3">
      <p className="text-xs font-medium uppercase tracking-wide text-bark-500">Sources</p>
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
    </div>
  );
}
