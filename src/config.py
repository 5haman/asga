import os

OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openrouter/mistral-large-latest")
OPENROUTER_MAX_TOKENS = int(os.getenv("OPENROUTER_MAX_TOKENS", "4096"))
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_SEED = int(os.getenv("OPENROUTER_SEED", "42"))
