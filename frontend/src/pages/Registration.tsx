import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AlertCircle } from 'lucide-react';

export default function Registration() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const navigate = useNavigate();
  
  const [status, setStatus] = useState('Initializing camera...');
  const [color, setColor] = useState('#888');
  const [progress, setProgress] = useState(0);
  const [embedding, setEmbedding] = useState<number[] | null>(null);
  const [box, setBox] = useState<number[] | null>(null);
  
  const [name, setName] = useState('');
  const [accessType, setAccessType] = useState('Permanent');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  // Current time truncated to minutes for min attribute
  const minDateTime = new Date();
  const pad = (n: number) => n.toString().padStart(2, '0');
  const minDateTimeStr = `${minDateTime.getFullYear()}-${pad(minDateTime.getMonth()+1)}-${pad(minDateTime.getDate())}T${pad(minDateTime.getHours())}:${pad(minDateTime.getMinutes())}`;

  useEffect(() => {
    navigator.mediaDevices.getUserMedia({ video: { width: 1280, height: 720 }, audio: false })
      .then(stream => {
        if (videoRef.current) videoRef.current.srcObject = stream;
      })
      .catch(err => setStatus('Error accessing camera: ' + err.message));

    const connectWs = () => {
      wsRef.current = new WebSocket('ws://localhost:8000/ws/enroll');
      wsRef.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.status === 'Finished') {
          setEmbedding(data.embedding);
          setStatus('Face data collected! Please fill the form.');
          setColor('#00FF00');
          setBox(null);
          wsRef.current?.close();
        } else {
          setStatus(data.status);
          setColor(data.color);
          setProgress(data.progress || 0);
          setBox(data.box || null);
        }
      };
    };
    connectWs();

    const interval = setInterval(() => {
      if (embedding) return; // Stop sending if finished
      if (videoRef.current && canvasRef.current && wsRef.current?.readyState === WebSocket.OPEN) {
        const video = videoRef.current;
        const canvas = canvasRef.current;
        if (video.videoWidth > 0) {
          canvas.width = video.videoWidth;
          canvas.height = video.videoHeight;
          const ctx = canvas.getContext('2d');
          if (ctx) {
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
            wsRef.current.send(canvas.toDataURL('image/jpeg', 0.5));
          }
        }
      }
    }, 300);

    return () => {
      clearInterval(interval);
      wsRef.current?.close();
      const stream = videoRef.current?.srcObject as MediaStream;
      stream?.getTracks().forEach(t => t.stop());
    };
  }, [embedding]);

  const handleSave = () => {
    setErrorMsg('');
    if (!name) {
      setErrorMsg('Please enter a name.');
      return;
    }
    
    let finalStart = null;
    let finalEnd = null;
    if (accessType === 'Temporary') {
      if (!startDate || !endDate) {
        setErrorMsg('Please enter both start and expiration dates.');
        return;
      }
      
      const startDt = new Date(startDate);
      const endDt = new Date(endDate);
      const now = new Date();
      now.setSeconds(0, 0);
      
      if (startDt < now) {
        setErrorMsg('Start time cannot be in the past.');
        return;
      }
      if (endDt <= startDt) {
        setErrorMsg('Expiration time must be at least 1 minute after start time.');
        return;
      }
      
      const pad = (n: number) => n.toString().padStart(2, '0');
      const getLocalISO = (d: Date) => `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}:00.000`;
      
      finalStart = getLocalISO(startDt);
      finalEnd = getLocalISO(endDt);
    }

    fetch('http://localhost:8000/api/employees', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name,
        status: accessType,
        embedding,
        start_date: finalStart,
        expiration_date: finalEnd
      })
    }).then(async res => {
      if (res.ok) {
        navigate('/employees');
      } else {
        const data = await res.json();
        setErrorMsg(data.detail || 'Failed to save employee.');
      }
    }).catch(() => {
      setErrorMsg('Network error occurred.');
    });
  };

  return (
    <div className="page-container" style={{ maxWidth: 800, margin: '0 auto' }}>
      <div className="page-header">
        <h2>Add Employee</h2>
      </div>
      
      {!embedding ? (
        <div className="camera-container">
          <video ref={videoRef} autoPlay playsInline muted className="camera-feed" />
          <canvas ref={canvasRef} style={{ display: 'none' }} />
          
          {box && videoRef.current && (
            <div style={{
              position: 'absolute',
              border: `2px solid ${color}`,
              borderRadius: '8px',
              left: `${(1 - box[2] / videoRef.current.videoWidth) * 100}%`,
              top: `${(box[1] / videoRef.current.videoHeight) * 100}%`,
              width: `${((box[2] - box[0]) / videoRef.current.videoWidth) * 100}%`,
              height: `${((box[3] - box[1]) / videoRef.current.videoHeight) * 100}%`,
              transition: 'all 0.1s ease',
              pointerEvents: 'none'
            }} />
          )}

          <div className="camera-overlay" style={{ borderColor: color }}>
            <div className="status-indicator" style={{ color }}>{status}</div>
            <div style={{ width: '100%', background: 'rgba(255,255,255,0.2)', height: '4px', marginTop: '8px' }}>
              <div style={{ width: `${progress * 100}%`, background: color, height: '100%', transition: 'width 0.3s' }} />
            </div>
          </div>
        </div>
      ) : (
        <div className="glass-panel">
          <div className="form-group">
            <label>Name</label>
            <input className="form-control" value={name} onChange={e => setName(e.target.value)} placeholder="Ivan Ivanov" />
          </div>
          
          <div className="form-group">
            <label>Access Type</label>
            <select className="form-control" value={accessType} onChange={e => setAccessType(e.target.value)}>
              <option value="Permanent">Permanent</option>
              <option value="Temporary">Temporary</option>
            </select>
          </div>

          {accessType === 'Temporary' && (
            <div style={{ display: 'flex', gap: '1rem' }}>
              <div className="form-group" style={{ flex: 1 }}>
                <label>Start Date & Time</label>
                <input 
                  type="datetime-local" 
                  className="form-control" 
                  min={minDateTimeStr}
                  value={startDate} 
                  onChange={e => setStartDate(e.target.value)} 
                  onKeyDown={e => e.preventDefault()}
                />
              </div>
              <div className="form-group" style={{ flex: 1 }}>
                <label>Expiration Date & Time</label>
                <input 
                  type="datetime-local" 
                  className="form-control" 
                  min={startDate || minDateTimeStr}
                  value={endDate} 
                  onChange={e => setEndDate(e.target.value)} 
                  onKeyDown={e => e.preventDefault()}
                />
              </div>
            </div>
          )}

          {errorMsg && (
            <div style={{
              background: 'rgba(239, 68, 68, 0.15)',
              borderLeft: '4px solid #ef4444',
              color: '#fca5a5',
              padding: '1rem',
              borderRadius: '6px',
              marginTop: '1rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem'
            }}>
              <AlertCircle size={20} />
              <span>{errorMsg}</span>
            </div>
          )}

          <button className="btn btn-primary" onClick={handleSave} style={{ width: '100%', marginTop: '1.5rem' }}>
            Save Employee
          </button>
        </div>
      )}
    </div>
  );
}
