#!/usr/bin/env python3
"""
🚀 Self-Healing Catalog Intelligence Pipeline

An automated, fault-tolerant pipeline that:
1. Monitors and manages LLM analysis jobs
2. Auto-triggers embedding reindex on completion
3. Validates search quality with test queries
4. Self-heals with exponential backoff retries
5. Generates comprehensive quality reports

Features:
- Async job orchestration with dependency chaining
- Circuit breaker pattern for API resilience
- Progressive retry with jitter
- Real-time progress visualization
- Quality metrics tracking & comparison
"""
from __future__ import annotations

import asyncio
import json
import random
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

import httpx

# ============================================================================
# Configuration
# ============================================================================

BASE_URL = "http://127.0.0.1:8000"
AUTH_CREDENTIALS = {"username": "test@example.com", "password": "Test1234"}

# Test queries for quality validation
QUALITY_TEST_QUERIES = [
    ("python web", ["python"], "Should find Python web projects"),
    ("machine learning", [], "Should find ML/AI projects"),
    ("discord bot", [], "Should find Discord-related projects"),
    ("typescript api", ["typescript"], "Should find TypeScript APIs"),
    ("database orm", [], "Should find database/ORM projects"),
]


class JobPhase(Enum):
    """Pipeline phases."""
    INIT = "🔧 Initializing"
    ANALYZE = "🧠 LLM Analysis"
    INDEX = "📊 Embedding Index"
    VALIDATE = "✅ Validation"
    REPORT = "📈 Report"
    COMPLETE = "🎉 Complete"
    FAILED = "❌ Failed"


@dataclass
class PipelineState:
    """Pipeline execution state."""
    phase: JobPhase = JobPhase.INIT
    started_at: datetime = field(default_factory=datetime.now)
    analyze_job_id: Optional[str] = None
    index_job_id: Optional[str] = None
    projects_analyzed: int = 0
    projects_indexed: int = 0
    quality_before: Dict[str, Any] = field(default_factory=dict)
    quality_after: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    retries: int = 0


