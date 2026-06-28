const BASE = "/api";

export interface Textbook {
  id: string;
  title: string;
  filename: string;
  status: string;
  current_stage: string | null;
  total_chapters: number;
  processed_chapters: number;
  created_at: string | null;
  stages?: StageStatus[];
}

export interface StageStatus {
  name: string;
  status: "pending" | "running" | "completed" | "failed";
  error: string | null;
}

export interface ChapterSummary {
  id: string;
  chapter_number: number;
  title: string;
  page_start: number | null;
  page_end: number | null;
  embedding_status: string;
  has_extraction: boolean;
}

export interface ChapterFull extends ChapterSummary {
  content_markdown: string | null;
  extracted_json: Record<string, unknown> | null;
}

export interface SearchResult {
  chapter_id: string;
  textbook_id: string;
  textbook_title: string;
  chapter_number: number;
  title: string;
  score: number;
  extracted_json: Record<string, unknown> | null;
}

export const api = {
  async uploadTextbook(file: File): Promise<{ textbook_id: string; title: string }> {
    const fd = new FormData();
    fd.append("file", file);
    const res = await fetch(`${BASE}/textbooks/upload`, { method: "POST", body: fd });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async listTextbooks(): Promise<Textbook[]> {
    const res = await fetch(`${BASE}/textbooks`);
    return res.json();
  },

  async getTextbook(id: string): Promise<Textbook> {
    const res = await fetch(`${BASE}/textbooks/${id}`);
    return res.json();
  },

  async resumePipeline(id: string): Promise<void> {
    await fetch(`${BASE}/textbooks/${id}/resume`, { method: "POST" });
  },

  async listChapters(textbookId: string): Promise<ChapterSummary[]> {
    const res = await fetch(`${BASE}/textbooks/${textbookId}/chapters`);
    return res.json();
  },

  async getChapter(id: string): Promise<ChapterFull> {
    const res = await fetch(`${BASE}/chapters/${id}`);
    return res.json();
  },

  async search(query: string, textbookId?: string): Promise<SearchResult[]> {
    const res = await fetch(`${BASE}/search`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, textbook_id: textbookId || null }),
    });
    return res.json();
  },

  sseUrl(textbookId: string): string {
    return `${BASE}/events/${textbookId}`;
  },
};
