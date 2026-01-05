"""
Quality Assessment Service.

Provides comprehensive quality analysis for projects:
- Production readiness determination
- Code quality scoring
- Best practices assessment
- Improvement recommendations
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from indexer_api.core.logging import get_logger
from indexer_api.catalog.llm.service import get_llm_service

logger = get_logger(__name__)


@dataclass
class QualityIndicators:
    """Quality indicator flags from file system analysis."""
    has_readme: bool = False
    has_license: bool = False
    has_tests: bool = False
    has_ci_cd: bool = False
    has_documentation: bool = False
    has_changelog: bool = False
    has_contributing: bool = False
    has_security_policy: bool = False
    has_package_json: bool = False
    has_docker: bool = False
    has_linting: bool = False
    has_type_hints: bool = False

    def to_dict(self) -> Dict[str, bool]:
        return {
            "has_readme": self.has_readme,
            "has_license": self.has_license,
            "has_tests": self.has_tests,
            "has_ci_cd": self.has_ci_cd,
            "has_documentation": self.has_documentation,
            "has_changelog": self.has_changelog,
            "has_contributing": self.has_contributing,
            "has_security_policy": self.has_security_policy,
            "has_package_json": self.has_package_json,
            "has_docker": self.has_docker,
            "has_linting": self.has_linting,
            "has_type_hints": self.has_type_hints,
        }

    def completeness_score(self) -> int:
        """Calculate a completeness score based on indicators (0-100)."""
        weights = {
            "has_readme": 15,
            "has_license": 10,
            "has_tests": 20,
            "has_ci_cd": 15,
            "has_documentation": 10,
            "has_changelog": 5,
            "has_contributing": 5,
            "has_security_policy": 5,
            "has_package_json": 5,
            "has_docker": 5,
            "has_linting": 5,
        }
        total = sum(weights[k] for k, v in self.to_dict().items() if v and k in weights)
        return min(total, 100)


@dataclass
class QualityAssessmentResult:
    """Complete quality assessment for a project."""
    production_readiness: str  # unknown, prototype, alpha, beta, production, mature, legacy, deprecated
    quality_score: float  # 0-100
    code_quality_score: int
    documentation_score: int
    test_score: int
    security_score: int
    maintainability_score: int
    key_features: List[str] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    production_blockers: List[str] = field(default_factory=list)
    recommended_improvements: List[str] = field(default_factory=list)
    technology_stack: List[str] = field(default_factory=list)
    use_cases: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code_quality_score": self.code_quality_score,
            "documentation_score": self.documentation_score,
            "test_score": self.test_score,
            "security_score": self.security_score,
            "maintainability_score": self.maintainability_score,
            "key_features": self.key_features,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "production_blockers": self.production_blockers,
            "recommended_improvements": self.recommended_improvements,
            "technology_stack": self.technology_stack,
            "use_cases": self.use_cases,
        }


class QualityAssessmentService:
    """Service for assessing project quality and production readiness."""

    # File patterns for quality indicators
    README_PATTERNS = ["README.md", "README.rst", "README.txt", "README"]
    LICENSE_PATTERNS = ["LICENSE", "LICENSE.md", "LICENSE.txt", "LICENCE", "COPYING"]
    TEST_PATTERNS = ["test", "tests", "spec", "specs", "__tests__", "test_*.py", "*_test.py"]
    CI_PATTERNS = [".github/workflows", ".gitlab-ci.yml", ".travis.yml", "Jenkinsfile", ".circleci", "azure-pipelines.yml"]
    DOC_PATTERNS = ["docs", "documentation", "doc", "wiki"]
    CHANGELOG_PATTERNS = ["CHANGELOG.md", "CHANGELOG", "HISTORY.md", "CHANGES.md", "NEWS.md"]
    CONTRIBUTING_PATTERNS = ["CONTRIBUTING.md", "CONTRIBUTING", "CONTRIBUTE.md"]
    SECURITY_PATTERNS = ["SECURITY.md", "SECURITY", ".github/SECURITY.md"]
    DOCKER_PATTERNS = ["Dockerfile", "docker-compose.yml", "docker-compose.yaml", ".dockerignore"]
    LINT_PATTERNS = [".eslintrc", ".eslintrc.js", ".eslintrc.json", "pylintrc", ".flake8", "pyproject.toml", ".prettierrc", "tslint.json", "biome.json"]

    def __init__(self):
        self.llm = get_llm_service()

    def scan_quality_indicators(self, project_path: Path) -> QualityIndicators:
        """Scan project filesystem for quality indicators."""
        indicators = QualityIndicators()

        if not project_path.exists():
            return indicators

        try:
            # Get all files and directories
            items = list(project_path.iterdir())
            item_names = [i.name.lower() for i in items]
            item_names_original = [i.name for i in items]

            # Check README
            indicators.has_readme = any(
                name.lower() in [p.lower() for p in self.README_PATTERNS]
                for name in item_names_original
            )

            # Check LICENSE
            indicators.has_license = any(
                name.lower() in [p.lower() for p in self.LICENSE_PATTERNS]
                for name in item_names_original
            )

            # Check for tests
            for pattern in self.TEST_PATTERNS:
                if pattern.lower() in item_names:
                    indicators.has_tests = True
                    break
            # Also check for pytest.ini, conftest.py
            if not indicators.has_tests:
                indicators.has_tests = any(
                    n in item_names for n in ["pytest.ini", "conftest.py", "jest.config.js", "vitest.config.ts"]
                )

            # Check CI/CD
            for pattern in self.CI_PATTERNS:
                if "/" in pattern:
                    parts = pattern.split("/")
                    check_path = project_path / parts[0]
                    if check_path.exists() and check_path.is_dir():
                        indicators.has_ci_cd = True
                        break
                elif pattern.lower() in item_names:
                    indicators.has_ci_cd = True
                    break

            # Check documentation
            indicators.has_documentation = any(
                name.lower() in [p.lower() for p in self.DOC_PATTERNS]
                for name in item_names_original
            )

            # Check changelog
            indicators.has_changelog = any(
                name.lower() in [p.lower() for p in self.CHANGELOG_PATTERNS]
                for name in item_names_original
            )

            # Check contributing
            indicators.has_contributing = any(
                name.lower() in [p.lower() for p in self.CONTRIBUTING_PATTERNS]
                for name in item_names_original
            )

            # Check security policy
            for pattern in self.SECURITY_PATTERNS:
                if "/" in pattern:
                    check_path = project_path / pattern
                    if check_path.exists():
                        indicators.has_security_policy = True
                        break
                elif pattern.lower() in item_names:
                    indicators.has_security_policy = True
                    break

            # Check package.json
            indicators.has_package_json = "package.json" in item_names_original

            # Check Docker
            indicators.has_docker = any(
                name.lower() in [p.lower() for p in self.DOCKER_PATTERNS]
                for name in item_names_original
            )

            # Check linting configs
            indicators.has_linting = any(
                name.lower() in [p.lower() for p in self.LINT_PATTERNS]
                for name in item_names_original
            ) or "pyproject.toml" in item_names

            # Check type hints (Python: py.typed, TypeScript: tsconfig.json)
            indicators.has_type_hints = any(
                name in ["py.typed", "tsconfig.json", "tsconfig.base.json"]
                for name in item_names_original
            )

        except Exception as e:
            logger.warning("quality_scan_error", path=str(project_path), error=str(e))

        return indicators

    async def assess_project(
        self,
        project_path: Path,
        readme_content: Optional[str] = None,
        file_list: Optional[List[str]] = None,
        existing_description: Optional[str] = None,
        languages: Optional[List[str]] = None,
        frameworks: Optional[List[str]] = None,
    ) -> Optional[QualityAssessmentResult]:
        """
        Perform comprehensive quality assessment of a project.

        Uses both filesystem analysis and LLM-based evaluation.
        """
        # First, scan filesystem for indicators
        indicators = self.scan_quality_indicators(project_path)

        # Build context for LLM
        context_parts = [f"Project: {project_path.name}"]

        if existing_description:
            context_parts.append(f"\nDescription: {existing_description}")

        if languages:
            context_parts.append(f"\nLanguages: {', '.join(languages)}")

        if frameworks:
            context_parts.append(f"\nFrameworks: {', '.join(frameworks)}")

        # Add quality indicators
        context_parts.append(f"\n\nQuality Indicators Found:")
        for key, value in indicators.to_dict().items():
            status = "Yes" if value else "No"
            context_parts.append(f"  - {key.replace('has_', '').replace('_', ' ').title()}: {status}")

        if readme_content:
            readme_truncated = readme_content[:3000] if len(readme_content) > 3000 else readme_content
            context_parts.append(f"\n\n## README:\n{readme_truncated}")

        if file_list:
            key_files = [f for f in file_list[:100] if not f.startswith(".")]
            context_parts.append(f"\n\n## Files ({len(file_list)} total):\n" + "\n".join(key_files[:50]))

        context = "\n".join(context_parts)

        # LLM quality assessment
        system_prompt = """You are a senior software architect performing a quality assessment.
