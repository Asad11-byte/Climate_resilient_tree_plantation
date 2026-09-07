export default function SourceResultCard({ source }) {
  return (
    <div className="rounded-lg border border-bark-500/15 bg-card/50 p-4">
      <div className="flex items-start justify-between gap-3">
        <p className="font-medium text-soil-900">{source.title || source.document_id}</p>
        {source.year && <span className="shrink-0 text-sm text-bark-500">{source.year}</span>}
      </div>
      <div className="mt-1.5 flex flex-wrap gap-x-3 gap-y-1 text-sm text-bark-700">
        {source.document_type && <span>{source.document_type}</span>}
        {source.source && <span>{source.source}</span>}
        {source.location && <span>{source.location}</span>}
        {source.page && <span>p. {source.page}</span>}
      </div>
      {source.source_url && (
        <a
          href={source.source_url}
          target="_blank"
          rel="noreferrer"
          className="mt-2 inline-block text-sm text-leaf-700 underline decoration-leaf-600/40 underline-offset-2 hover:decoration-leaf-600"
        >
          View source
        </a>
      )}
    </div>
  );
}
