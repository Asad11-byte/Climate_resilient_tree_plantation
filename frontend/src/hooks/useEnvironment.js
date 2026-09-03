import { useCallback, useState } from "react";
import { getEnvironment } from "../api/environment";
import { normalizeApiError } from "../api/client";

/**
 * Fetches the environmental record for a clicked map point. Not
 * auto-triggered on mount — call `fetchAt(lat, lon)` when the user picks a
 * location.
 */
export function useEnvironment() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchAt = useCallback(async (latitude, longitude) => {
    setLoading(true);
    setError(null);
    try {
      const record = await getEnvironment(latitude, longitude);
      setData(record);
    } catch (err) {
      setError(normalizeApiError(err));
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  return { data, loading, error, fetchAt };
}
