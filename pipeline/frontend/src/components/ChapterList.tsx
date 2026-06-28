import { useEffect, useState } from "react";
import { api, ChapterFull, ChapterSummary } from "../api";

interface Props {
  textbookId: string;
}

const ENTITY_KEYS = [
  "diseases", "medications", "labs", "interventions",
  "nursing_diagnoses", "patient_education", "safety_concerns",
  "clinical_judgment", "nclex_category",
] as const;

const KEY_LABEL: Record<string, string> = {
  diseases: "Diseases",
  medications: "Medications",
  labs: "Labs",
  interventions: "Interventions",
  nursing_diagnoses: "Nursing Diagnoses",
  patient_education: "Patient Education",
  safety_concerns: "Safety Concerns",
  clinical_judgment: "Clinical Judgment",
  nclex_category: "NCLEX Category",
};

export function ChapterList({ textbookId }: Props) {
  const [chapters, setChapters] = useState<ChapterSummary[]>([]);
  const [selected, setSelected] = useState<ChapterFull | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.listChapters(textbookId).then(setChapters);
  }, [textbookId]);

  async function openChapter(id: string) {
    setLoading(true);
    const ch = await api.getChapter(id);
    setSelected(ch);
    setLoading(false);
  }

  if (chapters.length === 0)
    return <p className="text-gray-400 text-sm py-4">No chapters yet — pipeline may still be running.</p>;

  return (
    <div className="flex gap-4 min-h-0">
      {/* Chapter list sidebar */}
      <ul className="w-64 shrink-0 space-y-1 overflow-y-auto max-h-[60vh]">
        {chapters.map((ch) => (
          <li
            key={ch.id}
            onClick={() => openChapter(ch.id)}
            className={`cursor-pointer rounded-lg px-3 py-2 text-sm transition-colors ${
              selected?.id === ch.id ? "bg-blue-100 text-blue-800 font-medium" : "hover:bg-gray-100 text-gray-700"
            }`}
          >
            <span className="text-gray-400 mr-1">#{ch.chapter_number}</span>
            {ch.title}
            <span className="ml-1 text-xs">
              {ch.has_extraction ? "✓" : ch.embedding_status === "completed" ? "~" : ""}
            </span>
          </li>
        ))}
      </ul>

      {/* Chapter detail panel */}
      <div className="flex-1 overflow-y-auto max-h-[60vh]">
        {loading && <p className="text-gray-400 text-sm animate-pulse">Loading...</p>}
        {selected && !loading && (
          <div>
            <h3 className="text-lg font-semibold text-gray-800 mb-1">
              Chapter {selected.chapter_number}: {selected.title}
            </h3>
            <p className="text-xs text-gray-400 mb-4">
              Pages {selected.page_start}–{selected.page_end}
            </p>

            {selected.extracted_json && (
              <div className="space-y-3">
                {ENTITY_KEYS.map((key) => {
                  const val = (selected.extracted_json as Record<string, unknown>)?.[key];
                  if (!val || (Array.isArray(val) && val.length === 0)) return null;
                  return (
                    <div key={key}>
                      <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
                        {KEY_LABEL[key]}
                      </p>
                      {Array.isArray(val) ? (
                        <div className="flex flex-wrap gap-1">
                          {(val as string[]).map((item, i) => (
                            <span key={i} className="bg-gray-100 text-gray-700 text-xs px-2 py-0.5 rounded-full">
                              {item}
                            </span>
                          ))}
                        </div>
                      ) : (
                        <span className="bg-purple-50 text-purple-700 text-xs px-2 py-0.5 rounded-full">
                          {String(val)}
                        </span>
                      )}
                    </div>
                  );
                })}
              </div>
            )}

            {!selected.extracted_json && (
              <p className="text-gray-400 text-sm">Extraction not yet complete.</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
