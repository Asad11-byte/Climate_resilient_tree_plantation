import { Link } from "react-router-dom";
import logoMark from "../assets/logo-mark.png";

const STEPS = [
  {
    n: 1,
    title: "Retrieve",
    body: "Your question is matched against ingested soil, climate, and species documents for Mandi Bahauddin.",
  },
  {
    n: 2,
    title: "Rerank",
    body: "The matched passages are re-ordered by actual relevance, so weak matches don't crowd out strong ones.",
  },
  {
    n: 3,
    title: "Answer, with sources",
    body: "A recommendation is written only from what was retrieved, with the documents behind it cited alongside it.",
  },
];

export default function Landing() {
  return (
    <div>
      {/* Full-bleed brand hero — the logo on its own native dark-green
          ground, the same treatment as the mark itself, rather than a
          generic light card with a stock illustration. */}
      <section className="-mx-4 rounded-none bg-brand-900 px-6 py-12 sm:-mx-6 sm:rounded-2xl sm:px-10 sm:py-16 lg:px-14">
        <div className="grid grid-cols-1 items-center gap-10 lg:grid-cols-[1.1fr_0.9fr]">
          <div>
            <h1 className="font-[var(--font-display)] text-4xl font-semibold leading-tight text-white sm:text-5xl">
              Know what will actually grow here.
            </h1>
            <p className="mt-5 max-w-lg text-lg text-brand-100">
              A tree plantation recommendation system for Mandi Bahauddin, Punjab, grounded in soil data, climate
              records, and species evidence — and honest when that evidence runs out.
            </p>
            <div className="mt-7 flex flex-wrap gap-3">
              <Link
                to="/assistant"
                className="rounded-lg bg-brand-400 px-5 py-2.5 text-sm font-medium text-brand-900 transition hover:bg-white"
              >
                Ask the Assistant
              </Link>
              <Link
                to="/map"
                className="rounded-lg border border-white/25 px-5 py-2.5 text-sm font-medium text-white transition hover:border-white/50"
              >
                Explore the Map
              </Link>
            </div>
          </div>

          <div className="flex justify-center lg:justify-end">
            <img
              src={logoMark}
              alt="Tree Plantation — Mandi Bahauddin"
              className="h-48 w-48 object-contain sm:h-64 sm:w-64"
            />
          </div>
        </div>
      </section>

      <section className="py-10">
        <div className="rounded-xl border border-bark-500/15 bg-card/60 p-5">
          <p className="text-xs font-medium text-bark-500">Example</p>
          <p className="mt-2 text-sm text-soil-900">"What tree species tolerate waterlogging near the Chenab?"</p>
          <div className="mt-3 rounded-lg border-2 border-dashed border-amber-500/50 bg-amber-500/5 px-3 py-2.5">
            <p className="text-xs font-semibold uppercase tracking-wide text-amber-500">No evidence found</p>
            <p className="mt-1 text-sm text-soil-900">
              The knowledge base doesn't currently have documented flood-tolerant species for that location — so
              the system says that, instead of guessing.
            </p>
          </div>
        </div>
      </section>

      <section className="border-t border-bark-500/15 py-10">
        <h2 className="font-[var(--font-display)] text-xl font-semibold text-soil-900">How an answer gets made</h2>
        <div className="mt-6 grid grid-cols-1 gap-6 sm:grid-cols-3">
          {STEPS.map((step) => (
            <div key={step.n}>
              <span className="font-[var(--font-display)] text-2xl text-leaf-600">{step.n}</span>
              <p className="mt-2 font-medium text-soil-900">{step.title}</p>
              <p className="mt-1 text-sm text-bark-700">{step.body}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="border-t border-bark-500/15 py-10">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h2 className="font-[var(--font-display)] text-xl font-semibold text-soil-900">
              See the system's status and tools
            </h2>
            <p className="mt-1 text-sm text-bark-700">Live service status, species profiles, and source search.</p>
          </div>
          <Link
            to="/dashboard"
            className="rounded-lg border border-bark-500/25 px-5 py-2.5 text-sm font-medium text-soil-900 transition hover:border-soil-800/40"
          >
            Open Dashboard
          </Link>
        </div>
      </section>
    </div>
  );
}
