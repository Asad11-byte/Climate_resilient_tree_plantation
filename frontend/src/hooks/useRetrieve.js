import { useCallback, useState } from "react";
import { postRetrieve } from "../api/retrieve";
import { normalizeApiError } from "../api/client";

export function useRetrieve() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [lastQuery, setLastQuery] = useState(null);

  const search = useCallback(async (query) => {
    if (!query?.trim()) return;
    setLoading(true);
    setError(null);
    setLastQuery(query);
    try {
      const result = await postRetrieve({ query });
      setData(result);
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setLoading(false);
    }
  }, []);

  const retry = useCallback(() => {
    if (lastQuery) search(lastQuery);
  }, [lastQuery, search]);

  return { data, loading, error, search, retry };
}
