import { useEffect, useState, useCallback } from "react";
import { api, Textbook } from "./api";
import { UploadPanel } from "./components/UploadPanel";
import { TextbookList } from "./components/TextbookList";
import { PipelineProgress } from "./components/PipelineProgress";
import { ChapterList } from "./components/ChapterList";
import { SearchPanel } from "./components/SearchPanel";

type Tab = "progress" | "chapters" | "search";

export default function App() {
  const [books, setBooks] = useState<Textbook[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>("progress");

  const loadBooks = useCallback(async () => {
    const data = await api.listTextbooks();
    setBooks(data);
  }, []);

  useEffect(() => { loadBooks(); }, [loadBooks]);

  function handleUploaded(id: string) {
    loadBooks();
    setSelectedId(id);
    setActiveTab("progress");
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4 flex items-center gap-3">
        <svg className="w-7 h-7 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
        </svg>
        <div>
          <h1 className="text-lg font-bold text-gray-900">Nursing Textbook Pipeline</h1>
          <p className="text-xs text-gray-400">Ingestion & semantic search dashboard</p>
        </div>
      </header>

      <div className="max-w-6xl mx-auto p-6 grid grid-cols-[300px_1fr] gap-6">
        {/* Left sidebar */}
        <aside className="space-y-4">
          <UploadPanel onUploaded={handleUploaded} />
          <div className="bg-white rounded-2xl shadow-sm p-4">
            <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">Textbooks</h2>
            <TextbookList
              books={books}
              selectedId={selectedId}
              onSelect={(id) => { setSelectedId(id); setActiveTab("progress"); }}
            />
          </div>
        </aside>

        {/* Main content */}
        <main>
          {!selectedId ? (
            <div className="h-full flex items-center justify-center text-gray-400">
              <div className="text-center">
                <p className="text-4xl mb-2">📚</p>
                <p>Upload a textbook or select one from the list.</p>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Tab bar */}
              <div className="flex gap-1 bg-white rounded-xl p-1 shadow-sm w-fit">
                {(["progress", "chapters", "search"] as Tab[]).map((tab) => (
                  <button
                    key={tab}
                    onClick={() => setActiveTab(tab)}
                    className={`px-4 py-1.5 rounded-lg text-sm font-medium capitalize transition-colors ${
                      activeTab === tab ? "bg-blue-600 text-white" : "text-gray-600 hover:bg-gray-100"
                    }`}
                  >
                    {tab}
                  </button>
                ))}
              </div>

              {/* Tab panels */}
              {activeTab === "progress" && (
                <PipelineProgress
                  textbookId={selectedId}
                  onClose={() => setSelectedId(null)}
                />
              )}
              {activeTab === "chapters" && (
                <div className="bg-white rounded-2xl shadow-sm p-5">
                  <ChapterList textbookId={selectedId} />
                </div>
              )}
              {activeTab === "search" && (
                <div className="bg-white rounded-2xl shadow-sm p-5">
                  <SearchPanel textbookId={selectedId} />
                </div>
              )}
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
