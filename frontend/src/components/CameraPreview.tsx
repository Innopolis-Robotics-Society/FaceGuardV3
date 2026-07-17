import { useEffect, useMemo, useRef, useState } from 'react';
import type { ReactNode } from 'react';
import type { BBox, ObjectFit } from '../camera/projectBBox';
import { projectBBox } from '../camera/projectBBox';
import type { CameraSource } from '../context/CameraContext';

interface CameraPreviewProps {
  cameraSource: CameraSource;
  stream: MediaStream | null;
  remoteFrame: string | null;
  box?: BBox;
  frameWidth?: number;
  frameHeight?: number;
  boxColor?: string;
  fit?: ObjectFit;
  placeholder: string;
  children?: ReactNode;
}

export default function CameraPreview({
  cameraSource,
  stream,
  remoteFrame,
  box,
  frameWidth,
  frameHeight,
  boxColor = '#00FF00',
  fit = 'cover',
  placeholder,
  children,
}: CameraPreviewProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const [containerSize, setContainerSize] = useState({ width: 0, height: 0 });
  const [mediaSize, setMediaSize] = useState({ width: 0, height: 0 });

  useEffect(() => {
    const video = videoRef.current;
    if (!video || cameraSource !== 'browser' || remoteFrame) return;
    video.srcObject = stream;
    return () => {
      video.srcObject = null;
    };
  }, [cameraSource, remoteFrame, stream]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    const update = (width: number, height: number) => setContainerSize({ width, height });
    const bounds = container.getBoundingClientRect();
    update(bounds.width, bounds.height);
    if (typeof ResizeObserver === 'undefined') return;
    const observer = new ResizeObserver(entries => {
      const entry = entries[0];
      if (entry) update(entry.contentRect.width, entry.contentRect.height);
    });
    observer.observe(container);
    return () => observer.disconnect();
  }, []);

  const updateVideoSize = () => {
    const video = videoRef.current;
    if (video?.videoWidth && video.videoHeight) {
      setMediaSize({ width: video.videoWidth, height: video.videoHeight });
    }
  };

  const projection = useMemo(() => {
    if (!box) return null;
    return projectBBox({
      box,
      frameWidth: frameWidth || mediaSize.width,
      frameHeight: frameHeight || mediaSize.height,
      containerWidth: containerSize.width,
      containerHeight: containerSize.height,
      fit,
      mirrored: cameraSource === 'browser',
    });
  }, [box, cameraSource, containerSize, fit, frameHeight, frameWidth, mediaSize]);

  const hasPreview = Boolean(remoteFrame) || (cameraSource === 'browser' && Boolean(stream));
  return (
    <div className="camera-container" ref={containerRef}>
      {remoteFrame ? (
        <img
          src={remoteFrame}
          alt={cameraSource === 'backend'
            ? 'Raspberry Pi camera preview'
            : 'Browser camera processed frame'}
          className={`camera-feed ${cameraSource === 'browser' ? 'camera-feed--mirrored' : ''}`}
          style={{ objectFit: fit }}
          onLoad={event => setMediaSize({
            width: event.currentTarget.naturalWidth,
            height: event.currentTarget.naturalHeight,
          })}
        />
      ) : cameraSource === 'browser' && stream ? (
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          className="camera-feed camera-feed--mirrored"
          style={{ objectFit: fit }}
          onLoadedMetadata={updateVideoSize}
          onResize={updateVideoSize}
        />
      ) : (
        <div className="camera-placeholder"><p>{placeholder}</p></div>
      )}

      {hasPreview && projection && (
        <div
          className="face-box"
          data-testid="face-box"
          style={{
            borderColor: boxColor,
            left: projection.left,
            top: projection.top,
            width: projection.width,
            height: projection.height,
          }}
        />
      )}
      {children}
    </div>
  );
}
