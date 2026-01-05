"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider } from "@/lib/auth/auth-context";
import { SettingsProvider } from "@/lib/settings-context";
import { MatrixRain } from "@/components/ui/matrix-rain";
import { useState } from "react";

export function Providers({ children }: { children: React.ReactNode }) {
    const [queryClient] = useState(
        () =>
            new QueryClient({
                defaultOptions: {
                    queries: {
                        staleTime: 60 * 1000, // 1 minute
                        refetchOnWindowFocus: false,
                    },
                },
            })
    );

    return (
        <QueryClientProvider client={queryClient}>
            <SettingsProvider>
                <AuthProvider>{children}</AuthProvider>
                <MatrixRain />
            </SettingsProvider>
        </QueryClientProvider>
    );
}
