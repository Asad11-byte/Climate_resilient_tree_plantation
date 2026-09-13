import axios from "axios";
import { supabase } from "./supabaseClient";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

export const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 30000, // Groq generation can take a few seconds; give it room
});

// Attaches the current Supabase session's access token (a JWT, already
// signed by Supabase — not the secret, just the token) to every request.
// getSession() reads from local storage and silently refreshes if the
// token is near expiry, so this never needs its own refresh logic.
apiClient.interceptors.request.use(async (config) => {
  const {
    data: { session },
  } = await supabase.auth.getSession();
  if (session?.access_token) {
    config.headers.Authorization = `Bearer ${session.access_token}`;
  }
  return config;
});

// A 401 here means the backend rejected the token (expired past refresh,
// revoked, or malformed) — the local session is stale, so clear it and
// send the user back to sign in rather than surfacing a raw API error.
/*apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      await supabase.auth.signOut();
      if (typeof window !== "undefined" && window.location.pathname !== "/login") {
        window.location.assign("/login");
      }
    }
    return Promise.reject(error);
  }
);*/
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    return Promise.reject(error);
  }
);

/**
 * Normalizes an axios error into a shape the hooks can render without
 * knowing about axios. Distinguishes:
 *  - "http": server responded with an error status (e.g. 503, 404, 401)
 *  - "network": request never reached the server
 */
export function normalizeApiError(error) {
  if (error.response) {
    return {
      type: "http",
      status: error.response.status,
      detail: error.response.data?.detail || error.message,
    };
  }
  return {
    type: "network",
    status: null,
    detail: "Could not reach the server. Check that the backend is running.",
  };
}