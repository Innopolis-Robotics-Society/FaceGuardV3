import { describe, expect, it } from 'vitest';
import { apiUrl, websocketAuthProtocols, websocketUrl } from './urls';

describe('runtime URLs', () => {
  it('uses the current hostname and matching secure protocols', () => {
    const locationHref = 'https://faceguard-pi.local:3000/employees';
    expect(apiUrl('/api/logs', { locationHref }))
      .toBe('https://faceguard-pi.local:8000/api/logs');
    expect(websocketUrl('/ws/recognize', { locationHref }))
      .toBe('wss://faceguard-pi.local:8000/ws/recognize');
    expect(websocketAuthProtocols('a.b.c')).toEqual(['faceguard.jwt', 'bearer.a.b.c']);
  });

  it('supports explicit API and WebSocket base overrides', () => {
    const locationHref = 'http://localhost:3000/';
    expect(apiUrl('/api/login', {
      locationHref,
      apiBaseUrl: 'http://api.internal:9000/base',
    })).toBe('http://api.internal:9000/base/api/login');
    expect(websocketUrl('/ws/enroll', {
      locationHref,
      websocketBaseUrl: 'wss://socket.internal/gateway',
    })).toBe('wss://socket.internal/gateway/ws/enroll');
  });
});
