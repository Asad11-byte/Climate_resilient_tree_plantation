import { apiClient } from "./client";

export async function getEnvironment(latitude, longitude) {
  const { data } = await apiClient.get("/environment", {
    params: { latitude, longitude },
  });
  return data;
}
