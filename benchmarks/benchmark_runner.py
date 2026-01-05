#!/usr/bin/env python3
"""
IndexerAPI Benchmark Runner

Captures comprehensive metrics during indexing operations for performance comparison.
"""
import asyncio
import json
import os
import platform
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
import psutil

# Configuration
API_BASE_URL = "http://127.0.0.1:8000/api/v1"
HEALTH_URL = "http://127.0.0.1:8000/health"
BENCHMARK_RESULTS_DIR = Path(__file__).parent / "results"
POLL_INTERVAL = 2  # seconds


@dataclass
class SystemInfo:
    """System information snapshot."""
    platform: str = ""
    python_version: str = ""
    cpu_model: str = ""
    cpu_cores_physical: int = 0
    cpu_cores_logical: int = 0
    ram_total_gb: float = 0.0
    disk_type: str = "unknown"

    @classmethod
    def capture(cls) -> "SystemInfo":
        """Capture current system information."""
        cpu_model = "Unknown"
        try:
            if platform.system() == "Windows":
                result = subprocess.run(
                    ["wmic", "cpu", "get", "name"],
                    capture_output=True, text=True, shell=True
                )
                lines = [l.strip() for l in result.stdout.strip().split('\n') if l.strip() and l.strip() != "Name"]
                if lines:
                    cpu_model = lines[0]
        except Exception:
            pass

        return cls(
            platform=f"{platform.system()} {platform.release()}",
            python_version=platform.python_version(),
            cpu_model=cpu_model,
            cpu_cores_physical=psutil.cpu_count(logical=False) or 0,
            cpu_cores_logical=psutil.cpu_count(logical=True) or 0,
            ram_total_gb=round(psutil.virtual_memory().total / (1024**3), 2),
        )


@dataclass
class ResourceSample:
    """Single resource usage sample."""
    timestamp: float
    cpu_percent: float
    memory_mb: float
    disk_read_mb: float
    disk_write_mb: float


@dataclass
class BenchmarkMetrics:
    """Metrics collected during a benchmark run."""
    # Timing
    start_time: str = ""
    end_time: str = ""
    duration_seconds: float = 0.0

    # Counts
    total_files: int = 0
    total_directories: int = 0
    total_size_bytes: int = 0

    # Throughput
    files_per_second: float = 0.0
    mb_per_second: float = 0.0
    dirs_per_second: float = 0.0

    # Resource usage (averages)
    avg_cpu_percent: float = 0.0
    peak_cpu_percent: float = 0.0
    avg_memory_mb: float = 0.0
    peak_memory_mb: float = 0.0
    total_disk_read_mb: float = 0.0
    total_disk_write_mb: float = 0.0

    # Samples for graphing
    resource_samples: list = field(default_factory=list)


@dataclass
class BenchmarkResult:
    """Complete benchmark result."""
    # Metadata
    benchmark_id: str = ""
    version: str = ""
    index_name: str = ""
    root_path: str = ""
    compute_hashes: bool = False

    # System info
    system: dict = field(default_factory=dict)

    # Metrics
    metrics: dict = field(default_factory=dict)

    # Index config
    include_patterns: list = field(default_factory=list)
    exclude_patterns: list = field(default_factory=list)


