"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { useState } from "react";

import { AnalysisProvider } from "@/contexts/AnalysisContext";
import { ApiKeyProvider } from "@/contexts/ApiKeyContext";

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 0,
            retry: 1,
            refetchOnWindowFocus: false,
          },
        },
      })
  );

  return (
    <ApiKeyProvider>
      <QueryClientProvider client={queryClient}>
        <AnalysisProvider>
          {children}
          {process.env.NODE_ENV === "development" && (
            <ReactQueryDevtools initialIsOpen={false} />
          )}
        </AnalysisProvider>
      </QueryClientProvider>
    </ApiKeyProvider>
  );
}
