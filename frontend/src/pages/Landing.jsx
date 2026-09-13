import { Link } from "react-router-dom";

const STEPS = [
  {
    n: "01",
    title: "Choose a location",
    body: "Select a point inside Mandi Bahauddin to bring local conditions into the conversation.",
  },
  {
    n: "02",
    title: "Understand the conditions",
    body: "Review the available soil, climate, and land-cover information for that point.",
  },
  {
    n: "03",
    title: "Get an evidence-backed answer",
    body: "Ask about suitable trees and inspect the sources behind every recommendation.",
  },
];

function PinIcon({ className = "" }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className={className} aria-hidden="true">
      <path d="M12 21s7-5.4 7-12a7 7 0 1 0-14 0c0 6.6 7 12 7 12Z" />
      <circle cx="12" cy="9" r="2.25" />
    </svg>
  );
}

function LeafIcon({ className = "" }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className={className} aria-hidden="true">
      <path d="M20 4C11 4 5 8.2 5 15c0 2 .9 3.8 2.4 5C15.3 19.7 20 13.7 20 4Z" />
      <path d="M4 20c3.1-4.3 6.8-7.1 11.2-8.6" strokeLinecap="round" />
    </svg>
  );
}

function SourceIcon({ className = "" }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className={className} aria-hidden="true">
      <path d="M7 3.75h7L18 7.6v12.65H7z" strokeLinejoin="round" />
      <path d="M14 3.75V8h4M10 12h5M10 15.5h5" strokeLinecap="round" />
    </svg>
  );
}

function WorkflowPreview() {
  return (
    <div className="relative overflow-hidden rounded-2xl border border-white/15 bg-white/10 p-5 shadow-lg backdrop-blur-sm sm:p-6">
      <div className="absolute -right-16 -top-20 h-48 w-48 rounded-full bg-brand-400/15 blur-2xl" aria-hidden="true" />
      <div className="relative flex items-center justify-between gap-3">
        <p className="text-sm font-medium text-brand-100">A clearer way to decide</p>
        <span className="rounded-full border border-brand-400/35 bg-brand-400/10 px-2.5 py-1 text-xs font-medium text-brand-100">Mandi Bahauddin</span>
      </div>

      <div className="relative mt-6 grid grid-cols-[auto_1fr] gap-x-3 gap-y-4">
        <div className="row-span-3 flex flex-col items-center">
          <span className="flex h-9 w-9 items-center justify-center rounded-full bg-brand-400 text-brand-900"><PinIcon className="h-5 w-5" /></span>
          <span className="my-1 h-7 w-px bg-white/20" />
          <span className="flex h-9 w-9 items-center justify-center rounded-full border border-white/20 bg-white/10 text-brand-100"><LeafIcon className="h-5 w-5" /></span>
          <span className="my-1 h-7 w-px bg-white/20" />
          <span className="flex h-9 w-9 items-center justify-center rounded-full border border-white/20 bg-white/10 text-brand-100"><SourceIcon className="h-5 w-5" /></span>
        </div>
        <div><p className="text-xs font-medium uppercase tracking-wide text-brand-100">Location selected</p><p className="mt-1 text-sm text-white">Environmental context is added to your question.</p></div>
        <div><p className="text-xs font-medium uppercase tracking-wide text-brand-100">Conditions reviewed</p><p className="mt-1 text-sm text-white">Soil, rainfall, temperature, and land-cover data stay visible.</p></div>
        <div><p className="text-xs font-medium uppercase tracking-wide text-brand-100">Evidence shown</p><p className="mt-1 text-sm text-white">Recommendations link back to the supporting sources.</p></div>
      </div>
    </div>
  );
}

