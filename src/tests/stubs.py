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


class CountingStubClient:
    """Wraps StubSuccessClient's behavior while tracking how many times it was called."""

    def __init__(self) -> None:
        self.call_count = 0

    def get_completion(self, system_prompt: str, user_prompt: str) -> str:
        self.call_count += 1
        return StubSuccessClient().get_completion(system_prompt, user_prompt)