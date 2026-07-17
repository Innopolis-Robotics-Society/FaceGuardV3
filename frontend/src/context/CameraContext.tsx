import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import type { ReactNode } from 'react';
import { getValidAuthToken, invalidateAuth } from '../auth/token';
import { parseBBox } from '../camera/projectBBox';
import type { BBox } from '../camera/projectBBox';
import { websocketAuthProtocols, websocketUrl } from '../lib/urls';

export type CameraSource = 'browser' | 'backend';

interface FrameData {
  box?: BBox;
  frameWidth?: number;
  frameHeight?: number;
}

export interface RecognitionData extends FrameData {
  status: string;
  color: string;
  name?: string;
  similarity?: string;
}

export interface EnrollData extends FrameData {
  status: string;
  color: string;
  progress: number;
  embedding?: number[];
}

interface CameraContextType {
  cameraSource: CameraSource;
  stream: MediaStream | null;
  remoteFrame: string | null;
  isRecognizing: boolean;
  startRecognition: () => void;
  stopRecognition: () => void;
  recognitionData: RecognitionData;
  isEnrolling: boolean;
  startEnroll: () => void;
  stopEnroll: () => void;
  enrollData: EnrollData;
  resetCamera: () => void;
}

interface CameraProviderProps {
  children: ReactNode;
  source?: CameraSource;
}

const defaultRecognitionData: RecognitionData = { status: 'Idle', color: '#888' };
const defaultEnrollData: EnrollData = { status: 'Idle', color: '#888', progress: 0 };
const MAX_RECONNECT_ATTEMPTS = 4;
const AUTH_CLOSE_CODES = new Set([1008, 4401, 4403]);
const FATAL_CLOSE_CODES = new Set([1002, 1003, 1007, 1011]);

const CameraContext = createContext<CameraContextType | null>(null);

function parseCameraSource(value: string | undefined): CameraSource {
  return value?.trim().toLowerCase() === 'backend' ? 'backend' : 'browser';
}

const configuredCameraSource = parseCameraSource(import.meta.env.VITE_CAMERA_SOURCE);

function positiveNumber(value: unknown) {
  return typeof value === 'number' && Number.isFinite(value) && value > 0
    ? value
    : undefined;
}

function stringValue(value: unknown, fallback: string) {
  return typeof value === 'string' ? value : fallback;
}

function stopStream(stream: MediaStream | null) {
  stream?.getTracks().forEach(track => track.stop());
}

function messageFromError(error: unknown) {
  return error instanceof Error ? error.message : String(error);
}

