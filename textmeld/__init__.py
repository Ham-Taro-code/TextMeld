"""
TextMeld - A tool to combine multiple text files into one for LLM training and prompts
"""

from .textmeld import TextMeld
from .cli import main

__version__ = "0.1.0"
__all__ = ["TextMeld", "main"]
