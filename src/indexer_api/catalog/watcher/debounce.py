"""
Root-level debouncer for filesystem events.

Collapses thousands of file events (e.g., from npm install) into a single
project-root-level refresh job.
"""
from __future__ import annotations

import asyncio
import time
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, Optional, Set

from indexer_api.core.logging import get_logger

logger = get_logger(__name__)

# Project markers that identify a project root
PROJECT_MARKERS = {
    # Python
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    "requirements.txt",
    "Pipfile",
    # JavaScript/TypeScript
    "package.json",
    # Rust
    "Cargo.toml",
    # Go
    "go.mod",
    # .NET
    "*.csproj",
    "*.sln",
    # Ruby
    "Gemfile",
    # Java
    "pom.xml",
    "build.gradle",
    # Generic
    ".git",
    "catalog-info.yaml",
}


@dataclass
class PendingRefresh:
    """A pending refresh job for a project root."""
    root_path: Path
    first_event_at: float
    last_event_at: float
    event_count: int = 1
    scheduled_task: Optional[asyncio.Task] = None


class RootDebouncer:
    """
    Debounces filesystem events at the project-root level.

    Instead of triggering a refresh for every file change, this:
    1. Detects the project root for any changed path
    2. Accumulates events for that root within a debounce window
    3. Triggers a single refresh job after the window expires
    """

    def __init__(
        self,
        debounce_seconds: float = 5.0,
        max_wait_seconds: float = 30.0,
        on_refresh: Optional[Callable[[Path], None]] = None,
    ):
        """
        Args:
            debounce_seconds: Time to wait after last event before triggering refresh
            max_wait_seconds: Maximum time to wait before forcing refresh
            on_refresh: Callback when a refresh should be triggered
        """
        self.debounce_seconds = debounce_seconds
        self.max_wait_seconds = max_wait_seconds
        self.on_refresh = on_refresh

        self._pending: Dict[Path, PendingRefresh] = {}
        self._root_cache: Dict[Path, Optional[Path]] = {}
        self._lock = asyncio.Lock()

    def find_project_root(self, path: Path) -> Optional[Path]:
        """Find the project root for a given path."""
        # Check cache first
        if path in self._root_cache:
            return self._root_cache[path]

        # Walk up the tree looking for project markers
        current = path if path.is_dir() else path.parent
        original = current

        while current != current.parent:
            for marker in PROJECT_MARKERS:
                if "*" in marker:
                    # Glob pattern
                    if list(current.glob(marker)):
                        self._root_cache[original] = current
                        return current
                else:
                    if (current / marker).exists():
                        self._root_cache[original] = current
                        return current
            current = current.parent

        # No project root found
        self._root_cache[original] = None
        return None

    async def handle_event(self, path: Path) -> None:
        """
        Handle a filesystem event.

        This debounces events at the project-root level.
        """
        root = self.find_project_root(path)
        if not root:
            # Not inside a project, ignore
            return

        async with self._lock:
            now = time.time()

            if root in self._pending:
                # Update existing pending refresh
                pending = self._pending[root]
                pending.last_event_at = now
                pending.event_count += 1

                # Check if we've exceeded max wait
                if now - pending.first_event_at >= self.max_wait_seconds:
                    logger.info(
                        "debounce_max_wait_exceeded",
                        root=str(root),
                        event_count=pending.event_count,
                    )
                    await self._trigger_refresh(root)
                else:
                    # Cancel and reschedule the delayed task
                    if pending.scheduled_task:
                        pending.scheduled_task.cancel()
                    pending.scheduled_task = asyncio.create_task(
                        self._delayed_refresh(root)
                    )
            else:
                # New pending refresh
                pending = PendingRefresh(
                    root_path=root,
                    first_event_at=now,
                    last_event_at=now,
                )
                pending.scheduled_task = asyncio.create_task(
                    self._delayed_refresh(root)
                )
                self._pending[root] = pending

                logger.debug(
                    "debounce_started",
                    root=str(root),
                    trigger_path=str(path),
                )

    async def _delayed_refresh(self, root: Path) -> None:
        """Wait for debounce period then trigger refresh."""
        try:
            await asyncio.sleep(self.debounce_seconds)
            await self._trigger_refresh(root)
        except asyncio.CancelledError:
            # Task was cancelled because more events came in
            pass

    async def _trigger_refresh(self, root: Path) -> None:
        """Trigger the refresh callback and clean up."""
        async with self._lock:
            pending = self._pending.pop(root, None)
            if pending and pending.scheduled_task:
                pending.scheduled_task.cancel()

        if pending:
            logger.info(
                "debounce_triggered",
                root=str(root),
                event_count=pending.event_count,
                wait_time=time.time() - pending.first_event_at,
            )

            if self.on_refresh:
                try:
                    # Support both sync and async callbacks
                    result = self.on_refresh(root)
                    if asyncio.iscoroutine(result):
                        await result
                except Exception as e:
                    logger.error(
                        "debounce_refresh_error",
                        root=str(root),
                        error=str(e),
                    )

    def clear_cache(self) -> None:
        """Clear the project root cache."""
        self._root_cache.clear()

    @property
    def pending_count(self) -> int:
        """Number of pending refresh jobs."""
        return len(self._pending)

    async def flush(self) -> None:
        """Force all pending refreshes to trigger immediately."""
        async with self._lock:
            roots = list(self._pending.keys())

        for root in roots:
            await self._trigger_refresh(root)
