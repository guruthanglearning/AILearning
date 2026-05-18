"use client";

import { useState } from "react";

import { StatusDot } from "@/components/ui/StatusDot";
import type { AgentContribution } from "@/types/api";

function formatAgentName(name: string): string {
  return name.replace(/Agent$/, "").replace(/([A-Z])/g, " $1").trim();
}

export function AgentStatusCard({ contribution }: { contribution: AgentContribution }) {
  const [expanded, setExpanded] = useState(false);

  const borderColor =
    contribution.status === "complete"
      ? "border-l-green-600"
      : contribution.status === "degraded"
      ? "border-l-amber-600"
      : "border-l-red-600";

  return (
    <div
      className={`bg-gray-900 border border-gray-800 border-l-2 ${borderColor} rounded-lg p-3`}
    >
      <div className="flex items-center gap-2 mb-1">
        <StatusDot status={contribution.status} />
        <span className="text-xs font-medium text-gray-200">
          {formatAgentName(contribution.agent_name)}
        </span>
      </div>
      <p className="text-xs text-gray-400">{contribution.headline}</p>
      {contribution.detail && (
        <>
          <button
            type="button"
            onClick={() => setExpanded((o) => !o)}
            className="mt-1 text-xs text-indigo-400 hover:text-indigo-300"
          >
            {expanded ? "Less ▲" : "More ▼"}
          </button>
          {expanded && (
            <p className="mt-1 text-xs text-gray-500">{contribution.detail}</p>
          )}
        </>
      )}
    </div>
  );
}
