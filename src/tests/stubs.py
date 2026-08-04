"""Stub clients for testing the EnrichmentClient without making actual API calls."""

import json


class StubSuccessClient:
    """Always returns a valid, schema-conforming enrichment response."""

    def get_completion(self, system_prompt: str, user_prompt: str) -> str:
        return json.dumps({
            "suggested_tasks": [
                {"description": "Install cabinets", "trade_category": "carpentry", "rough_estimate": 150_000},
            ],
            "confidence": 0.75,
            "ai_generated": True,
        })


class StubFailureClient:
    """Simulates an Azure failure — e.g. timeout, rate limit, or content-filter rejection."""

    def get_completion(self, system_prompt: str, user_prompt: str) -> str:
        raise RuntimeError("Simulated Azure OpenAI failure")


class StubMalformedClient:
    """Simulates the model returning text that isn't valid JSON at all"""

    def get_completion(self, system_prompt: str, user_prompt: str) -> str:
        return "not valid json at all"