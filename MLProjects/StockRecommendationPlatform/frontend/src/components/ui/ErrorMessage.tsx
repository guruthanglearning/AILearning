import { ApiError } from "@/lib/api";

interface ErrorMessageProps {
  error: Error | null;
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

  return (
    <div className="rounded-lg border border-red-800 bg-red-950 p-4 text-sm text-red-300">
      {message}
    </div>
  );
}
