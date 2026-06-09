import Link from "next/link";

import { ApiError } from "@/lib/api";

interface ErrorMessageProps {
  error: Error | null;
}

function isClaudeError(msg: string): boolean {
  return (
    msg.includes("ClaudeDecisionEngine") ||
    msg.includes("ANTHROPIC_API_KEY") ||
    msg.includes("Anthropic API") ||
    msg.includes("claude-opus") ||
    msg.toLowerCase().includes("claude decision")
  );
}

export function ErrorMessage({ error }: ErrorMessageProps) {
  if (!error) return null;

  let message = error.message;
  if (error instanceof ApiError) {
    if (error.statusCode === 401) {
      message = "API key missing or invalid — go to API Keys page to set one.";
    } else if (error.statusCode === 429) {
      message = "Rate limit reached — wait a moment before retrying.";
    } else if (error.statusCode === 422) {
      message = `Validation error: ${error.message}`;
    } else {
      message = `Error ${error.statusCode}: ${error.message}`;
    }
  }

  if (isClaudeError(message)) {
    const firstLine = message.split("\n")[0];
    return (
      <div className="rounded-lg border border-purple-800 bg-purple-950/60 p-4 space-y-2">
        <div className="flex items-center gap-2">
          <span className="text-xs font-bold uppercase tracking-wider text-purple-400 shrink-0">
            AI Engine Error
          </span>
          <div className="flex-1 border-t border-purple-800/50" />
        </div>
        <p className="text-sm text-purple-200">{firstLine}</p>
        <p className="text-xs text-purple-400/80">
          The Claude decision engine failed to produce an analysis verdict.{" "}
          <Link href="/logs" className="underline underline-offset-2 hover:text-purple-200 transition-colors">
            View the Logs page
          </Link>{" "}
          for the full error trace and ensure your <code className="bg-purple-900/50 px-1 rounded">ANTHROPIC_API_KEY</code> is valid.
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-red-800 bg-red-950 p-4 text-sm text-red-300">
      {message}
    </div>
  );
}
