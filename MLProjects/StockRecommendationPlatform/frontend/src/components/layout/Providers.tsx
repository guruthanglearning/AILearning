"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";

import { AnalysisProvider } from "@/contexts/AnalysisContext";
import { ApiKeyProvider } from "@/contexts/ApiKeyContext";
import { NotificationProvider } from "@/contexts/NotificationContext";
import { MomentumPrefetcher } from "@/components/layout/MomentumPrefetcher";
import { ToastContainer } from "@/components/ui/Toast";

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
        <NotificationProvider>
          <AnalysisProvider>
            {children}
            <MomentumPrefetcher />
            <ToastContainer />
          </AnalysisProvider>
        </NotificationProvider>
      </QueryClientProvider>
    </ApiKeyProvider>
  );
}
