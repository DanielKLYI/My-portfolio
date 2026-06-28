import { useCallback, useState } from "react";
import { api } from "../api";

interface Props {
  onUploaded: (id: string) => void;
}

export function UploadPanel({ onUploaded }: Props) {
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFile = useCallback(
    async (file: File) => {
      setError(null);
      setUploading(true);
      try {
        const { textbook_id } = await api.uploadTextbook(file);
        onUploaded(textbook_id);
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "Upload failed");
      } finally {
        setUploading(false);
      }
    },
    [onUploaded]
  );

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={onDrop}
      className={`border-2 border-dashed rounded-xl p-10 text-center transition-colors ${
        dragging ? "border-blue-400 bg-blue-50" : "border-gray-300 bg-white"
      }`}
    >
      {uploading ? (
        <p className="text-blue-600 font-medium animate-pulse">Uploading and starting pipeline...</p>
      ) : (
        <>
          <svg className="mx-auto mb-3 text-gray-400 w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
              d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
          <p className="text-gray-600 mb-2">Drag & drop a nursing textbook PDF here</p>
          <label className="cursor-pointer text-blue-600 hover:underline text-sm font-medium">
            or browse files
            <input type="file" accept=".pdf" className="hidden"
              onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFile(f); }} />
          </label>
        </>
      )}
      {error && <p className="mt-3 text-red-500 text-sm">{error}</p>}
    </div>
  );
}
