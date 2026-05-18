import type { DecisionChecklistItem } from "@/types/api";

const STATE_ICON: Record<string, string> = {
  pass: "✓",
  warn: "⚠",
  fail: "✗",
  neutral: "–",
};

const STATE_COLOR: Record<string, string> = {
  pass: "text-green-400",
  warn: "text-amber-400",
  fail: "text-red-400",
  neutral: "text-gray-400",
};

export function ChecklistSection({ items }: { items: DecisionChecklistItem[] }) {
  if (!items.length) return null;
  return (
    <div className="space-y-2">
      {items.map((item) => {
        const icon = STATE_ICON[item.state] ?? "–";
        const color = STATE_COLOR[item.state] ?? "text-gray-400";
        return (
          <div key={item.id} className="flex gap-3 text-sm">
            <span className={`${color} font-bold w-4 shrink-0`}>{icon}</span>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-gray-200">{item.label}</span>
                {item.weight !== 1 && (
                  <span className="text-xs text-gray-600">×{item.weight.toFixed(1)}</span>
                )}
              </div>
              <p className="text-xs text-gray-500 mt-0.5">{item.explanation}</p>
            </div>
          </div>
        );
      })}
    </div>
  );
}
