"use client";

import { useState } from "react";

import { Spinner } from "@/components/ui/Spinner";
import { useCreateWatchlist } from "@/hooks/useWatchlists";

export function CreateWatchlistForm() {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const mutation = useCreateWatchlist();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    await mutation.mutateAsync({ name: name.trim(), description: description.trim() || null });
    setName("");
    setDescription("");
  }

  return (
    <form onSubmit={handleSubmit} className="flex gap-3 items-end flex-wrap">
      <div>
        <label className="block text-xs text-gray-400 mb-1">Name *</label>
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="My Watchlist"
          maxLength={100}
          className="bg-gray-800 border border-gray-700 rounded-md px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500"
        />
      </div>
      <div>
        <label className="block text-xs text-gray-400 mb-1">Description</label>
        <input
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Optional"
          className="bg-gray-800 border border-gray-700 rounded-md px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500"
        />
      </div>
      <button
        type="submit"
        disabled={!name.trim() || mutation.isPending}
        className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded-md transition-colors"
      >
        {mutation.isPending && <Spinner size="sm" />}
        Create
      </button>
    </form>
  );
}