class BenchmarkRunner:
    """Runs benchmarks against the IndexerAPI."""

    def __init__(self, api_url: str = API_BASE_URL):
        self.api_url = api_url
        self.client = httpx.AsyncClient(base_url=api_url, timeout=300.0)
        self.auth_token: str | None = None
        self.org_id: str | None = None
        self.results_dir = BENCHMARK_RESULTS_DIR
        self.results_dir.mkdir(parents=True, exist_ok=True)

    async def authenticate(self, email: str = "bench2@test.com", password: str = "BenchmarkTest123") -> bool:
        """Authenticate with the API."""
        # Try to register first (in case user doesn't exist)
        reg_response = await self.client.post("/auth/register", json={
            "email": email,
            "password": password,
            "full_name": "Benchmark User",
            "organization_name": "Benchmark Org"
        })
        # If registration fails with "already registered", that's fine

        # Login - OAuth2 form data format
        response = await self.client.post("/auth/login", data={
            "username": email,
            "password": password
        })

        if response.status_code == 200:
            data = response.json()
            self.auth_token = data["access_token"]
            self.client.headers["Authorization"] = f"Bearer {self.auth_token}"

            # Get user info to get org_id
            me_response = await self.client.get("/auth/me")
            if me_response.status_code == 200:
                me_data = me_response.json()
                self.org_id = me_data["organization_id"]
            return True
        print(f"Login failed: {response.status_code} - {response.text}")
        return False

    async def create_index(
        self,
        name: str,
        root_path: str,
        compute_hashes: bool = False,
        include_patterns: list[str] | None = None,
        exclude_patterns: list[str] | None = None,
    ) -> dict | None:
        """Create a new index."""
        payload = {
            "name": name,
            "description": f"Benchmark index for {root_path}",
            "root_path": root_path,
            "compute_hashes": compute_hashes,
            "include_patterns": include_patterns or ["*"],
            "exclude_patterns": exclude_patterns or [
                "*.tmp", "*.temp", "~*", ".git", "__pycache__",
                "node_modules", ".venv", "venv", "$RECYCLE.BIN",
                "System Volume Information"
            ],
        }

        response = await self.client.post("/indexes", json=payload)
        if response.status_code == 201:
            return response.json()
        print(f"Failed to create index: {response.status_code} - {response.text}")
        return None

    async def start_scan(self, index_id: str, job_type: str = "full_scan") -> dict | None:
        """Start an indexing scan."""
        response = await self.client.post(
            f"/indexes/{index_id}/scan",
            json={"job_type": job_type}
        )
        if response.status_code == 202:
            return response.json()
        print(f"Failed to start scan: {response.status_code} - {response.text}")
        return None

    async def get_job_status(self, index_id: str, job_id: str) -> dict | None:
        """Get job status."""
        response = await self.client.get(f"/indexes/{index_id}/jobs/{job_id}")
        if response.status_code == 200:
            return response.json()
        return None

    async def get_index_stats(self, index_id: str) -> dict | None:
        """Get index statistics."""
        response = await self.client.get(f"/indexes/{index_id}/stats")
        if response.status_code == 200:
            return response.json()
        return None

    async def delete_index(self, index_id: str) -> bool:
        """Delete an index."""
        response = await self.client.delete(f"/indexes/{index_id}")
        return response.status_code == 200

    def _collect_resource_sample(self, start_disk: tuple) -> ResourceSample:
        """Collect a single resource usage sample."""
        disk_io = psutil.disk_io_counters()
        return ResourceSample(
            timestamp=time.time(),
            cpu_percent=psutil.cpu_percent(interval=None),
            memory_mb=psutil.Process().memory_info().rss / (1024**2),
            disk_read_mb=(disk_io.read_bytes - start_disk[0]) / (1024**2),
            disk_write_mb=(disk_io.write_bytes - start_disk[1]) / (1024**2),
        )

    async def run_benchmark(
        self,
        name: str,
        root_path: str,
        compute_hashes: bool = False,
        include_patterns: list[str] | None = None,
        exclude_patterns: list[str] | None = None,
        version: str = "1.0.0",
    ) -> BenchmarkResult:
        """Run a complete benchmark."""
        print(f"\n{'='*60}")
        print(f"BENCHMARK: {name}")
        print(f"Path: {root_path}")
        print(f"Compute hashes: {compute_hashes}")
        print(f"{'='*60}\n")

        # Capture system info
        system_info = SystemInfo.capture()
        print(f"System: {system_info.cpu_model}")
        print(f"RAM: {system_info.ram_total_gb}GB")
        print()

        # Create index
        print("Creating index...")
        index = await self.create_index(
            name=name,
            root_path=root_path,
            compute_hashes=compute_hashes,
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns,
        )

        if not index:
            raise RuntimeError("Failed to create index")

        index_id = index["id"]
        print(f"Index created: {index_id}")

        # Start scan and collect metrics
        print("Starting scan...")
        start_time = datetime.now()
        disk_io_start = psutil.disk_io_counters()
        start_disk = (disk_io_start.read_bytes, disk_io_start.write_bytes)

        job = await self.start_scan(index_id)
        if not job:
            raise RuntimeError("Failed to start scan")

        job_id = job["id"]
        print(f"Job started: {job_id}")

        # Monitor progress
        samples: list[ResourceSample] = []
        last_status = ""

        while True:
            job_status = await self.get_job_status(index_id, job_id)
            if not job_status:
                await asyncio.sleep(POLL_INTERVAL)
                continue

            status = job_status["status"]
            progress = job_status.get("progress_percent", 0)

            # Collect resource sample
            sample = self._collect_resource_sample(start_disk)
            samples.append(sample)

            # Print progress
            if status != last_status or progress % 10 == 0:
                print(f"  Status: {status} | Progress: {progress:.1f}% | "
                      f"CPU: {sample.cpu_percent:.1f}% | "
                      f"Mem: {sample.memory_mb:.1f}MB")
                last_status = status

            if status in ["completed", "failed"]:
                break

            await asyncio.sleep(POLL_INTERVAL)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Get final stats
        stats = await self.get_index_stats(index_id)

        # Calculate metrics
        total_files = stats.get("total_files", 0) if stats else 0
        total_dirs = stats.get("total_directories", 0) if stats else 0
        total_size = stats.get("total_size_bytes", 0) if stats else 0

        cpu_values = [s.cpu_percent for s in samples]
        mem_values = [s.memory_mb for s in samples]

        metrics = BenchmarkMetrics(
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
            duration_seconds=duration,
            total_files=total_files,
            total_directories=total_dirs,
            total_size_bytes=total_size,
            files_per_second=total_files / duration if duration > 0 else 0,
            mb_per_second=(total_size / (1024**2)) / duration if duration > 0 else 0,
            dirs_per_second=total_dirs / duration if duration > 0 else 0,
            avg_cpu_percent=sum(cpu_values) / len(cpu_values) if cpu_values else 0,
            peak_cpu_percent=max(cpu_values) if cpu_values else 0,
            avg_memory_mb=sum(mem_values) / len(mem_values) if mem_values else 0,
            peak_memory_mb=max(mem_values) if mem_values else 0,
            total_disk_read_mb=samples[-1].disk_read_mb if samples else 0,
            total_disk_write_mb=samples[-1].disk_write_mb if samples else 0,
            resource_samples=[asdict(s) for s in samples],
        )

        # Print summary
        print(f"\n{'='*60}")
        print("BENCHMARK COMPLETE")
        print(f"{'='*60}")
        print(f"Duration: {duration:.2f}s")
        print(f"Files: {total_files:,} ({metrics.files_per_second:.1f}/sec)")
        print(f"Directories: {total_dirs:,}")
        print(f"Total size: {total_size / (1024**3):.2f}GB")
        print(f"Throughput: {metrics.mb_per_second:.2f}MB/s")
        print(f"Avg CPU: {metrics.avg_cpu_percent:.1f}% (peak: {metrics.peak_cpu_percent:.1f}%)")
        print(f"Avg Memory: {metrics.avg_memory_mb:.1f}MB (peak: {metrics.peak_memory_mb:.1f}MB)")
        print(f"Disk I/O: Read {metrics.total_disk_read_mb:.1f}MB, Write {metrics.total_disk_write_mb:.1f}MB")
        print()

        # Create result
        result = BenchmarkResult(
            benchmark_id=f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            version=version,
            index_name=name,
            root_path=root_path,
            compute_hashes=compute_hashes,
            system=asdict(system_info),
            metrics=asdict(metrics),
            include_patterns=include_patterns or ["*"],
            exclude_patterns=exclude_patterns or [],
        )

        # Save result
        result_file = self.results_dir / f"{result.benchmark_id}.json"
        with open(result_file, "w") as f:
            json.dump(asdict(result), f, indent=2, default=str)
        print(f"Results saved: {result_file}")

        return result

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


