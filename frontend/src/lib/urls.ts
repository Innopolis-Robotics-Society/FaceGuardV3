interface UrlOptions {
  locationHref?: string;
  apiBaseUrl?: string;
  websocketBaseUrl?: string;
}

function currentHref() {
  return typeof window === 'undefined' ? 'http://localhost:3000/' : window.location.href;
}

function defaultApiBase(locationHref: string) {
  const url = new URL(locationHref);
  url.protocol = url.protocol === 'https:' ? 'https:' : 'http:';
  url.port = '8000';
  url.pathname = '/';
  url.search = '';
  url.hash = '';
  return url;
}

function appendPath(base: URL, path: string) {
  const url = new URL(base.toString());
  const basePath = url.pathname.replace(/\/$/, '');
  const suffix = path.startsWith('/') ? path : `/${path}`;
  url.pathname = `${basePath}${suffix}` || '/';
  return url;
}

export function apiUrl(path: string, options: UrlOptions = {}) {
  const locationHref = options.locationHref ?? currentHref();
  const configuredBase = options.apiBaseUrl ?? import.meta.env.VITE_API_BASE_URL;
  const base = configuredBase
    ? new URL(configuredBase, locationHref)
    : defaultApiBase(locationHref);
  return appendPath(base, path).toString();
}

export function websocketUrl(path: string, options: UrlOptions = {}) {
  const locationHref = options.locationHref ?? currentHref();
  const configuredWs = options.websocketBaseUrl ?? import.meta.env.VITE_WS_BASE_URL;
  const configuredApi = options.apiBaseUrl ?? import.meta.env.VITE_API_BASE_URL;
  const base = configuredWs
    ? new URL(configuredWs, locationHref)
    : configuredApi
      ? new URL(configuredApi, locationHref)
      : defaultApiBase(locationHref);
  base.protocol = base.protocol === 'https:' || base.protocol === 'wss:' ? 'wss:' : 'ws:';
  return appendPath(base, path).toString();
}

export function websocketAuthProtocols(token: string) {
  return ['faceguard.jwt', `bearer.${token}`];
}
