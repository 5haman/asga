import json
from pathlib import Path
from jsonschema import Draft7Validator, RefResolver

SCHEMA_DIR = Path("schemas/mcp")
SAMPLES_DIR = SCHEMA_DIR / "samples"


def test_samples_validate():
    for sample_path in SAMPLES_DIR.glob("*.json"):
        schema_path = SCHEMA_DIR / sample_path.name
        assert schema_path.exists(), f"Schema missing for {sample_path.name}"
        schema = json.loads(schema_path.read_text())
        data = json.loads(sample_path.read_text())
        base = SCHEMA_DIR.resolve().as_uri() + "/"
        resolver = RefResolver(base_uri=base, referrer=schema)
        validator = Draft7Validator(schema, resolver=resolver)
        validator.validate(data)
