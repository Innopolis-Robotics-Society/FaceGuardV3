import { act, render, screen, waitFor } from '@testing-library/react';
import { useEffect } from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { AUTH_TOKEN_KEY } from '../auth/token';
import { CameraProvider, useCamera } from './CameraContext';
import type { CameraSource } from './CameraContext';

class FakeWebSocket {
  static readonly CONNECTING = 0;
  static readonly OPEN = 1;
  static readonly CLOSING = 2;
  static readonly CLOSED = 3;
  static instances: FakeWebSocket[] = [];

  readonly url: string;
  readonly protocols?: string | string[];
  readyState = FakeWebSocket.CONNECTING;
  bufferedAmount = 0;
  sent: string[] = [];
  closeCalls = 0;
  onopen: ((event: Event) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;

  constructor(url: string, protocols?: string | string[]) {
    this.url = url;
    this.protocols = protocols;
    FakeWebSocket.instances.push(this);
  }

  open() {
    this.readyState = FakeWebSocket.OPEN;
    this.onopen?.(new Event('open'));
  }

  message(payload: Record<string, unknown>) {
    this.onmessage?.(new MessageEvent('message', { data: JSON.stringify(payload) }));
  }

  send(data: string) {
    this.sent.push(data);
  }

  close(code = 1000) {
    if (this.readyState === FakeWebSocket.CLOSED) return;
    this.closeCalls += 1;
    this.readyState = FakeWebSocket.CLOSED;
    this.onclose?.(new CloseEvent('close', { code }));
  }
}

function token(expSeconds = Math.floor(Date.now() / 1000) + 3600) {
  const payload = btoa(JSON.stringify({ sub: 'admin', exp: expSeconds }))
    .replace(/=/g, '')
    .replace(/\+/g, '-')
    .replace(/\//g, '_');
  return `header.${payload}.signature`;
}

function Harness({ operation }: { operation: 'recognize' | 'enroll' }) {
  const camera = useCamera();
  const { startEnroll, startRecognition, stopEnroll, stopRecognition } = camera;
  useEffect(() => {
    if (operation === 'enroll') startEnroll();
    else startRecognition();
    return operation === 'enroll' ? stopEnroll : stopRecognition;
  }, [operation, startEnroll, startRecognition, stopEnroll, stopRecognition]);

  return (
    <div>
      <span data-testid="status">
        {operation === 'enroll' ? camera.enrollData.status : camera.recognitionData.status}
      </span>
      <span data-testid="frame">{camera.remoteFrame ?? ''}</span>
      <span data-testid="enrolling">{String(camera.isEnrolling)}</span>
      <span data-testid="recognizing">{String(camera.isRecognizing)}</span>
      <span data-testid="embedding">{camera.enrollData.embedding?.join(',') ?? ''}</span>
    </div>
  );
}

function renderProvider(source: CameraSource, operation: 'recognize' | 'enroll' = 'recognize') {
  return render(
    <CameraProvider source={source}>
      <Harness operation={operation} />
    </CameraProvider>,
  );
}

describe('CameraProvider', () => {
  const getUserMedia = vi.fn();

  beforeEach(() => {
    FakeWebSocket.instances = [];
    vi.stubGlobal('WebSocket', FakeWebSocket);
    Object.defineProperty(navigator, 'mediaDevices', {
      configurable: true,
      value: { getUserMedia },
    });
    getUserMedia.mockReset();
    localStorage.setItem(AUTH_TOKEN_KEY, token());
  });

  it('never requests the browser camera in backend mode and consumes remote JPEG', async () => {
    renderProvider('backend');
    await waitFor(() => expect(FakeWebSocket.instances).toHaveLength(1));
    expect(getUserMedia).not.toHaveBeenCalled();
    expect(FakeWebSocket.instances[0].url).not.toContain('token=');
    const storedToken = localStorage.getItem(AUTH_TOKEN_KEY);
    expect(FakeWebSocket.instances[0].protocols).toEqual([
      'faceguard.jwt',
      `bearer.${storedToken}`,
    ]);

    act(() => {
      FakeWebSocket.instances[0].open();
      FakeWebSocket.instances[0].message({
        status: 'Access Granted',
        color: '#0f0',
        frame: 'data:image/jpeg;base64,Y2FtZXJh',
        box: [1, 2, 3, 4],
        frame_width: 640,
        frame_height: 480,
      });
    });
    expect(screen.getByTestId('frame')).toHaveTextContent('data:image/jpeg;base64,Y2FtZXJh');
  });

  it('stops browser tracks and keeps at most one frame in flight', async () => {
    vi.useFakeTimers();
    const stop = vi.fn();
    getUserMedia.mockResolvedValue({ getTracks: () => [{ stop }] } as unknown as MediaStream);
    Object.defineProperty(HTMLVideoElement.prototype, 'videoWidth', { configurable: true, value: 640 });
    Object.defineProperty(HTMLVideoElement.prototype, 'videoHeight', { configurable: true, value: 480 });

    const rendered = renderProvider('browser');
    await act(async () => {
      await Promise.resolve();
      await Promise.resolve();
    });
    expect(getUserMedia).toHaveBeenCalledOnce();
    expect(FakeWebSocket.instances).toHaveLength(1);

    act(() => {
      FakeWebSocket.instances[0].open();
      vi.advanceTimersByTime(0);
      vi.advanceTimersByTime(1000);
    });
    expect(FakeWebSocket.instances[0].sent).toHaveLength(1);
    act(() => {
      FakeWebSocket.instances[0].message({
        status: 'No face detected',
        color: '#888',
        box: null,
        frame_width: 640,
        frame_height: 480,
      });
    });
    expect(screen.getByTestId('frame')).toHaveTextContent(
      FakeWebSocket.instances[0].sent[0],
    );
    rendered.unmount();
    expect(stop).toHaveBeenCalled();
    expect(FakeWebSocket.instances[0].closeCalls).toBe(1);
    act(() => vi.advanceTimersByTime(30_000));
    expect(FakeWebSocket.instances).toHaveLength(1);
    expect(FakeWebSocket.instances[0].sent).toHaveLength(1);
  });

  it('does not reconnect after an authentication close', async () => {
    vi.useFakeTimers();
    renderProvider('backend');
    await act(async () => Promise.resolve());
    expect(FakeWebSocket.instances).toHaveLength(1);
    act(() => FakeWebSocket.instances[0].close(1008));
    act(() => vi.advanceTimersByTime(30_000));
    expect(FakeWebSocket.instances).toHaveLength(1);
    expect(localStorage.getItem(AUTH_TOKEN_KEY)).toBeNull();
  });

  it('caps reconnect attempts after abnormal disconnects', async () => {
    vi.useFakeTimers();
    renderProvider('backend');
    await act(async () => Promise.resolve());

    const retryDelays = [500, 1000, 2000, 4000];
    for (const delay of retryDelays) {
      act(() => FakeWebSocket.instances.at(-1)?.close(1006));
      act(() => vi.advanceTimersByTime(delay));
    }
    expect(FakeWebSocket.instances).toHaveLength(5);
    act(() => FakeWebSocket.instances.at(-1)?.close(1006));
    act(() => vi.advanceTimersByTime(30_000));
    expect(FakeWebSocket.instances).toHaveLength(5);
    expect(screen.getByTestId('status')).toHaveTextContent('Camera connection failed');
  });

  it('rejects an expired JWT before opening a socket', async () => {
    localStorage.setItem(AUTH_TOKEN_KEY, token(1));
    renderProvider('backend');
    await waitFor(() => expect(screen.getByTestId('status')).toHaveTextContent('Authentication expired'));
    expect(FakeWebSocket.instances).toHaveLength(0);
  });

  it('handles Finished once, closes resources and preserves the embedding', async () => {
    renderProvider('backend', 'enroll');
    await waitFor(() => expect(FakeWebSocket.instances).toHaveLength(1));
    const socket = FakeWebSocket.instances[0];
    act(() => {
      socket.open();
      socket.message({ status: 'Finished', embedding: [0.1, 0.2], frame_width: 640, frame_height: 480 });
      socket.message({ status: 'Finished', embedding: [9, 9], frame_width: 640, frame_height: 480 });
    });

    expect(screen.getByTestId('embedding')).toHaveTextContent('0.1,0.2');
    expect(screen.getByTestId('enrolling')).toHaveTextContent('false');
    expect(socket.closeCalls).toBe(1);
  });

  it('switches recognition and enrollment without keeping both operations active', async () => {
    const rendered = renderProvider('backend', 'recognize');
    await waitFor(() => expect(FakeWebSocket.instances).toHaveLength(1));
    const recognitionSocket = FakeWebSocket.instances[0];

    rendered.rerender(
      <CameraProvider source="backend">
        <Harness operation="enroll" />
      </CameraProvider>,
    );

    await waitFor(() => expect(FakeWebSocket.instances).toHaveLength(2));
    expect(recognitionSocket.closeCalls).toBe(1);
    expect(screen.getByTestId('recognizing')).toHaveTextContent('false');
    expect(screen.getByTestId('enrolling')).toHaveTextContent('true');
  });
});
