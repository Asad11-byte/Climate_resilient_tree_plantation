import { apiClient } from "./client";

/**
 * @param {{ query: string, top_k?: number|null, metadata_filter?: object|null }} params
 */
export async function postRetrieve({ query, top_k = null, metadata_filter = null }) {
  const { data } = await apiClient.post("/retrieve", { query, top_k, metadata_filter });
  return data;
}
