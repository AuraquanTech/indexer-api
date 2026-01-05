#!/usr/bin/env python3
"""Quick benchmark runner for Drive H:"""
import asyncio
import json
import time
from datetime import datetime
from pathlib import Path

import httpx
import psutil

API_BASE = "http://127.0.0.1:8000/api/v1"
RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)

async def run_benchmark():
    async with httpx.AsyncClient(base_url=API_BASE, timeout=30.0) as client:
        # Register/Login
        email, password = "bench3@test.com", "BenchmarkTest123"
        await client.post("/auth/register", json={
            "email": email, "password": password,
            "full_name": "Benchmark H", "organization_name": "Benchmark"
        })
        login = await client.post("/auth/login", data={"username": email, "password": password})
        token = login.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}

        # Start indexing Drive H:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting index on H:/")
        start_time = time.time()
        cpu_samples = []
        mem_samples = []

        resp = await client.post("/indexes", json={"root_path": "H:/", "name": "Drive H External"}, headers=headers)
        if resp.status_code != 201:
            print(f"Error creating index: {resp.text}")
            return

        index_data = resp.json()
        index_id = index_data["id"]
        print(f"Index created: {index_id}")

        # Trigger scan job
        scan_resp = await client.post(f"/indexes/{index_id}/scan", json={"job_type": "full_scan"}, headers=headers)
        if scan_resp.status_code != 202:
            print(f"Error starting scan: {scan_resp.text}")
            return

        job_data = scan_resp.json()
        job_id = job_data["id"]
        print(f"Scan job started: {job_id}")

        # Poll for completion
        while True:
            await asyncio.sleep(5)
            cpu_samples.append(psutil.cpu_percent())
            mem_samples.append(psutil.Process().memory_info().rss / 1024 / 1024)

            stats_resp = await client.get(f"/indexes/{index_id}/stats", headers=headers)
            if stats_resp.status_code == 200:
                stats = stats_resp.json()
                files = stats.get("total_files", 0)
                dirs = stats.get("total_directories", 0)
                size = stats.get("total_size", 0)
                elapsed = time.time() - start_time
                rate = files / elapsed if elapsed > 0 else 0
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Files: {files:,} | Dirs: {dirs:,} | Size: {size/(1024**3):.2f} GB | Rate: {rate:.0f} files/sec")

                # Check if indexing is complete (no new files for 30 seconds)
                if elapsed > 60 and files > 0:
                    await asyncio.sleep(30)
                    stats2 = (await client.get(f"/indexes/{index_id}/stats", headers=headers)).json()
                    if stats2.get("total_files", 0) == files:
                        print("Indexing appears complete!")
                        break

            if time.time() - start_time > 7200:  # 2 hour timeout
                print("Timeout reached")
                break

        # Save results
        end_time = time.time()
        duration = end_time - start_time
        final_stats = (await client.get(f"/indexes/{index_id}/stats", headers=headers)).json()

        result = {
            "benchmark_info": {
                "version": "1.0.0",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "drive": "H:",
                "drive_label": "External 1.9TB"
            },
            "system_info": {
                "platform": "Windows 10/11",
                "python_version": "3.12",
                "cpu_cores_logical": psutil.cpu_count(),
                "ram_total_gb": round(psutil.virtual_memory().total / (1024**3), 2)
            },
            "index_info": {
                "index_id": index_id,
                "root_path": "H:/"
            },
            "results": {
                "total_files": final_stats.get("total_files", 0),
                "total_directories": final_stats.get("total_directories", 0),
                "total_size_bytes": final_stats.get("total_size", 0),
                "total_size_human": f"{final_stats.get('total_size', 0)/(1024**4):.2f} TB",
                "indexing_duration_minutes": round(duration / 60, 1),
                "files_per_second": round(final_stats.get("total_files", 0) / duration) if duration > 0 else 0,
                "avg_cpu_percent": round(sum(cpu_samples) / len(cpu_samples), 1) if cpu_samples else 0,
                "peak_cpu_percent": max(cpu_samples) if cpu_samples else 0,
                "avg_memory_mb": round(sum(mem_samples) / len(mem_samples), 1) if mem_samples else 0,
                "peak_memory_mb": round(max(mem_samples), 1) if mem_samples else 0
            },
            "extensions_breakdown": final_stats.get("extensions", {})
        }

        result_file = RESULTS_DIR / f"drive_h_v1.0.0_{datetime.now().strftime('%Y%m%d')}.json"
        with open(result_file, "w") as f:
            json.dump(result, f, indent=2)

        print(f"\nResults saved to: {result_file}")
        print(f"Total files: {result['results']['total_files']:,}")
        print(f"Total size: {result['results']['total_size_human']}")
        print(f"Duration: {result['results']['indexing_duration_minutes']:.1f} minutes")
        print(f"Rate: {result['results']['files_per_second']:,} files/sec")

if __name__ == "__main__":
    asyncio.run(run_benchmark())
