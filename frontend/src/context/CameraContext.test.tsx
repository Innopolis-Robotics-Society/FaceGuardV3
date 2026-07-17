import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { AUTH_TOKEN_KEY } from '../auth/token';
import { CameraProvider, useCamera } from './CameraContext';


class FakeWebSocket {
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;
  static instances: FakeWebSocket[] = [];

  readyState = FakeWebSocket.CONNECTING;
  bufferedAmount = 0;
  sent: string[] = [];
  closeCalls: Array<[number | undefined, string | undefined]> = [];
  onopen: (() => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;
  url: string;
  protocols: string[];

  constructor(url: string, protocols: string[]) {
    this.url = url;
    this.protocols = protocols;
    FakeWebSocket.instances.push(this);
  }

  send(value: string) {
    this.sent.push(value);
  }

  close(code?: number, reason?: string) {
    this.closeCalls.push([code, reason]);
    this.readyState = FakeWebSocket.CLOSED;
  }

  open() {
    this.readyState = FakeWebSocket.OPEN;
    this.onopen?.();
  }

  message(data: Record<string, unknown>) {
    this.onmessage?.({ data: JSON.stringify(data) } as MessageEvent);
  }
}

function validToken() {
  const payload = btoa(JSON.stringify({ exp: Math.floor(Date.now() / 1000) + 3600 }));
  return `header.${payload}.signature`;
}

function Probe() {
  const camera = useCamera();
  return (
    <div>
      <button onClick={camera.startRecognition}>recognize</button>
      <span data-testid="source">{camera.cameraSource}</span>
      <span data-testid="status">{camera.recognitionData.status}</span>
      <span data-testid="remote">{camera.remoteFrame ?? ''}</span>
    </div>
  );
}


describe('camera modes and frame flow', () => {
  beforeEach(() => {
    FakeWebSocket.instances = [];
    vi.stubGlobal('WebSocket', FakeWebSocket);
    localStorage.setItem(AUTH_TOKEN_KEY, validToken());
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  it('uses backend frames without requesting a browser camera', async () => {
    const getUserMedia = vi.fn();
    Object.defineProperty(navigator, 'mediaDevices', {
      configurable: true,
      value: { getUserMedia },
    });
    render(<CameraProvider source="backend"><Probe /></CameraProvider>);

    fireEvent.click(screen.getByText('recognize'));
    await waitFor(() => expect(FakeWebSocket.instances).toHaveLength(1));
    const socket = FakeWebSocket.instances[0];

    expect(getUserMedia).not.toHaveBeenCalled();
    expect(socket.url).toBe('ws://localhost:8000/ws/recognize');
    expect(socket.protocols).toEqual([
      'faceguard.jwt',
      `bearer.${localStorage.getItem(AUTH_TOKEN_KEY)}`,
    ]);

    act(() => {
      socket.open();
      socket.message({
        status: 'Access Granted',
        color: '#00FF00',
        frame: 'data:image/jpeg;base64,backend-frame',
        frame_width: 640,
        frame_height: 480,
        box: [10, 20, 100, 200],
      });
    });

    expect(screen.getByTestId('status')).toHaveTextContent('Access Granted');
    expect(screen.getByTestId('remote'))
      .toHaveTextContent('data:image/jpeg;base64,backend-frame');
    expect(socket.sent).toEqual([]);
  });

  it('keeps at most one browser JPEG in flight and displays that exact JPEG', async () => {
    vi.useFakeTimers();
    const stop = vi.fn();
    const stream = { getTracks: () => [{ stop }] } as unknown as MediaStream;
    const getUserMedia = vi.fn().mockResolvedValue(stream);
    Object.defineProperty(navigator, 'mediaDevices', {
      configurable: true,
      value: { getUserMedia },
    });
    Object.defineProperty(HTMLVideoElement.prototype, 'videoWidth', {
      configurable: true,
      get: () => 640,
    });
    Object.defineProperty(HTMLVideoElement.prototype, 'videoHeight', {
      configurable: true,
      get: () => 480,
    });
    vi.spyOn(HTMLMediaElement.prototype, 'play').mockResolvedValue(undefined);
    vi.spyOn(HTMLCanvasElement.prototype, 'getContext')
      .mockReturnValue({ drawImage: vi.fn() } as unknown as CanvasRenderingContext2D);
    let frameNumber = 0;
    vi.spyOn(HTMLCanvasElement.prototype, 'toDataURL').mockImplementation(() => {
      frameNumber += 1;
      return `data:image/jpeg;base64,browser-frame-${frameNumber}`;
    });

    render(<CameraProvider source="browser"><Probe /></CameraProvider>);
    fireEvent.click(screen.getByText('recognize'));
    await act(async () => Promise.resolve());
    await act(async () => Promise.resolve());
    expect(getUserMedia).toHaveBeenCalledTimes(1);
    expect(FakeWebSocket.instances).toHaveLength(1);
    const socket = FakeWebSocket.instances[0];

    act(() => {
      socket.open();
      vi.runOnlyPendingTimers();
    });
    expect(socket.sent).toEqual([
      'data:image/jpeg;base64,browser-frame-1',
    ]);

    act(() => vi.advanceTimersByTime(1000));
    expect(socket.sent).toHaveLength(1);

    act(() => {
      socket.message({
        status: 'Recognizing...',
        color: '#FFFF00',
        frame_width: 640,
        frame_height: 480,
        box: [10, 20, 100, 200],
      });
    });
    expect(screen.getByTestId('remote'))
      .toHaveTextContent('data:image/jpeg;base64,browser-frame-1');

    act(() => vi.advanceTimersByTime(100));
    expect(socket.sent).toEqual([
      'data:image/jpeg;base64,browser-frame-1',
      'data:image/jpeg;base64,browser-frame-2',
    ]);
  });
});
