const SERVICE_LABELS = {
  groq: "Groq",
  jina_embeddings: "Jina embeddings",
  jina_reranker: "Jina reranker",
  qdrant: "Qdrant",
  supabase: "Supabase",
};

function ServiceDot({ label, ok }) {
  return (
    <span className="inline-flex items-center gap-1.5 text-xs text-bark-700">
      <span
        className={`h-1.5 w-1.5 rounded-full ${ok ? "bg-leaf-600" : "bg-clay-600"}`}
        aria-hidden="true"
      />
      {label}
    </span>
  );
}

export default function HealthStrip({ loading, error, data }) {
  if (loading) {
    return <p className="text-xs text-bark-500">Checking system status…</p>;
  }

  if (error) {
    return <p className="text-xs text-clay-600">Couldn't reach the backend to check status.</p>;
  }

  if (!data) return null;

  const isDegraded = data.status === "degraded";

  return (
    <div>
      {isDegraded && (
        <p className="mb-2 text-sm font-medium text-clay-600">
          Some services are degraded — answers may be incomplete or unavailable.
        </p>
      )}
      <div className="flex flex-wrap gap-x-4 gap-y-1.5">
        {Object.entries(data.services || {}).map(([key, ok]) => (
          <ServiceDot key={key} label={SERVICE_LABELS[key] || key} ok={ok} />
        ))}
      </div>
    </div>
  );
}
