import { useState } from "react";
import { api, SearchResult } from "../api";

interface Props {
  textbookId?: string;
}

const BADGE_COLORS: Record<string, string> = {
  diseases: "bg-red-50 text-red-700",
  medications: "bg-blue-50 text-blue-700",
  labs: "bg-yellow-50 text-yellow-700",
  interventions: "bg-green-50 text-green-700",
  nursing_diagnoses: "bg-purple-50 text-purple-700",
};

export function SearchPanel({ textbookId }: Props) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [searching, setSearching] = useState(false);

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!query.trim()) return;
    setSearching(true);
    const res = await api.search(query, textbookId);
    setResults(res);
    setSearching(false);
  }

  return (
    <div>
      <form onSubmit={handleSearch} className="flex gap-2 mb-5">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search across all chapters… e.g. 'heart failure interventions'"
          className="flex-1 border border-gray-300 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-300"
        />
        <button
          type="submit"
          disabled={searching}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium disabled:opacity-50"
        >
          {searching ? "…" : "Search"}
        </button>
      </form>

      {results.length === 0 && !searching && query && (
        <p className="text-gray-400 text-sm text-center py-6">No results found.</p>
      )}

      <ul className="space-y-4">
        {results.map((r) => (
          <li key={r.chapter_id} className="bg-white border border-gray-200 rounded-xl p-4">
            <div className="flex items-start justify-between mb-1">
              <div>
                <p className="font-medium text-gray-800 text-sm">
                  Ch.{r.chapter_number}: {r.title}
                </p>
                <p className="text-xs text-gray-400">{r.textbook_title}</p>
              </div>
              <span className="text-xs bg-blue-50 text-blue-700 px-2 py-0.5 rounded-full shrink-0">
                {(r.score * 100).toFixed(1)}% match
              </span>
            </div>

            {r.extracted_json && (
              <div className="mt-2 flex flex-wrap gap-1">
                {(["diseases", "medications", "labs", "interventions", "nursing_diagnoses"] as const).map((key) => {
                  const items = (r.extracted_json as Record<string, string[]>)?.[key] ?? [];
                  return items.slice(0, 3).map((item, i) => (
                    <span key={`${key}-${i}`}
                      className={`text-xs px-2 py-0.5 rounded-full ${BADGE_COLORS[key] ?? "bg-gray-100 text-gray-600"}`}>
                      {item}
                    </span>
                  ));
                })}
              </div>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
