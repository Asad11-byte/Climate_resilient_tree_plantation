import { useCallback, useState } from "react";

/**
 * Holds the currently selected map coordinates. Lifted to App level so the
 * Map Explorer's "Ask about this location" button can push a location into
 * the AI Assistant page.
 */
export function useMapSelection() {
  const [selection, setSelection] = useState(null); // { latitude, longitude } | null

  const select = useCallback((latitude, longitude) => {
    setSelection({ latitude, longitude });
  }, []);

  const clear = useCallback(() => setSelection(null), []);

  return { selection, select, clear };
}
