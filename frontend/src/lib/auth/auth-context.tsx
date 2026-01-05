"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { apiClient } from "../api/api";
import { useRouter, usePathname } from "next/navigation";

interface AuthContextType {
    isAuthenticated: boolean;
    isLoading: boolean;
    user: any | null;
    login: (token: string) => void;
    logout: () => void;
}

const AuthContext = createContext<AuthContextType>({
    isAuthenticated: false,
    isLoading: true,
    user: null,
    login: () => { },
    logout: () => { },
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [isLoading, setIsLoading] = useState(true);
    const [user, setUser] = useState(null);
    const router = useRouter();
    const pathname = usePathname();

    useEffect(() => {
        const initializeAuth = async () => {
            const token = localStorage.getItem("access_token");
            if (token) {
                try {
                    // Verify token by fetching user profile
                    const response = await apiClient.get("/auth/me");
                    setUser(response.data);
                    setIsAuthenticated(true);
                } catch (error) {
                    console.error("Auth check failed:", error);
                    logout();
                }
            }
            setIsLoading(false);
        };

        initializeAuth();
    }, []);

    const login = (token: string) => {
        localStorage.setItem("access_token", token);
        setIsAuthenticated(true);
        // Fetch user details immediately after login
        apiClient.get("/auth/me").then((res) => {
            setUser(res.data);
            router.push("/dashboard");
        }).catch((err) => {
            console.error("Failed to fetch user after login", err);
        });
    };

    const logout = () => {
        localStorage.removeItem("access_token");
        setIsAuthenticated(false);
        setUser(null);
        router.push("/login");
    };

    // Auth Guard: Redirect to login if not authenticated and not on public page
    useEffect(() => {
        if (!isLoading && !isAuthenticated && pathname !== "/login" && !pathname.startsWith("/(auth)")) {
            // Simple guard for now
            // router.push("/login"); // Commented out to prevent loops while dev
        }
    }, [isLoading, isAuthenticated, pathname, router]);


    return (
        <AuthContext.Provider
            value={{
                isAuthenticated,
                isLoading,
                user,
                login,
                logout,
            }}
        >
            {children}
        </AuthContext.Provider>
    );
}

export const useAuth = () => useContext(AuthContext);
