"use client";

import { useEffect } from "react";

import { useRouter } from "next/navigation";

import {
  useNotifications,
  type AppNotification,
} from "@/contexts/NotificationContext";

const AUTO_DISMISS_MS = 10_000;

const TYPE_STYLES: Record<AppNotification["type"], string> = {
  info:    "border-blue-500/50 bg-blue-950/90 text-blue-300",
  success: "border-green-500/50 bg-green-950/90 text-green-300",
  warning: "border-amber-500/50 bg-amber-950/90 text-amber-300",
  error:   "border-red-500/50 bg-red-950/90 text-red-300",
};

const TYPE_ICONS: Record<AppNotification["type"], string> = {
  info:    "ℹ",
  success: "✓",
  warning: "⚠",
  error:   "✕",
};

function Toast({ notification }: { notification: AppNotification }) {
  const { dismiss } = useNotifications();
  const router = useRouter();

  useEffect(() => {
    const id = setTimeout(() => dismiss(notification.id), AUTO_DISMISS_MS);
    return () => clearTimeout(id);
  }, [notification.id, dismiss]);

  function handleClick() {
    if (notification.action?.href) {
      router.push(notification.action.href);
      dismiss(notification.id);
    }
  }

  const hasAction = !!notification.action;

  return (
    <div
      role="alert"
      onClick={hasAction ? handleClick : undefined}
      className={[
        "flex items-start gap-3 px-4 py-3 rounded-lg border shadow-xl",
        "backdrop-blur-sm max-w-sm w-full",
        TYPE_STYLES[notification.type],
        hasAction ? "cursor-pointer hover:brightness-110 transition-[filter]" : "",
      ].join(" ")}
    >
      <span className="text-sm shrink-0 mt-px">{TYPE_ICONS[notification.type]}</span>

      <div className="flex-1 min-w-0">
        <p className="text-sm text-gray-100 leading-snug">{notification.message}</p>
        {notification.action && (
          <p className="text-xs text-gray-400 mt-1">
            {notification.action.label} →
          </p>
        )}
      </div>

      <button
        type="button"
        aria-label="Dismiss"
        onClick={(e) => { e.stopPropagation(); dismiss(notification.id); }}
        className="shrink-0 text-gray-500 hover:text-gray-200 transition-colors text-xs mt-px"
      >
        ✕
      </button>
    </div>
  );
}

export function ToastContainer() {
  const { notifications } = useNotifications();
  if (!notifications.length) return null;

  return (
    <div
      aria-live="polite"
      aria-atomic="false"
      className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 pointer-events-none"
    >
      {notifications.map((n) => (
        <div key={n.id} className="pointer-events-auto">
          <Toast notification={n} />
        </div>
      ))}
    </div>
  );
}
