import { Link } from "react-router-dom";
import { fieldValue } from "./fieldValue";
import LeafPlaceholderIcon from "../common/LeafPlaceholderIcon";

export default function SpeciesCard({ species }) {
  return (
    <Link
      to={`/species/${species.id}`}
      className="block rounded-lg border border-bark-500/15 bg-card/50 p-4 transition hover:border-leaf-600/40 hover:bg-card/80"
    >
      {species.image_url ? (
        <img
          src={species.image_url}
          alt={species.common_name}
          className="h-32 w-full rounded-md object-cover"
          loading="lazy"
        />
      ) : (
        <div className="flex h-32 items-center justify-center rounded-md bg-panel">
          <LeafPlaceholderIcon className="h-8 w-8 text-bark-500" />
        </div>
      )}

      <p className="mt-3 font-[var(--font-display)] text-lg font-semibold text-soil-900">
        {species.common_name}
      </p>
      <p className="text-sm italic text-bark-500">{species.scientific_name}</p>

      <dl className="mt-3 space-y-1 text-sm">
        <div className="flex justify-between gap-3">
          <dt className="text-bark-700">Water need</dt>
          <dd className="text-right text-soil-900">{fieldValue(species.water_requirement)}</dd>
        </div>
        <div className="flex justify-between gap-3">
          <dt className="text-bark-700">Drought tolerance</dt>
          <dd className="text-right text-soil-900">{fieldValue(species.drought_tolerance)}</dd>
        </div>
        <div className="flex justify-between gap-3">
          <dt className="text-bark-700">Growth rate</dt>
          <dd className="text-right text-soil-900">{fieldValue(species.growth_rate)}</dd>
        </div>
      </dl>

      <span className="mt-3 inline-block text-sm font-medium text-leaf-700">View details</span>
    </Link>
  );
}