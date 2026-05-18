import type { AgentContribution } from "@/types/api";

import { AgentStatusCard } from "./AgentStatusCard";

export function AgentStatusGrid({ contributions }: { contributions: AgentContribution[] }) {
  if (!contributions.length) return null;
  return (
    <div>
      <h2 className="text-sm font-medium text-gray-400 mb-3">Agent Status</h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
        {contributions.map((c) => (
          <AgentStatusCard key={c.agent_name} contribution={c} />
        ))}
      </div>
    </div>
  );
}
