'use client';

import React, { useState, useEffect } from 'react';

interface OutreachTemplate {
  id: string;
  name: string;
  type: 'cold_email' | 'follow_up' | 'demo_request' | 'partnership' | 'linkedin' | 'twitter';
  subject: string;
  body: string;
  variables: string[];
  conversionRate: number;
  timesUsed: number;
}

interface ProjectOutreach {
  projectId: number;
  projectName: string;
  targetAudience: string[];
  templates: OutreachTemplate[];
  suggestedLeads: {
    name: string;
    company: string;
    title: string;
    linkedin: string;
    relevanceScore: number;
  }[];
  outreachStats: {
    sent: number;
    opened: number;
    replied: number;
    meetings: number;
  };
}

interface OutreachData {
  projects: ProjectOutreach[];
  globalTemplates: OutreachTemplate[];
}

const TEMPLATE_TYPES = [
  { id: 'cold_email', name: 'Cold Email', icon: '📧', color: 'bg-blue-500/20 text-blue-400 border-blue-500/50' },
  { id: 'follow_up', name: 'Follow Up', icon: '🔄', color: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50' },
  { id: 'demo_request', name: 'Demo Request', icon: '🎥', color: 'bg-[#7000ff]/20 text-[#a855f7] border-[#7000ff]/50' },
  { id: 'partnership', name: 'Partnership', icon: '🤝', color: 'bg-[#00ff88]/20 text-[#00ff88] border-[#00ff88]/50' },
  { id: 'linkedin', name: 'LinkedIn', icon: '💼', color: 'bg-blue-600/20 text-blue-300 border-blue-600/50' },
  { id: 'twitter', name: 'Twitter/X', icon: '🐦', color: 'bg-gray-500/20 text-gray-300 border-gray-500/50' },
];

export default function OutreachTemplates() {
  const [data, setData] = useState<OutreachData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedProject, setSelectedProject] = useState<ProjectOutreach | null>(null);
  const [selectedTemplate, setSelectedTemplate] = useState<OutreachTemplate | null>(null);
  const [editedBody, setEditedBody] = useState('');
  const [activeTab, setActiveTab] = useState<'templates' | 'leads' | 'stats'>('templates');

  useEffect(() => {
    fetchOutreachData();
  }, []);

  const fetchOutreachData = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('http://localhost:8000/api/v1/catalog/outreach-templates?limit=10', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) throw new Error('Failed to fetch outreach data');
      const result = await response.json();
      setData(result);
      if (result.projects.length > 0) {
        setSelectedProject(result.projects[0]);
        if (result.projects[0].templates.length > 0) {
          setSelectedTemplate(result.projects[0].templates[0]);
          setEditedBody(result.projects[0].templates[0].body);
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const getTypeInfo = (type: string) => {
    return TEMPLATE_TYPES.find(t => t.id === type) || TEMPLATE_TYPES[0];
  };

  const highlightVariables = (text: string) => {
    return text.replace(/\{\{(\w+)\}\}/g, '<span class="bg-[#00f3ff]/30 text-[#00f3ff] px-1 rounded">{{$1}}</span>');
  };

  const handleCopyTemplate = () => {
    if (selectedTemplate) {
      navigator.clipboard.writeText(`Subject: ${selectedTemplate.subject}\n\n${editedBody}`);
      alert('Template copied to clipboard!');
    }
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
            <span className="text-[#ff003c]">///</span> CUSTOMER OUTREACH HUB
          </h2>
          <p className="text-gray-500 text-sm mt-1">AI-generated sales templates and lead discovery</p>
        </div>
        <button className="px-4 py-2 bg-gradient-to-r from-[#7000ff] to-[#00f3ff] text-white rounded-lg font-semibold hover:shadow-lg hover:shadow-[#7000ff]/20 transition-all">
          ✨ Generate New Template
        </button>
      </div>

      <div className="grid grid-cols-4 gap-6">
        {/* Project Selector */}
        <div className="space-y-4">
          <h3 className="text-sm font-semibold text-gray-400">SELECT PROJECT</h3>
          <div className="space-y-2 max-h-[500px] overflow-y-auto pr-2">
            {data?.projects.map((project) => (
              <button
                key={project.projectId}
                onClick={() => {
                  setSelectedProject(project);
                  if (project.templates.length > 0) {
                    setSelectedTemplate(project.templates[0]);
                    setEditedBody(project.templates[0].body);
                  }
                }}
                className={`w-full p-3 rounded-lg border text-left transition-all ${
                  selectedProject?.projectId === project.projectId
                    ? 'bg-[#00f3ff]/10 border-[#00f3ff]'
                    : 'bg-[#0a0a0f] border-[#1a1a2f] hover:border-[#2a2a4f]'
                }`}
              >
                <p className="font-semibold text-white truncate">{project.projectName}</p>
                <div className="flex gap-2 mt-2 text-xs">
                  <span className="text-gray-500">{project.templates.length} templates</span>
                  <span className="text-[#00ff88]">{project.outreachStats.meetings} meetings</span>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Main Content */}
        <div className="col-span-3 space-y-4">
          {/* Tabs */}
          <div className="flex gap-2 border-b border-[#1a1a2f] pb-2">
            {(['templates', 'leads', 'stats'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-4 py-2 rounded-t-lg transition-all ${
                  activeTab === tab
                    ? 'bg-[#1a1a2f] text-[#00f3ff] border-b-2 border-[#00f3ff]'
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                {tab.charAt(0).toUpperCase() + tab.slice(1)}
              </button>
            ))}
          </div>

          {activeTab === 'templates' && selectedProject && (
            <div className="grid grid-cols-2 gap-4">
              {/* Template List */}
              <div className="space-y-3">
                <h4 className="text-sm text-gray-400">Available Templates</h4>
                {selectedProject.templates.map((template) => {
                  const typeInfo = getTypeInfo(template.type);
                  return (
                    <button
                      key={template.id}
                      onClick={() => {
                        setSelectedTemplate(template);
                        setEditedBody(template.body);
                      }}
                      className={`w-full p-3 rounded-lg border text-left transition-all ${
                        selectedTemplate?.id === template.id
                          ? 'bg-[#7000ff]/10 border-[#7000ff]'
                          : 'bg-[#0a0a0f] border-[#1a1a2f] hover:border-[#2a2a4f]'
                      }`}
                    >
                      <div className="flex items-center gap-2 mb-2">
                        <span className={`px-2 py-0.5 text-xs rounded border ${typeInfo.color}`}>
                          {typeInfo.icon} {typeInfo.name}
                        </span>
                        <span className="text-xs text-[#00ff88]">{template.conversionRate}% conv</span>
                      </div>
                      <p className="font-semibold text-white text-sm">{template.name}</p>
                      <p className="text-xs text-gray-500 mt-1 truncate">{template.subject}</p>
                    </button>
                  );
                })}
              </div>

              {/* Template Editor */}
              {selectedTemplate && (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <h4 className="text-sm text-gray-400">Edit Template</h4>
                    <div className="flex gap-2">
                      <button
                        onClick={handleCopyTemplate}
                        className="px-3 py-1 bg-[#00f3ff]/20 text-[#00f3ff] rounded text-xs hover:bg-[#00f3ff]/30"
                      >
                        📋 Copy
                      </button>
                      <button className="px-3 py-1 bg-[#00ff88]/20 text-[#00ff88] rounded text-xs hover:bg-[#00ff88]/30">
                        📤 Send
                      </button>
                    </div>
                  </div>

                  <div className="bg-[#0a0a0f] border border-[#1a1a2f] rounded-lg p-4 space-y-3">
                    <div>
                      <label className="text-xs text-gray-500">Subject Line</label>
                      <input
                        type="text"
                        value={selectedTemplate.subject}
                        className="w-full mt-1 px-3 py-2 bg-[#050508] border border-[#1a1a2f] rounded text-white text-sm focus:border-[#00f3ff] focus:outline-none"
                        readOnly
                      />
                    </div>
                    <div>
                      <label className="text-xs text-gray-500">Message Body</label>
                      <textarea
                        value={editedBody}
                        onChange={(e) => setEditedBody(e.target.value)}
                        rows={10}
                        className="w-full mt-1 px-3 py-2 bg-[#050508] border border-[#1a1a2f] rounded text-white text-sm focus:border-[#00f3ff] focus:outline-none resize-none font-mono"
                      />
                    </div>
                    <div>
                      <label className="text-xs text-gray-500">Variables</label>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {selectedTemplate.variables.map((v) => (
                          <span key={v} className="px-2 py-0.5 bg-[#00f3ff]/20 text-[#00f3ff] rounded text-xs font-mono">
                            {`{{${v}}}`}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'leads' && selectedProject && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h4 className="text-sm text-gray-400">Suggested Leads for {selectedProject.projectName}</h4>
                <button className="px-3 py-1 bg-[#7000ff]/20 text-[#a855f7] rounded text-xs hover:bg-[#7000ff]/30">
                  🔍 Find More Leads
                </button>
              </div>
              <div className="grid grid-cols-2 gap-3">
                {selectedProject.suggestedLeads.map((lead, i) => (
                  <div key={i} className="bg-[#0a0a0f] border border-[#1a1a2f] rounded-lg p-4 hover:border-[#2a2a4f] transition-all">
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="font-semibold text-white">{lead.name}</p>
                        <p className="text-sm text-gray-400">{lead.title}</p>
                        <p className="text-xs text-gray-500">{lead.company}</p>
                      </div>
                      <div className="text-right">
                        <span className={`px-2 py-0.5 text-xs rounded ${
                          lead.relevanceScore >= 80 ? 'bg-[#00ff88]/20 text-[#00ff88]' :
                          lead.relevanceScore >= 60 ? 'bg-[#00f3ff]/20 text-[#00f3ff]' :
                          'bg-yellow-400/20 text-yellow-400'
                        }`}>
                          {lead.relevanceScore}% match
                        </span>
                      </div>
                    </div>
                    <div className="flex gap-2 mt-3">
                      <button className="flex-1 px-2 py-1 bg-blue-600/20 text-blue-300 rounded text-xs hover:bg-blue-600/30">
                        💼 LinkedIn
                      </button>
                      <button className="flex-1 px-2 py-1 bg-[#00f3ff]/20 text-[#00f3ff] rounded text-xs hover:bg-[#00f3ff]/30">
                        📧 Email
                      </button>
                      <button className="px-2 py-1 bg-[#1a1a2f] text-gray-400 rounded text-xs hover:bg-[#2a2a4f]">
                        ✓
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'stats' && selectedProject && (
            <div className="space-y-4">
              <h4 className="text-sm text-gray-400">Outreach Performance</h4>
              <div className="grid grid-cols-4 gap-4">
                <div className="bg-[#0a0a0f] border border-[#1a1a2f] rounded-lg p-4 text-center">
                  <p className="text-3xl font-bold text-[#00f3ff]">{selectedProject.outreachStats.sent}</p>
                  <p className="text-xs text-gray-500 mt-1">Emails Sent</p>
                </div>
                <div className="bg-[#0a0a0f] border border-[#1a1a2f] rounded-lg p-4 text-center">
                  <p className="text-3xl font-bold text-[#7000ff]">{selectedProject.outreachStats.opened}</p>
                  <p className="text-xs text-gray-500 mt-1">Opened</p>
                  <p className="text-xs text-[#7000ff]">
                    {((selectedProject.outreachStats.opened / selectedProject.outreachStats.sent) * 100).toFixed(1)}%
                  </p>
                </div>
                <div className="bg-[#0a0a0f] border border-[#1a1a2f] rounded-lg p-4 text-center">
                  <p className="text-3xl font-bold text-yellow-400">{selectedProject.outreachStats.replied}</p>
                  <p className="text-xs text-gray-500 mt-1">Replied</p>
                  <p className="text-xs text-yellow-400">
                    {((selectedProject.outreachStats.replied / selectedProject.outreachStats.sent) * 100).toFixed(1)}%
                  </p>
                </div>
                <div className="bg-[#0a0a0f] border border-[#1a1a2f] rounded-lg p-4 text-center">
                  <p className="text-3xl font-bold text-[#00ff88]">{selectedProject.outreachStats.meetings}</p>
                  <p className="text-xs text-gray-500 mt-1">Meetings Booked</p>
                  <p className="text-xs text-[#00ff88]">
                    {((selectedProject.outreachStats.meetings / selectedProject.outreachStats.sent) * 100).toFixed(1)}%
                  </p>
                </div>
              </div>

              {/* Funnel Visualization */}
              <div className="bg-[#0a0a0f] border border-[#1a1a2f] rounded-lg p-4">
                <h5 className="text-sm font-semibold text-gray-400 mb-4">Conversion Funnel</h5>
                <div className="space-y-2">
                  {[
                    { label: 'Sent', value: selectedProject.outreachStats.sent, color: 'bg-[#00f3ff]' },
                    { label: 'Opened', value: selectedProject.outreachStats.opened, color: 'bg-[#7000ff]' },
                    { label: 'Replied', value: selectedProject.outreachStats.replied, color: 'bg-yellow-400' },
                    { label: 'Meetings', value: selectedProject.outreachStats.meetings, color: 'bg-[#00ff88]' },
                  ].map((step, i) => (
                    <div key={i} className="flex items-center gap-3">
                      <span className="text-xs text-gray-400 w-16">{step.label}</span>
                      <div className="flex-1 h-6 bg-[#1a1a2f] rounded overflow-hidden">
                        <div
                          className={`h-full ${step.color} flex items-center justify-end pr-2`}
                          style={{ width: `${(step.value / selectedProject.outreachStats.sent) * 100}%` }}
                        >
                          <span className="text-xs font-bold text-black">{step.value}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
