"use client";

import { useState, useEffect } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Search, Sparkles, BrainCircuit, Mic, MicOff } from "lucide-react";
import { useDebounce } from "@/lib/hooks/use-debounce";
import { useSpeechRecognition } from "@/lib/hooks/use-speech-recognition";
import { SearchMode } from "@/lib/types";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { cn } from "@/lib/utils";

interface SearchBarProps {
    onSearch: (query: string, mode: SearchMode) => void;
    initialQuery?: string;
    initialMode?: SearchMode;
}

export function SearchBar({ onSearch, initialQuery = "", initialMode = "basic" }: SearchBarProps) {
    const [query, setQuery] = useState(initialQuery);
    const [mode, setMode] = useState<SearchMode>(initialMode);

    const { isListening, transcript, startListening, stopListening, isSupported } = useSpeechRecognition();

    // Sync transcript to query when listening
    useEffect(() => {
        if (isListening && transcript) {
            setQuery(transcript);
        }
    }, [isListening, transcript]);

    // Auto-trigger search when speech ends
    useEffect(() => {
        if (!isListening && transcript) {
            // Optional: switch to natural mode if speech detected
            if (mode !== 'natural') setMode('natural');
            onSearch(transcript, 'natural');
        }
    }, [isListening, transcript, onSearch, mode]);

    const debouncedQuery = useDebounce(query, 500);

    useEffect(() => {
        if (!isListening) {
            onSearch(debouncedQuery, mode);
        }
    }, [debouncedQuery, mode, onSearch, isListening]);

    const handleModeChange = (val: SearchMode) => {
        setMode(val);
    };

    const toggleListening = () => {
        if (isListening) {
            stopListening();
        } else {
            startListening();
        }
    };

    return (
        <div className="flex gap-2 w-full max-w-2xl">
            <div className="relative flex-1">
                <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                    type="search"
                    placeholder={isListening ? "Listening..." : (mode === 'natural' ? "Ask a question..." : "Search projects...")}
                    className={cn("pl-8 pr-12 transition-all", isListening && "border-amber-500 ring-2 ring-amber-500/20")}
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                />
                {isSupported && (
                    <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        className={cn("absolute right-1 top-1 h-8 w-8 hover:bg-transparent", isListening ? "text-red-500 animate-pulse" : "text-muted-foreground")}
                        onClick={toggleListening}
                        title="Voice Search"
                    >
                        {isListening ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
                    </Button>
                )}
            </div>
            <Select value={mode} onValueChange={(val) => handleModeChange(val as SearchMode)}>
                <SelectTrigger className="w-[140px]">
                    <SelectValue placeholder="Mode" />
                </SelectTrigger>
                <SelectContent>
                    <SelectItem value="basic">
                        <span className="flex items-center gap-2">
                            <Search className="w-3 h-3" /> Basic
                        </span>
                    </SelectItem>
                    <SelectItem value="semantic">
                        <span className="flex items-center gap-2">
                            <BrainCircuit className="w-3 h-3" /> Semantic
                        </span>
                    </SelectItem>
                    <SelectItem value="natural">
                        <span className="flex items-center gap-2">
                            <Sparkles className="w-3 h-3 text-amber-500" /> Natural
                        </span>
                    </SelectItem>
                </SelectContent>
            </Select>
        </div>
    );
}
