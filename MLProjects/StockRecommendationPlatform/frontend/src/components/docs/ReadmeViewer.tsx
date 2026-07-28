"use client";

import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeSlug from "rehype-slug";

import { getReadme } from "@/lib/api";

export function ReadmeViewer() {
  const [content, setContent] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getReadme()
      .then(setContent)
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load README"));
  }, []);

  if (error) {
    return (
      <p className="text-xs text-red-400 bg-red-900/20 border border-red-800/40 rounded px-3 py-2">
        {error}
      </p>
    );
  }

  if (!content) {
    return (
      <div className="flex items-center gap-2 text-xs text-gray-500">
        <span className="w-3 h-3 border border-gray-600 border-t-indigo-400 rounded-full animate-spin" />
        Loading README…
      </div>
    );
  }

  return (
    <article className="prose prose-invert prose-sm sm:prose-base max-w-none prose-a:text-indigo-400 prose-code:text-indigo-300 prose-pre:bg-gray-900 prose-pre:border prose-pre:border-gray-800 prose-table:text-sm prose-th:bg-gray-900">
      <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeSlug]}>
        {content}
      </ReactMarkdown>
    </article>
  );
}
