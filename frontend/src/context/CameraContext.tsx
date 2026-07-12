import { createContext, useContext, useEffect, useRef, useState } from 'react';
import type { ReactNode } from 'react';

type RecognitionData = { status: string; color: string; name?: string; similarity?: string };
type EnrollData = { status: string; color: string; progress: number; embedding?: number[]; box?: number[] };

interface CameraContextType {
  stream: MediaStream | null;
  
  isRecognizing: boolean;
  startRecognition: () => void;
  stopRecognition: () => void;
  recognitionData: RecognitionData;
  
  isEnrolling: boolean;
  startEnroll: () => void;
  stopEnroll: () => void;
  enrollData: EnrollData;
}

const defaultRecData = { status: 'Idle', color: '#888' };
const defaultEnrollData = { status: 'Idle', color: '#888', progress: 0 };

const CameraContext = createContext<CameraContextType | null>(null);

export function CameraProvider({ children }: { children: ReactNode }) {
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [isRecognizing, setIsRecognizing] = useState(false);
  const [isEnrolling, setIsEnrolling] = useState(false);
  
  const [recognitionData, setRecognitionData] = useState<RecognitionData>(defaultRecData);
  const [enrollData, setEnrollData] = useState<EnrollData>(defaultEnrollData);
  
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const intervalRef = useRef<number | null>(null);

  // Initialize camera and hidden elements
  useEffect(() => {
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
        console.error("Camera access error:", err);
      });
      
    return () => {
      if (wsRef.current) wsRef.current.close();
      if (intervalRef.current) clearInterval(intervalRef.current);
      if (videoRef.current && videoRef.current.srcObject) {
        const s = videoRef.current.srcObject as MediaStream;
        s.getTracks().forEach(t => t.stop());
      }
    };
  }, []);

  // Connection and capturing logic
  useEffect(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    if (!stream) return;
    if (!isRecognizing && !isEnrolling) {
      setRecognitionData(defaultRecData);
      setEnrollData(defaultEnrollData);
      return;
    }

    const isEnrollMode = isEnrolling; // enrollment takes precedence
    const token = localStorage.getItem('auth_token') || '';
    const endpoint = isEnrollMode ? `ws://localhost:8000/ws/enroll?token=${token}` : `ws://localhost:8000/ws/recognize?token=${token}`;
    const intervalTime = isEnrollMode ? 300 : 200;

    if (isEnrollMode) {
      setEnrollData({ status: 'Initializing camera...', color: '#888', progress: 0 });
    } else {
      setRecognitionData({ status: 'Connecting...', color: '#888' });
    }

    let activeWs: WebSocket | null = null;
    let isFinished = false;

    const connectWs = () => {
      if (isFinished) return;
      
      activeWs = new WebSocket(endpoint);
      wsRef.current = activeWs;

      activeWs.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (isEnrollMode) {
          if (data.status === 'Finished') {
            isFinished = true;
            setEnrollData(prev => ({ 
              ...prev, 
              status: 'Face data collected! Please fill the form.', 
              color: '#00FF00', 
              embedding: data.embedding, 
              box: undefined 
            }));
            activeWs?.close();
            activeWs = null;
          } else {
            setEnrollData({ status: data.status, color: data.color, progress: data.progress || 0, box: data.box || undefined });
          }
        } else {
          setRecognitionData({ status: data.status, color: data.color, name: data.name, similarity: data.similarity });
        }
      };
      
      activeWs.onclose = () => {
        if (!isFinished && activeWs !== null) {
          setTimeout(connectWs, 2000);
        }
      };
    };
    
    connectWs();

    // Frame capture loop
    intervalRef.current = window.setInterval(() => {
      if (isFinished) return;
      if (activeWs?.readyState !== WebSocket.OPEN) return;
      
      if (videoRef.current && canvasRef.current) {
        const video = videoRef.current;
        const canvas = canvasRef.current;
        if (video.videoWidth > 0) {
          canvas.width = video.videoWidth;
          canvas.height = video.videoHeight;
          const ctx = canvas.getContext('2d');
          if (ctx) {
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
            const base64 = canvas.toDataURL('image/jpeg', 0.5);
            activeWs.send(base64);
          }
        }
      }
    }, intervalTime);

    return () => {
      isFinished = true;
      if (activeWs) {
        activeWs.close();
        activeWs = null;
      }
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [isRecognizing, isEnrolling, stream]);

  const value = {
    stream,
    isRecognizing,
    startRecognition: () => setIsRecognizing(true),
    stopRecognition: () => setIsRecognizing(false),
    recognitionData,
    isEnrolling,
    startEnroll: () => setIsEnrolling(true),
    stopEnroll: () => setIsEnrolling(false),
    enrollData
  };

  return <CameraContext.Provider value={value}>{children}</CameraContext.Provider>;
}

export function useCamera() {
  const context = useContext(CameraContext);
  if (!context) {
    throw new Error("useCamera must be used within CameraProvider");
  }
  return context;
}
