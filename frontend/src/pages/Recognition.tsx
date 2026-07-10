import { useEffect, useRef } from 'react';
import { useCamera } from '../context/CameraContext';
import { Play, Square } from 'lucide-react';

export default function Recognition() {
  const { stream, isRecognizing, startRecognition, stopRecognition, recognitionData } = useCamera();
  const videoRef = useRef<HTMLVideoElement>(null);
  
  useEffect(() => {
    if (videoRef.current && stream) {
      videoRef.current.srcObject = stream;
    }
  }, [stream]);

  const { status, color, name, similarity } = recognitionData;

  return (
    <div className="page-container" style={{ textAlign: 'center' }}>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2>Live Recognition</h2>
        <div style={{ display: 'flex', gap: '1rem' }}>
          {!isRecognizing ? (
            <button className="btn btn-primary" onClick={startRecognition} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Play size={16} /> Start Recognition
            </button>
          ) : (
            <button className="btn" onClick={stopRecognition} style={{ background: '#ef4444', color: 'white', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Square size={16} /> Stop Recognition
            </button>
          )}
        </div>
      </div>
      
      <div className="camera-container">
        {stream ? (
          <video ref={videoRef} autoPlay playsInline muted className="camera-feed" />
        ) : (
          <div style={{ height: 480, display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#222', borderRadius: '12px' }}>
            <p>Camera not connected</p>
          </div>
        )}
        
        {isRecognizing && (
          <div className="camera-overlay" style={{ borderColor: color }}>
            <div className="status-indicator" style={{ color }}>{status}</div>
            {name && (
              <div className="status-details">
                <strong>Name:</strong> {name} <br/>
                <strong>Similarity:</strong> {similarity}
              </div>
            )}
          </div>
        )}
      </div>
      
      {isRecognizing && (
        <p style={{ marginTop: '1rem', color: '#888' }}>
          Background recognition is active. You can navigate to other pages and the camera will keep working.
        </p>
      )}
    </div>
  );
}
