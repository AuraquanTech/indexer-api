'use client';

import React, { useState, useEffect } from 'react';

interface ReadinessItem {
  id: string;
  category: string;
  item: string;
  status: 'complete' | 'incomplete' | 'warning' | 'critical';
  description: string;
  action: string;
  priority: number;
}

interface ProjectReadiness {
  projectName: string;
  projectId: number;
  overallScore: number;
  readyToLaunch: boolean;
  estimatedTimeToLaunch: string;
  blockers: number;
  warnings: number;
  items: ReadinessItem[];
  categories: {
    name: string;
    score: number;
    items: ReadinessItem[];
  }[];
}

interface LaunchReadinessData {
  projects: ProjectReadiness[];
  portfolioReadiness: number;
  readyToLaunchCount: number;
  totalBlockers: number;
}

export default function LaunchReadiness() {
  const [data, setData] = useState<LaunchReadinessData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedProject, setSelectedProject] = useState<ProjectReadiness | null>(null);
  const [filter, setFilter] = useState<'all' | 'ready' | 'blocked'>('all');

  useEffect(() => {
    fetchReadinessData();
  }, []);

  const fetchReadinessData = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('http://localhost:8000/api/v1/catalog/launch-readiness?limit=10', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) throw new Error('Failed to fetch readiness data');
      const result = await response.json();
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-[#00ff88]';
    if (score >= 60) return 'text-[#00f3ff]';
    if (score >= 40) return 'text-yellow-400';
    return 'text-[#ff003c]';
  };

  const getScoreBgColor = (score: number) => {
    if (score >= 80) return 'bg-[#00ff88]/20 border-[#00ff88]/50';
    if (score >= 60) return 'bg-[#00f3ff]/20 border-[#00f3ff]/50';
    if (score >= 40) return 'bg-yellow-400/20 border-yellow-400/50';
    return 'bg-[#ff003c]/20 border-[#ff003c]/50';
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'complete': return '✓';
      case 'incomplete': return '○';
      case 'warning': return '⚠';
      case 'critical': return '✗';
      default: return '○';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'complete': return 'text-[#00ff88]';
      case 'incomplete': return 'text-gray-400';
      case 'warning': return 'text-yellow-400';
      case 'critical': return 'text-[#ff003c]';
      default: return 'text-gray-400';
    }
  };

  const filteredProjects = data?.projects.filter(p => {
    if (filter === 'ready') return p.readyToLaunch;
    if (filter === 'blocked') return !p.readyToLaunch;
    return true;
  }) || [];

  if (loading) {
    return (
      <div className="bg-[#0a0a0f] border border-[#1a1a2f] rounded-lg p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-[#1a1a2f] rounded w-1/3"></div>
          <div className="h-32 bg-[#1a1a2f] rounded"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-[#0a0a0f] border border-[#ff003c]/50 rounded-lg p-6">
        <p className="text-[#ff003c]">Error: {error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-[#00f3ff] tracking-wider flex items-center gap-2">
            <span className="text-[#ff003c]">///</span> LAUNCH READINESS CENTER
          </h2>
          <p className="text-gray-500 text-sm mt-1">Track deployment blockers and launch status</p>
        </div>
        <div className="flex gap-2">
          {['all', 'ready', 'blocked'].map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f as typeof filter)}
              className={`px-3 py-1 text-xs rounded border transition-all ${
                filter === f
                  ? 'bg-[#00f3ff]/20 border-[#00f3ff] text-[#00f3ff]'
                  : 'bg-[#0a0a0f] border-[#1a1a2f] text-gray-400 hover:border-gray-600'
              }`}
            >
              {f.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      {/* Portfolio Overview */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-[#0a0a0f] border border-[#1a1a2f] rounded-lg p-4">
          <p className="text-gray-500 text-xs uppercase tracking-wider">Portfolio Readiness</p>
          <p className={`text-3xl font-bold mt-1 ${getScoreColor(data?.portfolioReadiness || 0)}`}>
            {data?.portfolioReadiness || 0}%
          </p>
        </div>
        <div className="bg-[#0a0a0f] border border-[#1a1a2f] rounded-lg p-4">
          <p className="text-gray-500 text-xs uppercase tracking-wider">Ready to Launch</p>
          <p className="text-3xl font-bold mt-1 text-[#00ff88]">
            {data?.readyToLaunchCount || 0}
          </p>
        </div>
        <div className="bg-[#0a0a0f] border border-[#1a1a2f] rounded-lg p-4">
          <p className="text-gray-500 text-xs uppercase tracking-wider">Total Blockers</p>
          <p className="text-3xl font-bold mt-1 text-[#ff003c]">
            {data?.totalBlockers || 0}
          </p>
        </div>
        <div className="bg-[#0a0a0f] border border-[#1a1a2f] rounded-lg p-4">
          <p className="text-gray-500 text-xs uppercase tracking-wider">Avg Time to Launch</p>
          <p className="text-3xl font-bold mt-1 text-[#00f3ff]">
            2.4<span className="text-lg">wks</span>
          </p>
        </div>
      </div>

      {/* Projects Grid */}
      <div className="grid grid-cols-2 gap-4">
        {filteredProjects.map((project) => (
          <div
            key={project.projectId}
            onClick={() => setSelectedProject(selectedProject?.projectId === project.projectId ? null : project)}
            className={`bg-[#0a0a0f] border rounded-lg p-4 cursor-pointer transition-all ${
              selectedProject?.projectId === project.projectId
                ? 'border-[#00f3ff] shadow-lg shadow-[#00f3ff]/10'
                : 'border-[#1a1a2f] hover:border-[#2a2a4f]'
            }`}
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <h3 className="font-semibold text-white truncate">{project.projectName}</h3>
                  {project.readyToLaunch && (
                    <span className="px-2 py-0.5 text-xs bg-[#00ff88]/20 text-[#00ff88] rounded border border-[#00ff88]/50">
                      READY
                    </span>
                  )}
                </div>
                <p className="text-gray-500 text-xs mt-1">
                  Est. {project.estimatedTimeToLaunch} to launch
                </p>
              </div>
              <div className={`w-16 h-16 rounded-full border-4 flex items-center justify-center ${getScoreBgColor(project.overallScore)}`}>
                <span className={`text-xl font-bold ${getScoreColor(project.overallScore)}`}>
                  {project.overallScore}
                </span>
              </div>
            </div>

            {/* Mini Progress Bars */}
            <div className="mt-4 space-y-2">
              {project.categories.slice(0, 4).map((cat) => (
                <div key={cat.name} className="flex items-center gap-2">
                  <span className="text-xs text-gray-500 w-20 truncate">{cat.name}</span>
                  <div className="flex-1 h-1.5 bg-[#1a1a2f] rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all ${
                        cat.score >= 80 ? 'bg-[#00ff88]' :
                        cat.score >= 60 ? 'bg-[#00f3ff]' :
                        cat.score >= 40 ? 'bg-yellow-400' : 'bg-[#ff003c]'
                      }`}
                      style={{ width: `${cat.score}%` }}
                    />
                  </div>
                  <span className="text-xs text-gray-400 w-8">{cat.score}%</span>
                </div>
              ))}
            </div>

            {/* Blockers Summary */}
            <div className="mt-3 flex items-center gap-4 text-xs">
              {project.blockers > 0 && (
                <span className="text-[#ff003c] flex items-center gap-1">
                  <span>✗</span> {project.blockers} blockers
                </span>
              )}
              {project.warnings > 0 && (
                <span className="text-yellow-400 flex items-center gap-1">
                  <span>⚠</span> {project.warnings} warnings
                </span>
              )}
              {project.blockers === 0 && project.warnings === 0 && (
                <span className="text-[#00ff88] flex items-center gap-1">
                  <span>✓</span> No issues
                </span>
              )}
            </div>

            {/* Expanded Details */}
            {selectedProject?.projectId === project.projectId && (
              <div className="mt-4 pt-4 border-t border-[#1a1a2f] space-y-3">
                <h4 className="text-sm font-semibold text-[#00f3ff]">Launch Checklist</h4>
                {project.items.filter(i => i.status !== 'complete').slice(0, 6).map((item) => (
                  <div key={item.id} className="flex items-start gap-3 p-2 bg-[#050508] rounded">
                    <span className={`text-lg ${getStatusColor(item.status)}`}>
                      {getStatusIcon(item.status)}
                    </span>
                    <div className="flex-1">
                      <p className="text-sm text-white">{item.item}</p>
                      <p className="text-xs text-gray-500 mt-0.5">{item.description}</p>
                      <p className="text-xs text-[#00f3ff] mt-1">→ {item.action}</p>
                    </div>
                    <span className={`text-xs px-2 py-0.5 rounded ${
                      item.status === 'critical' ? 'bg-[#ff003c]/20 text-[#ff003c]' :
                      item.status === 'warning' ? 'bg-yellow-400/20 text-yellow-400' :
                      'bg-gray-500/20 text-gray-400'
                    }`}>
                      {item.category}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
