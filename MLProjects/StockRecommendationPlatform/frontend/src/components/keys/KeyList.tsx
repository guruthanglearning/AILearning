"use client";

import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { Spinner } from "@/components/ui/Spinner";
import { useListApiKeys } from "@/hooks/useApiKeys";

import { KeyCard } from "./KeyCard";

export function KeyList() {
  const { data, isLoading, error } = useListApiKeys();

  if (isLoading) {
    return (
      <div className="flex justify-center py-8">
        <Spinner />
      </div>
    );
  }

  if (error) return <ErrorMessage error={error as Error} />;
  if (!data?.length) {
    return <p className="text-gray-500 text-sm">No keys found.</p>;
  }

  return (
    <div className="space-y-2">
      {data.map((key) => (
        <KeyCard key={key.id} apiKey={key} />
      ))}
    </div>
  );
}
