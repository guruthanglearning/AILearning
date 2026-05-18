"use client";

import { CreateWatchlistForm } from "@/components/watchlists/CreateWatchlistForm";
import { WatchlistCard } from "@/components/watchlists/WatchlistCard";
import { ApiKeyGate } from "@/components/layout/ApiKeyGate";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { Spinner } from "@/components/ui/Spinner";
import { useListWatchlists } from "@/hooks/useWatchlists";

export default function WatchlistsPage() {
  const { data, isLoading, error } = useListWatchlists();

  return (
    <ApiKeyGate>
      <div className="max-w-2xl space-y-6">
        <div>
          <h1 className="text-xl font-semibold text-white mb-1">Watchlists</h1>
          <p className="text-sm text-gray-400">Track symbols and analyze them quickly.</p>
        </div>

        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-4">
          <h2 className="text-sm font-medium text-gray-300">Create Watchlist</h2>
          <CreateWatchlistForm />
        </div>

        {isLoading && (
          <div className="flex justify-center py-8">
            <Spinner />
          </div>
        )}
        {error && <ErrorMessage error={error as Error} />}

        {data && data.length === 0 && (
          <p className="text-sm text-gray-500 text-center py-8">
            No watchlists yet — create one above.
          </p>
        )}

        <div className="space-y-3">
          {data?.map((wl) => (
            <WatchlistCard key={wl.id} watchlist={wl} />
          ))}
        </div>
      </div>
    </ApiKeyGate>
  );
}
