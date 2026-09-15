import { Link } from "react-router-dom";

/**
 * Renders species the backend actually confirmed are named in the answer
 * (matched server-side against real tree_species rows — see
 * app/services/species_linking/matcher.py). Never guesses at species names
 * client-side.
 *
 * A mention here means "this species is named in the answer," not "this is
 * the recommendation" — a species could be mentioned in an "avoid this"
 * context and still show up as a link. The chip is "learn more about this
 * species," the actual answer text carries the real meaning.
 */
export default function SpeciesMentionChips({ species }) {
  if (!species?.length) return null;

  return (
    <div className="mt-3 flex flex-wrap gap-1.5">
      {species.map((s) => (
        <Link
          key={s.id}
          to={`/species/${s.id}`}
          className="inline-flex items-center gap-1 rounded-full border border-leaf-700/50 bg-leaf-700/20 px-2.5 py-1 text-xs font-semibold text-leaf-700 shadow-sm transition hover:bg-leaf-700/30 dark:border-emerald-400/60 dark:bg-emerald-400/20 dark:text-emerald-300 dark:hover:bg-emerald-400/30"
        >
          <svg viewBox="0 0 24 24" fill="none" className="h-3 w-3 shrink-0">
            <path
              d="M12 3c-4 3-7 6.5-7 10.5A7 7 0 0 0 12 21a7 7 0 0 0 7-7.5C19 9.5 16 6 12 3Z"
              fill="currentColor"
              fillOpacity="0.9"
            />
          </svg>
          {s.common_name}
        </Link>
      ))}
    </div>
  );
}