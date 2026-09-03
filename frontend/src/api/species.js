import { apiClient } from "./client";

export async function getSpecies() {
  const { data } = await apiClient.get("/species");
  return data;
}

export async function getSpeciesById(id) {
  const { data } = await apiClient.get(`/species/${id}`);
  return data;
}
