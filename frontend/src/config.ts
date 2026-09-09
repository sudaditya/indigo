/**
 * Central config for the frontend.
 *
 * For local dev, values are hardcoded. In a real deployment these would
 * come from environment variables (import.meta.env.VITE_API_BASE) or a
 * config endpoint. Not doing that today — deferred to production hardening.
 */

export const API_BASE = 'http://localhost:8000/api';

/**
 * Auth token for Django REST API.
 * WARNING: Currently hardcoded in source. Fine for local POC only.
 * Production requires proper auth flow (login page, secure token storage).
 * See PROJECT.md backlog.
 */
export const API_TOKEN = 'c6f1cada6b327ee801ee6bac77e0c94b5ceb019c';