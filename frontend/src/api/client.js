import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

export const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 30000, // Groq generation can take a few seconds; give it room
});

/**
 * Normalizes an axios error into a shape the hooks can render without
 * knowing about axios. Distinguishes:
 *  - "http": server responded with an error status (e.g. 503, 404)
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
