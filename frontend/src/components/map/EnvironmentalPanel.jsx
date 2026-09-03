import ErrorState from "../common/ErrorState";
import EmptyState from "../common/EmptyState";

const FIELDS = [
  { key: "soil_ph", label: "Soil pH" },
  { key: "clay", label: "Clay", unit: "%" },
  { key: "sand", label: "Sand", unit: "%" },
  { key: "organic_carbon", label: "Organic carbon", unit: "g/kg" },
  { key: "temperature", label: "Temperature", unit: "°C" },
  { key: "rainfall", label: "Rainfall", unit: "mm" },
  { key: "ndvi", label: "NDVI" },
  { key: "ndwi", label: "NDWI" },
  { key: "land_cover", label: "Land cover" },
];

function FieldRow({ label, value, unit }) {
  const isMissing = value === null || value === undefined;
  return (
    <div className="flex items-baseline justify-between border-b border-bark-500/10 py-1.5 last:border-0">
      <span className="text-sm text-bark-700">{label}</span>
      <span className={`text-sm ${isMissing ? "italic text-bark-500" : "font-medium text-soil-900"}`}>
        {isMissing ? "Not available from these sources" : `${value}${unit ? ` ${unit}` : ""}`}
      </span>
    </div>
  );
}

/**
 * A loading skeleton specific to this panel — the map stays interactive
 * while a fresh coordinate's live SoilGrids/NASA POWER lookup is in flight.
 */
function PanelSkeleton() {
  return (
    <div className="animate-pulse space-y-2" aria-hidden="true">
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} className="h-4 w-full rounded bg-bark-500/10" />
      ))}
      <p className="pt-2 text-xs text-bark-500">Fetching live soil and climate data for this point…</p>
    </div>
  );
}

export default function EnvironmentalPanel({ position, loading, error, data, onRetry }) {
  if (!position) {
    return (
      <EmptyState
        title="Click a point on the map"
        description="Select a location in Mandi Bahauddin to see its environmental data."
      />
    );
  }

  if (loading) return <PanelSkeleton />;

  if (error) return <ErrorState error={error} onRetry={onRetry} />;

  if (!data) return null;

  if (!data.available) {
    return (
      <EmptyState
        title="Data unavailable for this location"
        description={data.message || "Neither the cache nor the live providers have coverage for this point."}
      />
    );
  }

  const record = data.record;

  return (
    <div>
      {record.data_source && (
        <p className="mb-2 text-xs text-bark-500">
          Estimated from: <span className="font-medium">{record.data_source}</span> — not a field measurement
        </p>
      )}
      <div>
        {FIELDS.map(({ key, label, unit }) => (
          <FieldRow key={key} label={label} value={record[key]} unit={unit} />
        ))}
      </div>
      {record.retrieved_at && (
        <p className="mt-2 text-xs text-bark-500">Retrieved {new Date(record.retrieved_at).toLocaleString()}</p>
      )}
    </div>
  );
}
