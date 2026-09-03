import { NavLink } from "react-router-dom";

const LINKS = [
  { to: "/", label: "Home", end: true },
  { to: "/dashboard", label: "Dashboard" },
  { to: "/assistant", label: "AI Assistant" },
  { to: "/map", label: "Map Explorer" },
  { to: "/species", label: "Tree Species" },
  { to: "/sources", label: "Knowledge Sources" },
  { to: "/about", label: "About" },
];

export default function NavBar() {
  return (
    <header className="border-b border-bark-500/15 bg-parchment-50/95 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <NavLink to="/" className="flex items-baseline gap-2">
          <span className="font-[var(--font-display)] text-lg font-semibold text-soil-900">
            Tree Plantation
          </span>
          <span className="text-xs text-bark-500">Mandi Bahauddin</span>
        </NavLink>
        <nav className="flex flex-wrap gap-1">
          {LINKS.map(({ to, label, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                `rounded-md px-3 py-1.5 text-sm transition ${
                  isActive
                    ? "bg-leaf-700 text-parchment-50"
                    : "text-bark-700 hover:bg-leaf-100"
                }`
              }
            >
              {label}
            </NavLink>
          ))}
        </nav>
      </div>
    </header>
  );
}
