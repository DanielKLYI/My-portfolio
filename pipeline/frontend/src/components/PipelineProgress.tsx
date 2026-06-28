import { useEffect, useState } from "react";
import { api, Textbook } from "../api";

const STAGE_LABELS: Record<string, string> = {
  parse: "Parse PDF",
  detect_chapters: "Detect Chapters",
  split_chapters: "Split Chapters",
  extract_entities: "Extract Entities",
  generate_embeddings: "Generate Embeddings",
};

interface Props {
  textbookId: string;
  onClose: () => void;
}

export function PipelineProgress({ textbookId, onClose }: Props) {
  const [book, setBook] = useState<Textbook | null>(null);

  useEffect(() => {
    // Initial load
    api.getTextbook(textbookId).then(setBook);

    // SSE stream for live updates
    const es = new EventSource(api.sseUrl(textbookId));
    es.onmessage = (e) => {
      const data: Textbook = JSON.parse(e.data);
      setBook(data);
      if (data.status === "completed" || data.status === "failed") {
        es.close();
      }
    };
    return () => es.close();
  }, [textbookId]);

  if (!book) return <div className="p-6 text-gray-500">Loading...</div>;

  const stages = book.stages ?? [];

  return (
    <div className="bg-white rounded-2xl shadow-lg p-6">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h2 className="text-lg font-semibold text-gray-800">{book.title}</h2>
          <p className="text-sm text-gray-400">{book.filename}</p>
        </div>
        <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl leading-none">&times;</button>
      </div>

      {/* Chapter progress bar */}
      {book.total_chapters > 0 && (
        <div className="mb-5">
          <div className="flex justify-between text-xs text-gray-500 mb-1">
            <span>Chapters processed</span>
            <span>{book.processed_chapters} / {book.total_chapters}</span>
          </div>
          <div className="w-full bg-gray-100 rounded-full h-2">
            <div
              className="bg-blue-500 h-2 rounded-full transition-all"
              style={{ width: `${(book.processed_chapters / book.total_chapters) * 100}%` }}
            />
          </div>
        </div>
      )}

      {/* Stage steps */}
      <ol className="space-y-2">
        {stages.map((stage, i) => (
          <li key={stage.name} className="flex items-center gap-3">
            <StageIcon status={stage.status} />
            <span className={`text-sm ${stage.status === "running" ? "font-semibold text-blue-600" : "text-gray-700"}`}>
              {STAGE_LABELS[stage.name] ?? stage.name}
            </span>
            {stage.error && (
              <span className="text-xs text-red-500 truncate max-w-xs" title={stage.error}>{stage.error}</span>
            )}
          </li>
        ))}
      </ol>

      {book.status === "failed" && (
        <button
          onClick={() => api.resumePipeline(textbookId)}
          className="mt-4 w-full py-2 rounded-lg bg-amber-500 hover:bg-amber-600 text-white text-sm font-medium"
        >
          Resume Pipeline
        </button>
      )}

      {book.status === "completed" && (
        <div className="mt-4 text-center text-green-600 text-sm font-medium">Pipeline complete</div>
      )}
    </div>
  );
}

function StageIcon({ status }: { status: string }) {
  if (status === "completed")
    return <span className="w-5 h-5 flex items-center justify-center rounded-full bg-green-100 text-green-600 text-xs">&#10003;</span>;
  if (status === "running")
    return <span className="w-5 h-5 flex items-center justify-center rounded-full bg-blue-100 text-blue-600 text-xs animate-spin">&#9696;</span>;
  if (status === "failed")
    return <span className="w-5 h-5 flex items-center justify-center rounded-full bg-red-100 text-red-500 text-xs">&#10007;</span>;
  return <span className="w-5 h-5 flex items-center justify-center rounded-full bg-gray-100 text-gray-400 text-xs">&#183;</span>;
}
