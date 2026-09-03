const STACK = [
  ["Retrieval", "Qdrant vector search over ingested agricultural and climate documents"],
  ["Reranking", "Jina reranker, to sort retrieved chunks by actual relevance to the query"],
  ["Generation", "Groq, constrained to write only from retrieved evidence"],
  ["Structured data", "Supabase — species profiles and environmental records"],
  ["Environmental lookups", "SoilGrids (soil properties) and NASA POWER (temperature, rainfall), fetched live on a cache miss"],
];

export default function About() {
  return (
    <div className="max-w-2xl">
      <h1 className="font-[var(--font-display)] text-2xl font-semibold text-soil-900">About this project</h1>
      <p className="mt-3 text-soil-900">
        This is a location-aware recommendation system for climate-resilient tree plantation in Mandi Bahauddin,
        Punjab, Pakistan — built as an AI Engineering final year project. It answers questions about tree species,
        soil, water, and climate for the district, and pairs every recommendation with the environmental data and
        source documents behind it.
      </p>

      <h2 className="mt-8 font-[var(--font-display)] text-lg font-semibold text-soil-900">
        How this avoids guessing
      </h2>
      <p className="mt-2 text-soil-900">
        The system is built around a simple constraint: it should never answer beyond what its evidence supports.
        Every query first goes through retrieval, so an answer is written only from the documents that were
        actually found — not from general knowledge. Sources are cited rather than paraphrased freely, so a claim
        can always be traced back to where it came from. And when retrieval doesn't turn up enough to support an
        answer, the system says so directly instead of producing something plausible-sounding — that's the
        <code className="mx-1 rounded bg-bark-500/10 px-1.5 py-0.5 text-sm">evidence_available: false</code>
        state you'll see in the AI Assistant.
      </p>

      <h2 className="mt-8 font-[var(--font-display)] text-lg font-semibold text-soil-900">Architecture</h2>
      <dl className="mt-3 divide-y divide-bark-500/10 rounded-lg border border-bark-500/15 bg-white/50">
        {STACK.map(([label, description]) => (
          <div key={label} className="grid grid-cols-[140px_1fr] gap-4 px-4 py-3">
            <dt className="text-sm text-bark-700">{label}</dt>
            <dd className="text-sm text-soil-900">{description}</dd>
          </div>
        ))}
      </dl>

      <h2 className="mt-8 font-[var(--font-display)] text-lg font-semibold text-soil-900">Scope</h2>
      <p className="mt-2 text-soil-900">
        The knowledge base and environmental lookups are scoped to Mandi Bahauddin district. Recommendations
        outside that area, or on topics the knowledge base hasn't ingested yet, will come back as
        "no evidence found" rather than a generic answer.
      </p>

      <h2 className="mt-8 font-[var(--font-display)] text-lg font-semibold text-soil-900">Frontend stack</h2>
      <p className="mt-2 text-soil-900">React, Vite, Tailwind CSS, React-Leaflet, and Axios.</p>
    </div>
  );
}
