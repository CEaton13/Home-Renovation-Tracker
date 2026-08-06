"""AI enrichment service for the Home Renovation Tracker API."""
import json

from renovation_tracker.azure_client import EnrichmentClient
from renovation_tracker.models.enrichment import EnrichmentPayload


SYSTEM_PROMPT = """You are a renovation-planning assistant that suggests a rough task \
breakdown for a home renovation project, given only its name, room, and budget.

Rules you must follow:
- Only suggest tasks plausible for the stated room and budget. Do not invent \
unrelated work.
- Never omit or downplay permit, safety, or building-code requirements a \
suggested task would normally need (e.g. electrical, plumbing, and structural \
work typically require a permit or licensed tradesperson in most US \
jurisdictions) — mention this in the task description when relevant.
- Do not underestimate costs to make the project look more affordable than \
realistic. If unsure, prefer a wider or more conservative estimate.
- Respond with ONLY a JSON object matching this shape, no other text:
{"suggested_tasks": [{"description": str, "trade_category": one of \
"plumbing"|"electrical"|"carpentry"|"painting"|"flooring"|"hvac"|"general", \
"rough_estimate": int}], "confidence": float between 0 and 1}
"""


def build_user_prompt(name: str, room: str, budget_cents: int) -> str:
    """Build the user-facing prompt content for a project enrichment call."""
    return (
        f"Project name: {name}\n"
        f"Room/area: {room}\n"
        f"Budget: {budget_cents} cents\n"
        "Suggest a task breakdown."
    )

def generate_enrichment(client: EnrichmentClient, name: str, room: str, budget_cents: int) -> EnrichmentPayload:
    """Call the enrichment client and validate its response."""
    user_prompt = build_user_prompt(name, room, budget_cents)
    raw_response = client.get_completion(SYSTEM_PROMPT, user_prompt)
    parsed = json.loads(raw_response)
    return EnrichmentPayload.model_validate(parsed)