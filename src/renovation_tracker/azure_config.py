"""Configuration loading for the Azure OpenAI client."""

import os 

from dotenv import load_dotenv

class AzureOpenAIConfig:
    """Holds validated Azure OpenAI configuration values."""

    def __init__(self, endpoint: str, api_key: str, deployment: str, api_version: str) -> None:
        self.endpoint = endpoint
        self.api_key = api_key
        self.deployment = deployment
        self.api_version = api_version


def load_azure_config() -> AzureOpenAIConfig:
    """Load and validate Azure OpenAI settings from the environment."""
    load_dotenv()

    required = {
        "AZURE_OPENAI_ENDPOINT": os.environ.get("AZURE_OPENAI_ENDPOINT"),
        "AZURE_OPENAI_API_KEY": os.environ.get("AZURE_OPENAI_API_KEY"),
        "AZURE_OPENAI_DEPLOYMENT": os.environ.get("AZURE_OPENAI_DEPLOYMENT"),
        "AZURE_OPENAI_API_VERSION": os.environ.get("AZURE_OPENAI_API_VERSION"),
    }

    missing = [key for key, value in required.items() if not value]
    if missing:
        raise RuntimeError(f"Missing required Azure OpenAI env vars: {', '.join(missing)}")

    return AzureOpenAIConfig(
        endpoint=required["AZURE_OPENAI_ENDPOINT"],
        api_key=required["AZURE_OPENAI_API_KEY"],
        deployment=required["AZURE_OPENAI_DEPLOYMENT"],
        api_version=required["AZURE_OPENAI_API_VERSION"],
    )