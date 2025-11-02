#!/usr/bin/env python3
"""
Clean SRT Subtitle Processor

Features:
- Reorders subtitle indices (renumbers sequentially)
- Removes duplicate/repeated sentences, keeping only one instance
- Handles multiple lines per subtitle block
- Preserves timing information
- Command-line interface for easy usage
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple, Dict

class SRTBlock:
    """Represents a single SRT subtitle block"""
    def __init__(self, index: int, timestamp: str, text: str):
        self.index = index
        self.timestamp = timestamp
        self.text = text.strip()

    def __str__(self):
        return f"{self.index}\n{self.timestamp}\n{self.text}\n"

    def get_clean_text(self) -> str:
        """Get text with normalized whitespace for comparison"""
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', self.text.strip())
        return text.lower()

def parse_srt_file(file_path: str) -> List[SRTBlock]:
    """Parse SRT file into SRTBlock objects"""
    blocks = []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        # Try with different encoding
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            content = f.read()

    # Split into blocks (separated by double newlines)
    raw_blocks = re.split(r'\n\s*\n', content.strip())

    for block in raw_blocks:
        lines = block.strip().split('\n')
        if len(lines) < 3:
            continue

        # Extract index
        try:
            index = int(lines[0].strip())
        except ValueError:
            continue

        # Extract timestamp
        timestamp = lines[1].strip()
        if '-->' not in timestamp:
            continue

        # Extract text (remaining lines)
        text = '\n'.join(lines[2:]).strip()

        if text:  # Only add blocks with text
            blocks.append(SRTBlock(index, timestamp, text))

    return blocks

def remove_duplicates(blocks: List[SRTBlock]) -> List[SRTBlock]:
    """Remove duplicate subtitle blocks based on text content"""
    seen_texts = set()
    unique_blocks = []

    for block in blocks:
        clean_text = block.get_clean_text()

        # Skip if we've seen this text before
        if clean_text in seen_texts:
            print(f"Removed duplicate: {clean_text[:50]}...")
            continue

        seen_texts.add(clean_text)
        unique_blocks.append(block)

    return unique_blocks

def renumber_blocks(blocks: List[SRTBlock]) -> List[SRTBlock]:
    """Renumber subtitle blocks sequentially"""
    for i, block in enumerate(blocks, 1):
        block.index = i
    return blocks

def write_srt_file(blocks: List[SRTBlock], output_path: str):
    """Write SRT blocks to file"""
    with open(output_path, 'w', encoding='utf-8') as f:
        for block in blocks:
            f.write(str(block))
            f.write('\n')

def clean_srt(input_file: str, output_file: str, remove_duplicates_flag: bool = True):
    """Main cleaning function"""
    print(f"Processing: {input_file}")
    print(f"Output: {output_file}")

    # Parse SRT file
    blocks = parse_srt_file(input_file)
    print(f"Found {len(blocks)} subtitle blocks")

    # Remove duplicates if requested
    if remove_duplicates_flag:
        original_count = len(blocks)
        blocks = remove_duplicates(blocks)
        removed_count = original_count - len(blocks)
        print(f"Removed {removed_count} duplicate blocks")

    # Renumber blocks
    blocks = renumber_blocks(blocks)
    print(f"Renumbered to {len(blocks)} sequential blocks")

    # Write output
    write_srt_file(blocks, output_file)
    print(f"Successfully saved to: {output_file}")

def main():
    if len(sys.argv) < 3:
        print("Usage: python clean_srt.py <input_file> <output_file> [--keep-duplicates]")
        print("\nArguments:")
        print("  input_file        Path to input SRT file")
        print("  output_file       Path to output SRT file")
        print("  --keep-duplicates Optional: Keep duplicate subtitles (default: remove them)")
        print("\nExample:")
        print("  python clean_srt.py input.srt output_clean.srt")
        print("  python clean_srt.py input.srt output_clean.srt --keep-duplicates")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    remove_duplicates_flag = '--keep-duplicates' not in sys.argv

    # Check if input file exists
    if not Path(input_file).exists():
        print(f"Error: Input file '{input_file}' not found!")
        sys.exit(1)

    # Check if output file would overwrite input
    if input_file == output_file:
        print("Error: Input and output files cannot be the same!")
        sys.exit(1)

    try:
        clean_srt(input_file, output_file, remove_duplicates_flag)
        print("\nCleaning completed successfully!")
    except Exception as e:
        print(f"Error during processing: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
