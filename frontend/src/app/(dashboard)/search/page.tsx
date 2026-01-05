"use client";

import { useState } from "react";
import { SearchBar } from "@/components/search/search-bar";
import { SearchMode, Project } from "@/lib/types";
import { projectsApi } from "@/lib/api/projects";
import { ProjectCard } from "@/components/projects/project-card";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Sparkles, ArrowRight, Mic } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { TechHologram } from "@/components/discovery/tech-hologram";

const EXAMPLE_QUERIES = [
    "Python APIs for file management",
    "Production-ready authentication libraries",
    "Projects with high test coverage",
    "TypeScript tools with Docker support",
    "Machine learning models for NLP",
    "FastAPI services with rate limiting"
];

export default function SearchPage() {
    const [query, setQuery] = useState("");
    const [mode, setMode] = useState<SearchMode>('natural');

    // We only run the query if it's not empty
    const { data: results, isLoading, isError } = useQuery({
        queryKey: ['search', query, mode],
        queryFn: () => projectsApi.search(query, mode),
        enabled: query.length > 2,
        staleTime: 1000 * 60 * 5 // Cache usually good for search results
    });

    const handleSearch = (q: string, m: SearchMode) => {
        setQuery(q);
        setMode(m);
    };

    return (
        <div className="flex flex-col items-center max-w-5xl mx-auto w-full py-8 gap-8">

            {/* Header Section */}
            <div className="text-center space-y-4 max-w-2xl">
                <div className="flex items-center justify-center gap-2 mb-2">
                    <Sparkles className="h-6 w-6 text-amber-500 animate-pulse" />
                    <span className="text-sm font-semibold text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-900/20 px-3 py-1 rounded-full border border-amber-200 dark:border-amber-800">
                        AI Powered
                    </span>
                </div>
                <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl bg-clip-text text-transparent bg-gradient-to-r from-gray-900 to-gray-600 dark:from-white dark:to-gray-400">
                    Ask your portfolio anything
                </h1>
                <p className="text-lg text-muted-foreground">
                    Use natural language to find projects by capability, tech stack, or quality metrics.
                </p>
            </div>

            {/* Search Input */}
            <div className="w-full max-w-2xl">
                <SearchBar initialMode="natural" onSearch={handleSearch} initialQuery={query} />
            </div>

            {/* Examples or Results */}
            <div className="w-full">
                {!query ? (
                    <div className="flex flex-col gap-4 items-center mt-8">
                        <h3 className="text-sm font-medium text-muted-foreground">Try these examples</h3>
                        <div className="flex flex-wrap justify-center gap-3">
                            {EXAMPLE_QUERIES.map((q) => (
                                <button
                                    key={q}
                                    onClick={() => { setQuery(q); setMode('natural'); }}
                                    className="group flex items-center gap-2 px-4 py-2 rounded-full bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 hover:border-primary/50 hover:shadow-md transition-all text-sm"
                                >
                                    <Sparkles className="w-3.5 h-3.5 text-muted-foreground group-hover:text-amber-500 transition-colors" />
                                    {q}
                                    <ArrowRight className="w-3.5 h-3.5 opacity-0 -ml-2 group-hover:opacity-100 group-hover:ml-0 transition-all" />
                                </button>
                            ))}
                        </div>

                        {/* Surprise Feature Placeholder: Tech Stack Hologram Button */}
                        {/* Interactive Discovery Mode - Tech Hologram */}
                        <div className="mt-8 text-center w-full flex flex-col items-center">
                            <div className="flex items-center justify-center gap-2 mb-4">
                                <div className="h-px bg-border w-24"></div>
                                <span className="text-xs text-muted-foreground uppercase tracking-wider">Discovery Mode</span>
                                <div className="h-px bg-border w-24"></div>
                            </div>

                            <TechHologram />
                        </div>
                    </div>
                ) : (
                    <div className="space-y-6">
                        <div className="flex items-center justify-between">
                            <h2 className="text-xl font-semibold">
                                {isLoading ? "Searching..." : `Found ${results?.length || 0} projects`}
                            </h2>
                            {mode === 'natural' && (
                                <Badge variant="secondary" className="gap-1">
                                    <Mic className="w-3 h-3" /> Interpreted by AI
                                </Badge>
                            )}
                        </div>

                        {isLoading ? (
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                                {[1, 2, 3, 4, 5, 6].map((i) => (
                                    <Card key={i} className="h-48 animate-pulse bg-muted/50" />
                                ))}
                            </div>
                        ) : (
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                                {results?.map((project) => (
                                    <ProjectCard key={project.id} project={project} />
                                ))}
                                {results?.length === 0 && (
                                    <div className="col-span-full py-12 text-center text-muted-foreground">
                                        No matching projects found. Try rephrasing your query.
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}
