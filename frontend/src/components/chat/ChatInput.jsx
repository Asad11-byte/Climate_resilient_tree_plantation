import { useRef, useState } from "react";
import { Link } from "react-router-dom";

const MAX_TEXTAREA_HEIGHT_PX = 160;

function PinIcon({ className = "" }) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" className={className} aria-hidden="true">
      <path d="M12 2a7 7 0 0 0-7 7c0 5.25 7 13 7 13s7-7.75 7-13a7 7 0 0 0-7-7Zm0 9.5A2.5 2.5 0 1 1 12 6.5a2.5 2.5 0 0 1 0 5Z" />
    </svg>
  );
}

function PinOffIcon({ className = "" }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      className={className}
      aria-hidden="true"
    >
      <path d="M12 21s7-5.4 7-12a7 7 0 0 0-11.5-5.4" />
      <path d="M5.4 7.4A7 7 0 0 0 5 9c0 6.6 7 12 7 12" />
      <path d="M3 3l18 18" />
    </svg>
  );
}

export default function ChatInput({ onSend, disabled, locationLabel, onClearLocation }) {
  const [value, setValue] = useState("");
  const textareaRef = useRef(null);

  const resize = (el) => {
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, MAX_TEXTAREA_HEIGHT_PX)}px`;
  };

  const handleChange = (e) => {
    setValue(e.target.value);
    resize(e.target);
  };

  const submit = () => {
    if (!value.trim() || disabled) return;
    onSend(value);
    setValue("");
    if (textareaRef.current) textareaRef.current.style.height = "auto";
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    submit();
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-2">
      {/* This row now renders in BOTH states rather than only when a
          location is attached. Previously the absence of a location was
          communicated by the absence of UI, which reads as "nothing to
          know here" instead of "this answer won't be location-specific" —
          and it also made the input area shift vertically the moment a
          location got attached. */}
      <div className="flex items-center gap-2 text-xs text-bark-700">
        {locationLabel ? (
          <>
            <span className="inline-flex items-center gap-1 rounded-full bg-leaf-100 px-2.5 py-1 text-leaf-700">
              <PinIcon className="h-3 w-3" />
              {locationLabel}
            </span>
            <button type="button" onClick={onClearLocation} className="underline hover:text-soil-900">
              Remove
            </button>
          </>
        ) : (
          <>
            <span className="inline-flex items-center gap-1 rounded-full bg-bark-500/10 px-2.5 py-1 text-bark-700">
              <PinOffIcon className="h-3 w-3" />
              No location selected
            </span>
            <Link
              to="/map"
              className="underline decoration-leaf-600/40 underline-offset-2 transition hover:text-leaf-700 hover:decoration-leaf-600"
            >
              Pick one on the map
            </Link>
          </>
        )}
      </div>

      <div className="flex items-end gap-2 rounded-3xl border border-bark-500/20 bg-card px-4 py-2.5 shadow-md transition focus-within:border-leaf-600 focus-within:ring-1 focus-within:ring-leaf-600">
        <textarea
          ref={textareaRef}
          value={value}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          placeholder="Ask about a species, soil, water, or plantation approach…"
          disabled={disabled}
          rows={1}
          className="focus-ring-none flex-1 resize-none bg-transparent py-1.5 text-sm text-soil-900 placeholder:text-bark-500/70 focus:outline-none disabled:opacity-60"
        />
        <button
          type="submit"
          disabled={disabled || !value.trim()}
          aria-label="Send message"
          className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-leaf-700 text-parchment-50 transition hover:bg-leaf-600 disabled:cursor-not-allowed disabled:opacity-40"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4">
            <path d="M4 12h15M13 5l7 7-7 7" />
          </svg>
        </button>
      </div>
    </form>
  );
}