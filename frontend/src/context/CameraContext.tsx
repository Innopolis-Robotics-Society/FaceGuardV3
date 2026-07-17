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

const defaultRecognitionData: RecognitionData = { status: 'Idle', color: '#888' };
const defaultEnrollData: EnrollData = { status: 'Idle', color: '#888', progress: 0 };
const CameraContext = createContext<CameraContextType | null>(null);
const AUTH_CLOSE_CODES = new Set([1008, 4401, 4403]);
const FATAL_CLOSE_CODES = new Set([1002, 1003, 1007, 1011]);
const MAX_RECONNECT_ATTEMPTS = 4;

function configuredSource(): CameraSource {
  return import.meta.env.VITE_CAMERA_SOURCE?.trim().toLowerCase() === 'backend'
    ? 'backend'
    : 'browser';
}

function stopStream(stream: MediaStream | null) {
  stream?.getTracks().forEach(track => track.stop());
}

function positiveNumber(value: unknown) {
  return typeof value === 'number' && Number.isFinite(value) && value > 0
    ? value
    : undefined;
}

export function CameraProvider({
  children,
  source = configuredSource(),
}: {
  children: ReactNode;
  source?: CameraSource;
}) {
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [remoteFrame, setRemoteFrame] = useState<string | null>(null);
  const [isRecognizing, setIsRecognizing] = useState(false);
  const [isEnrolling, setIsEnrolling] = useState(false);
  const [recognitionData, setRecognitionData] = useState(defaultRecognitionData);
  const [enrollData, setEnrollData] = useState(defaultEnrollData);

  const hiddenVideoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const activeStreamRef = useRef<MediaStream | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<number | null>(null);
  const captureTimerRef = useRef<number | null>(null);
  const activeModeRef = useRef<'recognize' | 'enroll' | null>(null);
  const activeMode = isEnrolling ? 'enroll' : isRecognizing ? 'recognize' : null;
  activeModeRef.current = activeMode;

  const clearTimers = useCallback(() => {
    if (reconnectTimerRef.current !== null) {
      window.clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }
    if (captureTimerRef.current !== null) {
      window.clearTimeout(captureTimerRef.current);
      captureTimerRef.current = null;
    }
  }, []);

  const closeSocket = useCallback(() => {
    clearTimers();
    const socket = wsRef.current;
    wsRef.current = null;
    if (socket && socket.readyState < WebSocket.CLOSING) {
      socket.onclose = null;
      socket.close(1000, 'Client stopped');
    }
  }, [clearTimers]);

  const stopBrowserCamera = useCallback(() => {
    stopStream(activeStreamRef.current);
    activeStreamRef.current = null;
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
    setRemoteFrame(null);
    setRecognitionData({ status: 'Starting camera...', color: '#888' });
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
    setRemoteFrame(null);
    setEnrollData({ status: 'Starting camera...', color: '#888', progress: 0 });
    setIsEnrolling(true);
  }, [closeSocket]);

  const stopEnroll = useCallback(() => {
    setIsEnrolling(false);
    setRemoteFrame(null);
  }, []);

  // Browser capture is lazy and active only while recognition/enrollment runs.
  useEffect(() => {
    if (source !== 'browser' || activeMode === null) {
      stopBrowserCamera();
      hiddenVideoRef.current = null;
      canvasRef.current = null;
      return;
    }

    let disposed = false;
    const hiddenVideo = document.createElement('video');
    hiddenVideo.autoplay = true;
    hiddenVideo.playsInline = true;
    hiddenVideo.muted = true;
    hiddenVideoRef.current = hiddenVideo;
    canvasRef.current = document.createElement('canvas');

    if (!navigator.mediaDevices?.getUserMedia) {
      const status = 'Camera API is unavailable. Use HTTPS or backend camera mode.';
      if (activeMode === 'enroll') {
        setEnrollData(previous => ({ ...previous, status, color: '#f00' }));
      } else {
        setRecognitionData({ status, color: '#f00' });
      }
      return () => {
        disposed = true;
      };
    }

    navigator.mediaDevices.getUserMedia({
      video: { width: { ideal: 1280 }, height: { ideal: 720 } },
      audio: false,
    }).then(cameraStream => {
      if (disposed) {
        stopStream(cameraStream);
        return;
      }
      activeStreamRef.current = cameraStream;
      hiddenVideo.srcObject = cameraStream;
      setStream(cameraStream);
      hiddenVideo.play().catch(() => undefined);
    }).catch(error => {
      if (disposed) return;
      const status = `Error accessing camera: ${error instanceof Error ? error.message : String(error)}`;
      if (activeModeRef.current === 'enroll') {
        setEnrollData(previous => ({ ...previous, status, color: '#f00' }));
      } else {
        setRecognitionData({ status, color: '#f00' });
      }
    });

    return () => {
      disposed = true;
      if (hiddenVideoRef.current === hiddenVideo) hiddenVideoRef.current = null;
      hiddenVideo.srcObject = null;
      stopBrowserCamera();
      canvasRef.current = null;
    };
  }, [activeMode, source, stopBrowserCamera]);

  useEffect(() => {
    closeSocket();
    if (activeMode === null) return;
    if (source === 'browser' && !stream) return;

    const token = getValidAuthToken();
    if (!token) {
      invalidateAuth();
      return;
    }

    const enrollMode = activeMode === 'enroll';
    const endpoint = websocketUrl(enrollMode ? '/ws/enroll' : '/ws/recognize');
    const protocols = websocketAuthProtocols(token);
    const minimumInterval = enrollMode ? 200 : 100;
    let disposed = false;
    let finished = false;
    let fatalResponse = false;
    let activeSocket: WebSocket | null = null;
    let reconnectAttempts = 0;
    let awaitingResponse = false;
    let pendingBrowserFrame: string | null = null;

    const setFailure = (status: string) => {
      if (enrollMode) {
        setEnrollData(previous => ({ ...previous, status, color: '#f00', box: undefined }));
      } else {
        setRecognitionData({ status, color: '#f00' });
      }
    };

    const stopOperation = () => {
      setRemoteFrame(null);
      if (enrollMode) setIsEnrolling(false);
      else setIsRecognizing(false);
    };

    const scheduleBrowserFrame = (socket: WebSocket, delay: number) => {
      if (source !== 'browser' || disposed || finished) return;
      if (captureTimerRef.current !== null) window.clearTimeout(captureTimerRef.current);
      captureTimerRef.current = window.setTimeout(() => {
        captureTimerRef.current = null;
        if (disposed || finished || activeSocket !== socket || socket.readyState !== WebSocket.OPEN) return;
        // At most one frame may be in flight: this prevents a browser/network backlog.
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
        if (!context) return;
        context.drawImage(video, 0, 0, canvas.width, canvas.height);
        pendingBrowserFrame = canvas.toDataURL('image/jpeg', 0.5);
        awaitingResponse = true;
        socket.send(pendingBrowserFrame);
      }, delay);
    };

    const connect = () => {
      if (disposed || finished) return;
      const socket = new WebSocket(endpoint, protocols);
      activeSocket = socket;
      wsRef.current = socket;
      awaitingResponse = false;
      pendingBrowserFrame = null;

      socket.onopen = () => scheduleBrowserFrame(socket, 0);
      socket.onmessage = event => {
        if (disposed || finished || activeSocket !== socket) return;
        awaitingResponse = false;
        let data: Record<string, unknown>;
        try {
          data = JSON.parse(String(event.data)) as Record<string, unknown>;
        } catch {
          setFailure('Invalid response from camera service');
          scheduleBrowserFrame(socket, minimumInterval);
          return;
        }

        reconnectAttempts = 0;
        fatalResponse = data.fatal === true;
        if (source === 'backend' && typeof data.frame === 'string') {
          setRemoteFrame(data.frame);
        } else if (source === 'browser' && pendingBrowserFrame) {
          // This exact JPEG produced the returned bbox and dimensions.
          setRemoteFrame(pendingBrowserFrame);
          pendingBrowserFrame = null;
        }
        const box = parseBBox(data.box);
        const frameWidth = positiveNumber(data.frame_width);
        const frameHeight = positiveNumber(data.frame_height);
        const status = typeof data.status === 'string' ? data.status : 'Processing...';
        const color = typeof data.color === 'string' ? data.color : '#888';

        if (enrollMode) {
          if (status === 'Finished') {
            finished = true;
            const embedding = Array.isArray(data.embedding)
              && data.embedding.every(value => typeof value === 'number' && Number.isFinite(value))
              ? data.embedding as number[]
              : undefined;
            setEnrollData(previous => ({
              ...previous,
              status: embedding ? 'Face data collected! Please fill the form.' : 'Invalid enrollment result',
              color: embedding ? '#00FF00' : '#f00',
              progress: embedding ? 1 : previous.progress,
              embedding,
              box: undefined,
              frameWidth,
              frameHeight,
            }));
            socket.close(1000, 'Enrollment finished');
            setIsEnrolling(false);
            return;
          }
          const progress = typeof data.progress === 'number' ? data.progress : 0;
          setEnrollData(previous => ({
            status,
            color,
            progress: Math.max(0, Math.min(1, progress)),
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
          stopOperation();
          socket.close(1000, 'Fatal camera error');
          return;
        }
        scheduleBrowserFrame(socket, minimumInterval);
      };

      socket.onclose = event => {
        if (wsRef.current === socket) wsRef.current = null;
        if (activeSocket === socket) activeSocket = null;
        if (disposed || finished || fatalResponse) return;
        if (AUTH_CLOSE_CODES.has(event.code)) {
          setFailure('Authentication rejected. Please sign in again.');
          stopOperation();
          invalidateAuth();
          return;
        }
        if (FATAL_CLOSE_CODES.has(event.code) || event.code === 1000) {
          setFailure('Camera service closed. Retry the operation.');
          stopOperation();
          return;
        }
        if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
          setFailure('Camera connection failed. Retry the operation.');
          stopOperation();
          return;
        }
        const delay = Math.min(500 * 2 ** reconnectAttempts, 4000);
        reconnectAttempts += 1;
        reconnectTimerRef.current = window.setTimeout(connect, delay);
      };
    };

    connect();
    return () => {
      disposed = true;
      clearTimers();
      pendingBrowserFrame = null;
      const socket = activeSocket;
      activeSocket = null;
      if (wsRef.current === socket) wsRef.current = null;
      if (socket && socket.readyState < WebSocket.CLOSING) {
        socket.close(1000, 'Operation changed');
      }
    };
  }, [activeMode, clearTimers, closeSocket, source, stream]);

  useEffect(() => () => {
    clearTimers();
    const socket = wsRef.current;
    if (socket && socket.readyState < WebSocket.CLOSING) socket.close();
    stopStream(activeStreamRef.current);
  }, [clearTimers]);

  const value = useMemo(() => ({
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

// oxlint-disable-next-line react/only-export-components
export function useCamera() {
  const context = useContext(CameraContext);
  if (!context) throw new Error('useCamera must be used within CameraProvider');
  return context;
}
