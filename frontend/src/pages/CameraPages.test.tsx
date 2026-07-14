import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { useCamera } from '../context/CameraContext';
import Recognition from './Recognition';
import Registration from './Registration';

vi.mock('../context/CameraContext', () => ({ useCamera: vi.fn() }));

const mockedUseCamera = vi.mocked(useCamera);

function cameraValue() {
  return {
    cameraSource: 'backend' as const,
    stream: null,
    remoteFrame: 'data:image/jpeg;base64,Y2FtZXJh',
    isRecognizing: true,
    startRecognition: vi.fn(),
    stopRecognition: vi.fn(),
    recognitionData: {
      status: 'Access Granted',
      color: '#00FF00',
      box: [64, 96, 192, 240] as [number, number, number, number],
      frameWidth: 640,
      frameHeight: 480,
    },
    isEnrolling: true,
    startEnroll: vi.fn(),
    stopEnroll: vi.fn(),
    enrollData: {
      status: 'Collecting: 1/30',
      color: '#00FF00',
      progress: 1 / 30,
      box: [64, 96, 192, 240] as [number, number, number, number],
      frameWidth: 640,
      frameHeight: 480,
    },
    resetCamera: vi.fn(),
  };
}

afterEach(() => vi.clearAllMocks());

describe('camera pages', () => {
  it('renders a bbox on Recognition in backend mode', async () => {
    mockedUseCamera.mockReturnValue(cameraValue());
    render(<Recognition />);
    expect(await waitFor(() => screen.getByTestId('face-box'))).toBeInTheDocument();
  });

  it('renders a bbox on Registration in backend mode', async () => {
    mockedUseCamera.mockReturnValue(cameraValue());
    render(
      <MemoryRouter>
        <Registration />
      </MemoryRouter>,
    );
    expect(await waitFor(() => screen.getByTestId('face-box'))).toBeInTheDocument();
  });

  it('keeps a fatal recognition error visible after the operation stops', () => {
    const value = cameraValue();
    mockedUseCamera.mockReturnValue({
      ...value,
      remoteFrame: null,
      isRecognizing: false,
      recognitionData: {
        status: 'Camera service closed with a fatal error.',
        color: '#f00',
      },
    });

    render(<Recognition />);
    expect(screen.getByText('Camera service closed with a fatal error.'))
      .toBeInTheDocument();
  });
});
