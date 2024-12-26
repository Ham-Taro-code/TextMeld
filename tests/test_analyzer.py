import pytest
from pathlib import Path
from textwrap import dedent

from textmeld.core import ProjectAnalyzer


@pytest.fixture
def sample_project(tmp_path):
    # Create a sample project with README and some files
    readme_content = dedent(
        """
        # Sample Project
        
        This is a test project.
    """
    ).strip()

    (tmp_path / "README.md").write_text(readme_content)

    # Create source files
    (tmp_path / "src").mkdir()
    (tmp_path / "src/main.py").write_text("def main(): pass")

    # Create docs
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs/api.md").write_text("# API Documentation")

    # Create .gitignore
    gitignore_content = dedent(
        """
        __pycache__/
        *.pyc
        .env
    """
    ).strip()
    (tmp_path / ".gitignore").write_text(gitignore_content)

    return tmp_path


def test_analyzer_initialization(sample_project):
    analyzer = ProjectAnalyzer(sample_project)
    assert analyzer.root_dir == Path(sample_project).resolve()
    assert not analyzer.structure  # Should be empty before analyze() is called
    assert not analyzer.readme  # Should be empty before analyze() is called


def test_analyze_with_readme(sample_project):
    analyzer = ProjectAnalyzer(sample_project)
    analyzer.analyze()

    assert analyzer.readme.startswith("# Sample Project")
    assert len(analyzer.structure) == 1


def test_as_text_output_formatting(sample_project):
    analyzer = ProjectAnalyzer(sample_project)
    analyzer.analyze()

    # Test with just structure (no readme or files)
    structure_only = analyzer.as_text(with_readme=False, with_files=False)
    assert "Files --" in structure_only
    assert "```README.md" not in structure_only  # Check for README content marker

    # Test with readme
    with_readme = analyzer.as_text(with_readme=True, with_files=False)
    assert "```README.md" in with_readme
    assert "# Sample Project" in with_readme

    # Test with files
    full_output = analyzer.as_text(with_readme=True, with_files=True)
    assert "File contents --" in full_output
    assert "```main.py" in full_output
    assert "```api.md" in full_output


def test_analyzer_with_no_readme(tmp_path):
    analyzer = ProjectAnalyzer(tmp_path)
    analyzer.analyze()

    assert not analyzer.readme
    output = analyzer.as_text(with_readme=True)
    assert "```README.md" not in output


def test_analyzer_with_max_depth(sample_project):
    analyzer = ProjectAnalyzer(sample_project, max_depth=0)
    analyzer.analyze()

    # At depth 0, we should see directory names but no contents
    text_output = analyzer.as_text(with_files=False)
    assert "src/" in text_output
    assert "docs/" in text_output
    assert "main.py" not in text_output
    assert "api.md" not in text_output


@pytest.mark.parametrize("encoding", ["utf-8"])
def test_analyzer_handles_different_encodings(tmp_path, encoding):
    # Create a file with specific encoding
    content = "Hello, world!"  # Use ASCII-only text for all encodings
    (tmp_path / "test.txt").write_text(content, encoding=encoding)

    analyzer = ProjectAnalyzer(tmp_path)
    analyzer.analyze()

    output = analyzer.as_text(with_files=True)
    assert content in output


def test_analyzer_handles_errors(tmp_path, monkeypatch):
    def mock_read_text(*args, **kwargs):
        raise UnicodeDecodeError("utf-8", b"", 0, 1, "test error")

    # Create a test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("test")

    # Mock read_text to raise UnicodeDecodeError
    monkeypatch.setattr(Path, "read_text", mock_read_text)

    analyzer = ProjectAnalyzer(tmp_path)
    analyzer.analyze()

    # Should not raise exception
    output = analyzer.as_text(with_files=True)
    assert "test.txt" in output
