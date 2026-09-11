/**
 * Thin wrapper around fetch() that applies our standard auth + accept headers.
 * All API calls should go through this instead of calling fetch() directly.
 *
 * Usage:
 *   const data = await apiFetch<WorksResponse>('/works');
 *   const drafts = await apiFetch<DraftsResponse>('/rbi/drafts/', { work: 7 });
 */
import { API_BASE, API_TOKEN } from '../config';

type QueryParams = Record<string, string | number | undefined>;

export async function apiFetch<T>(path: string, params?: QueryParams): Promise<T> {
  let url = `${API_BASE}${path}`;

  // Append query string if params provided (skipping undefined values)
  if (params) {
    const searchParams = new URLSearchParams();
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined) {
        searchParams.append(key, String(value));
      }
    }
    const qs = searchParams.toString();
    if (qs) url += `?${qs}`;
  }

  const response = await fetch(url, {
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