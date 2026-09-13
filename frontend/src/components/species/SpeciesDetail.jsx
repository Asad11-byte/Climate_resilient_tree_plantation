import { fieldValue } from "./fieldValue";
import LeafPlaceholderIcon from "../common/LeafPlaceholderIcon";

const ROWS = [
  ["Local names", "local_names"],
  ["Soil requirements", "soil_requirements"],
  ["Water requirement", "water_requirement"],
  ["Drought tolerance", "drought_tolerance"],
  ["Heat tolerance", "heat_tolerance"],
  ["Flood tolerance", "flood_tolerance"],
  ["Growth rate", "growth_rate"],
  ["Planting season", "planting_season"],
  ["Plantation use", "plantation_use"],
  ["Local presence", "local_presence"],
];

export default function SpeciesDetail({ species }) {
  return (
    <div>
      {species.image_url ? (
        <img
          src={species.image_url}
          alt={species.common_name}
          className="h-64 w-full rounded-lg object-cover"
          loading="lazy"
        />
      ) : (
        <div className="flex h-64 w-full items-center justify-center rounded-lg bg-panel">
          <LeafPlaceholderIcon className="h-12 w-12 text-bark-500" />
        </div>
      )}
      {species.image_url && species.image_source && (
        <p className="mt-1 text-xs text-bark-500">Photo: {species.image_source}</p>
      )}

      <p className="mt-4 font-[var(--font-display)] text-3xl font-semibold text-soil-900">{species.common_name}</p>
      <p className="mt-1 text-lg italic text-bark-500">{species.scientific_name}</p>

      {species.description && (
        <p className="mt-4 max-w-2xl text-soil-900">{species.description}</p>
      )}
      {!species.description && (
        <p className="mt-4 text-sm italic text-bark-500">{fieldValue(null)}</p>
      )}

      <dl className="mt-6 divide-y divide-bark-500/10 rounded-lg border border-bark-500/15 bg-card/50">
        {ROWS.map(([label, key]) => (
          <div key={key} className="grid grid-cols-[180px_1fr] gap-4 px-4 py-3">
            <dt className="text-sm text-bark-700">{label}</dt>
            <dd className="text-sm text-soil-900">{fieldValue(species[key])}</dd>
          </div>
        ))}
      </dl>

      <p className="mt-4 text-xs text-bark-500">
        {species.source_ids?.length
          ? `Backed by ${species.source_ids.length} source${species.source_ids.length === 1 ? "" : "s"} in the knowledge base.`
          : "No linked sources recorded for this entry."}
      </p>
    </div>
  );
}