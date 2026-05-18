import { Badge } from "@/components/ui/Badge";
import { ConfirmButton } from "@/components/ui/ConfirmButton";
import { useDeleteAlert } from "@/hooks/useAlerts";
import type { AlertResponse } from "@/types/api";

function condLabel(a: AlertResponse): string {
  if (a.condition === "price_above") return `Price > $${a.threshold_value}`;
  if (a.condition === "price_below") return `Price < $${a.threshold_value}`;
  return `Verdict → ${a.threshold_verdict?.replace(/_/g, " ")}`;
}

function fmtDate(iso: string) {
  return new Date(iso).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function AlertCard({ alert }: { alert: AlertResponse }) {
  const remove = useDeleteAlert();

  return (
    <div
      className={`flex items-center gap-4 p-3 rounded-lg border ${
        alert.triggered_at
          ? "border-amber-800 bg-amber-950/20"
          : "border-gray-800 bg-gray-900"
      }`}
    >
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="font-mono font-medium text-white">{alert.symbol}</span>
          <span className="text-sm text-gray-300">{condLabel(alert)}</span>
          {alert.triggered_at && (
            <Badge variant="warning" size="sm">
              Triggered {fmtDate(alert.triggered_at)}
            </Badge>
          )}
          {!alert.is_active && !alert.triggered_at && (
            <Badge variant="neutral" size="sm">inactive</Badge>
          )}
        </div>
        <p className="text-xs text-gray-500 mt-0.5">Created {fmtDate(alert.created_at)}</p>
      </div>
      <ConfirmButton
        onConfirm={() => remove.mutate(alert.id)}
        isLoading={remove.isPending}
        label="Delete"
      />
    </div>
  );
}
