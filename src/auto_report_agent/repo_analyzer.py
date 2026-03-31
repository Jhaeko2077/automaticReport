from __future__ import annotations

import subprocess
from pathlib import Path

from .models import RepoContext

TEXT_EXTENSIONS = {
    ".py",
    ".md",
    ".txt",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".java",
    ".go",
    ".rs",
    ".sh",
    ".sql",
    ".html",
    ".css",
}


def _safe_read(path: Path, max_chars: int) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")[:max_chars]
    except Exception:
        return ""


def _build_file_tree(repo_path: Path, max_entries: int = 500) -> str:
    lines: list[str] = []
    count = 0
    for p in sorted(repo_path.rglob("*")):
        if ".git" in p.parts:
            continue
        rel = p.relative_to(repo_path)
        depth = len(rel.parts) - 1
        prefix = "  " * depth
        marker = "/" if p.is_dir() else ""
        lines.append(f"{prefix}- {rel.name}{marker}")
        count += 1
        if count >= max_entries:
            lines.append("... (tree truncated)")
            break
    return "\n".join(lines)


def _collect_code_samples(repo_path: Path, max_files: int, max_file_chars: int) -> str:
    snippets: list[str] = []
    selected = 0
    read_all = max_files <= 0

    for p in sorted(repo_path.rglob("*")):
        if not read_all and selected >= max_files:
            break
        if not p.is_file() or ".git" in p.parts:
            continue
        if p.suffix.lower() not in TEXT_EXTENSIONS:
            continue

        rel = p.relative_to(repo_path)
        content = _safe_read(p, max_file_chars)
        if not content.strip():
            continue

        snippets.append(f"--- FILE: {rel} ---\n{content}")
        selected += 1

    return "\n\n".join(snippets)


def _read_readme(repo_path: Path, max_chars: int = 10000) -> str:
    for name in ("README.md", "readme.md", "README.txt", "README"):
        p = repo_path / name
        if p.exists():
            return _safe_read(p, max_chars)
    return "README not found."


def _git_recent_commits(repo_path: Path, limit: int) -> str:
    cmd = [
        "git",
        "-C",
        str(repo_path),
        "log",
        f"-{limit}",
        "--pretty=format:%h | %ad | %an | %s",
        "--date=short",
    ]
    try:
        output = subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT)
        return output.strip() or "No commit history found."
    except Exception:
        return "No git history available."


def build_repo_context(
    repo_path: str,
    max_files: int = 25,
    max_file_chars: int = 3000,
    commit_limit: int = 20,
) -> RepoContext:
    root = Path(repo_path).resolve()
    if not root.exists():
        raise FileNotFoundError(f"Repository path not found: {root}")

    return RepoContext(
        repo_path=str(root),
        readme_content=_read_readme(root),
        file_tree=_build_file_tree(root),
        code_samples=_collect_code_samples(root, max_files=max_files, max_file_chars=max_file_chars),
        recent_commits=_git_recent_commits(root, limit=commit_limit),
    )
