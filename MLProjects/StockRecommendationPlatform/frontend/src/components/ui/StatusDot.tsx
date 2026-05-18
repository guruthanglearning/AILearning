import type { AgentStatus } from "@/types/api";

const COLORS: Record<AgentStatus, string> = {
  complete: "bg-green-500",
  degraded: "bg-amber-500",
  failed: "bg-red-500",
};

export function StatusDot({ status }: { status: AgentStatus }) {
  return (
    <span
      className={`inline-block w-2 h-2 rounded-full ${COLORS[status]}`}
      title={status}
    />
  );
}
