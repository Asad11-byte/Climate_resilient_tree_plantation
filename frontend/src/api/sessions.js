import { apiClient } from "./client";

// apiClient's baseURL already ends in /api (see src/api/client.js), so
// paths here are relative to that — e.g. this hits {baseURL}/sessions.

export async function fetchSessions() {
  const { data } = await apiClient.get("/sessions");
  return data;
}

export async function createSession() {
  const { data } = await apiClient.post("/sessions");
  return data;
}

export async function renameSession(id, title) {
  const { data } = await apiClient.patch(`/sessions/${id}`, { title });
  return data;
}

export async function deleteSession(id) {
  await apiClient.delete(`/sessions/${id}`);
}

export async function fetchSessionMessages(id) {
  const { data } = await apiClient.get(`/sessions/${id}/messages`);
  return data;
}