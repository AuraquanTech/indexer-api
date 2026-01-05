"use client";

import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import {
    ProjectLifecycle,
    ProductionReadiness,
    ProjectType
} from "@/lib/types";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { FilterX } from "lucide-react";

interface FilterPanelProps {
    filters: {
        readiness: ProductionReadiness[];
        lifecycle: ProjectLifecycle[];
        // types: ProjectType[];
        // languages: string[];
    };
    onFilterChange: (key: string, value: any) => void;
    onClearFilters: () => void;
}

export function FilterPanel({ filters, onFilterChange, onClearFilters }: FilterPanelProps) {
    const toggleFilter = (key: string, item: string, current: string[]) => {
        if (current.includes(item)) {
            onFilterChange(key, current.filter((i) => i !== item));
        } else {
            onFilterChange(key, [...current, item]);
        }
    };

    return (
        <div className="w-64 space-y-6 pt-4">
            <div className="flex items-center justify-between">
                <h3 className="font-semibold">Filters</h3>
                <Button variant="ghost" size="sm" onClick={onClearFilters} className="h-8 px-2 text-xs">
                    <FilterX className="mr-1 h-3 w-3" />
                    Clear
                </Button>
            </div>

            <div className="space-y-4">
                <div>
                    <Label className="text-sm font-medium mb-2 block">Readiness</Label>
                    <ScrollArea className="h-[200px] border rounded-md p-2">
                        <div className="space-y-2">
                            {Object.values(ProductionReadiness).map((status) => (
                                <div key={status} className="flex items-center space-x-2">
                                    <Checkbox
                                        id={`readiness-${status}`}
                                        checked={filters.readiness.includes(status)}
                                        onCheckedChange={() => toggleFilter('readiness', status, filters.readiness)}
                                    />
                                    <Label htmlFor={`readiness-${status}`} className="text-sm font-normal capitalize cursor-pointer">
                                        {status}
                                    </Label>
                                </div>
                            ))}
                        </div>
                    </ScrollArea>
                </div>

                <div>
                    <Label className="text-sm font-medium mb-2 block">Lifecycle</Label>
                    <div className="space-y-2">
                        {Object.values(ProjectLifecycle).map((status) => (
                            <div key={status} className="flex items-center space-x-2">
                                <Checkbox
                                    id={`lifecycle-${status}`}
                                    checked={filters.lifecycle.includes(status)}
                                    onCheckedChange={() => toggleFilter('lifecycle', status, filters.lifecycle)}
                                />
                                <Label htmlFor={`lifecycle-${status}`} className="text-sm font-normal capitalize cursor-pointer">
                                    {status}
                                </Label>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}
