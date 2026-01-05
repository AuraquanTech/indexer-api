'use client';

import React, { useState, useEffect } from 'react';

interface LandingPageContent {
  headline: string;
  subheadline: string;
  valueProp: string[];
  features: { title: string; description: string; icon: string }[];
  ctaText: string;
  pricing: { tier: string; price: string; features: string[] }[];
  testimonialPlaceholder: string;
  seoTitle: string;
  seoDescription: string;
}

interface ProjectLandingPage {
  projectId: number;
  projectName: string;
  targetAudience: string[];
  marketCategory: string;
  generatedContent: LandingPageContent;
  template: 'minimal' | 'startup' | 'saas' | 'developer';
  colorScheme: { primary: string; secondary: string; accent: string };
  previewUrl: string | null;
  exportFormats: string[];
}

interface LandingPageData {
  projects: ProjectLandingPage[];
}

const TEMPLATES = [
  { id: 'minimal', name: 'Minimal', description: 'Clean, focused design', preview: '🎯' },
  { id: 'startup', name: 'Startup', description: 'Bold, modern look', preview: '🚀' },
  { id: 'saas', name: 'SaaS', description: 'Feature-rich layout', preview: '💼' },
  { id: 'developer', name: 'Developer', description: 'Technical, code-focused', preview: '👨‍💻' },
];

