"use client";

import { useEffect, useRef, useState } from "react";
import { Badge } from "@/components/ui/badge";

interface Tag {
    value: string;
    weight: number;
}

const TAGS: Tag[] = [
    { value: "Python", weight: 5 }, { value: "React", weight: 5 },
    { value: "TypeScript", weight: 5 }, { value: "Next.js", weight: 4 },
    { value: "FastAPI", weight: 4 }, { value: "Docker", weight: 4 },
    { value: "Kubernetes", weight: 3 }, { value: "Tailwind", weight: 3 },
    { value: "PostgreSQL", weight: 3 }, { value: "Redis", weight: 3 },
    { value: "GraphQL", weight: 3 }, { value: "AWS", weight: 3 },
    { value: "Azure", weight: 2 }, { value: "Go", weight: 3 },
    { value: "Rust", weight: 2 }, { value: "Zod", weight: 2 },
    { value: "Prisma", weight: 2 }, { value: "LLM", weight: 4 },
    { value: "OpenAI", weight: 3 }, { value: "LangChain", weight: 3 },
    { value: "Terraform", weight: 3 }, { value: "Jest", weight: 2 },
    { value: "PyTest", weight: 2 }, { value: "Vite", weight: 2 },
    { value: "Node.js", weight: 4 }, { value: "Express", weight: 3 },
    { value: "MongoDB", weight: 3 }, { value: "Vue", weight: 2 },
    { value: "Angular", weight: 2 }, { value: "Java", weight: 3 },
    { value: "Spring", weight: 3 }, { value: "C#", weight: 3 },
    { value: ".NET", weight: 3 }, { value: "Kotlin", weight: 2 },
    { value: "Swift", weight: 2 }, { value: "Flutter", weight: 2 },
];

export function TechHologram() {
    const containerRef = useRef<HTMLDivElement>(null);
    const [rotation, setRotation] = useState({ x: 0, y: 0 });

    useEffect(() => {
        let animationFrame: number;
        let angle = 0;

        const animate = () => {
            angle += 0.005;
            // Auto-rotation when idle
            setRotation(prev => ({
                x: Math.sin(angle) * 10,
                y: angle * 20
            }));
            animationFrame = requestAnimationFrame(animate);
        };

        animationFrame = requestAnimationFrame(animate);

        return () => cancelAnimationFrame(animationFrame);
    }, []);

    // Fibonacci sphere algorithm to distribute points on a sphere
    const tags = TAGS.map((tag, i) => {
        const phi = Math.acos(-1 + (2 * i) / TAGS.length);
        const theta = Math.sqrt(TAGS.length * Math.PI) * phi;

        // Convert spherical to cartesian
        const radius = 220; // Sphere radius
        const x = radius * Math.cos(theta) * Math.sin(phi);
        const y = radius * Math.sin(theta) * Math.sin(phi);
        const z = radius * Math.cos(phi);

        return { ...tag, x, y, z };
    });

    return (
        <div
            ref={containerRef}
            className="relative w-[500px] h-[500px] perspective-1000 mx-auto"
            style={{ perspective: "1000px" }}
        >
            <div
                className="absolute inset-0 preserve-3d transition-transform duration-100 ease-linear"
                style={{
                    transform: `rotateY(${rotation.y}deg) rotateX(${rotation.x}deg)`,
                    transformStyle: "preserve-3d"
                }}
            >
                {tags.map((tag, i) => (
                    <div
                        key={i}
                        className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 cursor-pointer hover:scale-125 transition-transform duration-300"
                        style={{
                            transform: `translate3d(${tag.x}px, ${tag.y}px, ${tag.z}px)`,
                            // Always face front (billboard effect)
                            // We apply opposite rotation to element
                        }}
                    >
                        <div
                            style={{
                                transform: `rotateX(${-rotation.x}deg) rotateY(${-rotation.y}deg)`,
                                opacity: Math.max(0.3, (tag.z + 220) / 440) // Fade items in back
                            }}
                        >
                            <Badge variant={tag.weight > 3 ? "default" : "outline"} className={tag.weight > 3 ? "text-lg py-1 px-3" : "text-xs"}>
                                {tag.value}
                            </Badge>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
