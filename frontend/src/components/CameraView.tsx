import { useRef, useCallback } from 'react';
import Webcam from 'react-webcam';

interface CameraViewProps {
  onCapture: (imageBase64: string) => void;
  loading: boolean;
}

const videoConstraints = {
  facingMode: 'environment',
  width: { ideal: 1280 },
  height: { ideal: 720 },
};

export default function CameraView({ onCapture, loading }: CameraViewProps) {
  const webcamRef = useRef<Webcam>(null);

  const capture = useCallback(() => {
    if (webcamRef.current && !loading) {
      const screenshot = webcamRef.current.getScreenshot();
      if (screenshot) {
        onCapture(screenshot);
      }
    }
  }, [onCapture, loading]);

  return (
    <div className="relative w-full h-full flex flex-col items-center">
      <Webcam
        ref={webcamRef}
        audio={false}
        screenshotFormat="image/jpeg"
        videoConstraints={videoConstraints}
        className="w-full h-auto max-h-[70vh] object-cover"
      />

      {/* Crosshair overlay */}
      <div className="absolute inset-0 pointer-events-none flex items-center justify-center">
        <div className="w-48 h-48 border-2 border-blue-400/50 rounded-lg" />
      </div>

      {/* Capture button */}
      <div className="mt-4 mb-6">
        <button
          onClick={capture}
          disabled={loading}
          className="w-16 h-16 rounded-full bg-white border-4 border-blue-500 hover:border-blue-400
                     disabled:opacity-50 disabled:cursor-not-allowed
                     flex items-center justify-center transition-all active:scale-95"
        >
          <div className="w-12 h-12 rounded-full bg-blue-500 hover:bg-blue-400 transition-colors" />
        </button>
      </div>
      <p className="text-slate-400 text-sm text-center px-4">
        Point camera at an HVAC part and tap to capture
      </p>
    </div>
  );
}
