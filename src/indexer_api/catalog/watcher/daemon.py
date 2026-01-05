"""
Filesystem watcher daemon for automatic project catalog updates.

Uses watchdog for cross-platform filesystem monitoring with
root-level debouncing to prevent event storms.
"""
from __future__ import annotations

import asyncio
import os
import threading
from pathlib import Path
from typing import Callable, List, Optional, Set

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from indexer_api.catalog.watcher.debounce import RootDebouncer
from indexer_api.core.logging import get_logger

logger = get_logger(__name__)

# Directories to ignore
IGNORE_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    ".env",
    ".idea",
    ".vscode",
    "target",
    "build",
    "dist",
    ".next",
    ".nuxt",
    "coverage",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
}

# File patterns to ignore
IGNORE_PATTERNS = {
    "*.pyc",
    "*.pyo",
    "*.egg-info",
    "*.so",
    "*.dll",
    "*.log",
    "*.tmp",
    "*.temp",
    "*.swp",
    "*.lock",
}


class CatalogEventHandler(FileSystemEventHandler):
    """
    Watchdog event handler that feeds events to the debouncer.
    """

    def __init__(
        self,
        debouncer: RootDebouncer,
        loop: asyncio.AbstractEventLoop,
    ):
        super().__init__()
        self.debouncer = debouncer
        self.loop = loop
        self._ignore_dirs = IGNORE_DIRS
        self._ignore_patterns = IGNORE_PATTERNS

    def _should_ignore(self, path: str) -> bool:
        """Check if a path should be ignored."""
        parts = Path(path).parts

        # Check directory components
        for part in parts:
            if part in self._ignore_dirs:
                return True

        # Check file patterns
        name = os.path.basename(path)
        for pattern in self._ignore_patterns:
            if pattern.startswith("*"):
                if name.endswith(pattern[1:]):
                    return True
            elif name == pattern:
                return True

        return False

    def on_any_event(self, event: FileSystemEvent) -> None:
        """Handle any filesystem event."""
        if event.is_directory:
            return

        path = event.src_path
        if self._should_ignore(path):
            return

        # Schedule debounce handling on the asyncio loop
        asyncio.run_coroutine_threadsafe(
            self.debouncer.handle_event(Path(path)),
            self.loop,
        )


class WatcherDaemon:
    """
    Daemon that watches configured paths for changes and triggers
    catalog refresh jobs.
    """

    def __init__(
        self,
        watch_paths: List[str],
        on_refresh: Callable[[Path], None],
        debounce_seconds: float = 5.0,
        max_wait_seconds: float = 30.0,
    ):
        """
        Args:
            watch_paths: Paths to watch for changes
            on_refresh: Callback when a project needs refresh
            debounce_seconds: Debounce window
            max_wait_seconds: Maximum wait before forcing refresh
        """
        self.watch_paths = [Path(p).resolve() for p in watch_paths]
        self.debouncer = RootDebouncer(
            debounce_seconds=debounce_seconds,
            max_wait_seconds=max_wait_seconds,
            on_refresh=on_refresh,
        )

        self._observer: Optional[Observer] = None
        self._running = False
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    async def start(self) -> None:
        """Start the watcher daemon."""
        if self._running:
            logger.warning("watcher_already_running")
            return

        self._loop = asyncio.get_event_loop()
        self._observer = Observer()

        handler = CatalogEventHandler(self.debouncer, self._loop)

        for path in self.watch_paths:
            if path.exists() and path.is_dir():
                self._observer.schedule(handler, str(path), recursive=True)
                logger.info("watcher_path_added", path=str(path))
            else:
                logger.warning("watcher_path_not_found", path=str(path))

        self._observer.start()
        self._running = True
        logger.info(
            "watcher_started",
            paths=[str(p) for p in self.watch_paths],
        )

    async def stop(self) -> None:
        """Stop the watcher daemon."""
        if not self._running:
            return

        # Flush pending refreshes
        await self.debouncer.flush()

        if self._observer:
            self._observer.stop()
            self._observer.join(timeout=5)
            self._observer = None

        self._running = False
        logger.info("watcher_stopped")

    @property
    def is_running(self) -> bool:
        """Check if the watcher is running."""
        return self._running

    @property
    def pending_refreshes(self) -> int:
        """Number of pending refresh jobs."""
        return self.debouncer.pending_count

    def add_watch_path(self, path: str) -> None:
        """Add a new path to watch."""
        resolved = Path(path).resolve()
        if resolved not in self.watch_paths:
            self.watch_paths.append(resolved)

            if self._running and self._observer and self._loop:
                handler = CatalogEventHandler(self.debouncer, self._loop)
                self._observer.schedule(handler, str(resolved), recursive=True)
                logger.info("watcher_path_added", path=str(resolved))

    def remove_watch_path(self, path: str) -> None:
        """Remove a path from watching."""
        resolved = Path(path).resolve()
        if resolved in self.watch_paths:
            self.watch_paths.remove(resolved)
            # Note: watchdog doesn't support removing individual watches easily
            logger.info("watcher_path_removed", path=str(resolved))
