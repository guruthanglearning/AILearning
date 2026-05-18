"use client";

import { AlertCard } from "@/components/alerts/AlertCard";
import { CreateAlertForm } from "@/components/alerts/CreateAlertForm";
import { ApiKeyGate } from "@/components/layout/ApiKeyGate";
import { Badge } from "@/components/ui/Badge";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { Spinner } from "@/components/ui/Spinner";
import { useListAlerts, useListTriggeredAlerts } from "@/hooks/useAlerts";

export default function AlertsPage() {
  const { data: allAlerts, isLoading: allLoading, error: allError } = useListAlerts();
  const { data: triggered, isLoading: trigLoading } = useListTriggeredAlerts();

  return (
    <ApiKeyGate>
      <div className="max-w-2xl space-y-8">
        <div>
          <h1 className="text-xl font-semibold text-white mb-1">Alerts</h1>
          <p className="text-sm text-gray-400">
            Price and verdict alerts. Polled every 30 seconds.
          </p>
        </div>

        {triggered && triggered.length > 0 && (
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <h2 className="text-sm font-medium text-amber-300">Triggered</h2>
              <Badge variant="warning">{triggered.length}</Badge>
            </div>
            {triggered.map((a) => (
              <AlertCard key={a.id} alert={a} />
            ))}
          </div>
        )}

        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-4">
          <h2 className="text-sm font-medium text-gray-300">Create Alert</h2>
          <CreateAlertForm />
        </div>

        <div className="space-y-3">
          <h2 className="text-sm font-medium text-gray-300">All Alerts</h2>
          {(allLoading || trigLoading) && (
            <div className="flex justify-center py-8">
              <Spinner />
            </div>
          )}
          {allError && <ErrorMessage error={allError as Error} />}
          {allAlerts?.length === 0 && (
            <p className="text-sm text-gray-500 text-center py-6">No alerts yet.</p>
          )}
          {allAlerts?.map((a) => (
            <AlertCard key={a.id} alert={a} />
          ))}
        </div>
      </div>
    </ApiKeyGate>
  );
}
