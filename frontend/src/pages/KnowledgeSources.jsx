import { useState } from "react";
import { useRetrieve } from "../hooks/useRetrieve";
import SourceResultCard from "../components/sources/SourceResultCard";
import { SourceListSkeleton } from "../components/common/Skeletons";
import ErrorState from "../components/common/ErrorState";
import EmptyState from "../components/common/EmptyState";

export default function KnowledgeSources() {
  const [query, setQuery] = useState("");
  const { data, loading, error, search, retry } = useRetrieve();

  const handleSubmit = (e) => {
    e.preventDefault();
    search(query);
  };

  return (
    <div>
      <h1 className="font-[var(--font-display)] text-2xl font-semibold text-soil-900">Knowledge Sources</h1>
      <p className="mt-1 text-sm text-bark-700">
        Search the retrieval layer directly to see which documents ground a given topic.
      </p>

      <form onSubmit={handleSubmit} className="mt-6 flex gap-2">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="e.g. soil salinity, drought-tolerant species, rainfall patterns…"
          className="flex-1 rounded-lg border border-bark-500/25 bg-card px-4 py-2.5 text-sm text-soil-900 placeholder:text-bark-500/70 focus:border-leaf-600 focus:outline-none focus:ring-1 focus:ring-leaf-600"
        />
        <button
          type="submit"
          disabled={loading || !query.trim()}
          className="rounded-lg bg-leaf-700 px-5 py-2.5 text-sm font-medium text-parchment-50 transition hover:bg-leaf-600 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Search
        </button>
      </form>

      <div className="mt-6">
        {!data && !loading && !error && (
          <EmptyState
            title="Search to see what's grounding an answer"
            description="Results show the actual documents the retrieval layer finds for a query, ranked by relevance."
          />
        )}

        {loading && <SourceListSkeleton />}

        {!loading && error && <ErrorState error={error} onRetry={retry} />}

        {!loading && !error && data && data.sources.length === 0 && (
          <EmptyState
            title="No matching sources"
            description={`Nothing in the knowledge base is close enough to "${data.query}" to surface as a source.`}
          />
        )}

        {!loading && !error && data && data.sources.length > 0 && (
          <div className="space-y-3">
            {data.query_category && (
              <p className="text-xs font-medium uppercase tracking-wide text-leaf-700">
                {data.query_category.replace("_", " ")}
              </p>
            )}
            {data.sources.map((source, i) => (
              <SourceResultCard key={source.document_id || i} source={source} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
