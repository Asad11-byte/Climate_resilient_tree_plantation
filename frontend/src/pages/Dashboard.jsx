import { Link } from "react-router-dom";
import { useHealth } from "../hooks/useHealth";
import HealthStrip from "../components/common/HealthStrip";

const QUICK_LINKS = [
  { to: "/assistant", label: "AI Assistant", description: "Ask an evidence-grounded question about plantation." },
  { to: "/map", label: "Map Explorer", description: "Inspect the environmental data behind a location." },
  { to: "/species", label: "Tree Species", description: "Browse the species profiles in the knowledge base." },
  { to: "/sources", label: "Knowledge Sources", description: "See what documents ground a given topic." },
];

export default function Dashboard() {
  const { data, loading, error } = useHealth();

  return (
    <div>
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="font-[var(--font-display)] text-2xl font-semibold text-soil-900">Dashboard</h1>
          <p className="mt-1 max-w-xl text-sm text-bark-700">
            An overview of the recommendation system for Mandi Bahauddin — jump into any tool below.
          </p>
        </div>
        <div className="rounded-lg border border-bark-500/15 bg-card/50 px-4 py-3">
          <HealthStrip loading={loading} error={error} data={data} />
        </div>
      </div>

      <div className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-2">
        {QUICK_LINKS.map(({ to, label, description }) => (
          <Link
            key={to}
            to={to}
            className="rounded-lg border border-bark-500/15 bg-card/50 p-4 transition hover:border-leaf-600/40 hover:bg-card/80"
          >
            <p className="font-[var(--font-display)] text-lg font-semibold text-soil-900">{label}</p>
            <p className="mt-1 text-sm text-bark-700">{description}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}