Analyze the project and provide a comprehensive evaluation.

Respond in valid JSON format:
{
    "production_readiness": "prototype|alpha|beta|production|mature|legacy|deprecated",
    "code_quality_score": 0-100,
    "documentation_score": 0-100,
    "test_score": 0-100,
    "security_score": 0-100,
    "maintainability_score": 0-100,
    "key_features": ["feature1", "feature2"],
    "strengths": ["strength1", "strength2"],
    "weaknesses": ["weakness1", "weakness2"],
    "production_blockers": ["blocker1 if any"],
    "recommended_improvements": ["improvement1", "improvement2"],
    "technology_stack": ["tech1", "tech2"],
    "use_cases": ["use case 1", "use case 2"]
}

Production Readiness Guidelines:
- prototype: Experimental, proof of concept, not functional
- alpha: Early development, core features incomplete, unstable
- beta: Feature complete but needs testing, some bugs expected
- production: Stable, tested, documented, ready for production use
- mature: Battle-tested, comprehensive docs, active maintenance
- legacy: Old but functional, may lack modern practices
- deprecated: Should not be used for new projects

Scoring Guidelines (0-100):
- 90-100: Excellent - Industry best practices
- 70-89: Good - Solid implementation
- 50-69: Fair - Works but needs improvement
- 30-49: Poor - Significant issues
- 0-29: Critical - Major problems

