from typing import Protocol

from openai import OpenAI

from renovation_tracker.azure_config import AzureOpenAIConfig


class EnrichmentClient(Protocol):
    """Interface the write path depends on. A test stub only needs to
    implement this one method — it does not need to be a real client
    at all.
    """

    def get_completion(self, system_prompt: str, user_prompt: str) -> str:
        """Return the raw text content of a model response."""
        ...


class AzureEnrichmentClient:
    """Real implementation of EnrichmentClient backed by the Azure AI
    Foundry unified (/openai/v1) endpoint.

    Uses the plain `OpenAI` client (not `AzureOpenAI`) pointed at the
    Foundry resource's unified endpoint via `base_url`. `AzureOpenAI`
    targets the older per-deployment REST surface, which this resource
    does not expose — Foundry's own sample code for this resource uses
    the unified endpoint with the plain client. See README.md's AI
    Enrichment section for the full rationale.
    """

    def __init__(self, config: AzureOpenAIConfig) -> None:
        self._client = OpenAI(base_url=config.endpoint, api_key=config.api_key)
        self._deployment = config.deployment

    def get_completion(self, system_prompt: str, user_prompt: str) -> str:
        """Call the deployed model and return its raw text response.

        Config rationale (see README.md's AI Enrichment section for the
        full writeup): `gpt-5-mini` is a reasoning model, so the Responses
        API rejects `temperature`/`top_p` for it — `reasoning.effort="low"`
        is the equivalent lever here, and a cheaper/faster choice than a
        higher effort level for a low-variance structured-extraction task
        that doesn't benefit from deeper reasoning. `text.format=json_object`
        enforces syntactically valid JSON at the API level rather than
        relying on prompt instructions alone. `max_output_tokens=2000` caps
        cost/latency while leaving headroom for a multi-task breakdown.
        """
        response = self._client.responses.create(
            model=self._deployment,
            instructions=system_prompt,
            input=user_prompt,
            max_output_tokens=2000,
            reasoning={"effort": "low"},
            text={"format": {"type": "json_object"}},
        )

        if response.status == "incomplete":
            raise RuntimeError(
                f"Model response incomplete: {response.incomplete_details}"
            )

        return response.output_text