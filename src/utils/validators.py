from __future__ import annotations

import json
from pathlib import Path
from jsonschema import Draft7Validator, RefResolver


def validate_envelope(data: dict, schema_name: str) -> None:
    """Validate MCP envelope ``data`` against a schema.

    Parameters
    ----------
    data:
        Envelope dictionary to validate.
    schema_name:
        Base name of the schema (without ``.json``) located in ``schemas/mcp``.
    """
    schema_path = Path("schemas/mcp") / f"{schema_name}.json"
    schema = json.loads(schema_path.read_text())
    base = schema_path.parent.resolve().as_uri() + "/"
    validator = Draft7Validator(schema, resolver=RefResolver(base_uri=base, referrer=schema))
    validator.validate(data)
