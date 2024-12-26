import pytest
from pathlib import Path
from textwrap import dedent

from textmeld.core import GitignoreParser


@pytest.fixture
def temp_gitignore(tmp_path):
    gitignore_content = dedent(
        """
        # Python
        __pycache__/
        *.py[cod]
        
        # Project specific
        .env
        /dist/
        node_modules
        
        # Empty lines and comments
        
        # Just a comment
    """
    ).strip()

    gitignore_file = tmp_path / ".gitignore"
    gitignore_file.write_text(gitignore_content)
    return gitignore_file


def test_gitignore_parser_init_without_file():
    parser = GitignoreParser()
    assert len(parser.patterns) == 0


def test_gitignore_parser_with_file(temp_gitignore):
    parser = GitignoreParser(temp_gitignore)
    assert len(parser.patterns) == 5  # Number of non-empty, non-comment lines
    expected_patterns = ["__pycache__/", "*.py[cod]", ".env", "/dist/", "node_modules"]
    assert parser.patterns == expected_patterns


@pytest.mark.parametrize(
    "file_path,expected",
    [
        ("file.pyc", True),
        ("some/path/file.pyc", True),
        ("__pycache__/file.py", True),
        ("path/__pycache__/file.py", True),
        ("dist/bundle.js", True),
        ("node_modules/package/index.js", True),
        (".env", True),
        ("config/.env", True),
        ("file.txt", False),
        ("src/main.py", False),
        ("assets/styles.css", False),
    ],
)
def test_is_ignored(temp_gitignore, file_path, expected):
    parser = GitignoreParser(temp_gitignore)
    assert parser.is_ignored(file_path) == expected