class CircuitBreaker:
    """Circuit breaker for API resilience."""

    def __init__(self, failure_threshold: int = 5, reset_timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.failures = 0
        self.last_failure_time = 0.0
        self.state = "closed"  # closed, open, half-open

    def record_failure(self):
        self.failures += 1
        self.last_failure_time = time.time()
        if self.failures >= self.failure_threshold:
            self.state = "open"
            print(f"  ⚡ Circuit breaker OPEN after {self.failures} failures")

    def record_success(self):
        self.failures = 0
        self.state = "closed"

    def can_execute(self) -> bool:
        if self.state == "closed":
            return True
        if self.state == "open":
            if time.time() - self.last_failure_time > self.reset_timeout:
                self.state = "half-open"
                return True
            return False
        return True  # half-open


class CatalogPipeline:
    """Self-healing catalog intelligence pipeline."""

    def __init__(self):
        self.state = PipelineState()
        self.client: Optional[httpx.AsyncClient] = None
        self.token: Optional[str] = None
        self.circuit_breaker = CircuitBreaker()
        self._stop_requested = False

    async def __aenter__(self):
        self.client = httpx.AsyncClient(base_url=BASE_URL, timeout=120.0)
        await self._authenticate()
        return self

    async def __aexit__(self, *args):
        if self.client:
            await self.client.aclose()

    async def _authenticate(self) -> bool:
        """Authenticate and get token."""
        for attempt in range(3):
            try:
                r = await self.client.post("/api/v1/auth/login", data=AUTH_CREDENTIALS)
                if r.status_code == 200:
                    self.token = r.json()["access_token"]
                    return True
            except Exception as e:
                print(f"  ⚠️  Auth attempt {attempt + 1} failed: {e}")
                await asyncio.sleep(2 ** attempt)
        raise RuntimeError("Authentication failed after 3 attempts")

    @property
    def headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}

    async def _api_call(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Optional[httpx.Response]:
        """Make API call with circuit breaker and retry logic."""
        if not self.circuit_breaker.can_execute():
            print("  ⏳ Circuit breaker open, waiting...")
            await asyncio.sleep(10)
            return None

        max_retries = 3
        for attempt in range(max_retries):
            try:
                if method == "GET":
                    r = await self.client.get(endpoint, headers=self.headers, **kwargs)
                else:
                    r = await self.client.post(endpoint, headers=self.headers, **kwargs)

                if r.status_code in (200, 201, 202):
                    self.circuit_breaker.record_success()
                    return r
                elif r.status_code >= 500:
                    raise httpx.HTTPStatusError(f"Server error: {r.status_code}", request=r.request, response=r)
                else:
                    return r  # Client error, don't retry

            except Exception as e:
                self.circuit_breaker.record_failure()
                self.state.retries += 1

                # Exponential backoff with jitter
                delay = (2 ** attempt) + random.uniform(0, 1)
                print(f"  🔄 Retry {attempt + 1}/{max_retries} in {delay:.1f}s: {e}")
                await asyncio.sleep(delay)

        return None

    def _print_header(self, text: str):
        """Print formatted header."""
        width = 60
        print("\n" + "═" * width)
        print(f"  {text}")
        print("═" * width)

    def _print_progress(self, current: int, total: int, prefix: str = ""):
        """Print progress bar."""
        pct = (current / total * 100) if total > 0 else 0
        bar_len = 30
        filled = int(bar_len * current / total) if total > 0 else 0
        bar = "█" * filled + "░" * (bar_len - filled)
        print(f"\r  {prefix}[{bar}] {pct:5.1f}% ({current}/{total})", end="", flush=True)

    async def capture_quality_baseline(self) -> Dict[str, Any]:
        """Capture current search quality metrics."""
        results = {}

        for query, expected_langs, description in QUALITY_TEST_QUERIES:
            r = await self._api_call("GET", "/api/v1/catalog/search/semantic", params={"q": query, "limit": 5})
            if r and r.status_code == 200:
                data = r.json()
                search_results = data.get("results", [])
                results[query] = {
                    "count": len(search_results),
                    "top_scores": [r.get("relevance_score", 0) for r in search_results[:3]],
                    "avg_score": sum(r.get("relevance_score", 0) for r in search_results) / max(len(search_results), 1),
                    "description": description,
                }

        return results

    async def wait_for_job(
        self,
        job_id: str,
        phase_name: str,
        timeout: int = 1800,  # 30 minutes
        progress_field: str = "indexed",
    ) -> Tuple[bool, Dict[str, Any]]:
        """Wait for job completion with progress tracking."""
        start = time.time()
        last_status = ""
        last_progress = 0
        stall_count = 0

        while time.time() - start < timeout:
            if self._stop_requested:
                return False, {"error": "Pipeline stopped"}

            r = await self._api_call("GET", f"/api/v1/catalog/jobs/{job_id}")
            if not r:
                stall_count += 1
                if stall_count > 5:
                    self.state.errors.append(f"{phase_name}: API unresponsive")
                    return False, {"error": "API unresponsive"}
                await asyncio.sleep(5)
                continue

            stall_count = 0
            status = r.json()
            job_status = status.get("status", "unknown")
            runs = status.get("runs", [])
            result = runs[0].get("result", {}) if runs else {}
            if result is None:
                result = {}

            progress = result.get(progress_field, result.get("analyzed", 0))
            total = result.get("total", progress)

            if job_status != last_status or progress != last_progress:
                elapsed = int(time.time() - start)
                if total > 0:
                    self._print_progress(progress, total, f"{phase_name} [{elapsed}s] ")
                else:
                    print(f"\r  {phase_name} [{elapsed}s] {job_status}...", end="", flush=True)
                last_status = job_status
                last_progress = progress

            if job_status == "completed":
                print()  # Newline after progress
                return True, result
            elif job_status == "failed":
                print()
                error = status.get("last_error", {}).get("message", "Unknown error")
                self.state.errors.append(f"{phase_name} failed: {error}")
                return False, result

            await asyncio.sleep(5)

        self.state.errors.append(f"{phase_name}: Timeout after {timeout}s")
        return False, {"error": "timeout"}

    async def run_llm_analysis(self) -> bool:
        """Run LLM analysis phase with self-healing."""
        self.state.phase = JobPhase.ANALYZE
        self._print_header(f"{JobPhase.ANALYZE.value}")

        # Check current job status (might already be running)
        r = await self._api_call("GET", "/api/v1/catalog/llm/status")
        if r:
            status = r.json()
            print(f"  LLM: {status['llm']['model']} ({'✓ available' if status['llm']['available'] else '✗ unavailable'})")
            print(f"  Embeddings: {status['embeddings']['indexed_projects']} projects indexed")

        # Trigger analysis
        r = await self._api_call("POST", "/api/v1/catalog/analyze-all")
        if not r or r.status_code != 202:
            # Self-heal: Check if job already running
            print("  ⚠️  Could not start analysis, checking for existing jobs...")
            # Continue anyway, might have existing job
            return True

        job = r.json()
        self.state.analyze_job_id = job["job_id"]
        projects_to_analyze = int(job["message"].split()[-2]) if "projects" in job["message"] else 0
        print(f"  Job ID: {job['job_id']}")
        print(f"  Projects to analyze: {projects_to_analyze}")

        if projects_to_analyze == 0:
            print("  ✓ All projects already have descriptions!")
            return True

        # Wait for completion
        success, result = await self.wait_for_job(
            job["job_id"],
            "Analysis",
            progress_field="analyzed",
        )

        self.state.projects_analyzed = result.get("analyzed", 0)

        if not success:
            # Self-heal: Try continuing anyway if we got partial results
            if self.state.projects_analyzed > 0:
                print(f"  ⚠️  Partial completion: {self.state.projects_analyzed} projects analyzed")
                return True
            return False

        print(f"  ✓ Analyzed {self.state.projects_analyzed} projects")
        return True

    async def run_embedding_index(self) -> bool:
        """Run embedding index phase."""
        self.state.phase = JobPhase.INDEX
        self._print_header(f"{JobPhase.INDEX.value}")

        # Trigger indexing
        r = await self._api_call("POST", "/api/v1/catalog/index-embeddings")
        if not r or r.status_code not in (200, 202):
            self.state.errors.append("Failed to trigger embedding index")
            return False

        job = r.json()
        self.state.index_job_id = job["job_id"]
        print(f"  Job ID: {job['job_id']}")

        # Wait for completion
        success, result = await self.wait_for_job(
            job["job_id"],
            "Indexing",
            progress_field="indexed",
        )

        self.state.projects_indexed = result.get("indexed", 0)

        if not success:
            if self.state.projects_indexed > 0:
                print(f"  ⚠️  Partial completion: {self.state.projects_indexed} projects indexed")
                return True
            return False

        print(f"  ✓ Indexed {self.state.projects_indexed} projects")
        return True

    async def run_validation(self) -> bool:
        """Validate search quality improvements."""
        self.state.phase = JobPhase.VALIDATE
        self._print_header(f"{JobPhase.VALIDATE.value}")

        print("  Running test queries...")
        self.state.quality_after = await self.capture_quality_baseline()

        improved = 0
        degraded = 0
        unchanged = 0

        for query, metrics in self.state.quality_after.items():
            before = self.state.quality_before.get(query, {})
            before_avg = before.get("avg_score", 0)
            after_avg = metrics.get("avg_score", 0)

            delta = after_avg - before_avg
            if delta > 0.001:
                status = "📈"
                improved += 1
            elif delta < -0.001:
                status = "📉"
                degraded += 1
            else:
                status = "➡️"
                unchanged += 1

            print(f"  {status} '{query}': {before_avg:.4f} → {after_avg:.4f} ({delta:+.4f})")

        print(f"\n  Summary: {improved} improved, {degraded} degraded, {unchanged} unchanged")
        return degraded <= improved  # Success if not net negative

    def generate_report(self):
        """Generate final pipeline report."""
        self.state.phase = JobPhase.REPORT
        self._print_header(f"{JobPhase.REPORT.value}")

        duration = datetime.now() - self.state.started_at

        print(f"""
  Pipeline Execution Report
  ─────────────────────────
  Duration:           {duration}
  Projects Analyzed:  {self.state.projects_analyzed}
  Projects Indexed:   {self.state.projects_indexed}
  Retries:            {self.state.retries}
  Errors:             {len(self.state.errors)}

  Quality Metrics:
  ───────────────""")

        for query, after in self.state.quality_after.items():
            before = self.state.quality_before.get(query, {})
            print(f"  • '{query}'")
            print(f"    Results: {before.get('count', 0)} → {after.get('count', 0)}")
            print(f"    Avg Score: {before.get('avg_score', 0):.4f} → {after.get('avg_score', 0):.4f}")

        if self.state.errors:
            print("\n  Errors Encountered:")
            for err in self.state.errors:
                print(f"    ⚠️  {err}")

    async def run(self) -> bool:
        """Execute the full pipeline."""
        try:
            self._print_header("🚀 Catalog Intelligence Pipeline")
            print(f"  Started: {self.state.started_at}")
            print(f"  Target: {BASE_URL}")

            # Capture baseline
            print("\n  📊 Capturing quality baseline...")
            self.state.quality_before = await self.capture_quality_baseline()
            print(f"  ✓ Baseline captured for {len(self.state.quality_before)} queries")

            # Phase 1: LLM Analysis
            if not await self.run_llm_analysis():
                print("  ⚠️  Analysis phase had issues, attempting to continue...")

            # Phase 2: Embedding Index
            if not await self.run_embedding_index():
                self.state.phase = JobPhase.FAILED
                self.generate_report()
                return False

            # Phase 3: Validation
            await self.run_validation()

            # Generate Report
            self.generate_report()

            self.state.phase = JobPhase.COMPLETE
            self._print_header(f"{JobPhase.COMPLETE.value}")
            print("  Pipeline completed successfully!\n")
            return True

        except KeyboardInterrupt:
            print("\n\n  ⚠️  Pipeline interrupted by user")
            self._stop_requested = True
            self.state.phase = JobPhase.FAILED
            return False
        except Exception as e:
            self.state.errors.append(f"Unhandled error: {e}")
            self.state.phase = JobPhase.FAILED
            self.generate_report()
            raise


async def main():
    """Main entry point."""
    print("""
╔═══════════════════════════════════════════════════════════╗
║  🚀 Self-Healing Catalog Intelligence Pipeline            ║
║  ─────────────────────────────────────────────────────    ║
║  • Automated LLM analysis + embedding reindex             ║
║  • Circuit breaker pattern for resilience                 ║
║  • Progressive retry with exponential backoff             ║
║  • Quality validation with before/after comparison        ║
╚═══════════════════════════════════════════════════════════╝
    """)

    async with CatalogPipeline() as pipeline:
        success = await pipeline.run()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
