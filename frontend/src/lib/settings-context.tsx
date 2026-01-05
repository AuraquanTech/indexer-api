"use client";

import { createContext, useContext, useState, useEffect } from "react";

interface SettingsContextType {
    matrixMode: boolean;
    toggleMatrixMode: () => void;
}

const SettingsContext = createContext<SettingsContextType | undefined>(undefined);

export function SettingsProvider({ children }: { children: React.ReactNode }) {
    const [matrixMode, setMatrixMode] = useState(false);

    useEffect(() => {
        const saved = localStorage.getItem("matrix_mode");
        if (saved === "true") setMatrixMode(true);
    }, []);

    const toggleMatrixMode = () => {
        setMatrixMode((prev) => {
            const next = !prev;
            localStorage.setItem("matrix_mode", String(next));
            return next;
        });
    };

    return (
        <SettingsContext.Provider value={{ matrixMode, toggleMatrixMode }}>
            {children}
        </SettingsContext.Provider>
    );
}

export const useSettings = () => {
    const context = useContext(SettingsContext);
    if (!context) throw new Error("useSettings must be used within a SettingsProvider");
    return context;
};
