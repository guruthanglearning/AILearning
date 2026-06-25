"use client";

import { useEffect, useRef, useState } from "react";

import { useListTriggeredAlerts } from "@/hooks/useAlerts";
import type { AlertResponse } from "@/types/api";

function formatAlertBody(alert: AlertResponse): string {
  const { symbol, condition, threshold_value, threshold_verdict } = alert;
  if (condition === "price_above") return `${symbol} price crossed above $${threshold_value}`;
  if (condition === "price_below") return `${symbol} price dropped below $${threshold_value}`;
  if (condition === "verdict_changes_to") return `${symbol} verdict changed to ${threshold_verdict}`;
  return `${symbol} alert triggered`;
}

interface Toast {
  id: string;
  body: string;
}

export function AlertNotifier() {
  const { data: triggered } = useListTriggeredAlerts();
  const notifiedIds = useRef<Set<string>>(new Set());
  const [toasts, setToasts] = useState<Toast[]>([]);
  const permissionRef = useRef<NotificationPermission>("default");

  useEffect(() => {
    if (typeof Notification === "undefined") return;
    permissionRef.current = Notification.permission;
    if (Notification.permission === "default") {
      Notification.requestPermission().then((p) => {
        permissionRef.current = p;
      });
    }
  }, []);

  useEffect(() => {
    if (!triggered?.length) return;

    const newAlerts = triggered.filter(
      (a) => a.triggered_at && !notifiedIds.current.has(a.id)
    );

    if (!newAlerts.length) return;

    newAlerts.forEach((alert) => {
      notifiedIds.current.add(alert.id);
      const body = formatAlertBody(alert);

      if (
        typeof Notification !== "undefined" &&
        permissionRef.current === "granted" &&
        document.visibilityState === "hidden"
      ) {
        new Notification("Stock Alert Triggered", { body, icon: "/favicon.ico" });
      } else {
        const toast: Toast = { id: alert.id, body };
        setToasts((prev) => [...prev, toast]);
        setTimeout(() => {
          setToasts((prev) => prev.filter((t) => t.id !== toast.id));
        }, 6000);
      }
    });
  }, [triggered]);

  if (!toasts.length) return null;

  return (
    <div className="fixed top-4 right-4 z-50 flex flex-col gap-2 max-w-sm">
      {toasts.map((t) => (
        <div
          key={t.id}
          className="bg-amber-500 text-gray-950 rounded-lg px-4 py-3 shadow-lg text-sm font-medium flex items-start gap-2"
        >
          <span className="mt-0.5">&#9888;</span>
          <div>
            <div className="font-semibold">Stock Alert Triggered</div>
            <div>{t.body}</div>
          </div>
          <button
            onClick={() => setToasts((prev) => prev.filter((x) => x.id !== t.id))}
            className="ml-auto shrink-0 opacity-70 hover:opacity-100"
            aria-label="Dismiss"
          >
            &#x2715;
          </button>
        </div>
      ))}
    </div>
  );
}
