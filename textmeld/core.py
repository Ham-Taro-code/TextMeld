import os
import sys
import fnmatch
import argparse
from pathlib import Path
from typing import Optional, Iterator

from .types import FileEntry, FileStructure, FileContent, PathLike
from .constants import (
    READABLE_EXTENSIONS,
    DEFAULT_MAX_DEPTH,
    GITIGNORE_FILENAME,
    README_FILENAME,
)


class GitignoreParser:
    """Handles .gitignore file parsing and pattern matching."""

    def __init__(self, gitignore_path: Optional[PathLike] = None) -> None:
        self.patterns: list[str] = []
        if gitignore_path:
            self.load_patterns(gitignore_path)

    def load_patterns(self, gitignore_path: PathLike) -> None:
        """Load patterns from a .gitignore file."""
        path = Path(gitignore_path)
        if not path.exists():
            return

        with path.open("r") as file:
            self.patterns = [
                line.strip()
                for line in file
                if line.strip() and not line.strip().startswith("#")
            ]

    def is_ignored(self, file_path: PathLike) -> bool:
        """Check if a file path matches any gitignore pattern."""
        if not self.patterns:
            return False

        file_path_str = str(file_path)
        path_parts = Path(file_path_str).parts

        for pattern in self.patterns:
            # Normalize pattern
            pattern = pattern.strip("/")

            # Handle directory-only patterns (ending with /)
            is_dir_only = pattern.endswith("/")
            if is_dir_only:
                pattern = pattern[:-1]

            # Convert pattern to parts
            pattern_parts = Path(pattern).parts

            # Handle patterns starting with /
            if pattern.startswith("/"):
                if len(path_parts) != len(pattern_parts):
                    continue
                pattern_str = str(Path(*pattern_parts[1:]))
            else:
                pattern_str = pattern

            # Check for direct file/directory match
            if fnmatch.fnmatch(file_path_str, pattern_str):
                return True

            # Check for parent directory match
            for i in range(len(path_parts)):
                parent_path = str(Path(*path_parts[: i + 1]))
                if fnmatch.fnmatch(parent_path, pattern_str):
                    return True

            # Check path components
            if "/" in pattern:
                # For patterns with path separators, match the full path
                if fnmatch.fnmatch(file_path_str, f"**/{pattern_str}"):
                    return True
            else:
                # For simple patterns, match against the base name and directory names
                if any(fnmatch.fnmatch(part, pattern_str) for part in path_parts):
                    return True

        return False


class FileExplorer:
    """Handles file system exploration and content reading."""

    def __init__(
        self,
        root_dir: PathLike,
        gitignore_parser: Optional[GitignoreParser] = None,
        max_depth: int = DEFAULT_MAX_DEPTH,
    ) -> None:
        self.root_dir = Path(root_dir).resolve()
        self.gitignore_parser = gitignore_parser or GitignoreParser()
        self.max_depth = max_depth

    def explore(self) -> FileStructure:
        """Explore the directory structure."""
        return {
            self.root_dir.name: self._recursive_explore(self.root_dir, current_depth=0)
        }

    def _recursive_explore(
        self, current_dir: Path, current_depth: int = 0
    ) -> list[FileEntry]:
        """
        Recursively explore directory structure up to max_depth.

        Args:
            current_dir: Current directory to explore
            current_depth: Current depth of recursion (0 is root)

        Note:
            - At depth 0: Show all directories but only root files
            - At depth N: Show directories and files up to depth N
        """
        result: list[FileEntry] = []

        try:
            for entry in current_dir.iterdir():
                if entry.name.startswith("."):
                    continue

                relative_path = entry.relative_to(self.root_dir)
                if self.gitignore_parser.is_ignored(relative_path):
                    continue

                if entry.is_dir():
                    # Always include directory entries
                    next_dir = []
                    # Only explore contents if we haven't reached max_depth
                    if current_depth < self.max_depth:
                        next_dir = self._recursive_explore(entry, current_depth + 1)
                    result.append({entry.name: next_dir})
                else:
                    # Include files only if we haven't reached max_depth
                    if current_depth <= self.max_depth:
                        result.append(entry.name)
        except PermissionError:
            pass  # Skip directories we can't access

        return result

    def read_file_contents(self, structure: FileStructure) -> Iterator[FileContent]:
        """Read contents of all readable files in the structure."""
        root_items = next(iter(structure.values()))
        yield from self._read_files(self.root_dir, root_items)

    def _read_files(
        self, current_path: Path, files: list[FileEntry]
    ) -> Iterator[FileContent]:
        for file in files:
            if isinstance(file, dict):
                dir_name = next(iter(file.keys()))
                yield from self._read_files(current_path / dir_name, file[dir_name])
            else:
                file_path = current_path / file
                if file_path.suffix in READABLE_EXTENSIONS:
                    try:
                        content = file_path.read_text()
                        yield (file, content)
                    except (UnicodeDecodeError, PermissionError):
                        continue


