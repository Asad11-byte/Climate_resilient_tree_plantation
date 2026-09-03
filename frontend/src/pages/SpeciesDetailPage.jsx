import { Link, useParams } from "react-router-dom";
import { useSpeciesDetail } from "../hooks/useSpecies";
import SpeciesDetail from "../components/species/SpeciesDetail";
import ErrorState from "../components/common/ErrorState";
import EmptyState from "../components/common/EmptyState";

export default function SpeciesDetailPage() {
  const { id } = useParams();
  const { data, loading, error, refetch } = useSpeciesDetail(id);

  return (
    <div>
      <Link to="/species" className="text-sm text-leaf-700 underline decoration-leaf-600/40 underline-offset-2">
        All species
      </Link>

      <div className="mt-4">
        {loading && (
          <div className="animate-pulse space-y-3" aria-hidden="true">
            <div className="h-8 w-1/3 rounded bg-bark-500/15" />
            <div className="h-4 w-1/4 rounded bg-bark-500/10" />
            <div className="mt-4 h-40 w-full rounded bg-bark-500/10" />
          </div>
        )}

        {!loading && error?.status === 404 && (
          <EmptyState
            title="Species not found"
            description="This entry may have been removed, or the link is out of date."
          />
        )}

        {!loading && error && error.status !== 404 && <ErrorState error={error} onRetry={refetch} />}

        {!loading && !error && data && <SpeciesDetail species={data} />}
      </div>
    </div>
  );
}
