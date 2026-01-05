'use client';

import React, { useState, useEffect } from 'react';

interface DeploymentTarget {
  id: string;
  name: string;
  icon: string;
  description: string;
  supported: boolean;
  pricing: string;
  bestFor: string[];
}

interface ProjectDeployConfig {
  projectId: number;
  projectName: string;
  projectType: string;
  language: string;
  framework: string | null;
  hasDocker: boolean;
  hasEnvExample: boolean;
  recommendedPlatform: string;
  deploymentStatus: 'not_deployed' | 'deploying' | 'deployed' | 'failed';
  deployedUrl: string | null;
  lastDeployed: string | null;
  envVars: { key: string; required: boolean; hasValue: boolean }[];
  estimatedCost: string;
}

interface DeployPipelineData {
  projects: ProjectDeployConfig[];
  deploymentTargets: DeploymentTarget[];
}

const DEPLOYMENT_TARGETS: DeploymentTarget[] = [
  {
    id: 'vercel',
    name: 'Vercel',
    icon: '▲',
    description: 'Best for Next.js, React, and static sites',
    supported: true,
    pricing: 'Free tier available',
    bestFor: ['Next.js', 'React', 'Vue', 'Static'],
  },
  {
    id: 'railway',
    name: 'Railway',
    icon: '🚂',
    description: 'Simple deployment for any language',
    supported: true,
    pricing: '$5/mo hobby plan',
    bestFor: ['Python', 'Node.js', 'Go', 'Docker'],
  },
  {
    id: 'fly',
    name: 'Fly.io',
    icon: '✈️',
    description: 'Edge deployment with global distribution',
    supported: true,
    pricing: 'Free tier available',
    bestFor: ['Docker', 'Go', 'Elixir', 'Edge'],
  },
  {
    id: 'render',
    name: 'Render',
    icon: '◉',
    description: 'Full-stack cloud platform',
    supported: true,
    pricing: 'Free tier available',
    bestFor: ['Python', 'Node.js', 'Docker', 'PostgreSQL'],
  },
  {
    id: 'aws',
    name: 'AWS Lambda',
    icon: '☁️',
    description: 'Serverless functions at scale',
    supported: true,
    pricing: 'Pay per invocation',
    bestFor: ['Serverless', 'API', 'Microservices'],
  },
];

