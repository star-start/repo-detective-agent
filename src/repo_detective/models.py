from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from pathlib import Path


class Severity(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass(slots=True)
class Finding:
    category: str
    severity: Severity
    message: str
    path: str | None = None
    line: int | None = None
    evidence: str | None = None

    @property
    def location(self) -> str:
        if not self.path:
            return "project"
        return f"{self.path}:{self.line}" if self.line else self.path


@dataclass(slots=True)
class AgentReport:
    root: Path
    score: int
    files_scanned: int
    stack: list[str] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
    actions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "root": str(self.root),
            "score": self.score,
            "files_scanned": self.files_scanned,
            "stack": self.stack,
            "findings": [asdict(finding) for finding in self.findings],
            "actions": self.actions,
        }