export default function LandingPageGenerator() {
  const [data, setData] = useState<LandingPageData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedProject, setSelectedProject] = useState<ProjectLandingPage | null>(null);
  const [selectedTemplate, setSelectedTemplate] = useState('startup');
  const [generating, setGenerating] = useState<number | null>(null);
  const [showPreview, setShowPreview] = useState(false);

  useEffect(() => {
    fetchLandingPageData();
  }, []);

  const fetchLandingPageData = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('http://localhost:8000/api/v1/catalog/landing-pages?limit=10', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) throw new Error('Failed to fetch landing page data');
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

  const handleGenerate = async (project: ProjectLandingPage) => {
    setGenerating(project.projectId);
    await new Promise(resolve => setTimeout(resolve, 2000));
    setGenerating(null);
    setShowPreview(true);
  };

  const handleExport = (format: string) => {
    alert(`Exporting ${selectedProject?.projectName} landing page as ${format}...\n\nIn production, this would generate:\n- Complete HTML/CSS files\n- Responsive design\n- SEO meta tags\n- Stripe checkout integration`);
  };

  if (loading) {
    return (
      <div className="bg-[#0a0a0f] border border-[#1a1a2f] rounded-lg p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-[#1a1a2f] rounded w-1/3"></div>
          <div className="h-64 bg-[#1a1a2f] rounded"></div>
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
            <span className="text-[#ff003c]">///</span> LANDING PAGE GENERATOR
          </h2>
          <p className="text-gray-500 text-sm mt-1">Auto-generate marketing pages with AI-powered copy</p>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Project Selector */}
        <div className="space-y-4">
          <h3 className="text-sm font-semibold text-gray-400">SELECT PROJECT</h3>
          <div className="space-y-2 max-h-[500px] overflow-y-auto pr-2">
            {data?.projects.map((project) => (
              <button
                key={project.projectId}
                onClick={() => {
                  setSelectedProject(project);
                  setShowPreview(false);
                }}
                className={`w-full p-3 rounded-lg border text-left transition-all ${
                  selectedProject?.projectId === project.projectId
                    ? 'bg-[#00f3ff]/10 border-[#00f3ff]'
                    : 'bg-[#0a0a0f] border-[#1a1a2f] hover:border-[#2a2a4f]'
                }`}
              >
                <p className="font-semibold text-white truncate">{project.projectName}</p>
                <p className="text-xs text-gray-500 mt-1">{project.marketCategory}</p>
                <div className="flex flex-wrap gap-1 mt-2">
                  {project.targetAudience.slice(0, 2).map((audience) => (
                    <span key={audience} className="px-2 py-0.5 text-xs bg-[#7000ff]/20 text-[#a855f7] rounded">
                      {audience}
                    </span>
                  ))}
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Template & Settings */}
        <div className="space-y-4">
          <h3 className="text-sm font-semibold text-gray-400">TEMPLATE STYLE</h3>
          <div className="grid grid-cols-2 gap-2">
            {TEMPLATES.map((template) => (
              <button
                key={template.id}
                onClick={() => setSelectedTemplate(template.id)}
                className={`p-3 rounded-lg border text-center transition-all ${
                  selectedTemplate === template.id
                    ? 'bg-[#7000ff]/20 border-[#7000ff]'
                    : 'bg-[#0a0a0f] border-[#1a1a2f] hover:border-[#2a2a4f]'
                }`}
              >
                <span className="text-2xl">{template.preview}</span>
                <p className="text-sm font-semibold text-white mt-1">{template.name}</p>
                <p className="text-xs text-gray-500">{template.description}</p>
              </button>
            ))}
          </div>

          {selectedProject && (
            <>
              <h3 className="text-sm font-semibold text-gray-400 mt-4">GENERATED CONTENT</h3>
              <div className="bg-[#0a0a0f] border border-[#1a1a2f] rounded-lg p-4 space-y-3">
                <div>
                  <label className="text-xs text-gray-500">Headline</label>
                  <p className="text-white font-semibold">{selectedProject.generatedContent.headline}</p>
                </div>
                <div>
                  <label className="text-xs text-gray-500">Subheadline</label>
                  <p className="text-gray-300 text-sm">{selectedProject.generatedContent.subheadline}</p>
                </div>
                <div>
                  <label className="text-xs text-gray-500">Value Props</label>
                  <ul className="mt-1 space-y-1">
                    {selectedProject.generatedContent.valueProp.map((prop, i) => (
                      <li key={i} className="text-sm text-gray-400 flex items-center gap-2">
                        <span className="text-[#00f3ff]">✓</span> {prop}
                      </li>
                    ))}
                  </ul>
                </div>
                <div>
                  <label className="text-xs text-gray-500">CTA Button</label>
                  <p className="text-[#00f3ff] font-semibold">{selectedProject.generatedContent.ctaText}</p>
                </div>
              </div>

              <button
                onClick={() => handleGenerate(selectedProject)}
                disabled={generating === selectedProject.projectId}
                className={`w-full py-3 rounded-lg font-semibold transition-all ${
                  generating === selectedProject.projectId
                    ? 'bg-[#7000ff]/20 text-[#a855f7] cursor-wait'
                    : 'bg-gradient-to-r from-[#7000ff] to-[#00f3ff] text-white hover:shadow-lg hover:shadow-[#7000ff]/20'
                }`}
              >
                {generating === selectedProject.projectId ? (
                  <span className="flex items-center justify-center gap-2">
                    <span className="animate-spin">⚡</span> Generating...
                  </span>
                ) : (
                  <span className="flex items-center justify-center gap-2">
                    ✨ Generate Landing Page
                  </span>
                )}
              </button>
            </>
          )}
        </div>

        {/* Preview */}
        <div className="space-y-4">
          <h3 className="text-sm font-semibold text-gray-400">PREVIEW</h3>
          {selectedProject && showPreview ? (
            <div className="bg-white rounded-lg overflow-hidden shadow-xl">
              {/* Mini Preview */}
              <div className="bg-gradient-to-br from-[#7000ff] to-[#00f3ff] p-6 text-white">
                <nav className="flex justify-between items-center mb-8">
                  <span className="font-bold">{selectedProject.projectName}</span>
                  <button className="px-3 py-1 bg-white/20 rounded text-sm">Sign In</button>
                </nav>
                <h1 className="text-2xl font-bold mb-2">{selectedProject.generatedContent.headline}</h1>
                <p className="text-white/80 text-sm mb-4">{selectedProject.generatedContent.subheadline}</p>
                <button className="px-4 py-2 bg-white text-[#7000ff] rounded font-semibold text-sm">
                  {selectedProject.generatedContent.ctaText}
                </button>
              </div>
              <div className="p-4 bg-gray-50">
                <div className="grid grid-cols-3 gap-2">
                  {selectedProject.generatedContent.features.slice(0, 3).map((feature, i) => (
                    <div key={i} className="text-center p-2">
                      <span className="text-xl">{feature.icon}</span>
                      <p className="text-xs font-semibold text-gray-800 mt-1">{feature.title}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-[#0a0a0f] border border-[#1a1a2f] rounded-lg p-8 text-center">
              <span className="text-4xl">🖼️</span>
              <p className="text-gray-500 mt-2">Click "Generate" to preview</p>
            </div>
          )}

          {selectedProject && showPreview && (
            <div className="space-y-2">
              <h4 className="text-xs text-gray-500 uppercase tracking-wider">Export Options</h4>
              <div className="grid grid-cols-2 gap-2">
                <button
                  onClick={() => handleExport('HTML')}
                  className="px-3 py-2 bg-[#0a0a0f] border border-[#1a1a2f] rounded text-sm text-white hover:border-[#00f3ff] transition-all"
                >
                  📄 Export HTML
                </button>
                <button
                  onClick={() => handleExport('Next.js')}
                  className="px-3 py-2 bg-[#0a0a0f] border border-[#1a1a2f] rounded text-sm text-white hover:border-[#00f3ff] transition-all"
                >
                  ▲ Next.js Component
                </button>
                <button
                  onClick={() => handleExport('Vercel')}
                  className="px-3 py-2 bg-[#0a0a0f] border border-[#1a1a2f] rounded text-sm text-white hover:border-[#00f3ff] transition-all"
                >
                  🚀 Deploy to Vercel
                </button>
                <button
                  onClick={() => handleExport('Figma')}
                  className="px-3 py-2 bg-[#0a0a0f] border border-[#1a1a2f] rounded text-sm text-white hover:border-[#00f3ff] transition-all"
                >
                  🎨 Figma Design
                </button>
              </div>
            </div>
          )}

          {/* SEO Preview */}
          {selectedProject && showPreview && (
            <div className="bg-[#0a0a0f] border border-[#1a1a2f] rounded-lg p-4 space-y-2">
              <h4 className="text-xs text-gray-500 uppercase tracking-wider">SEO Preview</h4>
              <div className="bg-white rounded p-3">
                <p className="text-blue-600 text-sm font-medium truncate">
                  {selectedProject.generatedContent.seoTitle}
                </p>
                <p className="text-green-700 text-xs">
                  {selectedProject.projectName.toLowerCase().replace(/\s+/g, '')}.com
                </p>
                <p className="text-gray-600 text-xs mt-1 line-clamp-2">
                  {selectedProject.generatedContent.seoDescription}
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
