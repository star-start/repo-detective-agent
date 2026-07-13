from __future__ import annotations

from pathlib import Path

from repo_detective.models import AgentReport, Finding, Severity
from repo_detective.tools import (
    detect_stack,
    inspect_hygiene,
    inspect_large_files,
    iter_project_files,
    scan_text_file,
)

PENALTIES = {
    Severity.CRITICAL: 25,
    Severity.HIGH: 15,
    Severity.MEDIUM: 7,
    Severity.LOW: 2,
    Severity.INFO: 0,
}


class DetectiveAgent:
    """A deterministic Observe → Reason → Act agent for codebase investigation."""

    def __init__(self, root: str | Path = ".") -> None:
        self.root = Path(root).expanduser().resolve()

    def observe(self) -> tuple[list[Path], list[Finding], list[str]]:
        if not self.root.is_dir():
            raise ValueError(f"Not a directory: {self.root}")
        files = list(iter_project_files(self.root))
        findings: list[Finding] = []
        for path in files:
            findings.extend(scan_text_file(self.root, path))
        findings.extend(inspect_hygiene(self.root, files))
        findings.extend(inspect_large_files(self.root, files))
        return files, findings, detect_stack(self.root, files)

    def reason(self, findings: list[Finding]) -> tuple[int, list[Finding]]:
        severity_order = {severity: index for index, severity in enumerate(Severity)}
        ordered = sorted(
            findings,
            key=lambda item: (severity_order[item.severity], item.path or "", item.line or 0),
        )
        penalty = sum(PENALTIES[finding.severity] for finding in ordered)
        return max(0, 100 - penalty), ordered

    def act(self, findings: list[Finding]) -> list[str]:
        actions: list[str] = []
        categories = {finding.category for finding in findings}
        if "possible-secret" in categories:
            actions.append("Rotate exposed credentials, remove them from Git history, and use environment variables.")
        if "testing" in categories:
            actions.append("Add one smoke test for the most important user flow, then grow coverage around risks.")
        if "project-hygiene" in categories:
            actions.append("Add the missing repository hygiene files before inviting collaborators.")
        if "large-file" in categories:
            actions.append("Move large generated assets out of Git or track intentional binaries with Git LFS.")
        if "work-marker" in categories:
            actions.append("Triage TODO/FIXME markers into issues; delete stale or context-free markers.")
        if not actions:
            actions.append("No urgent action found. Keep tests and dependency updates running in CI.")
        return actions

    def run(self) -> AgentReport:
        files, raw_findings, stack = self.observe()
        score, findings = self.reason(raw_findings)
        return AgentReport(
            root=self.root,
            score=score,
            files_scanned=len(files),
            stack=stack,
            findings=findings,
            actions=self.act(findings),
        )
