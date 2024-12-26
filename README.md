# TextMeld

A CLI tool that combines multiple text files into one, making it perfect for LLM training data preparation and prompt engineering.

## Installation

```bash
pip install textmeld
```

## Usage

```bash
# Basic usage
textmeld /path/to/your/directory

# Set maximum directory depth
textmeld /path/to/your/directory --max-depth 3
```

The tool will:
1. Respect .gitignore patterns if present
2. Include README.md content if available
3. Combine all text files into a single output
4. Skip binary and hidden files automatically

## Supported File Types

- Markdown (.md)
- Text (.txt)
- YAML (.yaml, .yml)
- JSON (.json)
- Python (.py)
- JavaScript (.js)
- TypeScript (.ts)
- JSX/TSX (.jsx, .tsx)
- HTML (.html)
- CSS (.css)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.