import { useState } from 'react';
import CameraView from './components/CameraView';
import UploadView from './components/UploadView';
import ResultOverlay from './components/ResultOverlay';
import PartDetails from './components/PartDetails';
import { recognizeImage, type PartMatch } from './api/client';

type View = 'camera' | 'upload';

export default function App() {
  const [view, setView] = useState<View>('camera');
  const [loading, setLoading] = useState(false);
  const [matches, setMatches] = useState<PartMatch[]>([]);
  const [selectedPart, setSelectedPart] = useState<PartMatch | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleCapture = async (imageBase64: string) => {
    setLoading(true);
    setError(null);
    setMatches([]);
    setSelectedPart(null);

    try {
      // Strip data URL prefix if present
      const base64Data = imageBase64.includes(',')
        ? imageBase64.split(',')[1]
        : imageBase64;

      const result = await recognizeImage(base64Data);
      if (result.matches.length > 0) {
        setMatches(result.matches);
      } else {
        setError('Part not recognized — try another angle or image.');
      }
    } catch (err) {
      setError('Failed to recognize part. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setMatches([]);
    setSelectedPart(null);
    setError(null);
  };

  return (
    <div className="min-h-screen bg-slate-900 flex flex-col">
      {/* Header */}
      <header className="bg-slate-800 border-b border-slate-700 px-4 py-3 flex items-center justify-between">
        <h1 className="text-lg font-bold text-white">HVAC Part Recognition</h1>
        <div className="flex gap-2">
          <button
            className={`px-3 py-1 rounded text-sm ${view === 'camera' ? 'bg-blue-600 text-white' : 'bg-slate-700 text-slate-300'}`}
            onClick={() => setView('camera')}
          >
            Camera
          </button>
          <button
            className={`px-3 py-1 rounded text-sm ${view === 'upload' ? 'bg-blue-600 text-white' : 'bg-slate-700 text-slate-300'}`}
            onClick={() => setView('upload')}
          >
            Upload
          </button>
        </div>
      </header>

      {/* Main content */}
      <main className="flex-1 relative">
        {view === 'camera' ? (
          <CameraView onCapture={handleCapture} loading={loading} />
        ) : (
          <UploadView onUpload={handleCapture} loading={loading} />
        )}

        {/* Loading overlay */}
        {loading && (
          <div className="absolute inset-0 bg-black/50 flex items-center justify-center z-20">
            <div className="bg-slate-800 rounded-lg p-6 text-center">
              <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-400 mx-auto mb-3" />
              <p className="text-slate-300">Analyzing part...</p>
            </div>
          </div>
        )}

        {/* Error message */}
        {error && !loading && (
          <div className="absolute bottom-4 left-4 right-4 bg-red-900/90 border border-red-700 rounded-lg p-4 z-20">
            <p className="text-red-200">{error}</p>
            <button
              className="mt-2 text-sm text-red-300 underline"
              onClick={handleClose}
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Results */}
        {matches.length > 0 && !selectedPart && (
          <ResultOverlay
            matches={matches}
            onSelect={setSelectedPart}
            onClose={handleClose}
          />
        )}

        {/* Part detail view */}
        {selectedPart && (
          <PartDetails
            part={selectedPart}
            onBack={() => setSelectedPart(null)}
            onClose={handleClose}
          />
        )}
      </main>
    </div>
  );
}
