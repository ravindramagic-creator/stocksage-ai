import { useState } from "react";

interface SearchBarProps {
  onSearch: (query: string) => void;
}

export function SearchBar({
  onSearch,
}: SearchBarProps) {
  const [query, setQuery] = useState("");

  function handleSubmit(
    event: React.FormEvent,
  ) {
    event.preventDefault();

    onSearch(query.trim());
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="flex w-full gap-2"
    >
      <input
        value={query}
        onChange={(event) =>
          setQuery(event.target.value)
        }
        placeholder="Search stocks..."
        className="
          w-full rounded-lg
          border border-slate-700
          bg-slate-900
          px-4 py-3
          text-white
          outline-none
          focus:border-blue-500
        "
      />

      <button
        type="submit"
        className="
          rounded-lg
          bg-blue-600
          px-5
          font-medium
          text-white
          hover:bg-blue-500
        "
      >
        Search
      </button>
    </form>
  );
}
