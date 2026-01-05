# Indexer Frontend Technical Specification

**Version:** 1.0
**Date:** January 2, 2026
**Backend API:** Indexer API v1 (FastAPI)
**Recommended Stack:** React/Next.js with Tailwind CSS or similar modern framework

---

## Table of Contents
1. [Project Overview](#project-overview)
2. [Backend API Reference](#backend-api-reference)
3. [Data Models](#data-models)
4. [Frontend Architecture](#frontend-architecture)
5. [Pages & Components](#pages--components)
6. [Feature Specifications](#feature-specifications)
7. [UI/UX Guidelines](#uiux-guidelines)
8. [Authentication](#authentication)
9. [API Integration](#api-integration)

---

## Project Overview

### Purpose
Create a modern, responsive web frontend for the Indexer API - a comprehensive project cataloging and quality assessment system that uses LLM-powered analysis to evaluate 1,512+ code projects.

### Current Backend Capabilities
- **1,512 projects** cataloged with metadata
- **LLM-powered quality assessment** using Ollama (qwen2.5-coder:14b)
- **Semantic search** with embeddings
- **Natural language search** with query understanding
- **Production readiness classification** (prototype → mature)
- **Quality scoring** (0-100 with breakdowns)
- **Similar project discovery**
- **Health reporting and analytics**

### API Base URL
```
http://127.0.0.1:8000/api/v1
```

---

## Backend API Reference

### Authentication Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/login` | Login with username/password, returns JWT |
| POST | `/auth/register` | Register new user |
| GET | `/auth/me` | Get current user info |

### Catalog Endpoints

#### Projects CRUD
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/catalog/projects` | List all projects (paginated) |
| GET | `/catalog/projects/{id}` | Get single project details |
| POST | `/catalog/projects` | Create new project |
| PATCH | `/catalog/projects/{id}` | Update project |
| DELETE | `/catalog/projects/{id}` | Delete project |

#### Search Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/catalog/search?q=` | Basic text search |
| GET | `/catalog/search/semantic?q=` | Semantic search with embeddings |
| GET | `/catalog/search/natural?q=` | Natural language search with LLM |
| GET | `/catalog/projects/{id}/similar` | Find similar projects |

#### Quality & Analysis
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/catalog/quality-report` | Full quality report |
| GET | `/catalog/projects/{id}/quality` | Project quality details |
| GET | `/catalog/production-ready` | List production-ready projects |
| POST | `/catalog/assess-quality` | Trigger bulk quality assessment |
| POST | `/catalog/projects/{id}/assess-quality` | Assess single project |
| POST | `/catalog/projects/{id}/analyze` | Trigger LLM analysis |
| POST | `/catalog/compare?project_ids=` | Compare multiple projects |

#### LLM Status & Jobs
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/catalog/llm/status` | Check LLM service status |
| GET | `/catalog/jobs/{id}` | Get job status |
| POST | `/catalog/index-embeddings` | Rebuild embedding index |

#### Health & Reports
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/catalog/health-report` | Portfolio health metrics |
| POST | `/catalog/scan` | Trigger filesystem scan |

---

## Data Models

### Project Object
```typescript
interface Project {
  id: string;
  organization_id: string;
  name: string;
  title?: string;
  description?: string;
  path: string;
  repository_url?: string;
  type: ProjectType;
  lifecycle: ProjectLifecycle;
  languages: string[];
  frameworks: string[];
  license_spdx?: string;
  tags: string[];
  health_score?: number;
  loc_total?: number;
  file_count?: number;
  last_synced_at?: string;

  // Quality fields
  production_readiness: ProductionReadiness;
  quality_score?: number;
  quality_assessment?: QualityAssessment;
  quality_indicators?: QualityIndicators;
  last_quality_check_at?: string;

  created_at: string;
  updated_at: string;
}
```

### Enums
```typescript
enum ProjectType {
  API = "api",
  LIBRARY = "library",
  CLI = "cli",
  WEB = "web",
  WEB_APP = "web_app",
  MOBILE_APP = "mobile_app",
  SERVICE = "service",
  MONOREPO = "monorepo",
  APPLICATION = "application",
  TOOL = "tool",
  FRAMEWORK = "framework",
  PLUGIN = "plugin",
  EXTENSION = "extension",
  SCRIPT = "script",
  CONFIG = "config",
  DOCS = "docs",
  BOT = "bot",
  GAME = "game",
  DATA = "data",
  TEMPLATE = "template",
  OTHER = "other"
}

enum ProjectLifecycle {
  ACTIVE = "active",
  MAINTENANCE = "maintenance",
  DEPRECATED = "deprecated",
  ARCHIVED = "archived"
}

enum ProductionReadiness {
  UNKNOWN = "unknown",
  PROTOTYPE = "prototype",
  ALPHA = "alpha",
  BETA = "beta",
  PRODUCTION = "production",
  MATURE = "mature",
  LEGACY = "legacy",
  DEPRECATED = "deprecated"
}
```

### Quality Assessment
```typescript
interface QualityAssessment {
  code_quality_score: number;      // 0-100
  documentation_score: number;     // 0-100
  test_score: number;              // 0-100
  security_score: number;          // 0-100
  maintainability_score: number;   // 0-100
  key_features: string[];
  strengths: string[];
  weaknesses: string[];
  production_blockers: string[];
  recommended_improvements: string[];
  technology_stack: string[];
  use_cases: string[];
}

interface QualityIndicators {
  has_readme: boolean;
  has_license: boolean;
  has_tests: boolean;
  has_ci_cd: boolean;
  has_documentation: boolean;
  has_changelog: boolean;
  has_contributing: boolean;
  has_security_policy: boolean;
  has_package_json: boolean;
  has_docker: boolean;
  has_linting: boolean;
  has_type_hints: boolean;
}
```

### Quality Report
```typescript
interface QualityReport {
  total_projects: number;
  assessed_projects: number;
  by_production_readiness: Record<string, number>;
  by_quality_tier: {
    excellent: number;  // 80+
    good: number;       // 60-79
    fair: number;       // 40-59
    poor: number;       // <40
    unknown: number;
  };
  avg_quality_score?: number;
  production_ready_count: number;
  needs_attention: ProjectSummary[];
  top_quality: ProjectSummary[];
  common_issues: Record<string, number>;
  technology_distribution: Record<string, number>;
  generated_at: string;
}
```

---

## Frontend Architecture

### Recommended Tech Stack
- **Framework:** Next.js 14+ (App Router) or Vite + React
- **Styling:** Tailwind CSS + shadcn/ui components
- **State Management:** TanStack Query (React Query) for server state
- **Charts:** Recharts or Chart.js for visualizations
- **Icons:** Lucide React
- **Forms:** React Hook Form + Zod validation
- **Tables:** TanStack Table for data grids

### Project Structure
```
src/
├── app/                    # Next.js App Router pages
│   ├── (auth)/            # Auth pages (login, register)
│   ├── dashboard/         # Main dashboard
│   ├── projects/          # Project pages
│   │   ├── [id]/          # Project detail
│   │   └── page.tsx       # Projects list
│   ├── search/            # Search pages
│   ├── quality/           # Quality reports
│   ├── compare/           # Project comparison
│   └── settings/          # Settings
├── components/
│   ├── ui/                # Base UI components
│   ├── charts/            # Chart components
│   ├── projects/          # Project-specific components
│   ├── search/            # Search components
│   └── layout/            # Layout components
├── lib/
│   ├── api/               # API client
│   ├── hooks/             # Custom hooks
│   └── utils/             # Utilities
└── types/                 # TypeScript types
```

---

## Pages & Components

### 1. Dashboard Page (`/dashboard`)

**Purpose:** Overview of entire project portfolio

**Components:**
- **StatsCards** - Key metrics (total projects, avg quality, production-ready count)
- **QualityDistributionChart** - Pie/donut chart of quality tiers
- **ReadinessBreakdown** - Bar chart of production readiness levels
- **TopProjectsTable** - Top 10 quality projects
- **NeedsAttentionTable** - Projects requiring improvement
- **TechnologyDistribution** - Language/framework breakdown
- **RecentActivity** - Recently updated projects
- **LLMStatusBadge** - Show if Ollama is available

**API Calls:**
```typescript
GET /catalog/quality-report
GET /catalog/health-report
GET /catalog/llm/status
```

### 2. Projects List Page (`/projects`)

**Purpose:** Browse and filter all projects

**Components:**
- **SearchBar** - Real-time search with mode toggle (basic/semantic/natural)
- **FilterPanel** - Filter by:
  - Production readiness (checkboxes)
  - Quality tier (checkboxes)
  - Lifecycle (dropdown)
  - Language (multi-select)
  - Type (dropdown)
- **ProjectGrid/Table** - Switchable view (grid cards vs data table)
- **ProjectCard** - Card showing:
  - Name, description
  - Quality score badge (color-coded)
  - Production readiness badge
  - Languages (tech icons)
  - Quick actions (view, compare, analyze)
- **Pagination** - Page navigation
- **SortDropdown** - Sort by quality, name, updated date

**API Calls:**
```typescript
GET /catalog/projects?page=1&per_page=50
GET /catalog/search?q=...
GET /catalog/search/semantic?q=...
GET /catalog/search/natural?q=...
```

### 3. Project Detail Page (`/projects/[id]`)

**Purpose:** Complete project information and quality details

**Sections:**
1. **Header Section**
   - Project name, title
   - Production readiness badge (large, color-coded)
   - Quality score gauge/meter
   - Action buttons (Analyze, Assess Quality, Find Similar)

2. **Overview Tab**
   - Description
   - Path (with copy button)
   - Repository URL (if available)
   - Type, Lifecycle
   - Languages (with icons)
   - Frameworks
   - Tags

3. **Quality Tab**
   - Overall score (large display)
   - Score breakdown radar chart:
     - Code Quality
     - Documentation
     - Testing
     - Security
     - Maintainability
   - Quality indicators checklist (has_readme, has_tests, etc.)
   - Strengths list (green checkmarks)
   - Weaknesses list (yellow warnings)
   - Production blockers (red alerts)
   - Recommended improvements (bullet list)

4. **Similar Projects Tab**
   - Grid of similar projects
   - Similarity scores

5. **Metadata Tab**
   - File count, LOC
   - Last synced
   - Created/updated dates
   - GitHub stats (if available)

**API Calls:**
```typescript
GET /catalog/projects/{id}
GET /catalog/projects/{id}/quality
GET /catalog/projects/{id}/similar
POST /catalog/projects/{id}/analyze
POST /catalog/projects/{id}/assess-quality
```

### 4. Search Page (`/search`)

**Purpose:** Advanced natural language search interface

**Components:**
- **LargeSearchInput** - Prominent search box with suggestions
- **SearchModeToggle** - Switch between:
  - Basic (keyword)
  - Semantic (embedding-based)
  - Natural Language (LLM-powered)
- **ExampleQueries** - Clickable example queries:
  - "Python APIs for file management"
  - "production-ready authentication libraries"
  - "projects with high test coverage"
  - "TypeScript tools with Docker support"
- **ResultsList** - Search results with:
  - Relevance score indicator
  - Highlighted matching terms
  - Quick quality preview
- **SearchFilters** - Post-search refinement

**API Calls:**
```typescript
GET /catalog/search/natural?q=...&limit=20
```

### 5. Quality Report Page (`/quality`)

**Purpose:** Comprehensive quality analytics

**Sections:**
1. **Summary Stats**
   - Total assessed / unassessed
   - Average quality score
   - Production ready count

2. **Charts Row**
   - Quality tier distribution (donut)
   - Production readiness distribution (bar)
   - Score distribution histogram

3. **Common Issues Analysis**
   - Bar chart of most common issues
   - Click to filter projects with issue

4. **Technology Distribution**
   - Treemap or bar chart of languages
   - Click to filter by language

5. **Projects Tables**
   - Tab: "Top Quality" - Best projects
   - Tab: "Needs Attention" - Projects with issues
   - Tab: "Production Ready" - Mature projects

6. **Actions**
   - Button: "Re-assess All Projects"
   - Button: "Rebuild Embeddings"
   - Job status indicator

**API Calls:**
```typescript
GET /catalog/quality-report
GET /catalog/production-ready
POST /catalog/assess-quality
```

### 6. Compare Page (`/compare`)

**Purpose:** Side-by-side project comparison

**Components:**
- **ProjectSelector** - Multi-select (2-5 projects)
- **ComparisonTable** - Side-by-side metrics:
  - Quality scores (all 5 dimensions)
  - Production readiness
  - Languages/frameworks
  - Quality indicators
- **RadarChart** - Overlay comparison of scores
- **LLMComparison** - AI-generated comparison summary
- **ShareButton** - Generate comparison link

**API Calls:**
```typescript
POST /catalog/compare?project_ids=id1,id2,id3
```

### 7. Scan/Import Page (`/import`)

**Purpose:** Add new projects to catalog

**Components:**
- **PathInput** - Directory paths to scan
- **ScanOptions**
  - Max depth slider
  - Include hidden toggle
  - Recursive toggle
- **ScanButton** - Trigger scan
- **JobProgress** - Show scan progress
- **PreviewResults** - Projects found preview

**API Calls:**
```typescript
POST /catalog/scan
GET /catalog/jobs/{id}
```

---

## Feature Specifications

### F1: Real-time Search with Debouncing
```typescript
// Search with 300ms debounce
const debouncedSearch = useDebouncedCallback(async (query: string) => {
  const results = await searchProjects(query, searchMode);
  setResults(results);
}, 300);
```

### F2: Quality Score Visualization
```typescript
// Color coding for quality scores
const getQualityColor = (score: number): string => {
  if (score >= 80) return 'emerald';  // Excellent
  if (score >= 60) return 'blue';     // Good
  if (score >= 40) return 'amber';    // Fair
  return 'red';                        // Poor
};

// Production readiness badge colors
const readinessColors: Record<string, string> = {
  production: 'bg-emerald-500',
  mature: 'bg-emerald-600',
  beta: 'bg-blue-500',
  alpha: 'bg-amber-500',
  prototype: 'bg-gray-500',
  legacy: 'bg-orange-500',
  deprecated: 'bg-red-500',
  unknown: 'bg-gray-400',
};
```

### F3: Polling for Job Status
```typescript
// Poll job status every 2 seconds until complete
const { data: job } = useQuery({
  queryKey: ['job', jobId],
  queryFn: () => getJobStatus(jobId),
  refetchInterval: (data) =>
    data?.status === 'completed' || data?.status === 'failed'
      ? false
      : 2000,
});
```

### F4: Export Functionality
- Export quality report as PDF
- Export project list as CSV
- Export comparison as image

### F5: Keyboard Shortcuts
- `/` - Focus search
- `g d` - Go to dashboard
- `g p` - Go to projects
- `g q` - Go to quality
- `?` - Show shortcuts

### F6: Dark Mode
Full dark mode support with system preference detection.

### F7: Responsive Design
- Mobile: Stacked cards, collapsed filters
- Tablet: 2-column grid
- Desktop: Full layout with sidebars

---

## UI/UX Guidelines

### Design Principles
1. **Data-Dense but Clear** - Show lots of info without clutter
2. **Action-Oriented** - Clear CTAs for analysis actions
3. **Progressive Disclosure** - Overview → Details
4. **Visual Hierarchy** - Quality scores prominent

### Color Palette
```css
/* Quality Tiers */
--excellent: #10b981; /* emerald-500 */
--good: #3b82f6;      /* blue-500 */
--fair: #f59e0b;      /* amber-500 */
--poor: #ef4444;      /* red-500 */

/* Production Readiness */
--production: #059669;
--mature: #047857;
--beta: #2563eb;
--alpha: #d97706;
--prototype: #6b7280;
--legacy: #ea580c;
--deprecated: #dc2626;
```

### Component Examples

#### Quality Score Badge
```tsx
<Badge
  variant={getQualityVariant(score)}
  className="text-lg font-bold"
>
  {score.toFixed(1)}
</Badge>
```

#### Production Readiness Pill
```tsx
<span className={cn(
  "px-3 py-1 rounded-full text-white text-sm font-medium",
  readinessColors[readiness]
)}>
  {readiness.toUpperCase()}
</span>
```

#### Project Card
```tsx
<Card className="hover:shadow-lg transition-shadow">
  <CardHeader className="flex flex-row items-start justify-between">
    <div>
      <CardTitle>{project.name}</CardTitle>
      <CardDescription>{project.description}</CardDescription>
    </div>
    <QualityBadge score={project.quality_score} />
  </CardHeader>
  <CardContent>
    <div className="flex gap-2 mb-2">
      <ReadinessPill readiness={project.production_readiness} />
      <LifecycleBadge lifecycle={project.lifecycle} />
    </div>
    <LanguageTags languages={project.languages} />
  </CardContent>
  <CardFooter>
    <Button variant="outline" size="sm">View Details</Button>
    <Button variant="ghost" size="sm">Compare</Button>
  </CardFooter>
</Card>
```

---

## Authentication

### JWT Token Flow
1. User logs in with email/password
2. Backend returns `access_token`
3. Store token in httpOnly cookie or secure localStorage
4. Include in all API requests: `Authorization: Bearer {token}`

### Protected Routes
All `/catalog/*` endpoints require authentication. Implement route guards.

```typescript
// API client with auth
const apiClient = axios.create({
  baseURL: 'http://127.0.0.1:8000/api/v1',
});

apiClient.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

### Login Flow
```typescript
const login = async (email: string, password: string) => {
  const response = await axios.post('/auth/login',
    new URLSearchParams({ username: email, password }),
    { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }
  );
  return response.data.access_token;
};
```

---

## API Integration

### React Query Setup
```typescript
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30 * 1000, // 30 seconds
      refetchOnWindowFocus: false,
    },
  },
});
```

### Custom Hooks Examples

```typescript
// useProjects hook
export function useProjects(params: ProjectListParams) {
  return useQuery({
    queryKey: ['projects', params],
    queryFn: () => fetchProjects(params),
  });
}

// useProject hook
export function useProject(id: string) {
  return useQuery({
    queryKey: ['project', id],
    queryFn: () => fetchProject(id),
    enabled: !!id,
  });
}

// useQualityReport hook
export function useQualityReport() {
  return useQuery({
    queryKey: ['quality-report'],
    queryFn: fetchQualityReport,
    staleTime: 60 * 1000, // 1 minute
  });
}

// useSearch hook
export function useSearch(query: string, mode: SearchMode) {
  return useQuery({
    queryKey: ['search', query, mode],
    queryFn: () => searchProjects(query, mode),
    enabled: query.length > 0,
  });
}

// useAssessQuality mutation
export function useAssessQuality() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (projectId?: string) => assessQuality(projectId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['quality-report'] });
    },
  });
}
```

---

## Summary Statistics (Current Data)

| Metric | Value |
|--------|-------|
| Total Projects | 1,512 |
| Avg Quality Score | 36.7/100 |
| Production Ready | 12 (0.8%) |
| Beta | 382 (25.3%) |
| Alpha | 755 (49.9%) |
| Prototype | 357 (23.6%) |
| Excellent Quality (80+) | 28 (1.9%) |
| Good Quality (60-79) | 155 (10.3%) |
| Fair Quality (40-59) | 447 (29.6%) |

---

## Recommended Implementation Order

### Phase 1: Core Infrastructure
1. Authentication (login/logout)
2. API client setup
3. Base layout and navigation
4. Dashboard with basic stats

### Phase 2: Projects & Search
1. Projects list with filtering
2. Project detail page
3. Basic search
4. Natural language search

### Phase 3: Quality Features
1. Quality report page
2. Quality visualization charts
3. Project comparison
4. Similar projects

### Phase 4: Advanced Features
1. Job management (scan, assess)
2. Real-time job status
3. Export functionality
4. Dark mode

### Phase 5: Polish
1. Keyboard shortcuts
2. Animations
3. Loading states
4. Error handling
5. Empty states

---

## Test Credentials

```
Email: test@example.com
Password: Test1234
```

---

## Notes for Implementation

1. **CORS**: Backend allows CORS from localhost - ensure frontend runs on localhost
2. **Error Handling**: All API calls can return 401 (unauthorized), 404 (not found), 500 (server error)
3. **Pagination**: Default page size is 50, max is 100
4. **Search Limits**: Max 100 results per search
5. **Job Polling**: Check job status every 2-5 seconds
6. **LLM Availability**: Check `/catalog/llm/status` to show/hide LLM features

---

*Document generated for Antigravity/Gemini Pro 3 frontend generation*
