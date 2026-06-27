"""Use case for enriching structural data with AI-generated insights.

This module consumes raw RepositoryBlueprint aggregates and communicates with
an abstract LLM interface to generate natural language documentation, such as
system descriptions, onboarding guides, and module summaries.
"""

import json
from dataclasses import asdict
from typing import Protocol, Any

from repolens.domain.models import RepositoryBlueprint


class LLMClientProtocol(Protocol):
    """Abstract boundary for communicating with an LLM service (e.g. OpenAI API).
    
    The infrastructure layer will provide the concrete HTTP client implementation.
    """
    def generate_completion(self, system_prompt: str, user_prompt: str) -> str:
        """Send a prompt to the LLM and return the textual response."""
        ...


class AIEnrichmentService:
    """Service that orchestrates LLM calls to enrich repository structural data."""

    def __init__(self, llm_client: LLMClientProtocol) -> None:
        """Initialize the enrichment service.
        
        Args:
            llm_client: An injected implementation of the LLM client protocol.
        """
        self.llm_client = llm_client

    def _serialize_blueprint(self, blueprint: RepositoryBlueprint) -> str:
        """Convert the immutable Blueprint into a lightweight JSON representation.
        
        This strips away complex object memory graphs into simple dictionaries
        optimized for LLM context windows.
        """
        # Convert dataclass to dict recursively
        raw_dict = asdict(blueprint)
        
        # In a full production implementation we would heavily filter the dict
        # here to ensure it fits within token limits (e.g., omitting deeply
        # nested parameters if the repo is massive). 
        # For Phase 3, standard serialization serves the purpose.
        return json.dumps(raw_dict, indent=2)

    def generate_repository_summary(self, blueprint: RepositoryBlueprint) -> str:
        """Generate a high-level markdown description of the repository.
        
        Args:
            blueprint: The pure structural model of the repository.
            
        Returns:
            A markdown-formatted natural language overview.
        """
        system_prompt = (
            "You are an expert Principal Software Engineer. "
            "Your task is to analyze the structural footprint of a codebase and write "
            "a concise, professional repository summary. "
            "Focus on the architectural layers, primary entry points, and domain purpose. "
            "Return ONLY valid Markdown. Do not include conversational filler."
        )

        repo_json = self._serialize_blueprint(blueprint)
        user_prompt = f"Analyze the following codebase structure and generate a summary:

{repo_json}"

        return self.llm_client.generate_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt
        )

    def generate_onboarding_guide(self, blueprint: RepositoryBlueprint) -> str:
        """Generate a developer onboarding roadmap based on the repository structure.
        
        Args:
            blueprint: The structural model of the repository.
            
        Returns:
            A markdown-formatted onboarding guide.
        """
        system_prompt = (
            "You are an expert Engineering Manager writing an onboarding guide for new developers. "
            "Using the provided repository structure, identify the core modules and classes. "
            "Explain where a new developer should start reading, what the key data structures are, "
            "and map out the flow of the application. "
            "Format the output strictly as a Markdown document."
        )

        repo_json = self._serialize_blueprint(blueprint)
        user_prompt = f"Generate a developer onboarding guide for this repository:

{repo_json}"

        return self.llm_client.generate_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt
        )

    def enrich_blueprint(self, blueprint: RepositoryBlueprint) -> RepositoryBlueprint:
        """Generate a high-level description and return a new enriched Blueprint.
        
        Since domain models are immutable, this returns a new copy.
        """
        description = self.generate_repository_summary(blueprint)
        
        # Since RepositoryBlueprint is frozen, we construct a new one 
        # (or use dataclasses.replace, but direct instantiation is clear here)
        from dataclasses import replace
        return replace(blueprint, description=description)
