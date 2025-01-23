import pytest
import os
import tempfile
import fnmatch
import shutil
from pathlib import Path
from textmeld.textmeld import TextMeld

@pytest.fixture
def temp_directory():
    """テスト用の一時ディレクトリを作成"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def sample_directory(temp_directory):
    """サンプルファイル構造を持つテストディレクトリを作成"""
    # ディレクトリ構造を作成
    src_dir = Path(temp_directory) / "src"
    src_dir.mkdir()
    
    # ファイルを作成
    (src_dir / "main.py").write_text("print('Hello')\n")
    (src_dir / "test.py").write_text("def test_func():\n    pass\n")
    
    # サブディレクトリとファイルを作成
    sub_dir = src_dir / "utils"
    sub_dir.mkdir()
    (sub_dir / "helper.py").write_text("def helper():\n    return True\n")
    
    # .gitignoreファイルを作成
    (src_dir / ".gitignore").write_text("*.pyc\n__pycache__/\n")
    
    return str(src_dir)

def test_textmeld_initialization():
    """TextMeldの初期化テスト"""
    # デフォルトの除外パターン
    meld = TextMeld()
    assert ".git" in meld.exclude_patterns
    
    # カスタムの除外パターン
    custom_patterns = ["*.log", "tmp/"]
    meld = TextMeld(exclude_patterns=custom_patterns)
    assert all(pattern in meld.exclude_patterns for pattern in custom_patterns)
    assert ".git" in meld.exclude_patterns

def test_load_gitignore(temp_directory):
    """gitignoreファイルの読み込みテスト"""
    # .gitignoreファイルを作成
    gitignore_content = "*.pyc\n# コメント\n\n__pycache__/\n"
    gitignore_path = Path(temp_directory) / ".gitignore"
    gitignore_path.write_text(gitignore_content)
    
    meld = TextMeld()
    meld.load_gitignore(temp_directory)
    
    assert "*.pyc" in meld.exclude_patterns
    assert "__pycache__/" in meld.exclude_patterns
    assert "# コメント" not in meld.exclude_patterns

def test_should_exclude_from_content():
    """ファイル除外判定のテスト"""
    meld = TextMeld(exclude_patterns=["*.log", "tmp/"])
    
    assert meld.should_exclude_from_content("error.log")
    assert meld.should_exclude_from_content("tmp/")
    assert not meld.should_exclude_from_content("main.py")
    assert not meld.should_exclude_from_content("logs/data.txt")

def test_generate_tree(sample_directory):
    """ディレクトリツリー生成のテスト"""
    meld = TextMeld()
    tree = meld.generate_tree(sample_directory)
    
    # 必要なファイルとディレクトリが含まれているか確認
    assert "main.py" in tree
    assert "test.py" in tree
    assert "utils/" in tree
    assert "helper.py" in tree
    
    # 除外されるべきファイルが含まれていないか確認
    assert "__pycache__" not in tree
    assert ".pyc" not in tree

def test_merge_files(sample_directory):
    """ファイル統合のテスト"""
    meld = TextMeld([".gitignore"])
    merged = meld.merge_files(sample_directory)
    
    # 各ファイルの内容が含まれているか確認
    assert "File: main.py" in merged
    assert "print('Hello')" in merged
    assert "File: test.py" in merged
    assert "def test_func():" in merged
    assert "File: helper.py" in merged
    assert "def helper():" in merged
    
    # 除外されるべきファイルが含まれていないか確認
    assert ".pyc" not in merged
    assert "__pycache__" not in merged

def test_process_directory(sample_directory):
    """ディレクトリ処理の総合テスト"""
    meld = TextMeld()
    result = meld.process_directory(sample_directory)
    
    # ディレクトリ構造セクションの確認
    assert "Directory Structure:" in result
    assert "=" * 20 in result
    
    # マージされた内容セクションの確認
    assert "Merged Content:" in result
    assert "File: main.py" in result
    assert "File: test.py" in result
    assert "File: helper.py" in result

@pytest.mark.parametrize("exclude_patterns,expected_files", [
    (["*.py"], []),  # 全てのPythonファイルを除外
    (["test*"], ["main.py", "helper.py"]),  # testで始まるファイルを除外
    (["utils/"], ["main.py", "test.py"]),  # utilsディレクトリを除外
])
def test_exclusion_patterns(sample_directory, exclude_patterns, expected_files):
    """様々な除外パターンのテスト"""
    meld = TextMeld(exclude_patterns=exclude_patterns)
    result = meld.process_directory(sample_directory)
    
    # 期待されるファイルが含まれ、除外されるべきファイルが含まれていないことを確認
    for file in expected_files:
        assert f"File: {file}" in result
    
    # 除外されるべきファイルが含まれていないことを確認
    excluded_files = set(["main.py", "test.py", "helper.py"]) - set(expected_files)
    for file in excluded_files:
        if any(fnmatch.fnmatch(file, pattern) for pattern in exclude_patterns):
            assert f"File: {file}" not in result

def test_exclude_gitignores_dir_structure():
    """gitignoreで除外されるファイルがディレクトリ構造に含まれないことを確認"""
    # テスト用のディレクトリ構造を作成
    temp_dir = tempfile.mkdtemp()
    src_dir = Path(temp_dir) / "src"
    src_dir.mkdir()
    (src_dir / "main.py").write_text("print('Hello')\n")
    (src_dir / "test.py").write_text("def test_func():\n    pass\n")
    (src_dir / ".gitignore").write_text("*.py\n")
    
    meld = TextMeld()
    result = meld.process_directory(str(src_dir))
    
    # .gitignoreで除外されるべきファイルがディレクトリ構造に含まれていないことを確認
    assert "main.py" not in result
    assert "test.py" not in result
    assert ".gitignore" in result
