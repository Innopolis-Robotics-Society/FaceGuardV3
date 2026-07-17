import { Play, Square } from 'lucide-react';
import CameraPreview from '../components/CameraPreview';
import { useCamera } from '../context/CameraContext';

export default function Recognition() {
  const {
    cameraSource,
    stream,
    remoteFrame,
    isRecognizing,
    startRecognition,
    stopRecognition,
    recognitionData,
  } = useCamera();
  const { status, color, name, similarity, box, frameWidth, frameHeight } = recognitionData;

  const placeholder = cameraSource === 'backend'
    ? isRecognizing
      ? 'Connecting to Raspberry Pi camera...'
      : status === 'Idle' ? 'Start recognition to view the camera' : status
    : isRecognizing
      ? 'Connecting to browser camera...'
      : status === 'Idle' ? 'Start recognition to view the camera' : status;

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

      <CameraPreview
        cameraSource={cameraSource}
        stream={stream}
        remoteFrame={remoteFrame}
        box={isRecognizing ? box : undefined}
        frameWidth={frameWidth}
        frameHeight={frameHeight}
        boxColor={color}
        placeholder={placeholder}
      >
        {isRecognizing && (
          <div className="camera-overlay" style={{ borderColor: color }}>
            <div className="status-indicator" style={{ color }}>{status}</div>
            {name && (
              <div className="status-details">
                <strong>Name:</strong> {name} <br />
                <strong>Similarity:</strong> {similarity}
              </div>
            )}
          </div>
        )}
      </CameraPreview>

      {isRecognizing && (
        <p style={{ marginTop: '1rem', color: '#888' }}>
          Background recognition is active. You can navigate to other pages and the camera will keep working.
        </p>
      )}
    </div>
  );
}
