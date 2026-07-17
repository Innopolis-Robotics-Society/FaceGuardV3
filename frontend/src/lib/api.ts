import { getValidAuthToken, invalidateAuth } from '../auth/token';
import { apiUrl } from './urls';

export async function apiFetch(path: string, init: RequestInit = {}) {
  const token = getValidAuthToken();
  if (!token) {
    invalidateAuth();
    throw new Error('Authentication required');
  }

  const headers = new Headers(init.headers);
  headers.set('Authorization', `Bearer ${token}`);
  const response = await fetch(apiUrl(path), { ...init, headers });
  if (response.status === 401 || response.status === 403) invalidateAuth();
  return response;
}
