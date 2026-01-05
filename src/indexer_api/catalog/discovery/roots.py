"""
Project discovery and manifest parsing.

Detects project roots and extracts metadata from various manifest formats.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
import tomllib  # Python 3.11+

from indexer_api.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ProjectManifest:
    """Extracted project metadata from manifest files."""
    name: str
    title: Optional[str] = None
    description: Optional[str] = None
    version: Optional[str] = None
    languages: List[str] = field(default_factory=list)
    frameworks: List[str] = field(default_factory=list)
    license_spdx: Optional[str] = None
    repository_url: Optional[str] = None
    authors: List[str] = field(default_factory=list)
    dependencies: Dict[str, str] = field(default_factory=dict)
    dev_dependencies: Dict[str, str] = field(default_factory=dict)
    keywords: List[str] = field(default_factory=list)
    extra: Dict[str, Any] = field(default_factory=dict)


# Manifest file priorities (higher = preferred)
MANIFEST_PRIORITY = {
    "catalog-info.yaml": 100,  # Backstage format
    "pyproject.toml": 90,
    "package.json": 85,
    "Cargo.toml": 80,
    "go.mod": 75,
    "setup.py": 70,
    "requirements.txt": 50,
    ".csproj": 60,
    "pom.xml": 55,
    "build.gradle": 55,
    "Gemfile": 50,
}

# Framework detection patterns
FRAMEWORK_PATTERNS = {
    # Python
    "fastapi": "FastAPI",
    "django": "Django",
    "flask": "Flask",
    "starlette": "Starlette",
    "pytorch": "PyTorch",
    "tensorflow": "TensorFlow",
    "numpy": "NumPy",
    "pandas": "Pandas",
    # JavaScript/TypeScript
    "react": "React",
    "vue": "Vue",
    "angular": "Angular",
    "next": "Next.js",
    "nuxt": "Nuxt",
    "express": "Express",
    "nestjs": "NestJS",
    "svelte": "Svelte",
    # Rust
    "actix-web": "Actix",
    "axum": "Axum",
    "rocket": "Rocket",
    "tokio": "Tokio",
}


class ProjectDiscovery:
    """
    Discovers projects in a directory tree and extracts metadata.
    """

    def __init__(
        self,
        max_depth: int = 10,
        skip_hidden: bool = True,
        skip_dirs: Optional[Set[str]] = None,
    ):
        self.max_depth = max_depth
        self.skip_hidden = skip_hidden
        self.skip_dirs = skip_dirs or {
            "node_modules",
            ".git",
            "__pycache__",
            ".venv",
            "venv",
            "target",
            "build",
            "dist",
            ".next",
        }

    def discover(self, root_path: Path) -> List[tuple[Path, ProjectManifest]]:
        """
        Discover all projects under a root path.

        Returns list of (project_path, manifest) tuples.
        """
        projects = []
        visited: Set[Path] = set()

        def scan_dir(path: Path, depth: int) -> None:
            if depth > self.max_depth:
                return

            if path in visited:
                return
            visited.add(path)

            # Check for project markers
            manifest = self.detect_project(path)
            if manifest:
                projects.append((path, manifest))
                # Don't recurse into detected projects (they're complete)
                return

            # Recurse into subdirectories
            try:
                for entry in path.iterdir():
                    if not entry.is_dir():
                        continue

                    name = entry.name
                    if self.skip_hidden and name.startswith("."):
                        continue
                    if name in self.skip_dirs:
                        continue

                    scan_dir(entry, depth + 1)
            except PermissionError:
                pass

        scan_dir(root_path.resolve(), 0)
        return projects

    def detect_project(self, path: Path) -> Optional[ProjectManifest]:
        """
        Detect if a path is a project root and extract manifest.
        """
        # Find the highest priority manifest file
        best_manifest = None
        best_priority = -1

        for manifest_file, priority in MANIFEST_PRIORITY.items():
            if "*" in manifest_file:
                # Glob pattern (e.g., *.csproj)
                matches = list(path.glob(manifest_file))
                if matches and priority > best_priority:
                    best_manifest = matches[0]
                    best_priority = priority
            else:
                manifest_path = path / manifest_file
                if manifest_path.exists() and priority > best_priority:
                    best_manifest = manifest_path
                    best_priority = priority

        if not best_manifest:
            return None

        # Parse the manifest
        return self.parse_manifest(best_manifest, path)

    def parse_manifest(self, manifest_path: Path, project_path: Path) -> ProjectManifest:
        """Parse a manifest file and return project metadata."""
        name = manifest_path.name.lower()

        try:
            if name == "pyproject.toml":
                return self._parse_pyproject(manifest_path, project_path)
            elif name == "package.json":
                return self._parse_package_json(manifest_path, project_path)
            elif name == "cargo.toml":
                return self._parse_cargo_toml(manifest_path, project_path)
            elif name == "go.mod":
                return self._parse_go_mod(manifest_path, project_path)
            elif name.endswith(".csproj"):
                return self._parse_csproj(manifest_path, project_path)
            elif name == "catalog-info.yaml":
                return self._parse_catalog_info(manifest_path, project_path)
            else:
                # Fallback: use directory name
                return ProjectManifest(
                    name=project_path.name,
                    languages=self._detect_languages(project_path),
                )
        except Exception as e:
            logger.warning(
                "manifest_parse_error",
                path=str(manifest_path),
                error=str(e),
            )
            return ProjectManifest(name=project_path.name)

    def _parse_pyproject(self, path: Path, project_path: Path) -> ProjectManifest:
        """Parse pyproject.toml."""
        with open(path, "rb") as f:
            data = tomllib.load(f)

        project = data.get("project", {})
        poetry = data.get("tool", {}).get("poetry", {})

        # Merge project and poetry sections
        name = project.get("name") or poetry.get("name") or project_path.name
        description = project.get("description") or poetry.get("description")
        version = project.get("version") or poetry.get("version")
        license_id = project.get("license") or poetry.get("license")
        keywords = project.get("keywords", []) + poetry.get("keywords", [])

        # Extract dependencies
        deps = {}
        if "dependencies" in project:
            for dep in project["dependencies"]:
                if isinstance(dep, str):
                    deps[dep.split(">=")[0].split("==")[0]] = ""
        if "dependencies" in poetry:
            deps.update(poetry["dependencies"])

        # Detect frameworks
        frameworks = self._detect_frameworks(deps, "python")

        # Repository URL
        repo_url = None
        urls = project.get("urls", {})
        for key in ["Repository", "Source", "Homepage"]:
            if key in urls:
                repo_url = urls[key]
                break

        return ProjectManifest(
            name=name,
            description=description,
            version=version,
            languages=["Python"],
            frameworks=frameworks,
            license_spdx=license_id if isinstance(license_id, str) else None,
            repository_url=repo_url,
            keywords=keywords,
            dependencies=deps,
        )

    def _parse_package_json(self, path: Path, project_path: Path) -> ProjectManifest:
        """Parse package.json."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        name = data.get("name", project_path.name)
        deps = data.get("dependencies", {})
        dev_deps = data.get("devDependencies", {})

        # Detect language (TypeScript if tsconfig exists or TS in deps)
        languages = ["JavaScript"]
        if (project_path / "tsconfig.json").exists() or "typescript" in {**deps, **dev_deps}:
            languages = ["TypeScript", "JavaScript"]

        # Detect frameworks
        all_deps = {**deps, **dev_deps}
        frameworks = self._detect_frameworks(all_deps, "js")

        # Repository URL
        repo = data.get("repository", {})
        repo_url = repo.get("url") if isinstance(repo, dict) else repo

        return ProjectManifest(
            name=name,
            description=data.get("description"),
            version=data.get("version"),
            languages=languages,
            frameworks=frameworks,
            license_spdx=data.get("license"),
            repository_url=repo_url,
            keywords=data.get("keywords", []),
            dependencies=deps,
            dev_dependencies=dev_deps,
        )

    def _parse_cargo_toml(self, path: Path, project_path: Path) -> ProjectManifest:
        """Parse Cargo.toml."""
        with open(path, "rb") as f:
            data = tomllib.load(f)

        package = data.get("package", {})
        deps = data.get("dependencies", {})

        frameworks = self._detect_frameworks(deps, "rust")

        return ProjectManifest(
            name=package.get("name", project_path.name),
            description=package.get("description"),
            version=package.get("version"),
            languages=["Rust"],
            frameworks=frameworks,
            license_spdx=package.get("license"),
            repository_url=package.get("repository"),
            keywords=package.get("keywords", []),
            dependencies={k: str(v) if isinstance(v, dict) else v for k, v in deps.items()},
        )

    def _parse_go_mod(self, path: Path, project_path: Path) -> ProjectManifest:
        """Parse go.mod."""
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        # Extract module name
        module_match = re.search(r"^module\s+(\S+)", content, re.MULTILINE)
        name = module_match.group(1) if module_match else project_path.name

        # Extract dependencies
        deps = {}
        for match in re.finditer(r"^\s+(\S+)\s+v([\d.]+)", content, re.MULTILINE):
            deps[match.group(1)] = match.group(2)

        return ProjectManifest(
            name=name,
            languages=["Go"],
            dependencies=deps,
        )

    def _parse_csproj(self, path: Path, project_path: Path) -> ProjectManifest:
        """Parse .csproj file (basic XML parsing)."""
        import xml.etree.ElementTree as ET

        tree = ET.parse(path)
        root = tree.getroot()

        # Try to get project name from AssemblyName or RootNamespace
        name = project_path.name
        for elem in root.iter():
            if elem.tag.endswith("AssemblyName") and elem.text:
                name = elem.text
                break
            elif elem.tag.endswith("RootNamespace") and elem.text:
                name = elem.text

        # Detect framework
        frameworks = []
        for elem in root.iter():
            if elem.tag.endswith("TargetFramework") and elem.text:
                if "net" in elem.text.lower():
                    frameworks.append(".NET")
                break

        return ProjectManifest(
            name=name,
            languages=["C#"],
            frameworks=frameworks,
        )

    def _parse_catalog_info(self, path: Path, project_path: Path) -> ProjectManifest:
        """Parse Backstage catalog-info.yaml."""
        import yaml

        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        metadata = data.get("metadata", {})
        spec = data.get("spec", {})

        return ProjectManifest(
            name=metadata.get("name", project_path.name),
            title=metadata.get("title"),
            description=metadata.get("description"),
            languages=spec.get("languages", []),
            frameworks=spec.get("frameworks", []),
            keywords=metadata.get("tags", []),
            extra={"backstage": data},
        )

    def _detect_frameworks(self, deps: Dict[str, Any], ecosystem: str) -> List[str]:
        """Detect frameworks from dependencies."""
        frameworks = []
        dep_names = {k.lower() for k in deps.keys()}

        for pattern, framework in FRAMEWORK_PATTERNS.items():
            if pattern.lower() in dep_names:
                frameworks.append(framework)

        return frameworks

    def _detect_languages(self, path: Path) -> List[str]:
        """Detect languages by file extensions."""
        extensions: Dict[str, str] = {
            ".py": "Python",
            ".js": "JavaScript",
            ".ts": "TypeScript",
            ".rs": "Rust",
            ".go": "Go",
            ".java": "Java",
            ".cs": "C#",
            ".rb": "Ruby",
            ".php": "PHP",
            ".swift": "Swift",
            ".kt": "Kotlin",
        }

        found = set()
        try:
            for entry in path.rglob("*"):
                if entry.is_file():
                    ext = entry.suffix.lower()
                    if ext in extensions:
                        found.add(extensions[ext])
                        if len(found) >= 3:
                            break
        except PermissionError:
            pass

        return list(found)
