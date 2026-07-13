from pathlib import Path

from repo_detective.agent import DetectiveAgent
from repo_detective.models import Severity
from repo_detective.reporters import render_markdown


def write(root: Path, relative: str, content: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_detects_secret_todo_and_missing_tests(tmp_path: Path) -> None:
    write(tmp_path, "README.md", "# Demo")
    write(tmp_path, "LICENSE", "MIT")
    write(tmp_path, ".gitignore", ".venv/")
    write(
        tmp_path,
        "app.py",
        'api_key = "sk-this-should-not-be-committed"\n# TODO: add retries\n',
    )

    report = DetectiveAgent(tmp_path).run()

    categories = {finding.category for finding in report.findings}
    assert {"possible-secret", "work-marker", "testing"} <= categories
    assert report.findings[0].severity == Severity.CRITICAL
    assert report.score < 100


def test_clean_project_gets_perfect_score(tmp_path: Path) -> None:
    write(tmp_path, "README.md", "# Demo")
    write(tmp_path, "LICENSE", "MIT")
    write(tmp_path, ".gitignore", ".venv/")
    write(tmp_path, "src/app.py", "def answer():\n    return 42\n")
    write(tmp_path, "tests/test_app.py", "def test_answer():\n    assert 42 == 42\n")

    report = DetectiveAgent(tmp_path).run()

    assert report.score == 100
    assert report.findings == []
    assert "Python" in report.stack


def test_markdown_report_contains_agent_sections(tmp_path: Path) -> None:
    write(tmp_path, "main.go", "package main\n")

    rendered = render_markdown(DetectiveAgent(tmp_path).run())

    assert "# Repo Detective Report" in rendered
    assert "## Findings" in rendered
    assert "## Recommended actions" in rendered
