from pathlib import Path

REQUIRED_PATHS = [
    "docs/prompts.md",
    "docs/spec.md",
    "src/adapters",
    "src/nodes",
    "src/planner.py",
    "src/critic.py",
    "src/state.py",
    "src/agent.py",
    "Dockerfile",
    ".github/workflows/ci.yml",
]

def test_required_paths_exist():
    for path in REQUIRED_PATHS:
        assert Path(path).exists(), f"Missing required path: {path}"
