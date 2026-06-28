"""PDF parsing utilities using PyMuPDF."""
import re
from dataclasses import dataclass, field
from pathlib import Path
import fitz  # PyMuPDF


@dataclass
class PageContent:
    number: int  # 1-based
    text: str
    headings: list[str] = field(default_factory=list)


@dataclass
class ChapterBoundary:
    chapter_number: int
    title: str
    page_start: int  # 1-based
    page_end: int    # 1-based, inclusive


@dataclass
class ParsedPDF:
    pages: list[PageContent]
    bookmarks: list[ChapterBoundary]  # from PDF outline, may be empty
    total_pages: int


CHAPTER_PATTERNS = [
    re.compile(r"^chapter\s+(\d+)[:\s\-–—]+(.+)$", re.IGNORECASE | re.MULTILINE),
    re.compile(r"^(\d+)\s*\.\s+(.{5,80})$", re.MULTILINE),
    re.compile(r"^unit\s+(\d+)[:\s\-–—]+(.+)$", re.IGNORECASE | re.MULTILINE),
]


def parse_pdf(file_path: str) -> ParsedPDF:
    doc = fitz.open(file_path)
    pages: list[PageContent] = []

    for i, page in enumerate(doc):
        text = page.get_text("text")
        # Extract bold/large text as potential headings
        blocks = page.get_text("dict")["blocks"]
        headings: list[str] = []
        for block in blocks:
            if block.get("type") != 0:
                continue
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    if span.get("size", 0) >= 14 or "Bold" in span.get("font", ""):
                        txt = span["text"].strip()
                        if len(txt) > 3:
                            headings.append(txt)
        pages.append(PageContent(number=i + 1, text=text, headings=headings))

    bookmarks = _extract_bookmarks(doc, len(pages))
    doc.close()
    return ParsedPDF(pages=pages, bookmarks=bookmarks, total_pages=len(pages))


def _extract_bookmarks(doc: fitz.Document, total_pages: int) -> list[ChapterBoundary]:
    toc = doc.get_toc()  # [[level, title, page], ...]
    if not toc:
        return []

    # Filter to top-level entries that look like chapters
    chapters: list[ChapterBoundary] = []
    chapter_entries = [(title, page) for level, title, page in toc if level == 1]

    for idx, (title, page_start) in enumerate(chapter_entries):
        page_end = chapter_entries[idx + 1][1] - 1 if idx + 1 < len(chapter_entries) else total_pages
        num = _infer_chapter_number(title, idx + 1)
        chapters.append(ChapterBoundary(
            chapter_number=num,
            title=title.strip(),
            page_start=page_start,
            page_end=page_end,
        ))

    return chapters


def detect_chapters_from_text(pages: list[PageContent]) -> list[ChapterBoundary]:
    """Heuristic chapter detection when PDF has no bookmarks."""
    candidates: list[tuple[int, int, str]] = []  # (chapter_num, page, title)

    for page in pages:
        first_lines = "\n".join(page.text.strip().splitlines()[:6])
        for pattern in CHAPTER_PATTERNS:
            for m in pattern.finditer(first_lines):
                try:
                    num = int(m.group(1))
                    title = m.group(2).strip()
                    candidates.append((num, page.number, title))
                    break
                except (ValueError, IndexError):
                    continue
        if candidates and candidates[-1][1] == page.number:
            continue  # already got one from this page

    if not candidates:
        return []

    chapters: list[ChapterBoundary] = []
    for idx, (num, page_start, title) in enumerate(candidates):
        page_end = candidates[idx + 1][1] - 1 if idx + 1 < len(candidates) else pages[-1].number
        chapters.append(ChapterBoundary(
            chapter_number=num,
            title=title,
            page_start=page_start,
            page_end=page_end,
        ))
    return chapters


def _infer_chapter_number(title: str, fallback: int) -> int:
    m = re.search(r"\b(\d+)\b", title)
    return int(m.group(1)) if m else fallback


def pages_to_markdown(pages: list[PageContent], page_start: int, page_end: int) -> str:
    """Convert a page range to markdown text."""
    lines: list[str] = []
    for page in pages:
        if page.number < page_start or page.number > page_end:
            continue
        for line in page.text.splitlines():
            stripped = line.strip()
            if not stripped:
                lines.append("")
                continue
            if stripped in page.headings:
                lines.append(f"## {stripped}")
            else:
                lines.append(stripped)
    return "\n".join(lines).strip()
