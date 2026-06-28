import { Textbook } from "../api";

const STATUS_STYLE: Record<string, string> = {
  uploaded: "bg-gray-100 text-gray-600",
  processing: "bg-blue-100 text-blue-700",
  completed: "bg-green-100 text-green-700",
  failed: "bg-red-100 text-red-600",
};

interface Props {
  books: Textbook[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}

export function TextbookList({ books, selectedId, onSelect }: Props) {
  if (books.length === 0)
    return <p className="text-gray-400 text-sm text-center py-8">No textbooks yet. Upload one above.</p>;

  return (
    <ul className="space-y-2">
      {books.map((book) => (
        <li
          key={book.id}
          onClick={() => onSelect(book.id)}
          className={`cursor-pointer rounded-xl p-4 border transition-all ${
            selectedId === book.id
              ? "border-blue-400 bg-blue-50 shadow-sm"
              : "border-gray-200 bg-white hover:border-gray-300"
          }`}
        >
          <div className="flex items-start justify-between gap-2">
            <div className="min-w-0">
              <p className="font-medium text-gray-800 truncate">{book.title}</p>
              <p className="text-xs text-gray-400 truncate">{book.filename}</p>
            </div>
            <span className={`shrink-0 text-xs px-2 py-0.5 rounded-full font-medium ${STATUS_STYLE[book.status] ?? "bg-gray-100 text-gray-600"}`}>
              {book.status}
            </span>
          </div>
          {book.total_chapters > 0 && (
            <div className="mt-2 flex items-center gap-2">
              <div className="flex-1 bg-gray-100 rounded-full h-1.5">
                <div
                  className="bg-blue-400 h-1.5 rounded-full"
                  style={{ width: `${(book.processed_chapters / book.total_chapters) * 100}%` }}
                />
              </div>
              <span className="text-xs text-gray-400 shrink-0">
                {book.processed_chapters}/{book.total_chapters} ch
              </span>
            </div>
          )}
        </li>
      ))}
    </ul>
  );
}
