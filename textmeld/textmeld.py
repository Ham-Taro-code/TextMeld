import os
from pathlib import Path
import typing as typ
import fnmatch
import re


def _is_text_file(file_path: str) -> bool:
    """ファイルがテキストファイルかどうかを判定"""
    try:
        with open(file_path, 'rb') as f:
            raw = f.read(1024)
        return True
    except Exception:
        return False


class TextMeld:
    def __init__(
        self,
        exclude_patterns: typ.Optional[list[str]] = None
    ):
        default_ignore_patterns = [".git", "__pycache__", ".lock"]
        self.exclude_patterns = exclude_patterns or []
        self.exclude_patterns.extend(default_ignore_patterns)
        self.base_dir = ""  # ベースディレクトリを保持

    def load_gitignore(self, directory: str) -> None:
        """.gitignoreファイルから除外パターンを読み込む"""
        gitignore_path = os.path.join(directory, ".gitignore")
        if not os.path.exists(gitignore_path):
            return

        with open(gitignore_path, 'r', encoding='utf-8') as f:
            ignore_pattern = f.read().splitlines()
            ignore_pattern = [p for p in ignore_pattern if p.strip() and not p.strip().startswith("#")]
            self.exclude_patterns.extend(ignore_pattern)

    def get_relative_path(self, file_path: str) -> str:
        """ベースディレクトリからの相対パスを取得"""
        return os.path.relpath(file_path, self.base_dir)

    def should_exclude_from_content(self, file_path: str) -> bool:
        """ファイルが除外パターンに一致するかチェック"""
        rel_path = self.get_relative_path(file_path)

        for pattern in self.exclude_patterns:
            # / が最後にある場合は削除
            if pattern.endswith("/"):
                pattern = pattern[:-1]
            # パターンを正規表現に変換
            regex_pattern = fnmatch.translate(pattern)
            if re.match(regex_pattern, rel_path):
                return True
        return False

    def generate_tree(self, directory: str, prefix: str = "") -> str:
        """ディレクトリツリーを生成（全てのファイルを表示）"""
        self.base_dir = directory  # ベースディレクトリを設定
        self.load_gitignore(directory)
        return self._generate_tree(directory, prefix)

    def _generate_tree(self, directory: str, prefix: str = "") -> str:
        tree = ""
        items = sorted(os.listdir(directory))

        for i, item in enumerate(items):
            is_last = i == len(items) - 1
            current_prefix = prefix + ("└── " if is_last else "├── ")
            next_prefix = prefix + ("    " if is_last else "│   ")

            full_path = os.path.join(directory, item)

            # check if file should be excluded
            if self.should_exclude_from_content(full_path):
                continue

            # If item is directory, item is appended with '/'
            if os.path.isdir(full_path):
                item += "/"

            tree += current_prefix + item + "\n"

            if os.path.isdir(full_path):
                tree += self._generate_tree(full_path, next_prefix)

        return tree

    def merge_files(self, directory: str) -> str:
        """ファイルの内容を統合（除外パターンに一致するファイルは除く）"""
        self.base_dir = directory  # ベースディレクトリを設定
        self.load_gitignore(directory)
        return self._merge_files(directory)

    def _merge_files(self, directory: str) -> str:
        merged_content = ""

        for item in os.listdir(directory):
            full_path = os.path.join(directory, item)
            
            if os.path.isdir(full_path):
                if not self.should_exclude_from_content(full_path):
                    merged_content += self._merge_files(full_path)
                continue

            if self.should_exclude_from_content(full_path):
                continue

            try:
                if not _is_text_file(full_path):
                    continue
                    
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    merged_content += f"\n{'='*10}\n"
                    merged_content += f"File: {self.get_relative_path(full_path)}\n"
                    merged_content += f"{'='*10}\n"
                    merged_content += content + "\n"
            except Exception as e:
                continue

        return merged_content

    def process_directory(self, directory: str) -> str:
        """ディレクトリを処理し、ツリーとマージされた内容を出力"""
        self.base_dir = directory  # ベースディレクトリを設定
        
        # ツリー構造を生成
        tree = self.generate_tree(directory)

        # ファイル内容を統合
        merged_content = self.merge_files(directory)

        output_str = "Directory Structure:\n"
        output_str += "="*20 + "\n"
        output_str += tree
        output_str += "\nMerged Content:\n"
        output_str += "="*20 + "\n"
        output_str += merged_content

        return output_str