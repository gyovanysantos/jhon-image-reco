import { type PartMatch } from '../api/client';

interface PartDetailsProps {
  part: PartMatch;
  onBack: () => void;
  onClose: () => void;
}

export default function PartDetails({ part, onBack, onClose }: PartDetailsProps) {
  const specs = part.specifications || {};
  const specEntries = Object.entries(specs);

  return (
    <div className="absolute inset-0 bg-slate-900/95 backdrop-blur-sm z-40 overflow-y-auto">
      <div className="max-w-lg mx-auto p-4">
        {/* Navigation */}
        <div className="flex items-center justify-between mb-4">
          <button
            onClick={onBack}
            className="text-blue-400 hover:text-blue-300 text-sm flex items-center gap-1"
          >
            ← Back to results
          </button>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white p-1"
          >
            ✕
          </button>
        </div>

        {/* Title */}
        <h2 className="text-xl font-bold text-white mb-2">
          {part.title || part.part_number}
        </h2>

        {/* Key info */}
        <div className="grid grid-cols-2 gap-3 mb-4">
          <div className="bg-slate-800 rounded-lg p-3">
            <p className="text-slate-400 text-xs uppercase">Order #</p>
            <p className="text-white font-mono font-bold">{part.part_number}</p>
          </div>
          {part.mfg_number && (
            <div className="bg-slate-800 rounded-lg p-3">
              <p className="text-slate-400 text-xs uppercase">Mfg #</p>
              <p className="text-white font-mono">{part.mfg_number}</p>
            </div>
          )}
          {part.brand && (
            <div className="bg-slate-800 rounded-lg p-3">
              <p className="text-slate-400 text-xs uppercase">Brand</p>
              <p className="text-white">{part.brand}</p>
            </div>
          )}
          <div className="bg-slate-800 rounded-lg p-3">
            <p className="text-slate-400 text-xs uppercase">Match</p>
            <p className="text-green-400 text-sm font-mono">
              {(part.confidence_score * 100).toFixed(1)}%
            </p>
          </div>
        </div>

        {/* Specifications */}
        {specEntries.length > 0 && (
          <div className="mb-4">
            <h3 className="text-sm font-semibold text-slate-300 uppercase mb-2">Specifications</h3>
            <div className="bg-slate-800 rounded-lg overflow-hidden">
              <table className="w-full text-sm">
                <tbody>
                  {specEntries.map(([key, value], i) => (
                    <tr key={key} className={i % 2 === 0 ? 'bg-slate-800' : 'bg-slate-750'}>
                      <td className="px-3 py-2 text-slate-400 font-medium">{key}</td>
                      <td className="px-3 py-2 text-white">{value}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Link to Johnstone Supply */}
        {part.url && (
          <a
            href={part.url}
            target="_blank"
            rel="noopener noreferrer"
            className="block w-full text-center bg-blue-600 hover:bg-blue-500 text-white font-medium rounded-lg py-3 mt-4 transition-colors"
          >
            View on Johnstone Supply
          </a>
        )}
      </div>
    </div>
  );
}
