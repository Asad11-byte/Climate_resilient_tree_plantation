import { useEffect, useMemo, useRef, useState } from "react";

/**
 * Claude-style app sidebar.
 *
 * Fully self-contained (no icon library or extra deps — icons are inline
 * SVG below). Manages its own "collapsed" (desktop rail) and "mobile open"
 * state internally; the conversation list, active id, and all actions are
 * passed in as props.
 *
 * Theming: only uses color tokens already confirmed elsewhere in this app
 * (bg-page, bg-card, soil-900/bark-700/bark-500 text, border-bark-500/15,
 * the amber/warning-subtle pair used for warnings, and translucent
 * bark-500/… tints for hover/active states). Translucent tints are used
 * deliberately for interactive states instead of solid shades like
 * soil-100/200, since those aren't confirmed to have dark-mode equivalents
 * — a tint over whatever the surface color already is reads correctly in
 * both themes without needing to know the dark palette.
 *
 * Usage:
 *   <Sidebar
 *     conversations={conversations}
 *     activeConversationId={activeId}
 *     onSelectConversation={(id) => ...}
 *     onNewChat={() => ...}
 *     onDeleteConversation={(id) => ...}
 *     onRenameConversation={(id, title) => ...}
 *     loading={loading}
 *     error={error}
 *   />
 */

const COLLAPSE_STORAGE_KEY = "sidebar:collapsed";

export default function Sidebar({
  conversations = [],
  activeConversationId = null,
  onSelectConversation = () => {},
  onNewChat = () => {},
  onDeleteConversation = null,
  onRenameConversation = null,
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
  }, [collapsed]);

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

  return (
    <>
      {/* Mobile top bar: only shown < md */}
      <div className="flex items-center gap-3 border-b border-bark-500/15 bg-card px-3 py-2.5 md:hidden">
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

      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/40 md:hidden"
          onClick={() => setMobileOpen(false)}
          aria-hidden="true"
        />
      )}

      <aside
        className={[
          "z-50 flex h-full flex-col border-r border-bark-500/15 bg-card transition-[width] duration-200 ease-in-out",
          "hidden md:flex",
          collapsed ? "md:w-16" : "md:w-72",
          mobileOpen ? "!fixed inset-y-0 left-0 !flex w-[85vw] max-w-72 shadow-xl" : "",
        ].join(" ")}
      >
        {/* Header row */}
        <div className="flex items-center gap-2 px-3 pb-2 pt-3">
          {!collapsed && (
            <span className="flex-1 truncate font-[var(--font-display)] text-sm font-semibold text-soil-900">
              {title}
            </span>
          )}
          <button
            type="button"
            onClick={() => setCollapsed((v) => !v)}
            className="hidden h-9 w-9 items-center justify-center rounded-lg text-bark-700 hover:bg-bark-500/10 md:inline-flex"
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
            title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {collapsed ? <IconPanelOpen /> : <IconPanelClose />}
          </button>
          <button
            type="button"
            onClick={() => setMobileOpen(false)}
            className="flex h-10 w-10 items-center justify-center rounded-lg text-bark-700 hover:bg-bark-500/10 md:hidden"
            aria-label="Close sidebar"
          >
            <IconX />
          </button>
        </div>

        {/* New chat */}
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

        {/* Search — compact pill, no border/height bloat */}
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

        {/* Conversation list */}
        <div className="flex-1 overflow-y-auto px-2 pb-3">
          {collapsed ? (
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
              <p className="mt-1 text-sm text-bark-700">
                {error.detail || "Check that the backend is running."}
              </p>
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

                            {/* Always visible on mobile (no hover on touch);
                                hover/focus-reveal on desktop so the list
                                stays clean until you need it. */}
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

        {footer && <div className="border-t border-bark-500/15 p-3">{footer}</div>}
      </aside>
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