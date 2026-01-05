"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { projectsApi } from "@/lib/api/projects";
import { Project, ProjectListParams, SearchMode, ProductionReadiness, ProjectLifecycle } from "@/lib/types";
import { ProjectCard } from "@/components/projects/project-card";
import { FilterPanel } from "@/components/projects/filter-panel";
import { SearchBar } from "@/components/search/search-bar";
import { Button } from "@/components/ui/button";
import { Loader2, LayoutGrid, List as ListIcon } from "lucide-react";

export default function ProjectsPage() {
    const [view, setView] = useState<'grid' | 'table'>('grid');
    const [query, setQuery] = useState("");
    const [searchMode, setSearchMode] = useState<SearchMode>('basic');

    const [filters, setFilters] = useState<{
        readiness: ProductionReadiness[];
        lifecycle: ProjectLifecycle[];
    }>({
        readiness: [],
        lifecycle: [],
    });

    const [page, setPage] = useState(1);
    const perPage = 20;

    // Query Params Construction
    const queryParams: ProjectListParams = {
        page,
        per_page: perPage,
        search: query || undefined,
        // Note: API might expect simpler params for array filters, need to adjust based on backend logic.
        // For now assuming client-side filtering or explicit single valued params?
        // The previous implementation plan suggested basic params.
        // We'll pass them but backend support depends on implementation.
    };

    const { data, isLoading } = useQuery({
        queryKey: ['projects', query, searchMode, filters, page],
        queryFn: async () => {
            // If we are in natural/semantic search mode, the endpoint returns a list, not paginated object
            if (query && (searchMode === 'semantic' || searchMode === 'natural')) {
                const results = await projectsApi.search(query, searchMode);
                // Manually filter result if needed or assume backend handles it
                // Simulating pagination wrapper for consistency
                return {
                    items: results,
                    total: results.length,
                    page: 1,
                    pages: 1,
                    per_page: results.length
                };
            }
            return projectsApi.getAll(queryParams);
        },
        placeholderData: (previousData) => previousData,
    });

    const handleSearch = (q: string, mode: SearchMode) => {
        setQuery(q);
        setSearchMode(mode);
        setPage(1); // Reset page on new search
    };

    const clearFilters = () => {
        setFilters({ readiness: [], lifecycle: [] });
    };

    return (
        <div className="flex flex-col gap-6 h-[calc(100vh-4rem)]">
            <div className="flex flex-col gap-4 border-b pb-4">
                <div className="flex items-center justify-between">
                    <h1 className="text-3xl font-bold tracking-tight">Projects</h1>
                    <div className="flex items-center gap-2">
                        <Button variant={view === 'grid' ? "default" : "outline"} size="icon" onClick={() => setView('grid')}>
                            <LayoutGrid className="h-4 w-4" />
                        </Button>
                        <Button variant={view === 'table' ? "default" : "outline"} size="icon" onClick={() => setView('table')}>
                            <ListIcon className="h-4 w-4" />
                        </Button>
                    </div>
                </div>
                <SearchBar onSearch={handleSearch} />
            </div>

            <div className="flex gap-6 flex-1 overflow-hidden">
                <aside className="hidden lg:block w-64 overflow-y-auto pr-2">
                    <FilterPanel
                        filters={filters}
                        onFilterChange={(k, v) => setFilters(prev => ({ ...prev, [k]: v }))}
                        onClearFilters={clearFilters}
                    />
                </aside>

                <main className="flex-1 overflow-y-auto">
                    {isLoading ? (
                        <div className="flex h-64 items-center justify-center">
                            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                        </div>
                    ) : (
                        <>
                            {view === 'grid' ? (
                                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                                    {data?.items.map((project: Project) => (
                                        <ProjectCard key={project.id} project={project} />
                                    ))}
                                </div>
                            ) : (
                                <div>Table View Placeholder</div>
                            )}

                            {!isLoading && data?.items.length === 0 && (
                                <div className="flex flex-col items-center justify-center h-64 text-center">
                                    <h3 className="text-lg font-semibold">No projects found</h3>
                                    <p className="text-muted-foreground">Try adjusting your filters or search query.</p>
                                    <Button variant="link" onClick={clearFilters} className="mt-2">Clear filters</Button>
                                </div>
                            )}

                            {/* Pagination */}
                            {data && data.pages > 1 && (
                                <div className="flex justify-center gap-2 mt-8 mb-4">
                                    <Button
                                        variant="outline"
                                        disabled={page === 1}
                                        onClick={() => setPage(p => Math.max(1, p - 1))}
                                    >
                                        Previous
                                    </Button>
                                    <span className="flex items-center text-sm font-medium">
                                        Page {page} of {data.pages}
                                    </span>
                                    <Button
                                        variant="outline"
                                        disabled={page === data.pages}
                                        onClick={() => setPage(p => p + 1)}
                                    >
                                        Next
                                    </Button>
                                </div>
                            )}
                        </>
                    )}
                </main>
            </div>
        </div>
    );
}
