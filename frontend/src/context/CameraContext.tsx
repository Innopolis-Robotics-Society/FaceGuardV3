import { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react';
import type { ReactNode } from 'react';

export type CameraSource = 'browser' | 'backend';

type RecognitionData = { status: string; color: string; name?: string; similarity?: string };
type EnrollData = { status: string; color: string; progress: number; embedding?: number[]; box?: number[] };

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
}

const configuredCameraSource = (import.meta.env.VITE_CAMERA_SOURCE || 'browser').toLowerCase();
const cameraSource: CameraSource = configuredCameraSource === 'backend' ? 'backend' : 'browser';

const defaultRecData = { status: 'Idle', color: '#888' };
const defaultEnrollData = { status: 'Idle', color: '#888', progress: 0 };

const CameraContext = createContext<CameraContextType | null>(null);

function websocketUrl(path: string, token: string) {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const hostname = window.location.hostname || 'localhost';
  return `${protocol}//${hostname}:8000${path}?token=${encodeURIComponent(token)}`;
}

export function CameraProvider({ children }: { children: ReactNode }) {
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [remoteFrame, setRemoteFrame] = useState<string | null>(null);
  const [isRecognizing, setIsRecognizing] = useState(false);
  const [isEnrolling, setIsEnrolling] = useState(false);

  const [recognitionData, setRecognitionData] = useState<RecognitionData>(defaultRecData);
  const [enrollData, setEnrollData] = useState<EnrollData>(defaultEnrollData);

  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const intervalRef = useRef<number | null>(null);

  // Browser mode keeps the existing WebRTC capture path. Backend mode never asks
  // the remote laptop for camera permission.
  useEffect(() => {
    if (cameraSource === 'backend') return;

    videoRef.current = document.createElement('video');
    videoRef.current.autoplay = true;
    videoRef.current.playsInline = true;
    videoRef.current.muted = true;

    canvasRef.current = document.createElement('canvas');

    navigator.mediaDevices.getUserMedia({ video: { width: 1280, height: 720 }, audio: false })
      .then(s => {
        setStream(s);
        if (videoRef.current) {
          videoRef.current.srcObject = s;
        }
      })
      .catch(err => {
        setRecognitionData({ status: 'Error accessing camera: ' + err.message, color: '#f00' });
        console.error('Camera access error:', err);
      });

    return () => {
      if (videoRef.current?.srcObject) {
        const activeStream = videoRef.current.srcObject as MediaStream;
        activeStream.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  // Keep one socket and, in browser mode, one capture interval for the active
  // operation. Enrollment takes precedence over background recognition.
  useEffect(() => {
    if (!isRecognizing && !isEnrolling) {
      setRecognitionData(defaultRecData);
      setEnrollData(defaultEnrollData);
      setRemoteFrame(null);
      return;
    }
    if (cameraSource === 'browser' && !stream) return;

    const isEnrollMode = isEnrolling;
    const token = localStorage.getItem('auth_token') || '';
    const endpoint = websocketUrl(isEnrollMode ? '/ws/enroll' : '/ws/recognize', token);
    const intervalTime = isEnrollMode ? 300 : 200;

    setRemoteFrame(null);
    if (isEnrollMode) {
      setEnrollData({ status: 'Initializing camera...', color: '#888', progress: 0 });
    } else {
      setRecognitionData({ status: 'Connecting...', color: '#888' });
    }

    let activeWs: WebSocket | null = null;
    let reconnectTimeout: number | null = null;
    let isDisposed = false;
    let isFinished = false;

    const clearCaptureInterval = () => {
      if (intervalRef.current !== null) {
        window.clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };

    const startCaptureInterval = (socket: WebSocket) => {
      if (cameraSource === 'backend') return;
      clearCaptureInterval();
      intervalRef.current = window.setInterval(() => {
        if (isDisposed || isFinished || socket.readyState !== WebSocket.OPEN) return;

        const video = videoRef.current;
        const canvas = canvasRef.current;
        if (!video || !canvas || video.videoWidth <= 0) return;

        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        const context = canvas.getContext('2d');
        if (!context) return;

        context.drawImage(video, 0, 0, canvas.width, canvas.height);
        socket.send(canvas.toDataURL('image/jpeg', 0.5));
      }, intervalTime);
    };

    const connectWs = () => {
      if (isDisposed || isFinished) return;

      const socket = new WebSocket(endpoint);
      activeWs = socket;
      wsRef.current = socket;

      socket.onopen = () => startCaptureInterval(socket);

      socket.onmessage = event => {
        const data = JSON.parse(event.data);
        if (data.frame) setRemoteFrame(data.frame);

        if (isEnrollMode) {
          if (data.status === 'Finished') {
            isFinished = true;
            setEnrollData(previous => ({
              ...previous,
              status: 'Face data collected! Please fill the form.',
              color: '#00FF00',
              embedding: data.embedding,
              box: undefined,
            }));
            clearCaptureInterval();
            socket.close();
          } else {
            setEnrollData({
              status: data.status,
              color: data.color,
              progress: data.progress ?? 0,
              box: data.box ?? undefined,
            });
          }
        } else {
          setRecognitionData({
            status: data.status,
            color: data.color,
            name: data.name,
            similarity: data.similarity,
          });
        }
      };

      socket.onclose = () => {
        if (wsRef.current === socket) wsRef.current = null;
        if (activeWs === socket) activeWs = null;
        clearCaptureInterval();
        if (!isDisposed && !isFinished) {
          reconnectTimeout = window.setTimeout(connectWs, 2000);
        }
      };
    };

    connectWs();

    return () => {
      isDisposed = true;
      if (reconnectTimeout !== null) window.clearTimeout(reconnectTimeout);
      clearCaptureInterval();
      if (activeWs) activeWs.close();
      if (wsRef.current === activeWs) wsRef.current = null;
    };
  }, [isRecognizing, isEnrolling, stream]);

  const startRecognition = useCallback(() => {
    setRemoteFrame(null);
    setIsRecognizing(true);
  }, []);
  const stopRecognition = useCallback(() => {
    setRemoteFrame(null);
    setIsRecognizing(false);
  }, []);
  const startEnroll = useCallback(() => {
    setRemoteFrame(null);
    setIsEnrolling(true);
  }, []);
  const stopEnroll = useCallback(() => {
    setRemoteFrame(null);
    setIsEnrolling(false);
  }, []);

  const value = {
    cameraSource,
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
  };

  return <CameraContext.Provider value={value}>{children}</CameraContext.Provider>;
}

export function useCamera() {
  const context = useContext(CameraContext);
  if (!context) {
    throw new Error('useCamera must be used within CameraProvider');
  }
  return context;
}
