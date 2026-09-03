import { useState } from "react";

export default function ChatInput({ onSend, disabled, locationLabel, onClearLocation }) {
  const [value, setValue] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!value.trim() || disabled) return;
    onSend(value);
    setValue("");
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-2">
      {locationLabel && (
        <div className="flex items-center gap-2 text-xs text-bark-700">
          <span className="rounded-full bg-leaf-100 px-2.5 py-1">📍 {locationLabel}</span>
          <button type="button" onClick={onClearLocation} className="underline hover:text-soil-900">
            Remove
          </button>
        </div>
      )}
      <div className="flex gap-2">
        <input
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="Ask about a species, soil, water, or plantation approach…"
          disabled={disabled}
          className="flex-1 rounded-lg border border-bark-500/25 bg-white px-4 py-2.5 text-sm text-soil-900 placeholder:text-bark-500/70 focus:border-leaf-600 focus:outline-none focus:ring-1 focus:ring-leaf-600 disabled:opacity-60"
        />
        <button
          type="submit"
          disabled={disabled || !value.trim()}
          className="rounded-lg bg-leaf-700 px-5 py-2.5 text-sm font-medium text-parchment-50 transition hover:bg-leaf-600 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Ask
        </button>
      </div>
    </form>
  );
}
