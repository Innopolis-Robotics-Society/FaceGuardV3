import { describe, expect, it } from 'vitest';

import { apiUrl, websocketAuthProtocols, websocketUrl } from './urls';


describe('runtime service URLs', () => {
  it('uses the page host and switches only the default service port', () => {
    const locationHref = 'https://faceguard.local:3000/employees';

    expect(apiUrl('/api/logs', { locationHref }))
      .toBe('https://faceguard.local:8000/api/logs');
    expect(websocketUrl('/ws/recognize', { locationHref }))
      .toBe('wss://faceguard.local:8000/ws/recognize');
  });

  it('honours explicit API and WebSocket bases including a path prefix', () => {
    const locationHref = 'https://faceguard.local/';

    expect(apiUrl('employees', {
      locationHref,
      apiBaseUrl: 'https://api.example.test/faceguard/',
    })).toBe('https://api.example.test/faceguard/employees');
    expect(websocketUrl('/enroll', {
      locationHref,
      websocketBaseUrl: 'wss://stream.example.test/camera/',
    })).toBe('wss://stream.example.test/camera/enroll');
  });

  it('carries JWT authentication in WebSocket subprotocols, not the URL', () => {
    const token = 'signed.jwt.value';

    expect(websocketAuthProtocols(token)).toEqual([
      'faceguard.jwt',
      `bearer.${token}`,
    ]);
    expect(websocketUrl('/ws/recognize', {
      locationHref: 'http://localhost:3000/',
    })).not.toContain(token);
  });
});
