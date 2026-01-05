"""
LLM Service for catalog intelligence.

Provides project summarization, auto-tagging, and natural language understanding
using Ollama or compatible LLM backends.
"""
from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

from indexer_api.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class LLMConfig:
    """LLM configuration."""
    base_url: str = "http://localhost:11434"
    model: str = "qwen2.5-coder:14b"  # Default model for text generation
    embedding_model: str = "nomic-embed-text"  # Model for embeddings
    timeout: float = 120.0  # Longer timeout for larger models
    max_tokens: int = 1024
    temperature: float = 0.3


@dataclass
class ProjectAnalysis:
    """Result of LLM project analysis."""
    summary: str
    suggested_tags: List[str]
    detected_type: str
    detected_frameworks: List[str]
    complexity_assessment: str
    key_features: List[str]
    improvement_suggestions: List[str]


class LLMService:
    """
    LLM service for project catalog intelligence.

    Provides:
    - Project summarization from README/code
    - Auto-tagging based on content analysis
    - Natural language query understanding
    - Code quality assessment
    """

    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or LLMConfig(
            base_url=os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434"),
            model=os.environ.get("CATALOG_LLM_MODEL", "qwen2.5-coder:14b"),
            embedding_model=os.environ.get("CATALOG_EMBEDDING_MODEL", "nomic-embed-text"),
        )
        self._client: Optional[httpx.AsyncClient] = None
        self._available: Optional[bool] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.config.base_url,
                timeout=self.config.timeout,
            )
        return self._client

    async def check_availability(self) -> bool:
        """Check if Ollama is available and model is loaded."""
        if self._available is not None:
            return self._available

        try:
            client = await self._get_client()
            response = await client.get("/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m.get("name", "").split(":")[0] for m in models]
                self._available = self.config.model.split(":")[0] in model_names
                logger.info(
                    "llm_availability_check",
                    available=self._available,
                    model=self.config.model,
                    available_models=model_names[:5],
                )
            else:
                self._available = False
        except Exception as e:
            logger.warning("llm_unavailable", error=str(e))
            self._available = False

        return self._available

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> Optional[str]:
        """Generate text using LLM."""
        if not await self.check_availability():
            return None

        try:
            client = await self._get_client()

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = await client.post(
                "/api/chat",
                json={
                    "model": self.config.model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": temperature or self.config.temperature,
                        "num_predict": max_tokens or self.config.max_tokens,
                    },
                },
            )

            if response.status_code == 200:
                return response.json().get("message", {}).get("content", "")

            logger.warning("llm_generation_failed", status=response.status_code)
            return None

        except Exception as e:
            logger.error("llm_generation_error", error=str(e))
            return None

    async def analyze_project(
        self,
        project_path: Path,
        readme_content: Optional[str] = None,
        file_list: Optional[List[str]] = None,
    ) -> Optional[ProjectAnalysis]:
        """
        Analyze a project and generate insights.

        Args:
            project_path: Path to the project
            readme_content: Content of README file if available
            file_list: List of files in the project
        """
        # Build context
        context_parts = [f"Project: {project_path.name}"]

        if readme_content:
            # Truncate if too long
            readme_truncated = readme_content[:3000] if len(readme_content) > 3000 else readme_content
            context_parts.append(f"\n## README:\n{readme_truncated}")

        if file_list:
            # Show key files
            key_files = [f for f in file_list[:50] if not f.startswith(".")]
            context_parts.append(f"\n## Files:\n" + "\n".join(key_files))

        context = "\n".join(context_parts)

        system_prompt = """You are a software project analyzer. Analyze the given project and provide structured insights.

Respond in valid JSON format with these fields:
{
    "summary": "2-3 sentence description of what this project does",
    "suggested_tags": ["tag1", "tag2", "tag3"],
    "detected_type": "library|application|cli|api|web|mobile|data|ml|devops|other",
    "detected_frameworks": ["framework1", "framework2"],
    "complexity_assessment": "simple|moderate|complex",
    "key_features": ["feature1", "feature2", "feature3"],
    "improvement_suggestions": ["suggestion1", "suggestion2"]
}

Be concise and accurate. Only include frameworks you're confident about."""

        prompt = f"Analyze this software project:\n\n{context}"

        result = await self.generate(prompt, system_prompt=system_prompt, temperature=0.2)

        if not result:
            return None

        try:
            # Parse JSON response
            # Handle potential markdown code blocks
            if "```json" in result:
                result = result.split("```json")[1].split("```")[0]
            elif "```" in result:
                result = result.split("```")[1].split("```")[0]

            data = json.loads(result.strip())

            return ProjectAnalysis(
                summary=data.get("summary", ""),
                suggested_tags=data.get("suggested_tags", []),
                detected_type=data.get("detected_type", "other"),
                detected_frameworks=data.get("detected_frameworks", []),
                complexity_assessment=data.get("complexity_assessment", "moderate"),
                key_features=data.get("key_features", []),
                improvement_suggestions=data.get("improvement_suggestions", []),
            )
        except json.JSONDecodeError as e:
            logger.warning("llm_json_parse_error", error=str(e), response=result[:200])
            return None

    async def generate_summary(
        self,
        readme_content: str,
        project_name: str,
    ) -> Optional[str]:
        """Generate a concise project summary from README content."""
        system_prompt = """You are a technical writer. Generate a concise 2-3 sentence summary of the software project based on the README content. Focus on what the project does and its main use case."""

        # Truncate if needed
        content = readme_content[:4000] if len(readme_content) > 4000 else readme_content
        prompt = f"Project: {project_name}\n\nREADME:\n{content}\n\nProvide a 2-3 sentence summary:"

        return await self.generate(prompt, system_prompt=system_prompt, temperature=0.3)

    async def suggest_tags(
        self,
        project_name: str,
        description: Optional[str] = None,
        languages: Optional[List[str]] = None,
        frameworks: Optional[List[str]] = None,
        file_patterns: Optional[List[str]] = None,
    ) -> List[str]:
        """Suggest tags for a project based on available information."""
        context_parts = [f"Project: {project_name}"]

        if description:
            context_parts.append(f"Description: {description}")
        if languages:
            context_parts.append(f"Languages: {', '.join(languages)}")
        if frameworks:
            context_parts.append(f"Frameworks: {', '.join(frameworks)}")
        if file_patterns:
            context_parts.append(f"Key files: {', '.join(file_patterns[:20])}")

        context = "\n".join(context_parts)

        system_prompt = """Suggest 3-5 relevant tags for categorizing this software project.
Tags should be lowercase, single words or hyphenated phrases.
Focus on: domain (web, ml, cli), purpose (api, tool, library), and key features.
Respond with only a JSON array of strings, like: ["tag1", "tag2", "tag3"]"""

        result = await self.generate(context, system_prompt=system_prompt, temperature=0.2)

        if not result:
            return []

        try:
            # Handle potential formatting
            if "[" in result:
                start = result.index("[")
                end = result.rindex("]") + 1
                result = result[start:end]
            return json.loads(result)
        except (json.JSONDecodeError, ValueError):
            return []

    async def understand_query(
        self,
        natural_query: str,
    ) -> Dict[str, Any]:
        """
        Parse a natural language search query into structured filters.

        Returns dict with:
        - keywords: list of search terms
        - filters: dict of filter conditions
        - intent: search|list|analyze|compare
        """
        system_prompt = """Parse this search query for a software project catalog into structured filters.

Respond in JSON format:
{
    "keywords": ["term1", "term2"],
    "filters": {
        "languages": ["python", "typescript"],
        "type": "api|web|cli|library|null",
        "lifecycle": "active|archived|deprecated|null",
        "has_tests": true|false|null,
        "min_health_score": 0-100|null
    },
    "intent": "search|list|analyze|compare"
}

IMPORTANT: Only include filters when EXPLICITLY mentioned in the query.
- "python web" -> languages: ["python"], but NO type filter (web is not a type filter here)
- "python library" -> languages: ["python"], type: "library"
- "active projects" -> lifecycle: "active", but no other filters
Use null for anything not explicitly specified."""

        result = await self.generate(
            f"Query: {natural_query}",
            system_prompt=system_prompt,
            temperature=0.1,
        )

        if not result:
            # Fallback to simple keyword extraction
            return {
                "keywords": natural_query.lower().split(),
                "filters": {},
                "intent": "search",
            }

        try:
            if "```json" in result:
                result = result.split("```json")[1].split("```")[0]
            elif "```" in result:
                result = result.split("```")[1].split("```")[0]

            data = json.loads(result.strip())
            # Clean up null values
            if "filters" in data:
                data["filters"] = {k: v for k, v in data["filters"].items() if v is not None}
            return data
        except (json.JSONDecodeError, ValueError):
            return {
                "keywords": natural_query.lower().split(),
                "filters": {},
                "intent": "search",
            }

    async def expand_query(
        self,
        query: str,
    ) -> str:
        """
        Expand a search query with related terms for better semantic matching.

        This improves retrieval by adding synonyms and related concepts.

        Args:
            query: Original search query

        Returns:
            Expanded query with related terms
        """
        system_prompt = """Expand this software project search query with 2-3 related terms.
Add synonyms and related concepts that would help find relevant projects.
Keep the original terms and add space-separated additions.

Examples:
- "python web" -> "python web framework api http server"
- "machine learning" -> "machine learning ml ai neural network deep learning"
- "discord bot" -> "discord bot chatbot automation messaging"

Just output the expanded query, nothing else."""

        result = await self.generate(
            f"Query: {query}",
            system_prompt=system_prompt,
            temperature=0.2,
            max_tokens=100,
        )

        if result and len(result) < 200:  # Sanity check
            return result.strip()
        return query  # Fallback to original

    async def compare_projects(
        self,
        projects: List[Dict[str, Any]],
    ) -> Optional[str]:
        """Generate a comparison analysis of multiple projects."""
        if len(projects) < 2:
            return None

        context = "Compare these software projects:\n\n"
        for i, proj in enumerate(projects[:5], 1):  # Max 5 projects
            context += f"## Project {i}: {proj.get('name', 'Unknown')}\n"
            if proj.get("description"):
                context += f"Description: {proj['description']}\n"
            if proj.get("languages"):
                context += f"Languages: {', '.join(proj['languages'])}\n"
            if proj.get("frameworks"):
                context += f"Frameworks: {', '.join(proj['frameworks'])}\n"
            context += "\n"

        system_prompt = """You are a software architect. Compare the given projects and provide:
1. Key similarities
2. Key differences
3. Use case recommendations (when to use each)
4. Overall assessment

Be concise and technical."""

        return await self.generate(context, system_prompt=system_prompt, temperature=0.4)

    async def close(self):
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None


# Global instance
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Get the global LLM service instance."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
