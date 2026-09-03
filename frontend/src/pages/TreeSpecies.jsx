import { useSpeciesList } from "../hooks/useSpecies";
import SpeciesCard from "../components/species/SpeciesCard";
import { SpeciesGridSkeleton } from "../components/common/Skeletons";
import ErrorState from "../components/common/ErrorState";
import EmptyState from "../components/common/EmptyState";

export default function TreeSpecies() {
  const { data, loading, error, refetch } = useSpeciesList();

  return (
    <div>
      <h1 className="font-[var(--font-display)] text-2xl font-semibold text-soil-900">Tree Species</h1>
      <p className="mt-1 text-sm text-bark-700">
        Every profile here reflects what the evidence base actually contains — gaps are shown, not filled in.
      </p>

      <div className="mt-6">
        {loading && <SpeciesGridSkeleton />}
        {!loading && error && <ErrorState error={error} onRetry={refetch} />}
        {!loading && !error && data?.length === 0 && (
          <EmptyState
            title="No species recorded yet"
            description="Nothing has been ingested into the knowledge base for this category yet."
          />
        )}
        {!loading && !error && data?.length > 0 && (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {data.map((species) => (
              <SpeciesCard key={species.id} species={species} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
