"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { projectsApi } from "@/lib/api/projects";
import { BattleView } from "@/components/comparison/battle-view";
import { Project } from "@/lib/types";
import { Swords, Check, ChevronsUpDown } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
    Command,
    CommandEmpty,
    CommandGroup,
    CommandInput,
    CommandItem,
    CommandList,
} from "@/components/ui/command";
import {
    Popover,
    PopoverContent,
    PopoverTrigger,
} from "@/components/ui/popover";

export default function ComparePage() {
    const [openA, setOpenA] = useState(false);
    const [openB, setOpenB] = useState(false);
    const [selectedIdA, setSelectedIdA] = useState<string | null>(null);
    const [selectedIdB, setSelectedIdB] = useState<string | null>(null);

    // Ideally fetch simple list for combobox
    const { data, isLoading } = useQuery({
        queryKey: ['projects-list'],
        queryFn: () => projectsApi.getAll({ per_page: 100 }), // Limit for dropdown
    });

    const projects = data?.items || [];

    const projectA = projects.find(p => p.id === selectedIdA);
    const projectB = projects.find(p => p.id === selectedIdB);

    const ProjectSelector = ({
        activeId,
        onSelect,
        open,
        setOpen,
        label
    }: {
        activeId: string | null,
        onSelect: (id: string) => void,
        open: boolean,
        setOpen: (v: boolean) => void,
        label: string
    }) => (
        <Popover open={open} onOpenChange={setOpen}>
            <PopoverTrigger asChild>
                <Button
                    variant="outline"
                    role="combobox"
                    aria-expanded={open}
                    className="w-[250px] justify-between"
                >
                    {activeId
                        ? projects.find((p) => p.id === activeId)?.name
                        : `Select ${label}...`}
                    <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
                </Button>
            </PopoverTrigger>
            <PopoverContent className="w-[250px] p-0">
                <Command>
                    <CommandInput placeholder={`Search ${label}...`} />
                    <CommandList>
                        <CommandEmpty>No project found.</CommandEmpty>
                        <CommandGroup>
                            {projects.map((project) => (
                                <CommandItem
                                    key={project.id}
                                    value={project.name}
                                    onSelect={(currentValue) => {
                                        onSelect(project.id);
                                        setOpen(false);
                                    }}
                                >
                                    <Check
                                        className={cn(
                                            "mr-2 h-4 w-4",
                                            activeId === project.id ? "opacity-100" : "opacity-0"
                                        )}
                                    />
                                    {project.name}
                                </CommandItem>
                            ))}
                        </CommandGroup>
                    </CommandList>
                </Command>
            </PopoverContent>
        </Popover>
    );

    return (
        <div className="flex flex-col gap-8 max-w-5xl mx-auto w-full items-center py-8">
            <div className="text-center space-y-2">
                <h1 className="text-4xl font-extrabold flex items-center justify-center gap-3">
                    <Swords className="h-10 w-10 text-red-500" />
                    Battle Mode
                </h1>
                <p className="text-muted-foreground">Select two projects to compare their stats head-to-head.</p>
            </div>

            <div className="flex flex-wrap gap-8 items-center justify-center p-6 border rounded-xl bg-card shadow-sm">
                <div className="flex flex-col items-center gap-2">
                    <span className="text-xs font-bold text-muted-foreground uppercase">Challenger 1</span>
                    <ProjectSelector
                        label="Project A"
                        activeId={selectedIdA}
                        onSelect={setSelectedIdA}
                        open={openA}
                        setOpen={setOpenA}
                    />
                </div>

                <div className="font-black text-2xl text-muted-foreground">VS</div>

                <div className="flex flex-col items-center gap-2">
                    <span className="text-xs font-bold text-muted-foreground uppercase">Challenger 2</span>
                    <ProjectSelector
                        label="Project B"
                        activeId={selectedIdB}
                        onSelect={setSelectedIdB}
                        open={openB}
                        setOpen={setOpenB}
                    />
                </div>
            </div>

            <div className="w-full min-h-[400px]">
                {projectA && projectB ? (
                    <BattleView projectA={projectA} projectB={projectB} />
                ) : (
                    <div className="flex items-center justify-center h-64 border-2 border-dashed rounded-xl bg-muted/30">
                        <p className="text-muted-foreground">Select two projects to start the battle.</p>
                    </div>
                )}
            </div>
        </div>
    );
}
