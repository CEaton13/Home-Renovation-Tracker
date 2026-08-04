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
    """

    def __init__(self, config: AzureOpenAIConfig) -> None:
        self._client = OpenAI(base_url=config.endpoint, api_key=config.api_key)
        self._deployment = config.deployment

    def get_completion(self, system_prompt: str, user_prompt: str) -> str:
        """Call the deployed model and return its raw text response."""
        response = self._client.responses.create(
            model=self._deployment,
            instructions=system_prompt,
            input=user_prompt,
            max_output_tokens=800,
        )
        return response.output_text