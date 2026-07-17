import { render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import CameraPreview from './CameraPreview';

describe('CameraPreview', () => {
  it('renders a backend JPEG without mirroring and projects its bbox', async () => {
    render(
      <CameraPreview
        cameraSource="backend"
        stream={null}
        remoteFrame="data:image/jpeg;base64,Y2FtZXJh"
        box={[64, 96, 192, 240]}
        frameWidth={640}
        frameHeight={480}
        placeholder="waiting"
      />,
    );

    const image = screen.getByRole('img');
    expect(image).not.toHaveClass('camera-feed--mirrored');
    const box = await waitFor(() => screen.getByTestId('face-box'));
    expect(box).toHaveStyle({ left: '80px', top: '45px', width: '160px', height: '180px' });
  });

  it('renders the processed browser snapshot and mirrors both image and bbox', async () => {
    render(
      <CameraPreview
        cameraSource="browser"
        stream={{} as MediaStream}
        remoteFrame="data:image/jpeg;base64,Y2FtZXJh"
        box={[64, 96, 192, 240]}
        frameWidth={640}
        frameHeight={480}
        placeholder="waiting"
      />,
    );

    const image = screen.getByRole('img');
    expect(image).toHaveClass('camera-feed--mirrored');
    const box = await waitFor(() => screen.getByTestId('face-box'));
    expect(box).toHaveStyle({ left: '560px', top: '45px', width: '160px', height: '180px' });
  });
});
