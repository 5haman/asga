
# Autonomous Software Generation Agent


```bash
export OPENROUTER_API_KEY=sk-...
export OPENROUTER_MAX_TOKENS=4096
pip install -r requirements.txtuvicorn src.agent:app --reload
```

For the SSE gateway use:

```bash
uvicorn src.gateway:app --reload
```
