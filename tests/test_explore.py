import pytest
from pathlib import Path

from textmeld.core import FileExplorer, GitignoreParser
from textmeld.constants import READABLE_EXTENSIONS


@pytest.fixture
def sample_project(tmp_path):
    # Create a sample project structure
    (tmp_path / "src").mkdir()
    (tmp_path / "src/main.py").write_text("print('hello')")
    (tmp_path / "src/utils").mkdir()
    (tmp_path / "src/utils/helper.py").write_text("def help(): pass")

    (tmp_path / "docs").mkdir()
    (tmp_path / "docs/index.md").write_text("# Documentation")

    # Create some files that should be ignored
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "__pycache__/main.cpython-39.pyc").write_text("")
    (tmp_path / ".env").write_text("SECRET=123")

    # Create a binary file
    (tmp_path / "binary.bin").write_bytes(b"\x00\x01\x02\x03")

    return tmp_path


@pytest.fixture
def explorer(sample_project):
    gitignore_content = """
    __pycache__/
    *.pyc
    .env
    """
    gitignore_path = sample_project / ".gitignore"
    gitignore_path.write_text(gitignore_content)

    gitignore_parser = GitignoreParser(gitignore_path)
    return FileExplorer(sample_project, gitignore_parser)


def test_explore_respects_gitignore(explorer, sample_project):
    structure = explorer.explore()

    # Get the root directory contents
    root_contents = next(iter(structure.values()))

    # Convert to a flat list of paths for easier testing
    def flatten_structure(items, prefix=""):
        result = []
        for item in items:
            if isinstance(item, dict):
                for key, value in item.items():
                    result.extend(flatten_structure(value, f"{prefix}{key}/"))
            else:
                result.append(f"{prefix}{item}")
        return result

    paths = set(flatten_structure(root_contents))

    # Check that expected files are included
    assert "src/main.py" in paths
    assert "docs/index.md" in paths
    assert "src/utils/helper.py" in paths

    # Check that ignored files are not included
    assert not any("__pycache__" in path for path in paths)
    assert not any(path.endswith(".pyc") for path in paths)
    assert ".env" not in paths


def test_max_depth_limit(sample_project):
    # Test with max_depth=0 to only get root level
    explorer = FileExplorer(sample_project, max_depth=0)
    structure = explorer.explore()

    root_contents = next(iter(structure.values()))

    # Convert items to a simple set for easier testing
    items = set()
    for item in root_contents:
        if isinstance(item, dict):
            items.add(list(item.keys())[0])
        else:
            items.add(item)

    # At depth 0, we should only see the root level items
    assert "src" in items
    assert "docs" in items
    assert "binary.bin" in items

    # We shouldn't see any nested files
    flattened = [item for item in root_contents if not isinstance(item, dict)]
    nested_files = [
        item
        for item in root_contents
        if isinstance(item, dict)
        for file in item.values()
        if file  # Only include non-empty lists
    ]
    assert len(nested_files) == 0, "Should not contain files from nested directories"


def test_read_file_contents(explorer, sample_project):
    structure = explorer.explore()
    contents = list(explorer.read_file_contents(structure))

    # Convert to dict for easier testing
    content_dict = {filename: content for filename, content in contents}

    assert "main.py" in content_dict
    assert content_dict["main.py"] == "print('hello')"

    assert "index.md" in content_dict
    assert content_dict["index.md"] == "# Documentation"

    # Binary files should be skipped
    assert "binary.bin" not in content_dict


def test_handles_permission_error(tmp_path, monkeypatch):
    def mock_iterdir(*args):
        raise PermissionError()

    # Mock iterdir to raise PermissionError
    monkeypatch.setattr(Path, "iterdir", mock_iterdir)

    explorer = FileExplorer(tmp_path)
    structure = explorer.explore()

    # Should return empty structure without raising exception
    assert structure == {tmp_path.name: []}