export default function Landing() {
  return (
    <div>
      <section className="-mx-4 rounded-none bg-brand-900 px-6 py-12 sm:-mx-6 sm:rounded-2xl sm:px-10 sm:py-16 lg:px-14 lg:py-20">
        <div className="grid items-center gap-10 lg:grid-cols-[1.05fr_0.95fr] lg:gap-14">
          <div>
            <p className="inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/10 px-3 py-1.5 text-xs font-medium text-brand-100"><span className="h-1.5 w-1.5 rounded-full bg-brand-400" aria-hidden="true" />Location-aware tree planning</p>
            <h1 className="mt-5 max-w-xl font-[var(--font-display)] text-4xl font-semibold leading-[1.08] text-white sm:text-5xl lg:text-6xl">Make tree-planting decisions with local evidence.</h1>
            <p className="mt-5 max-w-xl text-base leading-7 text-brand-100 sm:text-lg">Explore conditions in Mandi Bahauddin, compare tree species, and ask questions grounded in soil, climate, and source documents—not assumptions.</p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link to="/map" className="inline-flex items-center gap-2 rounded-lg bg-brand-400 px-5 py-3 text-sm font-semibold text-brand-900 transition hover:bg-white focus-visible:outline-white">Start with a location <span aria-hidden="true">→</span></Link>
              <Link to="/assistant" className="rounded-lg border border-white/25 px-5 py-3 text-sm font-medium text-white transition hover:border-white hover:bg-white/10 focus-visible:outline-white">Ask the assistant</Link>
            </div>
            <p className="mt-4 text-xs text-brand-100">Recommendations are limited to the evidence currently available.</p>
          </div>
          <WorkflowPreview />
        </div>
      </section>

      <section className="py-10 sm:py-14">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div><p className="text-xs font-semibold uppercase tracking-[0.14em] text-leaf-700">How it works</p><h2 className="mt-2 font-[var(--font-display)] text-2xl font-semibold text-soil-900 sm:text-3xl">From map point to planting decision</h2></div>
          <Link to="/map" className="text-sm font-medium text-leaf-700 underline decoration-leaf-600/40 underline-offset-4 hover:decoration-leaf-600">Explore the map</Link>
        </div>
        <ol className="mt-7 grid grid-cols-1 gap-4 md:grid-cols-3">
          {STEPS.map((step) => (
            <li key={step.n} className="rounded-xl border border-bark-500/15 bg-card p-5 shadow-sm"><span className="font-[var(--font-display)] text-lg font-semibold text-leaf-700">{step.n}</span><h3 className="mt-5 font-[var(--font-display)] text-xl font-semibold text-soil-900">{step.title}</h3><p className="mt-2 text-sm leading-6 text-bark-700">{step.body}</p></li>
          ))}
        </ol>
      </section>

      <section className="border-y border-bark-500/15 py-10 sm:py-12">
        <div className="grid gap-6 rounded-2xl border border-brand-800 bg-brand-900 p-6 shadow-md sm:p-8 md:grid-cols-[auto_1fr] md:items-start">
          <span className="flex h-11 w-11 items-center justify-center rounded-full bg-white/10 text-brand-400"><SourceIcon className="h-5 w-5" /></span>
          <div><p className="text-xs font-semibold uppercase tracking-[0.14em] text-brand-100">Evidence before confidence</p><h2 className="mt-2 font-[var(--font-display)] text-2xl font-semibold text-white">The system tells you when it does not know.</h2><p className="mt-3 max-w-2xl text-sm leading-6 text-brand-100">If the knowledge base cannot support an answer for a location or species, you will see that gap clearly instead of receiving a plausible-sounding guess.</p></div>
        </div>
      </section>

      <section className="flex flex-wrap items-center justify-between gap-5 py-10 sm:py-14">
        <div><p className="text-xs font-semibold uppercase tracking-[0.14em] text-leaf-700">Explore further</p><h2 className="mt-2 font-[var(--font-display)] text-2xl font-semibold text-soil-900">Browse species and inspect the evidence base.</h2><p className="mt-2 text-sm text-bark-700">Compare recorded species profiles or search the documents behind a topic.</p></div>
        <div className="flex flex-wrap gap-3"><Link to="/species" className="rounded-lg border border-bark-500/25 bg-card px-4 py-2.5 text-sm font-medium text-soil-900 transition hover:border-leaf-600/50">Browse species</Link><Link to="/sources" className="rounded-lg border border-bark-500/25 bg-card px-4 py-2.5 text-sm font-medium text-soil-900 transition hover:border-leaf-600/50">Search sources</Link></div>
      </section>
    </div>
  );
}
