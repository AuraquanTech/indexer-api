'use client';

import React, { useState, useEffect } from 'react';

interface RevenueMetrics {
  projectId: number;
  projectName: string;
  status: 'pre-revenue' | 'launched' | 'growing' | 'mature';
  mrr: number;
  arr: number;
  projectedMrr: number;
  growthRate: number;
  customers: number;
  churnRate: number;
  ltv: number;
  cac: number;
  revenueHistory: { month: string; revenue: number }[];
  topCustomers: { name: string; revenue: number; plan: string }[];
}

interface RevenueData {
  projects: RevenueMetrics[];
  totalMrr: number;
  totalArr: number;
  avgGrowthRate: number;
  totalCustomers: number;
  portfolioHealth: 'excellent' | 'good' | 'needs_attention' | 'critical';
}

export default function RevenueTracker() {
  const [data, setData] = useState<RevenueData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedProject, setSelectedProject] = useState<RevenueMetrics | null>(null);
  const [timeRange, setTimeRange] = useState<'30d' | '90d' | '1y' | 'all'>('90d');

  useEffect(() => {
    fetchRevenueData();
  }, []);

  const fetchRevenueData = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('http://localhost:8000/api/v1/catalog/revenue-metrics?limit=10', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) throw new Error('Failed to fetch revenue data');
      const result = await response.json();
      setData(result);
      if (result.projects.length > 0) {
        setSelectedProject(result.projects[0]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount: number) => {
    if (amount >= 1000000) return `$${(amount / 1000000).toFixed(1)}M`;
    if (amount >= 1000) return `$${(amount / 1000).toFixed(1)}K`;
    return `$${amount.toFixed(0)}`;
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'mature': return <span className="px-2 py-0.5 text-xs bg-[#00ff88]/20 text-[#00ff88] rounded border border-[#00ff88]/50">MATURE</span>;
      case 'growing': return <span className="px-2 py-0.5 text-xs bg-[#00f3ff]/20 text-[#00f3ff] rounded border border-[#00f3ff]/50">GROWING</span>;
      case 'launched': return <span className="px-2 py-0.5 text-xs bg-[#7000ff]/20 text-[#a855f7] rounded border border-[#7000ff]/50">LAUNCHED</span>;
      default: return <span className="px-2 py-0.5 text-xs bg-yellow-400/20 text-yellow-400 rounded border border-yellow-400/50">PRE-REVENUE</span>;
    }
  };

  const getHealthColor = (health: string) => {
    switch (health) {
      case 'excellent': return 'text-[#00ff88]';
      case 'good': return 'text-[#00f3ff]';
      case 'needs_attention': return 'text-yellow-400';
      default: return 'text-[#ff003c]';
    }
  };

  // Simple sparkline component
  const Sparkline = ({ data, color }: { data: number[]; color: string }) => {
    const max = Math.max(...data);
    const min = Math.min(...data);
    const range = max - min || 1;
    const height = 30;
    const width = 100;
    const points = data.map((v, i) => {
      const x = (i / (data.length - 1)) * width;
      const y = height - ((v - min) / range) * height;
      return `${x},${y}`;
    }).join(' ');

    return (
      <svg width={width} height={height} className="inline-block">
        <polyline
          fill="none"
          stroke={color}
          strokeWidth="2"
          points={points}
        />
      </svg>
    );
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
            <span className="text-[#ff003c]">///</span> REVENUE COMMAND CENTER
          </h2>
          <p className="text-gray-500 text-sm mt-1">Track actual vs projected revenue across your portfolio</p>
        </div>
        <div className="flex gap-2">
          {(['30d', '90d', '1y', 'all'] as const).map((range) => (
            <button
              key={range}
              onClick={() => setTimeRange(range)}
              className={`px-3 py-1 text-xs rounded border transition-all ${
                timeRange === range
                  ? 'bg-[#00f3ff]/20 border-[#00f3ff] text-[#00f3ff]'
                  : 'bg-[#0a0a0f] border-[#1a1a2f] text-gray-400 hover:border-gray-600'
              }`}
            >
              {range.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      {/* Portfolio Overview */}
      <div className="grid grid-cols-5 gap-4">
        <div className="bg-gradient-to-br from-[#00f3ff]/20 to-[#7000ff]/20 border border-[#00f3ff]/30 rounded-lg p-4">
          <p className="text-gray-400 text-xs uppercase tracking-wider">Total MRR</p>
          <p className="text-3xl font-bold mt-1 text-white">{formatCurrency(data?.totalMrr || 0)}</p>
          <p className="text-xs text-[#00ff88] mt-1">+12.5% from last month</p>
        </div>
        <div className="bg-[#0a0a0f] border border-[#1a1a2f] rounded-lg p-4">
          <p className="text-gray-500 text-xs uppercase tracking-wider">Total ARR</p>
          <p className="text-3xl font-bold mt-1 text-[#00f3ff]">{formatCurrency(data?.totalArr || 0)}</p>
        </div>
        <div className="bg-[#0a0a0f] border border-[#1a1a2f] rounded-lg p-4">
          <p className="text-gray-500 text-xs uppercase tracking-wider">Avg Growth</p>
          <p className="text-3xl font-bold mt-1 text-[#00ff88]">{data?.avgGrowthRate || 0}%</p>
        </div>
        <div className="bg-[#0a0a0f] border border-[#1a1a2f] rounded-lg p-4">
          <p className="text-gray-500 text-xs uppercase tracking-wider">Total Customers</p>
          <p className="text-3xl font-bold mt-1 text-[#7000ff]">{data?.totalCustomers || 0}</p>
        </div>
        <div className="bg-[#0a0a0f] border border-[#1a1a2f] rounded-lg p-4">
          <p className="text-gray-500 text-xs uppercase tracking-wider">Portfolio Health</p>
          <p className={`text-2xl font-bold mt-1 uppercase ${getHealthColor(data?.portfolioHealth || 'good')}`}>
            {data?.portfolioHealth?.replace('_', ' ') || 'Good'}
          </p>
        </div>
      </div>

      {/* Revenue by Project */}
      <div className="grid grid-cols-3 gap-6">
        {/* Project List */}
        <div className="space-y-4">
          <h3 className="text-sm font-semibold text-gray-400">REVENUE BY PROJECT</h3>
          <div className="space-y-2 max-h-[400px] overflow-y-auto pr-2">
            {data?.projects.map((project) => (
              <button
                key={project.projectId}
                onClick={() => setSelectedProject(project)}
                className={`w-full p-3 rounded-lg border text-left transition-all ${
                  selectedProject?.projectId === project.projectId
                    ? 'bg-[#00f3ff]/10 border-[#00f3ff]'
                    : 'bg-[#0a0a0f] border-[#1a1a2f] hover:border-[#2a2a4f]'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <p className="font-semibold text-white truncate">{project.projectName}</p>
                  {getStatusBadge(project.status)}
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-2xl font-bold text-[#00f3ff]">{formatCurrency(project.mrr)}</p>
                    <p className="text-xs text-gray-500">MRR</p>
                  </div>
                  <div className="text-right">
                    <Sparkline
                      data={project.revenueHistory.map(h => h.revenue)}
                      color={project.growthRate > 0 ? '#00ff88' : '#ff003c'}
                    />
                    <p className={`text-xs ${project.growthRate > 0 ? 'text-[#00ff88]' : 'text-[#ff003c]'}`}>
                      {project.growthRate > 0 ? '+' : ''}{project.growthRate}%
                    </p>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Selected Project Details */}
        <div className="col-span-2 space-y-4">
          {selectedProject && (
            <>
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-white">{selectedProject.projectName}</h3>
                {getStatusBadge(selectedProject.status)}
              </div>

              {/* Key Metrics */}
              <div className="grid grid-cols-4 gap-3">
                <div className="bg-[#0a0a0f] border border-[#1a1a2f] rounded-lg p-3">
                  <p className="text-gray-500 text-xs">MRR</p>
                  <p className="text-xl font-bold text-[#00f3ff]">{formatCurrency(selectedProject.mrr)}</p>
                </div>
                <div className="bg-[#0a0a0f] border border-[#1a1a2f] rounded-lg p-3">
                  <p className="text-gray-500 text-xs">Projected MRR</p>
                  <p className="text-xl font-bold text-[#7000ff]">{formatCurrency(selectedProject.projectedMrr)}</p>
                </div>
                <div className="bg-[#0a0a0f] border border-[#1a1a2f] rounded-lg p-3">
                  <p className="text-gray-500 text-xs">Customers</p>
                  <p className="text-xl font-bold text-white">{selectedProject.customers}</p>
                </div>
                <div className="bg-[#0a0a0f] border border-[#1a1a2f] rounded-lg p-3">
                  <p className="text-gray-500 text-xs">Churn Rate</p>
                  <p className={`text-xl font-bold ${selectedProject.churnRate < 5 ? 'text-[#00ff88]' : 'text-[#ff003c]'}`}>
                    {selectedProject.churnRate}%
                  </p>
                </div>
              </div>

              {/* Unit Economics */}
              <div className="bg-[#0a0a0f] border border-[#1a1a2f] rounded-lg p-4">
                <h4 className="text-sm font-semibold text-gray-400 mb-3">UNIT ECONOMICS</h4>
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <p className="text-xs text-gray-500">LTV (Lifetime Value)</p>
                    <p className="text-2xl font-bold text-[#00ff88]">{formatCurrency(selectedProject.ltv)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">CAC (Acquisition Cost)</p>
                    <p className="text-2xl font-bold text-[#ff003c]">{formatCurrency(selectedProject.cac)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">LTV:CAC Ratio</p>
                    <p className={`text-2xl font-bold ${(selectedProject.ltv / selectedProject.cac) >= 3 ? 'text-[#00ff88]' : 'text-yellow-400'}`}>
                      {(selectedProject.ltv / selectedProject.cac).toFixed(1)}:1
                    </p>
                  </div>
                </div>
                <div className="mt-4">
                  <div className="flex justify-between text-xs text-gray-500 mb-1">
                    <span>Payback Period Progress</span>
                    <span>{Math.round((selectedProject.cac / (selectedProject.mrr / selectedProject.customers || 1)))} months</span>
                  </div>
                  <div className="h-2 bg-[#1a1a2f] rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-[#ff003c] via-yellow-400 to-[#00ff88]"
                      style={{ width: `${Math.min(100, (selectedProject.ltv / selectedProject.cac) * 20)}%` }}
                    />
                  </div>
                </div>
              </div>

              {/* Revenue Chart Placeholder */}
              <div className="bg-[#0a0a0f] border border-[#1a1a2f] rounded-lg p-4">
                <h4 className="text-sm font-semibold text-gray-400 mb-3">REVENUE TREND</h4>
                <div className="h-32 flex items-end justify-between gap-1">
                  {selectedProject.revenueHistory.map((item, i) => {
                    const maxRev = Math.max(...selectedProject.revenueHistory.map(h => h.revenue));
                    const height = (item.revenue / maxRev) * 100;
                    return (
                      <div key={i} className="flex-1 flex flex-col items-center gap-1">
                        <div
                          className="w-full bg-gradient-to-t from-[#7000ff] to-[#00f3ff] rounded-t"
                          style={{ height: `${height}%` }}
                        />
                        <span className="text-xs text-gray-500">{item.month}</span>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Top Customers */}
              <div className="bg-[#0a0a0f] border border-[#1a1a2f] rounded-lg p-4">
                <h4 className="text-sm font-semibold text-gray-400 mb-3">TOP CUSTOMERS</h4>
                <div className="space-y-2">
                  {selectedProject.topCustomers.map((customer, i) => (
                    <div key={i} className="flex items-center justify-between p-2 bg-[#050508] rounded">
                      <div className="flex items-center gap-3">
                        <span className="w-6 h-6 bg-gradient-to-br from-[#7000ff] to-[#00f3ff] rounded-full flex items-center justify-center text-xs font-bold text-white">
                          {i + 1}
                        </span>
                        <div>
                          <p className="text-sm text-white">{customer.name}</p>
                          <p className="text-xs text-gray-500">{customer.plan}</p>
                        </div>
                      </div>
                      <p className="text-sm font-semibold text-[#00ff88]">{formatCurrency(customer.revenue)}/mo</p>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
