"use client";

import { useEffect, useState } from "react";

interface ConfirmButtonProps {
  onConfirm: () => void;
  label?: string;
  confirmLabel?: string;
  isLoading?: boolean;
  className?: string;
}

export function ConfirmButton({
  onConfirm,
  label = "Delete",
  confirmLabel = "Confirm?",
  isLoading = false,
  className = "",
}: ConfirmButtonProps) {
  const [confirming, setConfirming] = useState(false);

  useEffect(() => {
    if (!confirming) return;
    const t = setTimeout(() => setConfirming(false), 3000);
    return () => clearTimeout(t);
  }, [confirming]);

  if (confirming) {
    return (
      <button
        type="button"
        onClick={() => { setConfirming(false); onConfirm(); }}
        disabled={isLoading}
        className={`text-xs text-red-400 border border-red-700 rounded px-2 py-1 hover:bg-red-900 transition-colors ${className}`}
      >
        {confirmLabel}
      </button>
    );
  }

  return (
    <button
      type="button"
      onClick={() => setConfirming(true)}
      disabled={isLoading}
      className={`text-xs text-gray-400 border border-gray-700 rounded px-2 py-1 hover:text-red-400 hover:border-red-700 transition-colors ${className}`}
    >
      {label}
    </button>
  );
}
