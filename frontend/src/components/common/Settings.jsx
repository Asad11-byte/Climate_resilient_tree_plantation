
import { useEffect, useRef, useState } from "react";
import { Settings, Sun, Moon, LogOut } from "lucide-react";
import { useTheme } from "../../hooks/useTheme";
import { useAuth } from "../../context/AuthContext";

export default function ThemeToggle({ className = "" }) {
  const { theme, toggleTheme } = useTheme();
  const { signOut } = useAuth();

  const [open, setOpen] = useState(false);
  const menuRef = useRef(null);

  const isDark = theme === "dark";

  useEffect(() => {
    const handleOutsideClick = (event) => {
      if (!menuRef.current?.contains(event.target)) {
        setOpen(false);
      }
    };

    const handleEscape = (event) => {
      if (event.key === "Escape") {
        setOpen(false);
      }
    };

    document.addEventListener("mousedown", handleOutsideClick);
    document.addEventListener("keydown", handleEscape);

    return () => {
      document.removeEventListener("mousedown", handleOutsideClick);
      document.removeEventListener("keydown", handleEscape);
    };
  }, []);

  const handleSignOut = async () => {
    try {
      setOpen(false);
      await signOut();
    } catch (error) {
      console.error("Sign out failed:", error);
    }
  };

  return (
    <div ref={menuRef} className="relative">
      {/* Settings button */}
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        aria-label="Settings"
        aria-expanded={open}
        title="Settings"
        className={`flex h-9 w-9 items-center justify-center rounded-full text-brand-100 transition hover:bg-white/10 ${className}`}
      >
        <Settings
          size={19}
          strokeWidth={2}
          className="shrink-0"
        />
      </button>

      {/* Settings menu */}
      {open && (
        <div className="absolute right-0 top-11 z-[1000] w-52 overflow-hidden rounded-xl border border-bark-500/15 bg-card p-1.5 shadow-xl">
          <div className="px-3 py-2">
            <p className="text-xs font-semibold text-soil-900">
              Settings
            </p>
          </div>

          {/* Theme */}
          <button
            type="button"
            onClick={toggleTheme}
            className="flex w-full items-center justify-between rounded-lg px-3 py-2.5 text-sm text-soil-900 transition hover:bg-bark-500/10"
          >
            <span className="flex items-center gap-3">
              {isDark ? (
                <Sun
                  size={17}
                  strokeWidth={2}
                  className="text-bark-700"
                />
              ) : (
                <Moon
                  size={17}
                  strokeWidth={2}
                  className="text-bark-700"
                />
              )}

              <span>Theme</span>
            </span>

            <span className="text-xs text-bark-500">
              {isDark ? "Dark" : "Light"}
            </span>
          </button>

          <div className="my-1 border-t border-bark-500/10" />

          {/* Sign out */}
          <button
            type="button"
            onClick={handleSignOut}
            className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-danger transition hover:bg-danger-subtle"
          >
            <LogOut
              size={17}
              strokeWidth={2}
            />

            <span>Sign out</span>
          </button>
        </div>
      )}
    </div>
  );
}
