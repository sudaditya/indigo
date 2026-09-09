/**
 * Thin wrapper around fetch() that applies our standard auth + accept headers.
 * All API calls should go through this instead of calling fetch() directly.
 *
 * Usage:
 *   const data = await apiFetch<WorksResponse>('/works');
 *   const doc = await apiFetch<DocumentContent>(`/documents/${id}/content`);
 */
import { API_BASE, API_TOKEN } from '../config';

export async function apiFetch<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Authorization': `Token ${API_TOKEN}`,
      'Accept': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`API ${path} returned ${response.status}: ${response.statusText}`);
  }

  return response.json() as Promise<T>;
}