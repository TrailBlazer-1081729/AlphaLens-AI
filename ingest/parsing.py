import re
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


def parse_10k_items(markdown_text: str, source: str = "SEC 10-K") -> List[Dict[str, Any]]:
    """
    Splits a 10-K markdown document into major SEC items.
    Simple, deterministic, and strictly line-based.
    """

    lines = markdown_text.split('\n')

    item_sequence = [
        "1", "1A", "1B", "1C", "2", "3", "4", "5", "6",
        "7", "7A", "8", "9", "9A", "9B", "9C",
        "10", "11", "12", "13", "14", "15"
    ]

    item_regex = re.compile(r'^#{0,6}\s*Item\s*(\d+[A-C]?)\.?(?:\s+(.+))?', re.IGNORECASE)

    potential_items = []

    for i, line in enumerate(lines):
        clean_line = line.strip()

        # FIX: Handle headers formatted as markdown table rows (e.g., "| Item 1. | | Business |")
        # but still skip Table of Contents rows.
        if '|' in clean_line:
            if 'Item' in clean_line:
                # Strip the pipes and collapse spaces so it becomes "Item 1. Business"
                clean_line = clean_line.replace('|', ' ')
                clean_line = re.sub(r'\s+', ' ', clean_line).strip()
            else:
                # It's a regular data table (not an Item header), skip it
                continue

        if re.search(r'\.{2,}', clean_line):
            continue

        # This skips TOC rows that end in page numbers (e.g., "Item 1. Business 12")
        if re.search(r'\s\d{1,3}\s*$', clean_line):
            continue

        match = item_regex.match(clean_line)
        if match:
            item_id = match.group(1).upper()

            # FIX: If the title is on the same line, grab it. Otherwise, peek ahead past blank lines.
            title = match.group(2)
            if not title:
                # Look ahead a few lines to find the title, skipping empty lines
                for j in range(i + 1, min(i + 5, len(lines))):
                    peek_line = lines[j].strip()
                    if peek_line:  # Found a non-empty line
                        # Strip markdown hashes to get the raw title text
                        clean_peek = peek_line.lstrip('#').strip()
                        # Make sure this line isn't another Item header
                        if clean_peek and not item_regex.match(peek_line):
                            title = clean_peek
                        break  # Stop looking once we find a non-empty line

            # Fallback if we still couldn't find a title
            if not title:
                title = "Unknown"

            title = title.strip().rstrip('.')

            if item_id in item_sequence:
                potential_items.append({
                    "item_id": item_id,
                    "title": title,
                    "line_num": i
                })

    valid_items = []
    last_idx = -1
    last_line = -100

    for item in potential_items:
        idx = item_sequence.index(item["item_id"])
        line_gap = item["line_num"] - last_line

        if idx > last_idx and line_gap > 2:
            valid_items.append(item)
            last_idx = idx
            last_line = item["line_num"]

        elif idx == 0 and line_gap > 2:
            valid_items = [item]
            last_idx = idx
            last_line = item["line_num"]

    if not valid_items:
        logger.warning("No valid SEC items detected. Returning whole document as one part.")
        return [{
            "part_number": 1,
            "topic": "Whole Document",
            "text": markdown_text,
            "source": source,
            "type": "finance_reports",
            "metadata": {
                "part": "UNKNOWN",
                "item": "UNKNOWN"
            }
        }]

    parts = []
    part_number = 1

    for i, item in enumerate(valid_items):
        start_line = item["line_num"]
        end_line = valid_items[i + 1]["line_num"] if i + 1 < len(valid_items) else len(lines)

        text = "\n".join(lines[start_line:end_line]).strip()

        item_num = int(re.match(r'(\d+)', item["item_id"]).group(1))
        if item_num <= 4:
            part = "PART I"
        elif item_num <= 9:
            part = "PART II"
        elif item_num <= 14:
            part = "PART III"
        else:
            part = "PART IV"

        parts.append({
            "part_number": part_number,
            "topic": f"Item {item['item_id']}. {item['title']}",
            "text": text,
            "source": source,
            "type": "finance_reports",
            "metadata": {
                "part": part,
                "item": f"Item {item['item_id']}"
            }
        })
        part_number += 1

    return parts


def merge_small_parts(
        parts: list[dict],
        target_words: int = 4000,
        max_words: int = 6000,
) -> list[dict]:
    """
    Merge consecutive small SEC Item parts.

    The order of the document is preserved.

    A merged part will grow until it reaches approximately
    target_words, but it will never exceed max_words.
    """

    if not parts:
        return parts

    merged_parts = []

    current = parts[0].copy()
    current_words = len(current["text"].split())

    for part in parts[1:]:

        part_words = len(part["text"].split())

        if (
                current_words >= target_words
                or current_words + part_words > max_words
        ):
            merged_parts.append(current)

            current = part.copy()
            current_words = part_words
            continue

        current["text"] += "\n\n" + part["text"]

        current["topic"] += " | " + part["topic"]

        current["metadata"]["item"] += ", " + part["metadata"]["item"]

        current_words += part_words

    merged_parts.append(current)

    for i, part in enumerate(merged_parts, start=1):
        part["part_number"] = i

    return merged_parts


if __name__ == "__main__":

    from pathlib import Path

    test_file = Path(__file__).parent.parent / "knowledge-base/finance_reports/CSCO_2024_10k.md"

    if not test_file.exists():
        print(f"❌ File not found: {test_file.resolve()}")
        raise SystemExit(1)

    print(f"📄 Reading: {test_file.name}")

    with open(test_file, "r", encoding="utf-8") as f:
        markdown = f.read()

    print("🧠 Parsing document...\n")

    parts = parse_10k_items(markdown, source=str(test_file))

    parts = merge_small_parts(
        parts,
        target_words=8000,
        max_words=10000,
    )

    print("=" * 100)
    print(f"✅ Found {len(parts)} SEC Item(s)")
    print("=" * 100)

    for part in parts:
        word_count = len(part["text"].split())

        print(f"\nPart #{part['part_number']}")
        print(f"Topic : {part['topic']}")
        print(f"Part  : {part['metadata']['part']}")
        print(f"Item  : {part['metadata']['item']}")
        print(f"Words : {word_count}")
        print("-" * 100)

    print("\n" + "=" * 100)
    print("PREVIEW")
    print("=" * 100)

    for part in parts:
        print(f"\n[{part['topic']}]")
        print(part["text"][:300].replace("\n", " "))
        print("...")