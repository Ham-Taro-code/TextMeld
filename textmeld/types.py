from typing import TypeAlias, Union
from pathlib import Path

FileEntry = Union[str, dict[str, list]]
FileStructure = dict[str, list[FileEntry]]
FileContent = tuple[str, str]  # (filename, content)
PathLike: TypeAlias = Union[str, Path]
