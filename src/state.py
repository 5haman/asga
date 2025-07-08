from dataclasses import dataclass

@dataclass
class RepoState:
    """Repository state for agent workflow."""
    path: str
