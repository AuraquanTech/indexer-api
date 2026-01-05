'use client';

import React, { useState, useEffect } from 'react';

interface Lead {
  id: string;
  email: string;
  name: string | null;
  company: string | null;
  source: string;
  status: 'new' | 'contacted' | 'qualified' | 'converted';
  createdAt: string;
  projectInterest: string[];
}

interface WaitlistStats {
  projectId: number;
  projectName: string;
  totalSignups: number;
  thisWeek: number;
  conversionRate: number;
  topSources: { source: string; count: number }[];
  recentLeads: Lead[];
  waitlistActive: boolean;
  launchDate: string | null;
}

interface LeadCaptureData {
  projects: WaitlistStats[];
  totalLeads: number;
  totalThisWeek: number;
  avgConversionRate: number;
}

export default function LeadCapture() {
  const [data, setData] = useState<LeadCaptureData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedProject, setSelectedProject] = useState<WaitlistStats | null>(null);
  const [showEmbedCode, setShowEmbedCode] = useState(false);

  useEffect(() => {
    fetchLeadData();
  }, []);

  const fetchLeadData = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('http://localhost:8000/api/v1/catalog/lead-capture?limit=10', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) throw new Error('Failed to fetch lead data');
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

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'new': return 'bg-[#00f3ff]/20 text-[#00f3ff] border-[#00f3ff]/50';
      case 'contacted': return 'bg-yellow-400/20 text-yellow-400 border-yellow-400/50';
      case 'qualified': return 'bg-[#7000ff]/20 text-[#a855f7] border-[#7000ff]/50';
      case 'converted': return 'bg-[#00ff88]/20 text-[#00ff88] border-[#00ff88]/50';
      default: return 'bg-gray-500/20 text-gray-400 border-gray-500/50';
    }
  };

  const generateEmbedCode = (projectName: string) => {
    return `<!-- ${projectName} Waitlist Widget -->
<div id="${projectName.toLowerCase().replace(/\s+/g, '-')}-waitlist"></div>
<script src="https://your-domain.com/waitlist.js"></script>
<script>
  Waitlist.init({
    project: '${projectName}',
    theme: 'dark',
    onSuccess: (email) => console.log('Signup:', email)
  });
</script>`;
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
            <span className="text-[#ff003c]">///</span> LEAD CAPTURE & WAITLIST
          </h2>
          <p className="text-gray-500 text-sm mt-1">Capture leads and build pre-launch momentum</p>
        </div>
        <button
          onClick={() => setShowEmbedCode(!showEmbedCode)}
          className="px-4 py-2 bg-[#7000ff]/20 border border-[#7000ff] text-[#a855f7] rounded-lg hover:bg-[#7000ff]/30 transition-all"
        >
          {showEmbedCode ? 'Hide' : 'Get'} Embed Code
        </button>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-[#0a0a0f] border border-[#1a1a2f] rounded-lg p-4">
          <p className="text-gray-500 text-xs uppercase tracking-wider">Total Leads</p>
          <p className="text-3xl font-bold mt-1 text-[#00f3ff]">{data?.totalLeads.toLocaleString()}</p>
        </div>
        <div className="bg-[#0a0a0f] border border-[#1a1a2f] rounded-lg p-4">
          <p className="text-gray-500 text-xs uppercase tracking-wider">This Week</p>
          <p className="text-3xl font-bold mt-1 text-[#00ff88]">+{data?.totalThisWeek}</p>
        </div>
        <div className="bg-[#0a0a0f] border border-[#1a1a2f] rounded-lg p-4">
          <p className="text-gray-500 text-xs uppercase tracking-wider">Avg Conversion</p>
          <p className="text-3xl font-bold mt-1 text-[#7000ff]">{data?.avgConversionRate}%</p>
        </div>
        <div className="bg-[#0a0a0f] border border-[#1a1a2f] rounded-lg p-4">
          <p className="text-gray-500 text-xs uppercase tracking-wider">Active Waitlists</p>
          <p className="text-3xl font-bold mt-1 text-yellow-400">
            {data?.projects.filter(p => p.waitlistActive).length}
          </p>
        </div>
      </div>

      {/* Embed Code Modal */}
      {showEmbedCode && selectedProject && (
        <div className="bg-[#0a0a0f] border border-[#7000ff] rounded-lg p-4">
          <h3 className="text-sm font-semibold text-[#a855f7] mb-2">
            Embed Code for {selectedProject.projectName}
          </h3>
          <pre className="bg-[#050508] p-4 rounded-lg overflow-x-auto text-xs text-gray-300 font-mono">
            {generateEmbedCode(selectedProject.projectName)}
          </pre>
          <div className="flex gap-2 mt-3">
            <button
              onClick={() => navigator.clipboard.writeText(generateEmbedCode(selectedProject.projectName))}
              className="px-3 py-1 bg-[#7000ff]/20 text-[#a855f7] rounded text-sm hover:bg-[#7000ff]/30"
            >
              📋 Copy Code
            </button>
            <button className="px-3 py-1 bg-[#00f3ff]/20 text-[#00f3ff] rounded text-sm hover:bg-[#00f3ff]/30">
              📧 Email Integration Guide
            </button>
          </div>
        </div>
      )}

      <div className="grid grid-cols-3 gap-6">
        {/* Project Waitlists */}
        <div className="space-y-4">
          <h3 className="text-sm font-semibold text-gray-400">PROJECT WAITLISTS</h3>
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
                <div className="flex items-center justify-between">
                  <p className="font-semibold text-white truncate">{project.projectName}</p>
                  {project.waitlistActive ? (
                    <span className="w-2 h-2 bg-[#00ff88] rounded-full animate-pulse"></span>
                  ) : (
                    <span className="w-2 h-2 bg-gray-500 rounded-full"></span>
                  )}
                </div>
                <div className="flex items-center justify-between mt-2">
                  <span className="text-2xl font-bold text-[#00f3ff]">{project.totalSignups}</span>
                  <span className="text-xs text-[#00ff88]">+{project.thisWeek} this week</span>
                </div>
                <div className="mt-2 h-1.5 bg-[#1a1a2f] rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-[#7000ff] to-[#00f3ff]"
                    style={{ width: `${Math.min(project.conversionRate * 10, 100)}%` }}
                  />
                </div>
                <p className="text-xs text-gray-500 mt-1">{project.conversionRate}% conversion</p>
              </button>
            ))}
          </div>
        </div>

        {/* Lead Details */}
        <div className="col-span-2 space-y-4">
          {selectedProject && (
            <>
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-gray-400">
                  LEADS FOR {selectedProject.projectName.toUpperCase()}
                </h3>
                <div className="flex gap-2">
                  <button className="px-3 py-1 bg-[#00f3ff]/20 text-[#00f3ff] rounded text-xs hover:bg-[#00f3ff]/30">
                    Export CSV
                  </button>
                  <button className="px-3 py-1 bg-[#00ff88]/20 text-[#00ff88] rounded text-xs hover:bg-[#00ff88]/30">
                    Send Campaign
                  </button>
                </div>
              </div>

              {/* Lead Sources */}
              <div className="bg-[#0a0a0f] border border-[#1a1a2f] rounded-lg p-4">
                <h4 className="text-xs text-gray-500 uppercase tracking-wider mb-3">Top Sources</h4>
                <div className="flex gap-4">
                  {selectedProject.topSources.map((source) => (
                    <div key={source.source} className="flex-1">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm text-white">{source.source}</span>
                        <span className="text-sm text-[#00f3ff]">{source.count}</span>
                      </div>
                      <div className="h-2 bg-[#1a1a2f] rounded-full overflow-hidden">
                        <div
                          className="h-full bg-[#00f3ff]"
                          style={{ width: `${(source.count / selectedProject.totalSignups) * 100}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Recent Leads Table */}
              <div className="bg-[#0a0a0f] border border-[#1a1a2f] rounded-lg overflow-hidden">
                <table className="w-full">
                  <thead className="bg-[#050508]">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">Email</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">Source</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">Status</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">Date</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#1a1a2f]">
                    {selectedProject.recentLeads.map((lead) => (
                      <tr key={lead.id} className="hover:bg-[#050508]">
                        <td className="px-4 py-3">
                          <div>
                            <p className="text-sm text-white">{lead.email}</p>
                            {lead.company && (
                              <p className="text-xs text-gray-500">{lead.company}</p>
                            )}
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <span className="text-sm text-gray-400">{lead.source}</span>
                        </td>
                        <td className="px-4 py-3">
                          <span className={`px-2 py-0.5 text-xs rounded border ${getStatusColor(lead.status)}`}>
                            {lead.status.toUpperCase()}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          <span className="text-sm text-gray-400">{lead.createdAt}</span>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex gap-1">
                            <button className="p-1 hover:bg-[#1a1a2f] rounded" title="Send Email">
                              📧
                            </button>
                            <button className="p-1 hover:bg-[#1a1a2f] rounded" title="Mark Qualified">
                              ✓
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Quick Actions */}
              <div className="grid grid-cols-3 gap-4">
                <button className="p-4 bg-[#0a0a0f] border border-[#1a1a2f] rounded-lg hover:border-[#00f3ff] transition-all text-left">
                  <span className="text-2xl">📧</span>
                  <p className="font-semibold text-white mt-2">Email All Leads</p>
                  <p className="text-xs text-gray-500">Send announcement to waitlist</p>
                </button>
                <button className="p-4 bg-[#0a0a0f] border border-[#1a1a2f] rounded-lg hover:border-[#00f3ff] transition-all text-left">
                  <span className="text-2xl">🎁</span>
                  <p className="font-semibold text-white mt-2">Early Access Offer</p>
                  <p className="text-xs text-gray-500">Create exclusive discount</p>
                </button>
                <button className="p-4 bg-[#0a0a0f] border border-[#1a1a2f] rounded-lg hover:border-[#00f3ff] transition-all text-left">
                  <span className="text-2xl">📊</span>
                  <p className="font-semibold text-white mt-2">Analytics Report</p>
                  <p className="text-xs text-gray-500">View detailed metrics</p>
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
