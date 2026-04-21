import { type PartMatch } from '../api/client';

interface ResultOverlayProps {
  matches: PartMatch[];
  onSelect: (part: PartMatch) => void;
  onClose: () => void;
}

export default function ResultOverlay({ matches, onSelect, onClose }: ResultOverlayProps) {
  return (
    <div className="absolute bottom-0 left-0 right-0 bg-slate-800/95 backdrop-blur-sm border-t border-slate-700 rounded-t-2xl max-h-[60vh] overflow-y-auto z-30 animate-slide-up">
      <div className="p-4">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-semibold text-white">
            {matches.length} Match{matches.length !== 1 ? 'es' : ''} Found
          </h2>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white p-1"
          >
            ✕
          </button>
        </div>

        <div className="space-y-3">
          {matches.map((match) => (
            <button
              key={match.part_number}
              onClick={() => onSelect(match)}
              className="w-full bg-slate-700/50 hover:bg-slate-700 rounded-lg p-4 text-left transition-colors"
            >
              <div className="flex justify-between items-start">
                <div className="flex-1 min-w-0">
                  <h3 className="text-white font-medium truncate">
                    {match.title || match.part_number}
                  </h3>
                  <p className="text-slate-400 text-sm mt-1">
                    Order #: {match.part_number}
                    {match.brand && ` · ${match.brand}`}
                  </p>
                  {match.mfg_number && (
                    <p className="text-slate-500 text-xs mt-1">
                      Mfg #: {match.mfg_number}
                    </p>
                  )}
                </div>
                <span className="ml-3 px-2 py-1 bg-green-900/50 text-green-400 text-xs font-mono rounded">
                  {(match.confidence_score * 100).toFixed(1)}%
                </span>
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