export function CameraProvider({ children, source = configuredCameraSource }: CameraProviderProps) {
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [remoteFrame, setRemoteFrame] = useState<string | null>(null);
  const [isRecognizing, setIsRecognizing] = useState(false);
  const [isEnrolling, setIsEnrolling] = useState(false);
  const [recognitionData, setRecognitionData] =
    useState<RecognitionData>(defaultRecognitionData);
  const [enrollData, setEnrollData] = useState<EnrollData>(defaultEnrollData);

  const hiddenVideoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const activeStreamRef = useRef<MediaStream | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);
  const captureTimeoutRef = useRef<number | null>(null);
  const activeModeRef = useRef<'recognize' | 'enroll' | null>(null);

  const activeMode = isEnrolling ? 'enroll' : isRecognizing ? 'recognize' : null;
  const cameraActive = activeMode !== null;
  activeModeRef.current = activeMode;

  const clearSocketTimers = useCallback(() => {
    if (reconnectTimeoutRef.current !== null) {
      window.clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    if (captureTimeoutRef.current !== null) {
      window.clearTimeout(captureTimeoutRef.current);
      captureTimeoutRef.current = null;
    }
  }, []);

  const closeSocket = useCallback(() => {
    clearSocketTimers();
    const socket = wsRef.current;
    wsRef.current = null;
    if (socket && socket.readyState < WebSocket.CLOSING) {
      socket.onclose = null;
      socket.close(1000, 'Client stopped');
    }
  }, [clearSocketTimers]);

  const stopBrowserCamera = useCallback(() => {
    const activeStream = activeStreamRef.current;
    activeStreamRef.current = null;
    stopStream(activeStream);
    if (hiddenVideoRef.current) hiddenVideoRef.current.srcObject = null;
    setStream(null);
  }, []);

  const resetCamera = useCallback(() => {
    closeSocket();
    stopBrowserCamera();
    setIsRecognizing(false);
    setIsEnrolling(false);
    setRemoteFrame(null);
    setRecognitionData(defaultRecognitionData);
    setEnrollData(defaultEnrollData);
  }, [closeSocket, stopBrowserCamera]);

  const startRecognition = useCallback(() => {
    closeSocket();
    setIsEnrolling(false);
    setEnrollData(defaultEnrollData);
    setRecognitionData({ status: 'Starting camera...', color: '#888' });
    setRemoteFrame(null);
    setIsRecognizing(true);
  }, [closeSocket]);

  const stopRecognition = useCallback(() => {
    setIsRecognizing(false);
    setRemoteFrame(null);
    setRecognitionData(defaultRecognitionData);
  }, []);

  const startEnroll = useCallback(() => {
    closeSocket();
    setIsRecognizing(false);
    setRecognitionData(defaultRecognitionData);
    setEnrollData({ status: 'Starting camera...', color: '#888', progress: 0 });
    setRemoteFrame(null);
    setIsEnrolling(true);
  }, [closeSocket]);

  const stopEnroll = useCallback(() => {
    setIsEnrolling(false);
    setRemoteFrame(null);
  }, []);

  // Acquire the laptop camera lazily and only in browser mode. The disposed
  // guard also stops a stream that resolves after React StrictMode cleanup.
  useEffect(() => {
    if (source !== 'browser' || !cameraActive) {
      stopBrowserCamera();
      hiddenVideoRef.current = null;
      canvasRef.current = null;
      return;
    }

    let disposed = false;
    let acquiredStream: MediaStream | null = null;
    const hiddenVideo = document.createElement('video');
    hiddenVideo.autoplay = true;
    hiddenVideo.playsInline = true;
    hiddenVideo.muted = true;
    hiddenVideoRef.current = hiddenVideo;
    canvasRef.current = document.createElement('canvas');

    const mediaDevices = navigator.mediaDevices;
    if (!mediaDevices?.getUserMedia) {
      const status = 'Camera API is unavailable. Use HTTPS or backend camera mode.';
      if (activeModeRef.current === 'enroll') {
        setEnrollData(previous => ({ ...previous, status, color: '#f00' }));
      } else {
        setRecognitionData({ status, color: '#f00' });
      }
      return () => {
        disposed = true;
      };
    }

    mediaDevices
      .getUserMedia({
        video: { width: { ideal: 1280 }, height: { ideal: 720 } },
        audio: false,
      })
      .then(cameraStream => {
        if (disposed) {
          stopStream(cameraStream);
          return;
        }
        acquiredStream = cameraStream;
        activeStreamRef.current = cameraStream;
        hiddenVideo.srcObject = cameraStream;
        setStream(cameraStream);
        hiddenVideo.play().catch(error => {
          console.debug('Hidden camera preview did not autoplay:', error);
        });
      })
      .catch(error => {
        if (disposed) return;
        const status = `Error accessing camera: ${messageFromError(error)}`;
        if (activeModeRef.current === 'enroll') {
          setEnrollData(previous => ({ ...previous, status, color: '#f00' }));
        } else {
          setRecognitionData({ status, color: '#f00' });
        }
      });

    return () => {
      disposed = true;
      if (activeStreamRef.current === acquiredStream) {
        stopStream(acquiredStream);
        activeStreamRef.current = null;
      }
      hiddenVideo.srcObject = null;
      if (hiddenVideoRef.current === hiddenVideo) hiddenVideoRef.current = null;
      canvasRef.current = null;
    };
  }, [cameraActive, source, stopBrowserCamera]);

  useEffect(() => {
    closeSocket();
    if (activeMode === null) return;
    if (source === 'browser' && !stream) return;

    const token = getValidAuthToken();
    if (!token) {
      const status = 'Authentication expired. Please sign in again.';
      if (activeMode === 'enroll') {
        setEnrollData(previous => ({ ...previous, status, color: '#f00' }));
      } else {
        setRecognitionData({ status, color: '#f00' });
      }
      if (activeMode === 'enroll') setIsEnrolling(false);
      else setIsRecognizing(false);
      invalidateAuth();
      return;
    }

    const isEnrollMode = activeMode === 'enroll';
    const endpoint = websocketUrl(isEnrollMode ? '/ws/enroll' : '/ws/recognize');
    const authProtocols = websocketAuthProtocols(token);
    const minimumFrameInterval = isEnrollMode ? 200 : 100;
    let disposed = false;
    let finished = false;
    let fatalResponse = false;
    let activeSocket: WebSocket | null = null;
    let reconnectAttempts = 0;
    let awaitingResponse = false;
    let pendingBrowserFrame: string | null = null;

    setRemoteFrame(null);
    if (isEnrollMode) {
      setEnrollData(previous => ({
        ...previous,
        status: 'Connecting...',
        color: '#888',
        box: undefined,
      }));
    } else {
      setRecognitionData({ status: 'Connecting...', color: '#888' });
    }

    const clearCaptureTimeout = () => {
      if (captureTimeoutRef.current !== null) {
        window.clearTimeout(captureTimeoutRef.current);
        captureTimeoutRef.current = null;
      }
    };

    const scheduleBrowserFrame = (socket: WebSocket, delay: number) => {
      if (source !== 'browser' || disposed || finished) return;
      clearCaptureTimeout();
      captureTimeoutRef.current = window.setTimeout(() => {
        captureTimeoutRef.current = null;
        if (
          disposed ||
          finished ||
          activeSocket !== socket ||
          socket.readyState !== WebSocket.OPEN
        ) {
          return;
        }
        if (awaitingResponse || socket.bufferedAmount > 0) {
          scheduleBrowserFrame(socket, 25);
          return;
        }

        const video = hiddenVideoRef.current;
        const canvas = canvasRef.current;
        if (!video || !canvas || video.videoWidth <= 0 || video.videoHeight <= 0) {
          scheduleBrowserFrame(socket, 50);
          return;
        }

        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        const context = canvas.getContext('2d');
        if (!context) {
          scheduleBrowserFrame(socket, 100);
          return;
        }
        context.drawImage(video, 0, 0, canvas.width, canvas.height);
        pendingBrowserFrame = canvas.toDataURL('image/jpeg', 0.5);
        awaitingResponse = true;
        socket.send(pendingBrowserFrame);
      }, delay);
    };

    const updateRemoteFrame = (value: unknown) => {
      if (source === 'backend' && typeof value === 'string' && value.startsWith('data:image/jpeg;base64,')) {
        setRemoteFrame(value);
      } else if (source === 'browser' && pendingBrowserFrame) {
        // The bbox describes the submitted canvas snapshot, not the newer
        // live video frame. Display that exact snapshot to keep them atomic.
        setRemoteFrame(pendingBrowserFrame);
        pendingBrowserFrame = null;
      }
    };

    const setConnectionFailure = (status: string) => {
      if (isEnrollMode) {
        setEnrollData(previous => ({ ...previous, status, color: '#f00', box: undefined }));
      } else {
        setRecognitionData({ status, color: '#f00' });
      }
    };

    const stopCurrentOperation = () => {
      clearCaptureTimeout();
      setRemoteFrame(null);
      if (isEnrollMode) setIsEnrolling(false);
      else setIsRecognizing(false);
    };

    const connect = () => {
      if (disposed || finished) return;
      const socket = new WebSocket(endpoint, authProtocols);
      activeSocket = socket;
      wsRef.current = socket;
      awaitingResponse = false;
      pendingBrowserFrame = null;

      socket.onopen = () => {
        if (source === 'browser') scheduleBrowserFrame(socket, 0);
      };

      socket.onmessage = event => {
        if (disposed || finished || activeSocket !== socket) return;
        awaitingResponse = false;

        let data: Record<string, unknown>;
        try {
          data = JSON.parse(String(event.data)) as Record<string, unknown>;
        } catch {
          setConnectionFailure('Invalid response from camera service');
          scheduleBrowserFrame(socket, minimumFrameInterval);
          return;
        }

        reconnectAttempts = 0;
        fatalResponse = data.fatal === true;
        updateRemoteFrame(data.frame);
        const box = parseBBox(data.box);
        const frameWidth = positiveNumber(data.frame_width);
        const frameHeight = positiveNumber(data.frame_height);
        const status = stringValue(data.status, 'Processing...');
        const color = stringValue(data.color, '#888');

        if (isEnrollMode) {
          if (status === 'Finished') {
            finished = true;
            clearCaptureTimeout();
            const embedding = Array.isArray(data.embedding) &&
              data.embedding.every(value => typeof value === 'number' && Number.isFinite(value))
              ? data.embedding as number[]
              : undefined;
            setEnrollData(previous => ({
              ...previous,
              status: embedding
                ? 'Face data collected! Please fill the form.'
                : 'Invalid enrollment result',
              color: embedding ? '#00FF00' : '#f00',
              progress: embedding ? 1 : previous.progress,
              embedding,
              box: undefined,
              frameWidth,
              frameHeight,
            }));
            if (wsRef.current === socket) wsRef.current = null;
            socket.close(1000, 'Enrollment finished');
            setIsEnrolling(false);
            return;
          }

          const rawProgress = typeof data.progress === 'number' && Number.isFinite(data.progress)
            ? data.progress
            : 0;
          setEnrollData(previous => ({
            status,
            color,
            progress: Math.max(0, Math.min(1, rawProgress)),
            embedding: previous.embedding,
            box,
            frameWidth,
            frameHeight,
          }));
        } else {
          setRecognitionData({
            status,
            color,
            name: typeof data.name === 'string' ? data.name : undefined,
            similarity: typeof data.similarity === 'string' ? data.similarity : undefined,
            box,
            frameWidth,
            frameHeight,
          });
        }

        if (fatalResponse) {
          if (wsRef.current === socket) wsRef.current = null;
          stopCurrentOperation();
          socket.close(1000, 'Fatal camera error');
          return;
        }
        scheduleBrowserFrame(socket, minimumFrameInterval);
      };

      socket.onclose = event => {
        clearCaptureTimeout();
        if (wsRef.current === socket) wsRef.current = null;
        if (activeSocket === socket) activeSocket = null;
        if (disposed || finished || fatalResponse) return;

        if (AUTH_CLOSE_CODES.has(event.code)) {
          setConnectionFailure('Authentication rejected. Please sign in again.');
          stopCurrentOperation();
          invalidateAuth();
          return;
        }
        if (FATAL_CLOSE_CODES.has(event.code)) {
          setConnectionFailure('Camera service closed with a fatal error.');
          stopCurrentOperation();
          return;
        }
        if (event.code === 1000) {
          setConnectionFailure('Camera connection closed. Retry the operation.');
          stopCurrentOperation();
          return;
        }
        if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
          setConnectionFailure('Camera connection failed. Retry the operation.');
          stopCurrentOperation();
          return;
        }

        const delay = Math.min(500 * 2 ** reconnectAttempts, 4000);
        reconnectAttempts += 1;
        reconnectTimeoutRef.current = window.setTimeout(() => {
          reconnectTimeoutRef.current = null;
          connect();
        }, delay);
      };
    };

    connect();

    return () => {
      disposed = true;
      clearSocketTimers();
      const socket = activeSocket;
      activeSocket = null;
      pendingBrowserFrame = null;
      if (wsRef.current === socket) wsRef.current = null;
      if (socket && socket.readyState < WebSocket.CLOSING) {
        socket.close(1000, 'Operation changed');
      }
    };
  }, [activeMode, clearSocketTimers, closeSocket, source, stream]);

  useEffect(() => () => {
    clearSocketTimers();
    const socket = wsRef.current;
    wsRef.current = null;
    if (socket && socket.readyState < WebSocket.CLOSING) socket.close(1000, 'Provider unmounted');
    stopStream(activeStreamRef.current);
    activeStreamRef.current = null;
    if (hiddenVideoRef.current) hiddenVideoRef.current.srcObject = null;
  }, [clearSocketTimers]);

  const value = useMemo<CameraContextType>(() => ({
    cameraSource: source,
    stream,
    remoteFrame,
    isRecognizing,
    startRecognition,
    stopRecognition,
    recognitionData,
    isEnrolling,
    startEnroll,
    stopEnroll,
    enrollData,
    resetCamera,
  }), [
    enrollData,
    isEnrolling,
    isRecognizing,
    recognitionData,
    remoteFrame,
    resetCamera,
    source,
    startEnroll,
    startRecognition,
    stopEnroll,
    stopRecognition,
    stream,
  ]);

  return <CameraContext.Provider value={value}>{children}</CameraContext.Provider>;
}

// oxlint-disable-next-line react/only-export-components -- Context providers and their hook are one API.
export function useCamera() {
  const context = useContext(CameraContext);
  if (!context) throw new Error('useCamera must be used within CameraProvider');
  return context;
}
