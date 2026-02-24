import json
import base64
import anthropic
from .prompt_templates import HAZOP_EXTRACTION_PROMPT, CAUSES_GENERATION_PROMPT, WORKSHEET_GENERATION_PROMPT


def extract_json_from_response(text):
    """Extract JSON from Claude's response, stripping markdown fences if present."""
    text = text.strip()
    if text.startswith("```"):
        # Remove opening fence (```json or ```)
        first_newline = text.index("\n")
        text = text[first_newline + 1:]
        # Remove closing fence
        if text.endswith("```"):
            text = text[:-3].strip()
    return json.loads(text)


def extract_hazop_items(pdf_base64, api_key):
    """Send PDF to Claude API and extract HAZOP-relevant items."""
    client = anthropic.Anthropic(api_key=api_key)

    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=8192,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": pdf_base64,
                        },
                    },
                    {
                        "type": "text",
                        "text": HAZOP_EXTRACTION_PROMPT,
                    },
                ],
            }
        ],
    )

    response_text = message.content[0].text
    return extract_json_from_response(response_text)


def generate_causes(instruments_causes, deviation, api_key):
    """Generate instrument-based causes for a single deviation using Claude."""
    client = anthropic.Anthropic(api_key=api_key)

    instruments_json = json.dumps(instruments_causes, indent=2)
    prompt = CAUSES_GENERATION_PROMPT.format(
        instruments_json=instruments_json,
        deviation=deviation,
    )

    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )

    response_text = message.content[0].text
    return extract_json_from_response(response_text)


def generate_worksheet(extracted_items, confirmed_causes, analysis_params, pdf_filename, api_key):
    """Generate complete HAZOP worksheet rows using a single comprehensive Claude call."""
    client = anthropic.Anthropic(api_key=api_key)

    extraction_json = json.dumps(extracted_items, indent=2)
    causes_json = json.dumps(confirmed_causes, indent=2)

    prompt = WORKSHEET_GENERATION_PROMPT.format(
        extraction_json=extraction_json,
        causes_json=causes_json,
        max_pressure_gas=analysis_params.get("max_pressure_gas", "N/A"),
        max_pressure_liquid=analysis_params.get("max_pressure_liquid", "N/A"),
        max_liquid_inventory=analysis_params.get("max_liquid_inventory", "N/A"),
        drawing_ref=pdf_filename or "Not specified",
        pdlor_dollar_per_bbl=analysis_params.get("pdlor_dollar_per_bbl", 19),
        pdlor_apc_production_lost=analysis_params.get("pdlor_apc_production_lost", 84942),
    )

    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=8192,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )

    response_text = message.content[0].text
    return extract_json_from_response(response_text)
