"use client";

import dynamic from "next/dynamic";

const ReadmeViewer = dynamic(
  () => import("@/components/docs/ReadmeViewer").then((m) => m.ReadmeViewer),
  { ssr: false },
);

export default function DocsPage() {
  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-lg font-semibold text-white">Documentation</h1>
        <p className="text-xs text-gray-500 mt-0.5">
          Live project README — always reflects the current state of the codebase.
        </p>
      </div>
      <ReadmeViewer />
    </div>
  );
}
