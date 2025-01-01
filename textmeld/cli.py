import argparse
import sys
from typing import List, Optional
from textmeld.textmeld import TextMeld

def parse_args() -> argparse.Namespace:
    """コマンドライン引数をパース"""
    parser = argparse.ArgumentParser(
        description="A tool to merge multiple text files into one file"
    )
    parser.add_argument(
        "directory",
        help="Path to the directory to be processed"
    )
    parser.add_argument(
        "-o", "--output",
        help="Path to the output file (if not specified, output to stdout)",
        default=None
    )
    parser.add_argument(
        "-e", "--exclude",
        help="File patterns to exclude (can specify multiple)",
        action="append",
        default=None
    )
    return parser.parse_args()

def main() -> int:
    """メイン関数"""
    try:
        args = parse_args()
        
        # TextMeldインスタンスの作成
        meld = TextMeld(exclude_patterns=args.exclude)
        
        # ディレクトリの処理
        result = meld.process_directory(args.directory)
        
        # 結果の出力
        if args.output:
            # ファイルに出力
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(result)
            print(f"Result has been output to {args.output}.", file=sys.stderr)
        else:
            # 標準出力に出力
            print(result)
        
        return 0
    
    except KeyboardInterrupt:
        print("\nProcess was interrupted.", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())