export default function DeployPipeline() {
  const [data, setData] = useState<DeployPipelineData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedProject, setSelectedProject] = useState<ProjectDeployConfig | null>(null);
  const [selectedTarget, setSelectedTarget] = useState<string>('vercel');
  const [deploying, setDeploying] = useState<number | null>(null);
  const [showEnvModal, setShowEnvModal] = useState(false);

  useEffect(() => {
    fetchDeployData();
  }, []);

  const fetchDeployData = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('http://localhost:8000/api/v1/catalog/deploy-config?limit=10', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) throw new Error('Failed to fetch deploy config');
      const result = await response.json();
      setData({ ...result, deploymentTargets: DEPLOYMENT_TARGETS });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const handleDeploy = async (project: ProjectDeployConfig) => {
    setDeploying(project.projectId);
    // Simulate deployment
    await new Promise(resolve => setTimeout(resolve, 3000));
    setDeploying(null);
    // In real implementation, this would trigger actual deployment
    alert(`Deployment initiated for ${project.projectName} to ${selectedTarget}!\n\nIn production, this would:\n1. Connect to your ${selectedTarget} account\n2. Create deployment config\n3. Push code and build\n4. Return live URL`);
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'deployed':
        return <span className="px-2 py-0.5 text-xs bg-[#00ff88]/20 text-[#00ff88] rounded border border-[#00ff88]/50">LIVE</span>;
      case 'deploying':
        return <span className="px-2 py-0.5 text-xs bg-[#00f3ff]/20 text-[#00f3ff] rounded border border-[#00f3ff]/50 animate-pulse">DEPLOYING</span>;
      case 'failed':
        return <span className="px-2 py-0.5 text-xs bg-[#ff003c]/20 text-[#ff003c] rounded border border-[#ff003c]/50">FAILED</span>;
      default:
        return <span className="px-2 py-0.5 text-xs bg-gray-500/20 text-gray-400 rounded border border-gray-500/50">NOT DEPLOYED</span>;
    }
  };

  const getLanguageColor = (lang: string) => {
    const colors: Record<string, string> = {
      python: 'bg-blue-500/20 text-blue-400 border-blue-500/50',
      javascript: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50',
      typescript: 'bg-blue-400/20 text-blue-300 border-blue-400/50',
      go: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/50',
      rust: 'bg-orange-500/20 text-orange-400 border-orange-500/50',
    };
    return colors[lang.toLowerCase()] || 'bg-gray-500/20 text-gray-400 border-gray-500/50';
  };

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
            <span className="text-[#ff003c]">///</span> ONE-CLICK DEPLOY PIPELINE
          </h2>
          <p className="text-gray-500 text-sm mt-1">Deploy your projects to production instantly</p>
        </div>
      </div>

      {/* Deployment Targets */}
      <div className="bg-[#0a0a0f] border border-[#1a1a2f] rounded-lg p-4">
        <h3 className="text-sm font-semibold text-gray-400 mb-3">SELECT DEPLOYMENT TARGET</h3>
        <div className="flex gap-3 overflow-x-auto pb-2">
          {DEPLOYMENT_TARGETS.map((target) => (
            <button
              key={target.id}
              onClick={() => setSelectedTarget(target.id)}
              className={`flex-shrink-0 p-3 rounded-lg border transition-all ${
                selectedTarget === target.id
                  ? 'bg-[#00f3ff]/10 border-[#00f3ff] shadow-lg shadow-[#00f3ff]/10'
                  : 'bg-[#050508] border-[#1a1a2f] hover:border-[#2a2a4f]'
              }`}
            >
              <div className="flex items-center gap-2">
                <span className="text-2xl">{target.icon}</span>
                <div className="text-left">
                  <p className={`font-semibold ${selectedTarget === target.id ? 'text-[#00f3ff]' : 'text-white'}`}>
                    {target.name}
                  </p>
                  <p className="text-xs text-gray-500">{target.pricing}</p>
                </div>
              </div>
            </button>
          ))}
        </div>
        <p className="text-xs text-gray-500 mt-2">
          {DEPLOYMENT_TARGETS.find(t => t.id === selectedTarget)?.description}
        </p>
      </div>

      {/* Projects List */}
      <div className="space-y-3">
        {data?.projects.map((project) => (
          <div
            key={project.projectId}
            className={`bg-[#0a0a0f] border rounded-lg overflow-hidden transition-all ${
              selectedProject?.projectId === project.projectId
                ? 'border-[#00f3ff]'
                : 'border-[#1a1a2f] hover:border-[#2a2a4f]'
            }`}
          >
            {/* Project Header */}
            <div
              className="p-4 cursor-pointer"
              onClick={() => setSelectedProject(
                selectedProject?.projectId === project.projectId ? null : project
              )}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-[#7000ff] to-[#00f3ff] flex items-center justify-center text-white font-bold">
                    {project.projectName.charAt(0).toUpperCase()}
                  </div>
                  <div>
                    <h3 className="font-semibold text-white">{project.projectName}</h3>
                    <div className="flex items-center gap-2 mt-1">
                      <span className={`px-2 py-0.5 text-xs rounded border ${getLanguageColor(project.language)}`}>
                        {project.language}
                      </span>
                      {project.framework && (
                        <span className="px-2 py-0.5 text-xs bg-[#7000ff]/20 text-[#a855f7] rounded border border-[#7000ff]/50">
                          {project.framework}
                        </span>
                      )}
                      {project.hasDocker && (
                        <span className="px-2 py-0.5 text-xs bg-blue-500/20 text-blue-400 rounded border border-blue-500/50">
                          🐳 Docker
                        </span>
                      )}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  {getStatusBadge(project.deploymentStatus)}
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDeploy(project);
                    }}
                    disabled={deploying === project.projectId}
                    className={`px-4 py-2 rounded-lg font-semibold text-sm transition-all ${
                      deploying === project.projectId
                        ? 'bg-[#00f3ff]/20 text-[#00f3ff] cursor-wait'
                        : 'bg-gradient-to-r from-[#00f3ff] to-[#7000ff] text-black hover:shadow-lg hover:shadow-[#00f3ff]/20'
                    }`}
                  >
                    {deploying === project.projectId ? (
                      <span className="flex items-center gap-2">
                        <span className="animate-spin">⚡</span> Deploying...
                      </span>
                    ) : (
                      <span className="flex items-center gap-2">
                        🚀 Deploy to {DEPLOYMENT_TARGETS.find(t => t.id === selectedTarget)?.name}
                      </span>
                    )}
                  </button>
                </div>
              </div>
            </div>

            {/* Expanded Details */}
            {selectedProject?.projectId === project.projectId && (
              <div className="border-t border-[#1a1a2f] p-4 bg-[#050508]">
                <div className="grid grid-cols-3 gap-4">
                  {/* Deployment Config */}
                  <div className="space-y-3">
                    <h4 className="text-sm font-semibold text-[#00f3ff]">Deployment Config</h4>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-500">Platform:</span>
                        <span className="text-white">{project.recommendedPlatform}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500">Est. Cost:</span>
                        <span className="text-[#00ff88]">{project.estimatedCost}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500">Docker Ready:</span>
                        <span className={project.hasDocker ? 'text-[#00ff88]' : 'text-yellow-400'}>
                          {project.hasDocker ? '✓ Yes' : '⚠ Generate'}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Environment Variables */}
                  <div className="space-y-3">
                    <h4 className="text-sm font-semibold text-[#00f3ff]">Environment Variables</h4>
                    <div className="space-y-1">
                      {project.envVars.slice(0, 4).map((env) => (
                        <div key={env.key} className="flex items-center justify-between text-sm">
                          <span className="text-gray-400 font-mono text-xs">{env.key}</span>
                          <span className={env.hasValue ? 'text-[#00ff88]' : 'text-[#ff003c]'}>
                            {env.hasValue ? '✓' : '✗'}
                          </span>
                        </div>
                      ))}
                      {project.envVars.length > 4 && (
                        <p className="text-xs text-gray-500">+{project.envVars.length - 4} more</p>
                      )}
                    </div>
                    <button className="text-xs text-[#00f3ff] hover:underline">
                      Configure Environment →
                    </button>
                  </div>

                  {/* Quick Actions */}
                  <div className="space-y-3">
                    <h4 className="text-sm font-semibold text-[#00f3ff]">Quick Actions</h4>
                    <div className="space-y-2">
                      <button className="w-full px-3 py-2 text-sm bg-[#1a1a2f] text-white rounded hover:bg-[#2a2a4f] transition-all flex items-center gap-2">
                        <span>📄</span> Generate Dockerfile
                      </button>
                      <button className="w-full px-3 py-2 text-sm bg-[#1a1a2f] text-white rounded hover:bg-[#2a2a4f] transition-all flex items-center gap-2">
                        <span>⚙️</span> Create .env Template
                      </button>
                      <button className="w-full px-3 py-2 text-sm bg-[#1a1a2f] text-white rounded hover:bg-[#2a2a4f] transition-all flex items-center gap-2">
                        <span>📝</span> Generate CI/CD Config
                      </button>
                    </div>
                  </div>
                </div>

                {/* Deployment URL */}
                {project.deployedUrl && (
                  <div className="mt-4 p-3 bg-[#00ff88]/10 border border-[#00ff88]/30 rounded-lg flex items-center justify-between">
                    <div>
                      <p className="text-xs text-[#00ff88] uppercase tracking-wider">Live URL</p>
                      <a href={project.deployedUrl} target="_blank" rel="noopener noreferrer" className="text-white hover:text-[#00f3ff]">
                        {project.deployedUrl}
                      </a>
                    </div>
                    <button className="px-3 py-1 text-sm bg-[#00ff88]/20 text-[#00ff88] rounded hover:bg-[#00ff88]/30">
                      Open →
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
