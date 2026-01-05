"use client";

import { useEffect, useRef } from "react";
import { Project } from "@/lib/types";

interface ProjectDNAProps {
    project: Project;
    width?: number;
    height?: number;
}

export function ProjectDNA({ project, width = 300, height = 400 }: ProjectDNAProps) {
    const canvasRef = useRef<HTMLCanvasElement>(null);

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;
        const ctx = canvas.getContext("2d");
        if (!ctx) return;

        // Animation variables
        let animationFrameId: number;
        let t = 0;

        // DNA Parameters derived from project metrics
        const quality = project.quality_score || 0;
        const complexity = (project.loc_total || 1000) / 5000; // complexity affects rotation speed
        const health = project.health_score || 50;

        // Color palette based on main language
        const getBaseColor = (lang: string) => {
            const colors: Record<string, string> = {
                TypsScript: "#3178c6",
                JavaScript: "#f7df1e",
                Python: "#3776ab",
                Rust: "#dea584",
                Go: "#00add8",
                Java: "#b07219",
                HTML: "#e34c26",
                CSS: "#563d7c",
            };
            return colors[lang] || "#888888";
        };

        const mainColor = getBaseColor(project.languages[0]);
        const secondaryColor = quality > 80 ? "#10b981" : quality > 50 ? "#f59e0b" : "#ef4444";

        const drawHelix = (time: number) => {
            ctx.clearRect(0, 0, width, height);

            const particleCount = 40;
            const strandSpacing = 20;
            const amplitude = 40;
            const speed = 0.02 + (complexity * 0.005);

            // Center canvas
            ctx.save();
            ctx.translate(width / 2, height / 2);

            for (let i = -particleCount / 2; i < particleCount / 2; i++) {
                const y = i * strandSpacing;
                const phase = (i * 0.5) + (time * speed);

                // Strand 1
                const x1 = Math.sin(phase) * amplitude;
                const z1 = Math.cos(phase); // depth scale
                const scale1 = 0.5 + (z1 + 1) * 0.5; // 0.5 to 1.5
                const alpha1 = 0.3 + (z1 + 1) * 0.35;

                // Strand 2 (Opposite)
                const x2 = Math.sin(phase + Math.PI) * amplitude;
                const z2 = Math.cos(phase + Math.PI);
                const scale2 = 0.5 + (z2 + 1) * 0.5;
                const alpha2 = 0.3 + (z2 + 1) * 0.35;

                // Draw Connector (Base Pairs)
                ctx.beginPath();
                ctx.moveTo(x1, y);
                ctx.lineTo(x2, y);
                ctx.strokeStyle = `rgba(150, 150, 150, ${Math.min(alpha1, alpha2) * 0.5})`;
                ctx.lineWidth = 1;
                ctx.stroke();

                // Draw Particle 1
                ctx.beginPath();
                ctx.arc(x1, y, 6 * scale1 * (quality / 100), 0, Math.PI * 2);
                ctx.fillStyle = mainColor;
                ctx.globalAlpha = alpha1;
                ctx.fill();

                // Draw Particle 2
                ctx.beginPath();
                ctx.arc(x2, y, 6 * scale2 * (health / 100), 0, Math.PI * 2);
                ctx.fillStyle = secondaryColor;
                ctx.globalAlpha = alpha2;
                ctx.fill();
            }

            ctx.restore();
        };

        const animate = () => {
            t++;
            drawHelix(t);
            animationFrameId = requestAnimationFrame(animate);
        };

        animate();

        return () => {
            cancelAnimationFrame(animationFrameId);
        };
    }, [project, width, height]);

    return (
        <div className="relative flex flex-col items-center justify-center p-4 bg-gradient-to-b from-gray-50 to-gray-100 dark:from-gray-900 dark:to-black rounded-xl border shadow-inner">
            <canvas
                ref={canvasRef}
                width={width}
                height={height}
                className="rounded-lg"
            />
            <div className="absolute bottom-4 text-xs font-mono text-muted-foreground bg-background/80 px-2 py-1 rounded backdrop-blur-sm">
                DNA: {project.id.substring(0, 8)}
            </div>
        </div>
    );
}