class ProjectAnalyzer:
    """Main class for analyzing project structure and contents."""

    def __init__(self, root_dir: PathLike, max_depth: int = DEFAULT_MAX_DEPTH):
        self.root_dir = Path(root_dir).resolve()
        self.gitignore_parser = GitignoreParser(self.root_dir / GITIGNORE_FILENAME)
        self.explorer = FileExplorer(self.root_dir, self.gitignore_parser, max_depth)
        self.structure: FileStructure = {}
        self.readme = ""

    def analyze(self) -> None:
        """Analyze the project structure and read README if present."""
        self.structure = self.explorer.explore()
        self._read_readme()

    def _read_readme(self) -> None:
        """Read README.md if it exists."""
        readme_path = self.root_dir / README_FILENAME
        if readme_path.exists():
            try:
                self.readme = readme_path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, PermissionError):
                self.readme = ""

    def _sort_key(self, item: FileEntry) -> tuple[int, str]:
        """
        Custom sort key for file entries.
        Returns a tuple of (is_file, name) where is_file is 0 for directories and 1 for files.
        This ensures directories come before files, and then sorts alphabetically within each type.
        """
        if isinstance(item, dict):
            # For directories, get the directory name (first and only key)
            return (0, next(iter(item.keys())))
        else:
            # For files, use the filename
            return (1, str(item))

    def _format_structure(self, structure: FileStructure, indent: int = 0) -> str:
        """Format directory structure as text with proper indentation."""
        text = ""
        for key, value in structure.items():
            text += " " * indent + key + "/\n"

            # Sort the items using custom sort key
            for item in sorted(value, key=self._sort_key):
                if isinstance(item, dict):
                    # Handle directory
                    dir_name = next(iter(item.keys()))
                    dir_contents = item[dir_name]
                    text += " " * (indent + 2) + dir_name + "/\n"
                    # Sort directory contents
                    for content_item in sorted(dir_contents, key=str):
                        text += " " * (indent + 4) + str(content_item) + "\n"
                else:
                    # Handle file
                    text += " " * (indent + 2) + str(item) + "\n"
        return text

    def as_text(self, with_readme: bool = True, with_files: bool = False) -> str:
        """Generate a text representation of the project structure."""
        parts = []

        # Only include README content if requested and available
        if with_readme and self.readme:
            parts.append(f"```{README_FILENAME}\n{self.readme}```\n")

        # Add file structure
        parts.append("Files --\n" + self._format_structure(self.structure))

        # Add file contents if requested
        if with_files:
            parts.append("File contents --")
            for filename, content in self.explorer.read_file_contents(self.structure):
                parts.append(f"```{filename}\n{content}```")

        return "\n".join(parts)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Explore files in a directory while respecting .gitignore patterns."
    )
    parser.add_argument("directory", type=str, help="The directory to explore")
    parser.add_argument(
        "--max-depth",
        type=int,
        default=DEFAULT_MAX_DEPTH,
        help="Maximum depth to explore",
    )
    args = parser.parse_args()

    try:
        analyzer = ProjectAnalyzer(args.directory, args.max_depth)
        analyzer.analyze()
        print(analyzer.as_text(with_files=True))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
