from __future__ import annotations

from pathlib import Path

from git import Repo


def apply_patch_in_branch(repo_root: str, scan_id: int, candidate_id: int, diff_text: str) -> str:
    repo = Repo(repo_root)
    branch_name = f"ai-prune/{scan_id}/{candidate_id}"

    if branch_name in [h.name for h in repo.heads]:
        repo.git.checkout(branch_name)
    else:
        repo.git.checkout("-b", branch_name)

    patch_file = Path(repo_root) / ".tmp_candidate.patch"
    patch_file.write_text(diff_text, encoding="utf-8")
    repo.git.apply(str(patch_file))
    patch_file.unlink(missing_ok=True)
    repo.git.add(all=True)
    repo.index.commit(f"refactor: apply de-llmifier candidate {scan_id}/{candidate_id}")
    return branch_name


def revert_branch(repo_root: str, branch_name: str) -> None:
    repo = Repo(repo_root)
    if branch_name in [h.name for h in repo.heads]:
        repo.git.checkout("main")
        repo.git.branch("-D", branch_name)