Be realistic and critical. Only score high if evidence supports it."""

        prompt = f"Assess this project's quality and production readiness:\n\n{context}"

        result = await self.llm.generate(prompt, system_prompt=system_prompt, temperature=0.2)

        if not result:
            # Fallback to indicator-based assessment
            return self._fallback_assessment(indicators)

        try:
            # Parse JSON response
            if "```json" in result:
                result = result.split("```json")[1].split("```")[0]
            elif "```" in result:
                result = result.split("```")[1].split("```")[0]

            data = json.loads(result.strip())

            # Calculate overall quality score
            scores = [
                data.get("code_quality_score", 50),
                data.get("documentation_score", 50),
                data.get("test_score", 50),
                data.get("security_score", 50),
                data.get("maintainability_score", 50),
            ]
            overall_score = sum(scores) / len(scores)

            # Boost/penalize based on indicators
            indicator_bonus = indicators.completeness_score() * 0.1  # Up to 10 points
            overall_score = min(100, overall_score + indicator_bonus)

            return QualityAssessmentResult(
                production_readiness=data.get("production_readiness", "unknown"),
                quality_score=round(overall_score, 1),
                code_quality_score=data.get("code_quality_score", 50),
                documentation_score=data.get("documentation_score", 50),
                test_score=data.get("test_score", 50),
                security_score=data.get("security_score", 50),
                maintainability_score=data.get("maintainability_score", 50),
                key_features=data.get("key_features", []),
                strengths=data.get("strengths", []),
                weaknesses=data.get("weaknesses", []),
                production_blockers=data.get("production_blockers", []),
                recommended_improvements=data.get("recommended_improvements", []),
                technology_stack=data.get("technology_stack", []),
                use_cases=data.get("use_cases", []),
            )

        except json.JSONDecodeError as e:
            logger.warning("quality_json_parse_error", error=str(e), response=result[:200])
            return self._fallback_assessment(indicators)

    def _fallback_assessment(self, indicators: QualityIndicators) -> QualityAssessmentResult:
        """Generate assessment from indicators only when LLM fails."""
        score = indicators.completeness_score()

        # Determine readiness from indicators
        if score >= 80 and indicators.has_tests and indicators.has_ci_cd:
            readiness = "production"
        elif score >= 60 and indicators.has_tests:
            readiness = "beta"
        elif score >= 40:
            readiness = "alpha"
        else:
            readiness = "prototype"

        weaknesses = []
        improvements = []
        if not indicators.has_readme:
            weaknesses.append("Missing README documentation")
            improvements.append("Add a comprehensive README")
        if not indicators.has_tests:
            weaknesses.append("No test suite found")
            improvements.append("Add unit and integration tests")
        if not indicators.has_ci_cd:
            weaknesses.append("No CI/CD pipeline")
            improvements.append("Set up automated CI/CD")
        if not indicators.has_license:
            weaknesses.append("Missing license file")
            improvements.append("Add an appropriate license")

        strengths = []
        if indicators.has_readme:
            strengths.append("Has README documentation")
        if indicators.has_tests:
            strengths.append("Has test suite")
        if indicators.has_ci_cd:
            strengths.append("Has CI/CD pipeline")
        if indicators.has_docker:
            strengths.append("Docker containerized")

        return QualityAssessmentResult(
            production_readiness=readiness,
            quality_score=float(score),
            code_quality_score=score,
            documentation_score=100 if indicators.has_readme else 30,
            test_score=100 if indicators.has_tests else 0,
            security_score=50,
            maintainability_score=score,
            strengths=strengths,
            weaknesses=weaknesses,
            production_blockers=[w for w in weaknesses[:2]] if score < 50 else [],
            recommended_improvements=improvements,
        )


# Global instance
_quality_service: Optional[QualityAssessmentService] = None


def get_quality_service() -> QualityAssessmentService:
    """Get the global quality assessment service instance."""
    global _quality_service
    if _quality_service is None:
        _quality_service = QualityAssessmentService()
    return _quality_service