async def run_drive_benchmarks(
    drives: list[str],
    compute_hashes: bool = False,
    version: str = "1.0.0",
):
    """Run benchmarks on multiple drives."""
    runner = BenchmarkRunner()

    try:
        # Wait for server to be ready
        print("Waiting for server...")
        async with httpx.AsyncClient() as health_client:
            for _ in range(30):
                try:
                    response = await health_client.get(HEALTH_URL)
                    if response.status_code == 200:
                        print("Server is ready!")
                        break
                except Exception:
                    pass
                await asyncio.sleep(1)
            else:
                print("Server not available!")
                return

        # Authenticate
        print("Authenticating...")
        if not await runner.authenticate():
            print("Authentication failed!")
            return
        print("Authenticated successfully!")

        # Run benchmarks for each drive
        results = []
        for drive in drives:
            drive_path = f"{drive}/"
            drive_name = f"Drive_{drive.replace(':', '')}"

            try:
                result = await runner.run_benchmark(
                    name=drive_name,
                    root_path=drive_path,
                    compute_hashes=compute_hashes,
                    version=version,
                )
                results.append(result)
            except Exception as e:
                print(f"Benchmark failed for {drive}: {e}")

        # Print comparison
        if len(results) > 1:
            print(f"\n{'='*60}")
            print("BENCHMARK COMPARISON")
            print(f"{'='*60}")
            print(f"{'Drive':<10} {'Files':>12} {'Duration':>12} {'Files/sec':>12} {'MB/s':>10}")
            print("-" * 60)
            for r in results:
                m = r.metrics
                print(f"{r.index_name:<10} {m['total_files']:>12,} {m['duration_seconds']:>11.1f}s "
                      f"{m['files_per_second']:>12.1f} {m['mb_per_second']:>10.1f}")

    finally:
        await runner.close()


