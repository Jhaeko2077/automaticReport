from dataclasses import dataclass


@dataclass
class RepoContext:
    repo_path: str
    readme_content: str
    file_tree: str
    code_samples: str
    recent_commits: str

    def to_prompt_context(self) -> str:
        return (
            f"REPO: {self.repo_path}\n\n"
            f"=== README ===\n{self.readme_content}\n\n"
            f"=== FILE TREE ===\n{self.file_tree}\n\n"
            f"=== CODE SAMPLES ===\n{self.code_samples}\n\n"
            f"=== RECENT COMMITS ===\n{self.recent_commits}\n"
        )
