import { useCallback, useState, useRef } from 'react';

interface UploadViewProps {
  onUpload: (imageBase64: string) => void;
  loading: boolean;
}

export default function UploadView({ onUpload, loading }: UploadViewProps) {
  const [preview, setPreview] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback(
    (file: File) => {
      if (!file.type.startsWith('image/')) return;

      const reader = new FileReader();
      reader.onload = () => {
        const result = reader.result as string;
        setPreview(result);
        onUpload(result);
      };
      reader.readAsDataURL(file);
    },
    [onUpload],
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragActive(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile],
  );

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) handleFile(file);
    },
    [handleFile],
  );

  return (
    <div className="flex flex-col items-center justify-center p-6 min-h-[60vh]">
      <div
        className={`w-full max-w-md border-2 border-dashed rounded-xl p-8 text-center transition-colors cursor-pointer
          ${dragActive ? 'border-blue-400 bg-blue-900/20' : 'border-slate-600 hover:border-slate-500'}`}
        onDragOver={(e) => {
          e.preventDefault();
          setDragActive(true);
        }}
        onDragLeave={() => setDragActive(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
      >
        {preview ? (
          <img
            src={preview}
            alt="Uploaded part"
            className="max-h-64 mx-auto rounded-lg"
          />
        ) : (
          <>
            <svg
              className="w-12 h-12 mx-auto text-slate-500 mb-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
              />
            </svg>
            <p className="text-slate-400 mb-2">
              Drag &amp; drop an image here, or click to browse
            </p>
            <p className="text-slate-500 text-sm">
              Supports JPG, PNG, WebP
            </p>
          </>
        )}

        <input
          ref={inputRef}
          type="file"
          accept="image/*"
          className="hidden"
          onChange={handleChange}
          disabled={loading}
        />
      </div>
    </div>
  );
}