def compare_results(results_dir: Path = BENCHMARK_RESULTS_DIR):
    """Compare all benchmark results in the results directory."""
    results = []
    for f in results_dir.glob("*.json"):
        with open(f) as fp:
            results.append(json.load(fp))

    if not results:
        print("No benchmark results found.")
        return

    # Sort by date
    results.sort(key=lambda r: r.get("metrics", {}).get("start_time", ""))

    print(f"\n{'='*80}")
    print("BENCHMARK HISTORY")
    print(f"{'='*80}")
    print(f"{'ID':<30} {'Version':<10} {'Files':>12} {'Duration':>10} {'Files/s':>10} {'MB/s':>8}")
    print("-" * 80)

    for r in results:
        m = r.get("metrics", {})
        print(f"{r['benchmark_id']:<30} {r['version']:<10} "
              f"{m.get('total_files', 0):>12,} "
              f"{m.get('duration_seconds', 0):>9.1f}s "
              f"{m.get('files_per_second', 0):>10.1f} "
              f"{m.get('mb_per_second', 0):>8.1f}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="IndexerAPI Benchmark Runner")
    parser.add_argument("--drives", nargs="+", default=["E:", "H:"],
                        help="Drives to benchmark")
    parser.add_argument("--hashes", action="store_true",
                        help="Compute file hashes during indexing")
    parser.add_argument("--version", default="1.0.0",
                        help="Version tag for this benchmark")
    parser.add_argument("--compare", action="store_true",
                        help="Compare existing benchmark results")

    args = parser.parse_args()

    if args.compare:
        compare_results()
    else:
        asyncio.run(run_drive_benchmarks(
            drives=args.drives,
            compute_hashes=args.hashes,
            version=args.version,
        ))
