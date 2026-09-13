import { useEffect, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";

/**
 * Claude-style app sidebar.
 *
 * Fully self-contained (no icon library or extra deps — icons are inline
 * SVG below). Manages its own "collapsed" (desktop rail) and "mobile open"
 * state internally; the conversation list, active id, and all actions are
 * passed in as props.
 *
 * POSITIONING — read this before mounting: both the desktop rail and the
 * mobile drawer/top-bar are `fixed` to the true viewport, not flow-
 * positioned relative to wherever <Sidebar /> happens to be rendered in
 * the tree. This is deliberate: a flow-positioned sidebar silently
 * inherits any padding/max-width/centering on its parent (e.g. a page
 * layout's `px-4 py-6` content wrapper), which shows up as unwanted gaps
 * on the left/top/bottom and shifts the whole sidebar inward. Pinning it
 * to the viewport — and, for the mobile drawer specifically, rendering it
 * through a portal straight to `document.body` — makes it immune to that
 * regardless of where this component gets mounted.
 *
 * NAVBAR OFFSET: this app also has a global `NavBar` that renders above
 * `<main>` in normal document flow (see Layout.jsx), not fixed. A fixed
 * `top-0` here would sit at the true viewport top and paint over NavBar's
 * left edge, which is exactly the overlap bug this used to have. Instead,
 * every fixed element below reads `top-[var(--navbar-height,64px)]` —
 * NavBar publishes its real rendered height into that CSS variable (see
 * NavBar.jsx), so this sidebar always starts exactly where NavBar ends,
 * even if NavBar's height changes (nav wrapping, mobile dropdown, a future
 * logo change). The `64px` fallback only matters for the first paint
 * before NavBar's effect runs.
 *
 * Because of that, THE PAGE CONTENT NEXT TO THIS SIDEBAR MUST RESERVE
 * matching space itself:
 *   - Mobile (below md): add `pt-14` to your top-level content wrapper —
 *     that's this sidebar's own mobile top bar height (on top of whatever
 *     space NavBar already reserves via normal flow — no extra math needed
 *     there since NavBar isn't fixed).
 *   - Desktop (md and up): add `md:pl-16` when the sidebar is collapsed,
 *     or `md:pl-72` when expanded. If you want this to track automatically,
 *     lift the `collapsed` state up (see the `onCollapsedChange` prop) and
 *     apply the matching class based on it.
 *
 * Theming: only uses color tokens already confirmed elsewhere in this app
 * (bg-page, bg-card, soil-900/bark-700/bark-500 text, border-bark-500/15,
 * the amber/warning-subtle pair used for warnings, and translucent
 * bark-500/… tints for hover/active states).
 *
 * Usage:
 *   <Sidebar
 *     conversations={conversations}
 *     activeConversationId={activeId}
 *     onSelectConversation={(id) => ...}
 *     onNewChat={() => ...}
 *     onDeleteConversation={(id) => ...}
 *     onRenameConversation={(id, title) => ...}
 *     onCollapsedChange={(collapsed) => ...}   // optional, see above
 *     loading={loading}
 *     error={error}
 *   />
 */

const COLLAPSE_STORAGE_KEY = "sidebar:collapsed";

// Shared fallback for the first paint, before NavBar's ResizeObserver has
// run and set the real value. Keep in sync with NavBar's actual height —
// it only needs to be approximately right; it self-corrects immediately
// once NavBar mounts.
const NAVBAR_OFFSET = "var(--navbar-height,64px)";

export default function Sidebar({
  conversations = [],
  activeConversationId = null,
  onSelectConversation = () => {},
  onNewChat = () => {},
  onDeleteConversation = null,
  onRenameConversation = null,
  onCollapsedChange = null,
  loading = false,
  error = null,
  title = "AI Assistant",
  footer = null,
}) {
  const [collapsed, setCollapsed] = useState(() => {
    if (typeof window === "undefined") return false;
    return window.localStorage.getItem(COLLAPSE_STORAGE_KEY) === "1";
  });
  const [mobileOpen, setMobileOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [renamingId, setRenamingId] = useState(null);
  const [renameValue, setRenameValue] = useState("");
  const renameInputRef = useRef(null);

  useEffect(() => {
    window.localStorage.setItem(COLLAPSE_STORAGE_KEY, collapsed ? "1" : "0");
    onCollapsedChange?.(collapsed);
  }, [collapsed]); // eslint-disable-line react-hooks/exhaustive-deps

  // Mobile drawer niceties: don't let the page scroll behind it, and let
  // Escape close it like any other overlay.
  useEffect(() => {
    if (!mobileOpen) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const handleKey = (e) => {
      if (e.key === "Escape") setMobileOpen(false);
    };
    document.addEventListener("keydown", handleKey);
    return () => {
      document.body.style.overflow = previousOverflow;
      document.removeEventListener("keydown", handleKey);
    };
  }, [mobileOpen]);

  const handleSelect = (id) => {
    onSelectConversation(id);
    setMobileOpen(false);
  };

  const handleNewChat = () => {
    onNewChat();
    setMobileOpen(false);
  };

  const filtered = useMemo(() => {
    if (!query.trim()) return conversations;
    const q = query.trim().toLowerCase();
    return conversations.filter((c) => (c.title || "Untitled chat").toLowerCase().includes(q));
  }, [conversations, query]);

  const groups = useMemo(() => groupByRecency(filtered), [filtered]);

  const startRename = (c) => {
    setRenamingId(c.id);
    setRenameValue(c.title || "");
  };

  const commitRename = (id) => {
    const value = renameValue.trim();
    if (value && onRenameConversation) onRenameConversation(id, value);
    setRenamingId(null);
  };

  const handleDelete = (c) => {
    if (!onDeleteConversation) return;
    const label = c.title || "this chat";
    if (window.confirm(`Delete "${label}"? This can't be undone.`)) {
      onDeleteConversation(c.id);
    }
  };

  // Shared conversation-list body — used by both the desktop rail and the
  // mobile drawer so behavior/markup never drifts between the two.
  const listContent = (isCollapsedRail) => (
    <div className="flex-1 overflow-y-auto px-2 pb-3">
      {isCollapsedRail ? (
        <div className="mt-1 flex flex-col items-center gap-1">
          {conversations.slice(0, 8).map((c) => (
            <button
              key={c.id}
              type="button"
              onClick={() => handleSelect(c.id)}
              title={c.title || "Untitled chat"}
              className={[
                "flex h-9 w-9 items-center justify-center rounded-lg",
                c.id === activeConversationId
                  ? "bg-bark-500/15 text-soil-900"
                  : "text-bark-700 hover:bg-bark-500/10",
              ].join(" ")}
            >
              <IconMessage />
            </button>
          ))}
        </div>
      ) : loading ? (
        <SidebarSkeleton />
      ) : error ? (
        <div className="mt-4 rounded-lg border border-amber-500/40 bg-warning-subtle px-3 py-2.5">
          <p className="text-xs font-semibold uppercase tracking-wide text-amber-500">Couldn't load chats</p>
          <p className="mt-1 text-sm text-bark-700">{error.detail || "Check that the backend is running."}</p>
        </div>
      ) : conversations.length === 0 ? (
        <p className="mt-4 px-2 text-sm text-bark-500">No conversations yet.</p>
      ) : filtered.length === 0 ? (
        <p className="mt-4 px-2 text-sm text-bark-500">No chats match "{query}".</p>
      ) : (
        Object.entries(groups).map(([label, items]) =>
          items.length === 0 ? null : (
            <div key={label} className="mb-3">
              <p className="px-2 pb-1 pt-2 text-xs font-medium text-bark-500">{label}</p>
              <ul className="space-y-0.5">
                {items.map((c) => (
                  <li key={c.id} className="group flex items-center gap-0.5 rounded-lg">
                    {renamingId === c.id ? (
                      <input
                        ref={renameInputRef}
                        autoFocus
                        value={renameValue}
                        onChange={(e) => setRenameValue(e.target.value)}
                        onBlur={() => commitRename(c.id)}
                        onKeyDown={(e) => {
                          if (e.key === "Enter") {
                            e.preventDefault();
                            renameInputRef.current?.blur();
                          }
                          if (e.key === "Escape") setRenamingId(null);
                        }}
                        className="w-full rounded-lg border border-bark-500/30 bg-page px-2 py-1.5 text-sm text-soil-900 focus:outline-none"
                      />
                    ) : (
                      <>
                        <button
                          type="button"
                          onClick={() => handleSelect(c.id)}
                          className={[
                            "min-w-0 flex-1 truncate rounded-lg px-2 py-2 text-left text-sm",
                            c.id === activeConversationId
                              ? "bg-bark-500/15 text-soil-900"
                              : "text-bark-700 hover:bg-bark-500/10",
                          ].join(" ")}
                        >
                          {c.title || "Untitled chat"}
                        </button>

                        {onRenameConversation && (
                          <button
                            type="button"
                            onClick={() => startRename(c)}
                            aria-label="Rename chat"
                            className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md text-bark-500 opacity-100 hover:bg-bark-500/10 hover:text-soil-900 md:opacity-0 md:group-hover:opacity-100 md:group-focus-within:opacity-100"
                          >
                            <IconPencil />
                          </button>
                        )}
                        {onDeleteConversation && (
                          <button
                            type="button"
                            onClick={() => handleDelete(c)}
                            aria-label="Delete chat"
                            className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md text-bark-500 opacity-100 hover:bg-red-500/10 hover:text-red-600 md:opacity-0 md:group-hover:opacity-100 md:group-focus-within:opacity-100"
                          >
                            <IconTrash />
                          </button>
                        )}
                      </>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )
        )
      )}
    </div>
  );

  return (
    <>
      {/* Mobile top bar — fixed to the true viewport width, starting below
          NavBar (see NAVBAR_OFFSET) rather than at the very top, so it
          stacks under the global nav instead of painting over its corner.
          Page content needs `pt-14` on mobile to clear it (see the
          file-level comment above) — NavBar's own space is already
          reserved by normal document flow, so that padding only needs to
          account for this bar's own height. */}
      <div
        style={{ top: NAVBAR_OFFSET }}
        className="fixed inset-x-0 z-30 flex items-center gap-3 border-b border-bark-500/15 bg-card px-3 py-2.5 md:hidden"
      >
        <button
          type="button"
          onClick={() => setMobileOpen(true)}
          className="flex h-10 w-10 items-center justify-center rounded-lg text-bark-700 hover:bg-bark-500/10"
          aria-label="Open sidebar"
        >
          <IconMenu />
        </button>
        <span className="font-[var(--font-display)] text-sm font-semibold text-soil-900">{title}</span>
      </div>

      {/* Desktop rail — fixed to the true viewport left edge, starting
          below NavBar for the same reason as the mobile bar above. Page
          content needs matching `md:pl-16` / `md:pl-72` (see file-level
          comment). */}
      <aside
        style={{ top: NAVBAR_OFFSET }}
        className={[
          "fixed bottom-0 left-0 z-20 hidden flex-col border-r border-bark-500/15 bg-card transition-[width] duration-200 ease-in-out md:flex",
          collapsed ? "md:w-16" : "md:w-72",
        ].join(" ")}
      >
        <div className="flex items-center gap-2 px-3 pb-2 pt-3">
          {!collapsed && (
            <span className="flex-1 truncate font-[var(--font-display)] text-sm font-semibold text-soil-900">
              {title}
            </span>
          )}
          <button
            type="button"
            onClick={() => setCollapsed((v) => !v)}
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg text-bark-700 hover:bg-bark-500/10"
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
            title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {collapsed ? <IconPanelOpen /> : <IconPanelClose />}
          </button>
        </div>

        <div className="px-3 pb-3">
          <button
            type="button"
            onClick={handleNewChat}
            className={[
              "flex w-full items-center gap-2 rounded-xl border border-bark-500/15 bg-card text-sm font-medium text-soil-900 shadow-sm hover:bg-bark-500/10",
              collapsed ? "justify-center px-0 py-2.5" : "px-3 py-2.5",
            ].join(" ")}
            title="New chat"
          >
            <IconPlus />
            {!collapsed && <span>New chat</span>}
          </button>
        </div>

        {!collapsed && (
          <div className="px-3 pb-2">
            <div className="flex items-center gap-2 rounded-lg bg-bark-500/10 px-2.5 py-1">
              <IconSearch className="h-3.5 w-3.5 shrink-0 text-bark-500" />
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search chats"
                className="w-full bg-transparent py-0.5 text-sm text-soil-900 placeholder:text-bark-500 focus:outline-none"
                aria-label="Search chats"
              />
              {query && (
                <button
                  type="button"
                  onClick={() => setQuery("")}
                  className="shrink-0 rounded p-0.5 text-bark-500 hover:text-soil-900"
                  aria-label="Clear search"
                >
                  <IconX className="h-3 w-3" />
                </button>
              )}
            </div>
          </div>
        )}

        {listContent(collapsed)}

        {footer && !collapsed && <div className="border-t border-bark-500/15 p-3">{footer}</div>}
      </aside>

      {/* Mobile drawer + backdrop — portaled straight to document.body.
          This is what actually fixes both complaints at once: a portal
          guarantees the true viewport as its frame of reference (no
          inherited padding, ever), and rendering it always-mounted (rather
          than conditionally) is what makes the slide/fade transition
          below possible at all — the previous version snapped between
          `hidden` and `!flex`, which can't be animated. Both the backdrop
          and the drawer itself start below NavBar (NAVBAR_OFFSET) so
          NavBar stays visible/usable while this is open, rather than
          being dimmed or covered by the drawer's corner. */}
      {typeof document !== "undefined" &&
        createPortal(
          <div className="md:hidden">
            <div
              onClick={() => setMobileOpen(false)}
              aria-hidden="true"
              style={{ top: NAVBAR_OFFSET }}
              className={[
                "fixed inset-x-0 bottom-0 z-40 bg-black/40 transition-opacity duration-200 ease-in-out",
                mobileOpen ? "opacity-100" : "pointer-events-none opacity-0",
              ].join(" ")}
            />
            <aside
              style={{ top: NAVBAR_OFFSET }}
              className={[
                "fixed bottom-0 left-0 z-50 flex w-[85vw] max-w-72 flex-col border-r border-bark-500/15 bg-card shadow-xl transition-transform duration-300 ease-in-out",
                mobileOpen ? "translate-x-0" : "-translate-x-full",
              ].join(" ")}
              role="dialog"
              aria-modal="true"
              aria-label={title}
            >
              <div className="flex items-center gap-2 px-3 pb-2 pt-3">
                <span className="flex-1 truncate font-[var(--font-display)] text-sm font-semibold text-soil-900">
                  {title}
                </span>
                <button
                  type="button"
                  onClick={() => setMobileOpen(false)}
                  className="flex h-10 w-10 items-center justify-center rounded-lg text-bark-700 hover:bg-bark-500/10"
                  aria-label="Close sidebar"
                >
                  <IconX />
                </button>
              </div>

              <div className="px-3 pb-3">
                <button
                  type="button"
                  onClick={handleNewChat}
                  className="flex w-full items-center gap-2 rounded-xl border border-bark-500/15 bg-card px-3 py-2.5 text-sm font-medium text-soil-900 shadow-sm hover:bg-bark-500/10"
                >
                  <IconPlus />
                  <span>New chat</span>
                </button>
              </div>

              <div className="px-3 pb-2">
                <div className="flex items-center gap-2 rounded-lg bg-bark-500/10 px-2.5 py-1">
                  <IconSearch className="h-3.5 w-3.5 shrink-0 text-bark-500" />
                  <input
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Search chats"
                    className="w-full bg-transparent py-0.5 text-sm text-soil-900 placeholder:text-bark-500 focus:outline-none"
                    aria-label="Search chats"
                  />
                  {query && (
                    <button
                      type="button"
                      onClick={() => setQuery("")}
                      className="shrink-0 rounded p-0.5 text-bark-500 hover:text-soil-900"
                      aria-label="Clear search"
                    >
                      <IconX className="h-3 w-3" />
                    </button>
                  )}
                </div>
              </div>

              {listContent(false)}

              {footer && <div className="border-t border-bark-500/15 p-3">{footer}</div>}
            </aside>
          </div>,
          document.body,
        )}
    </>
  );
}

function groupByRecency(conversations) {
  const now = new Date();
  const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const startOfYesterday = new Date(startOfToday);
  startOfYesterday.setDate(startOfYesterday.getDate() - 1);
  const startOfWeek = new Date(startOfToday);
  startOfWeek.setDate(startOfWeek.getDate() - 7);
  const startOfMonth = new Date(startOfToday);
  startOfMonth.setDate(startOfMonth.getDate() - 30);

  const groups = {
    Today: [],
    Yesterday: [],
    "Previous 7 days": [],
    "Previous 30 days": [],
    Older: [],
  };

  const sorted = [...conversations].sort(
    (a, b) => new Date(b.updatedAt || 0) - new Date(a.updatedAt || 0)
  );

  for (const c of sorted) {
    const d = c.updatedAt ? new Date(c.updatedAt) : null;
    if (!d || Number.isNaN(d.getTime())) groups.Older.push(c);
    else if (d >= startOfToday) groups.Today.push(c);
    else if (d >= startOfYesterday) groups.Yesterday.push(c);
    else if (d >= startOfWeek) groups["Previous 7 days"].push(c);
    else if (d >= startOfMonth) groups["Previous 30 days"].push(c);
    else groups.Older.push(c);
  }
  return groups;
}

function SidebarSkeleton() {
  return (
    <div className="mt-2 space-y-1.5 px-2">
      {Array.from({ length: 6 }).map((_, i) => (
        <div key={i} className="h-7 animate-pulse rounded-lg bg-bark-500/10" />
      ))}
    </div>
  );
}

/* --- Inline icons (no external icon library required) --- */

function IconMenu(props) {
  return (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.6" className="h-5 w-5" {...props}>
      <path d="M3 5.5h14M3 10h14M3 14.5h14" strokeLinecap="round" />
    </svg>
  );
}

function IconPanelClose(props) {
  return (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.6" className="h-5 w-5" {...props}>
      <rect x="2.5" y="3.5" width="15" height="13" rx="2.5" />
      <path d="M8 3.5v13" />
      <path d="M6 8.5l-1.8 1.5L6 11.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function IconPanelOpen(props) {
  return (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.6" className="h-5 w-5" {...props}>
      <rect x="2.5" y="3.5" width="15" height="13" rx="2.5" />
      <path d="M8 3.5v13" />
      <path d="M5 8.5l1.8 1.5L5 11.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function IconPlus(props) {
  return (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.8" className="h-4 w-4" {...props}>
      <path d="M10 4v12M4 10h12" strokeLinecap="round" />
    </svg>
  );
}

function IconSearch(props) {
  return (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.6" className="h-4 w-4" {...props}>
      <circle cx="8.5" cy="8.5" r="5.5" />
      <path d="M16 16l-3.5-3.5" strokeLinecap="round" />
    </svg>
  );
}

function IconX(props) {
  return (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.8" className="h-5 w-5" {...props}>
      <path d="M5 5l10 10M15 5L5 15" strokeLinecap="round" />
    </svg>
  );
}

function IconMessage(props) {
  return (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.6" className="h-4 w-4" {...props}>
      <path d="M3 4.5h14v9H8.5L5 16.5v-3H3v-9z" strokeLinejoin="round" />
    </svg>
  );
}

function IconPencil(props) {
  return (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.6" className="h-4 w-4" {...props}>
      <path d="M12.9 3.9l3.2 3.2-9 9-3.6.4.4-3.6 9-9z" strokeLinejoin="round" />
    </svg>
  );
}

function IconTrash(props) {
  return (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.6" className="h-4 w-4" {...props}>
      <path d="M4 6h12M8 6V4.5h4V6m-7 0l.7 9.3a1 1 0 001 .9h6.6a1 1 0 001-.9L15 6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}