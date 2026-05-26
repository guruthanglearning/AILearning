import type { AgentContribution } from "@/types/api";

import { AgentStatusCard } from "./AgentStatusCard";

const AGENT_ORDER = [
  "MarketDataAgent",
  "FundamentalsAgent",
  "TechnicalsAgent",
  "FinancialsAgent",
  "OptionsAgent",
  "RiskProWorkflowAgent",
  "SentimentMLAgent",
];

export function AgentStatusGrid({
  contributions,
  streaming = false,
}: {
  contributions: AgentContribution[];
  streaming?: boolean;
}) {
  if (!contributions.length && !streaming) return null;

  const doneNames = new Set(contributions.map((c) => c.agent_name));
  const pendingNames = streaming ? AGENT_ORDER.filter((n) => !doneNames.has(n)) : [];

  return (
    <div>
      <h2 className="text-sm font-medium text-gray-400 mb-3">Agent Status</h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
        {AGENT_ORDER.map((name) => {
          const c = contributions.find((x) => x.agent_name === name);
          if (c) return <AgentStatusCard key={name} contribution={c} />;
          if (pendingNames.includes(name)) {
            return <AgentStatusCard key={name} agentName={name} pending />;
          }
          return null;
        })}
      </div>
    </div>
  );
}
