import { useEffect, useRef, useState } from 'react';

export default function Recognition() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  
  const [status, setStatus] = useState('Initializing camera...');
  const [color, setColor] = useState('#888');
  const [name, setName] = useState('-');
  const [similarity, setSimilarity] = useState('-');
  
  useEffect(() => {
    // Start Camera
    navigator.mediaDevices.getUserMedia({ video: { width: 1280, height: 720 }, audio: false })
      .then(stream => {
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }
      })
      .catch(err => setStatus('Error accessing camera: ' + err.message));

    // Connect WebSocket
    const connectWs = () => {
      wsRef.current = new WebSocket('ws://localhost:8000/ws/recognize');
      wsRef.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        setStatus(data.status);
        setColor(data.color);
        setName(data.name || '-');
        setSimilarity(data.similarity || '-');
      };
      wsRef.current.onclose = () => {
        setTimeout(connectWs, 2000); // Reconnect
      };
    };
    connectWs();

    // Frame capture loop
    const interval = setInterval(() => {
      if (videoRef.current && canvasRef.current && wsRef.current?.readyState === WebSocket.OPEN) {
        const video = videoRef.current;
        const canvas = canvasRef.current;
        if (video.videoWidth > 0) {
          canvas.width = video.videoWidth;
          canvas.height = video.videoHeight;
          const ctx = canvas.getContext('2d');
          if (ctx) {
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
            const base64 = canvas.toDataURL('image/jpeg', 0.5); // compress
            wsRef.current.send(base64);
          }
        }
      }
    }, 200); // 5 FPS

    return () => {
      clearInterval(interval);
      wsRef.current?.close();
      const stream = videoRef.current?.srcObject as MediaStream;
      stream?.getTracks().forEach(t => t.stop());
    };
  }, []);

  return (
    <div className="page-container" style={{ textAlign: 'center' }}>
      <div className="page-header">
        <h2>Live Recognition</h2>
      </div>
      
      <div className="camera-container">
        <video ref={videoRef} autoPlay playsInline muted className="camera-feed" />
        <canvas ref={canvasRef} style={{ display: 'none' }} />
        
        <div className="camera-overlay" style={{ borderColor: color }}>
          <div className="status-indicator" style={{ color }}>{status}</div>
          <div className="status-details">
            <strong>Name:</strong> {name} <br/>
            <strong>Similarity:</strong> {similarity}
          </div>
        </div>
      </div>
    </div>
  );
}
