from __future__ import annotations

import re
from collections.abc import Iterable
from pathlib import Path

from repo_detective.models import Finding, Severity

IGNORED_DIRS = {
    ".git",
    ".idea",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "vendor",
}
TEXT_SUFFIXES = {
    ".c",
    ".cpp",
    ".css",
    ".go",
    ".h",
    ".html",
    ".java",
    ".js",
    ".json",
    ".jsx",
    ".kt",
    ".md",
    ".php",
    ".py",
    ".rb",
    ".rs",
    ".sh",
    ".sql",
    ".swift",
    ".toml",
    ".ts",
    ".tsx",
    ".yaml",
    ".yml",
}
CODE_SUFFIXES = {
    ".c",
    ".cpp",
    ".go",
    ".h",
    ".java",
    ".js",
    ".jsx",
    ".kt",
    ".php",
    ".py",
    ".rb",
    ".rs",
    ".sh",
    ".swift",
    ".ts",
    ".tsx",
}
TODO_PATTERN = re.compile(r"\b(TODO|FIXME|HACK|XXX)\b[:\s-]*(.*)", re.IGNORECASE)
SECRET_PATTERN = re.compile(
    r"\b(api[_-]?key|access[_-]?token|secret|password)\b\s*[:=]\s*[\"']([^\"']{8,})[\"']",
    re.IGNORECASE,
)
PLACEHOLDERS = ("example", "placeholder", "your_", "changeme", "dummy", "test_")


def iter_project_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if not path.is_file() or any(part in IGNORED_DIRS for part in path.parts):
            continue
        yield path


def detect_stack(root: Path, files: list[Path]) -> list[str]:
    names = {path.name for path in files}
    suffixes = {path.suffix.lower() for path in files}
    stack: list[str] = []
    signals = [
        ("Python", ".py" in suffixes or "pyproject.toml" in names),
        ("JavaScript/TypeScript", bool({".js", ".jsx", ".ts", ".tsx"} & suffixes)),
        ("Rust", ".rs" in suffixes or "Cargo.toml" in names),
        ("Go", ".go" in suffixes or "go.mod" in names),
        ("Swift", ".swift" in suffixes or "Package.swift" in names),
        ("Docker", "Dockerfile" in names or "compose.yaml" in names),
    ]
    for label, detected in signals:
        if detected:
            stack.append(label)
    return stack or ["Unknown"]


def scan_text_file(root: Path, path: Path) -> list[Finding]:
    if path.suffix.lower() not in TEXT_SUFFIXES and path.name not in {"Dockerfile", "Makefile"}:
        return []
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return []

    findings: list[Finding] = []
    relative = str(path.relative_to(root))
    for line_number, line in enumerate(text.splitlines(), start=1):
        todo = TODO_PATTERN.search(line) if path.suffix.lower() in CODE_SUFFIXES else None
        if todo:
            detail = todo.group(2).strip() or "Unexplained work marker"
            findings.append(
                Finding("work-marker", Severity.LOW, f"{todo.group(1).upper()}: {detail}", relative, line_number)
            )

        secret = SECRET_PATTERN.search(line)
        if secret and not any(marker in secret.group(2).lower() for marker in PLACEHOLDERS):
            findings.append(
                Finding(
                    "possible-secret",
                    Severity.CRITICAL,
                    f"Possible hard-coded {secret.group(1)}",
                    relative,
                    line_number,
                    "Value hidden",
                )
            )
    return findings


def inspect_hygiene(root: Path, files: list[Path]) -> list[Finding]:
    names = {path.name.lower() for path in files if path.parent == root}
    findings: list[Finding] = []
    expected = [
        ("readme", {"readme.md", "readme.rst"}, "Add a README with setup and usage instructions"),
        ("license", {"license", "license.md", "license.txt"}, "Choose and add a project license"),
        ("gitignore", {".gitignore"}, "Add a .gitignore before committing generated files"),
    ]
    for category, candidates, message in expected:
        if not names & candidates:
            findings.append(Finding("project-hygiene", Severity.MEDIUM, message, evidence=category))

    source_files = [path for path in files if path.suffix in {".py", ".js", ".ts", ".go", ".rs"}]
    test_files = [path for path in files if "test" in path.name.lower() or "tests" in path.parts]
    if source_files and not test_files:
        findings.append(
            Finding("testing", Severity.HIGH, "Source code exists, but no test files were detected")
        )
    return findings


def inspect_large_files(root: Path, files: list[Path], limit_bytes: int = 1_000_000) -> list[Finding]:
    findings: list[Finding] = []
    for path in files:
        try:
            size = path.stat().st_size
        except OSError:
            continue
        if size > limit_bytes:
            findings.append(
                Finding(
                    "large-file",
                    Severity.MEDIUM,
                    f"Large file ({size / 1_000_000:.1f} MB) may not belong in Git",
                    str(path.relative_to(root)),
                )
            )
    return findings
