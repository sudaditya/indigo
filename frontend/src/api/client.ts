/**
 * Thin wrapper around fetch() that applies our standard auth + accept headers.
 *
 * Supports GET (with optional query params) and POST (with JSON body).
 * Future: PATCH/PUT/DELETE if needed.
 *
 * Usage:
 *   const data = await apiFetch<WorksResponse>('/works');
 *   const drafts = await apiFetch<DraftsResponse>('/rbi/drafts/', { work: 7 });
 *   const created = await apiPost<DraftAmendment>('/rbi/drafts/', { ... });
 */
import { API_BASE, API_TOKEN } from '../config';

type QueryParams = Record<string, string | number | undefined>;

function buildUrl(path: string, params?: QueryParams): string {
  let url = `${API_BASE}${path}`;
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
  return url;
}

const baseHeaders = () => ({
  'Authorization': `Token ${API_TOKEN}`,
  'Accept': 'application/json',
});

export async function apiFetch<T>(path: string, params?: QueryParams): Promise<T> {
  const url = buildUrl(path, params);
  const response = await fetch(url, { headers: baseHeaders() });
  if (!response.ok) {
    throw new Error(`API ${path} returned ${response.status}: ${response.statusText}`);
  }
  return response.json() as Promise<T>;
}

/**
 * POST JSON body to an endpoint. On error, tries to extract the DRF
 * validation error body for a helpful message.
 */
export async function apiPost<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: {
      ...baseHeaders(),
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    // Try to get DRF's error details for a useful message
    let errorDetail = `${response.status} ${response.statusText}`;
    try {
      const errBody = await response.json();
      errorDetail = JSON.stringify(errBody);
    } catch {
      // Response body wasn't JSON — stick with status
    }
    throw new Error(`POST ${path} failed: ${errorDetail}`);
  }

  return response.json() as Promise<T>;
}
/**
 * POST a multipart form (for file uploads). Unlike apiPost, we DON'T set
 * Content-Type — the browser sets it automatically with the correct
 * boundary parameter for multipart/form-data.
 */
export async function apiPostForm<T>(path: string, formData: FormData): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: {
      // NOTE: NO Content-Type — let the browser set it with the boundary
      'Authorization': `Token ${API_TOKEN}`,
      'Accept': 'application/json',
    },
    body: formData,
  });

  if (!response.ok) {
    let errorDetail = `${response.status} ${response.statusText}`;
    try {
      const errBody = await response.json();
      // DRF errors often come with a 'detail' key
      if (errBody.detail) {
        errorDetail = errBody.detail;
      } else {
        errorDetail = JSON.stringify(errBody);
      }
    } catch {
      // Response body wasn't JSON — stick with status
    }
    throw new Error(errorDetail);
  }

  return response.json() as Promise<T>;
}