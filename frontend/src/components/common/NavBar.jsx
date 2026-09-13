import { useEffect, useRef, useState } from "react";
import { NavLink } from "react-router-dom";
import logoMark from "../../assets/logo-mark.png";
import ThemeToggle from "./ThemeToggle";

const LINKS = [
  { to: "/", label: "Home", end: true },
  { to: "/dashboard", label: "Dashboard" },
  { to: "/assistant", label: "AI Assistant" },
  { to: "/map", label: "Map Explorer" },
  { to: "/species", label: "Tree Species" },
  { to: "/sources", label: "Knowledge Sources" },
  { to: "/about", label: "About" },
];

function NavLinks({ onNavigate, className = "" }) {
  return (
    <nav className={className}>
      {LINKS.map(({ to, label, end }) => (
        <NavLink
          key={to}
          to={to}
          end={end}
          onClick={onNavigate}
          className={({ isActive }) =>
            `rounded-md px-3 py-1.5 text-sm transition ${
              isActive ? "bg-white/15 text-white" : "text-brand-100 hover:bg-white/10"
            }`
          }
        >
          {label}
        </NavLink>
      ))}
    </nav>
  );
}

export default function NavBar() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const headerRef = useRef(null);

  // Publish our real rendered height as a CSS variable on the root element.
  // Anything elsewhere in the app that's fixed-positioned relative to the
  // true viewport (Sidebar's rail/drawer, most notably) reads this instead
  // of a guessed pixel value — so it stays correct even when this header's
  // height changes (nav links wrapping at odd widths, the mobile dropdown
  // opening, a future logo/copy change, etc.) instead of silently drifting
  // out of sync with a hardcoded offset.
  useEffect(() => {
    const el = headerRef.current;
    if (!el) return undefined;

    const publishHeight = () => {
      document.documentElement.style.setProperty("--navbar-height", `${el.offsetHeight}px`);
    };

    publishHeight();
    const observer = new ResizeObserver(publishHeight);
    observer.observe(el);
    return () => observer.disconnect();
  }, [mobileOpen]);

  return (
    // Brand green stays constant across light/dark mode on purpose — it's
    // fixed identity color (sampled from the logo), not a themeable
    // surface, so the site keeps a consistent visual anchor at the top
    // regardless of which mode the content area is in.
    <header ref={headerRef} className="sticky top-0 z-20 bg-brand-900">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3 sm:px-6">
        <NavLink to="/" className="flex items-center gap-2.5" onClick={() => setMobileOpen(false)}>
          <img src={logoMark} alt="" className="h-9 w-9 object-contain" />
          <span className="font-[var(--font-display)] text-lg font-semibold text-white">
            Tree Plantation
          </span>
        </NavLink>

        <NavLinks className="hidden flex-wrap gap-1 md:flex" />

        <div className="flex items-center gap-1">
          <ThemeToggle className="hidden md:flex" />
          <button
            type="button"
            onClick={() => setMobileOpen((v) => !v)}
            aria-label={mobileOpen ? "Close menu" : "Open menu"}
            aria-expanded={mobileOpen}
            className="flex h-9 w-9 items-center justify-center rounded-md text-white transition hover:bg-white/10 md:hidden"
          >
            {mobileOpen ? (
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" className="h-5 w-5">
                <path strokeLinecap="round" d="M6 6l12 12M18 6L6 18" />
              </svg>
            ) : (
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" className="h-5 w-5">
                <path strokeLinecap="round" d="M4 7h16M4 12h16M4 17h16" />
              </svg>
            )}
          </button>
        </div>
      </div>

      {mobileOpen && (
        <div className="border-t border-white/10 px-4 pb-4 md:hidden">
          <NavLinks onNavigate={() => setMobileOpen(false)} className="flex flex-col gap-1 pt-2" />
          <div className="mt-2 flex items-center justify-between border-t border-white/10 pt-3">
            <span className="text-sm text-brand-100">Theme</span>
            <ThemeToggle />
          </div>
        </div>
      )}
    </header>
  );
}