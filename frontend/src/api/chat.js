import { apiClient } from "./client";

/**
 * @param {{ query: string, latitude?: number|null, longitude?: number|null, top_k?: number|null }} params
 */
export async function postChat({ query, latitude = null, longitude = null, top_k = null }) {
  const { data } = await apiClient.post("/chat", { query, latitude, longitude, top_k });
  return data;
}
