from __future__ import annotations

from pathlib import Path

from git import Repo


def git_clone_or_pull(repo_url: str, dest: str) -> Repo:
    """Clone ``repo_url`` into ``dest`` if not present, otherwise pull updates."""
    path = Path(dest)
    if path.exists():
        repo = Repo(str(path))
        repo.remote().pull()
    else:
        repo = Repo.clone_from(repo_url, str(path))
    return repo


def plan_changes(repo_path: str) -> str:
    """Return a markdown plan containing required tags."""
    _ = repo_path  # unused for now
    return "refactor: clean code\nfeature: add new endpoint"
