from __future__ import annotations

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


EXCLUDED_DIRS = {
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "node_modules",
    ".mypy_cache",
    ".pytest_cache",
    ".idea",
    ".vscode",
    "dist",
    "build",
}


def _safe_read(path: Path, max_chars: int) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")[:max_chars]
    except Exception:
        return ""


def _iter_repo_paths(repo_path: Path):
    for p in sorted(repo_path.rglob("*")):
        rel = p.relative_to(repo_path)
        if any(part in EXCLUDED_DIRS or part.startswith(".") for part in rel.parts):
            continue
        yield p


def _build_file_tree(repo_path: Path, max_entries: int = 500) -> str:
    lines: list[str] = []
    count = 0
    for p in _iter_repo_paths(repo_path):
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

    for p in _iter_repo_paths(repo_path):
        if not read_all and selected >= max_files:
            break
        if not p.is_file():
            continue
        if p.suffix.lower() not in TEXT_EXTENSIONS:
            continue

        rel = p.relative_to(repo_path)
        content = _safe_read(p, max_file_chars)
        if not content.strip():
            continue

        snippets.append(f"### Archivo: {rel}\n{content}")
        selected += 1

    return "\n\n".join(snippets)


def _read_readme(repo_path: Path, max_chars: int = 10000) -> str:
    for name in ("README.md", "readme.md", "README.txt", "README"):
        p = repo_path / name
        if p.exists():
            return _safe_read(p, max_chars)
    return "README not found."


def build_repo_context(
    repo_path: str,
    max_files: int = 25,
    max_file_chars: int = 3000,
) -> RepoContext:
    root = Path(repo_path).resolve()
    if not root.exists():
        raise FileNotFoundError(f"Repository path not found: {root}")

    return RepoContext(
        repo_path=str(root),
        readme_content=_read_readme(root),
        file_tree=_build_file_tree(root),
        code_samples=_collect_code_samples(root, max_files=max_files, max_file_chars=max_file_chars),
    )
