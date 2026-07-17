export const AUTH_TOKEN_KEY = 'auth_token';
export const AUTH_INVALIDATED_EVENT = 'faceguard:auth-invalidated';

interface JwtPayload {
  exp?: number;
  [key: string]: unknown;
}

function decodeBase64Url(value: string) {
  const normalized = value.replace(/-/g, '+').replace(/_/g, '/');
  const padded = normalized.padEnd(Math.ceil(normalized.length / 4) * 4, '=');
  const binary = atob(padded);
  const bytes = Uint8Array.from(binary, character => character.charCodeAt(0));
  return new TextDecoder().decode(bytes);
}

export function decodeJwtPayload(token: string): JwtPayload | null {
  const parts = token.split('.');
  if (parts.length !== 3 || !parts[1]) return null;
  try {
    const payload = JSON.parse(decodeBase64Url(parts[1]));
    return payload && typeof payload === 'object' ? payload as JwtPayload : null;
  } catch {
    return null;
  }
}

export function isUsableJwt(token: string | null, nowMs = Date.now()) {
  if (!token) return false;
  const payload = decodeJwtPayload(token);
  return typeof payload?.exp === 'number' && payload.exp * 1000 > nowMs;
}

export function getValidAuthToken() {
  const token = localStorage.getItem(AUTH_TOKEN_KEY);
  if (isUsableJwt(token)) return token;
  if (token !== null) localStorage.removeItem(AUTH_TOKEN_KEY);
  return null;
}

export function storeAuthToken(token: string) {
  localStorage.setItem(AUTH_TOKEN_KEY, token);
}

export function invalidateAuth() {
  localStorage.removeItem(AUTH_TOKEN_KEY);
  window.dispatchEvent(new Event(AUTH_INVALIDATED_EVENT));
}
