import argparse
import asyncio
import os
import re
import sys
from asyncio import Semaphore
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import frontmatter
from ankify.anki import AnkiConnect, Card
from tqdm import tqdm



def extract_front_matter(markdown_text: str) -> Tuple[Dict[str, Any], str]:
    """
    Extract YAML front matter from markdown text using the python-frontmatter package.

    Args:
        markdown_text: The markdown text containing front matter

    Returns:
        A tuple (metadata, content) where metadata is a dictionary of front matter
        and content is the text without the front matter
    """
    try:
        post = frontmatter.loads(markdown_text)
        return post.metadata, post.content
    except ImportError:
        # Fallback to regex-based extraction
        pattern = r'^---\s*\n(.*?)\n---\s*\n'
        match = re.search(pattern, markdown_text, re.DOTALL)
        if match:
            import yaml
            try:
                metadata = yaml.safe_load(match.group(1))
                content = re.sub(pattern, '', markdown_text, flags=re.DOTALL)
                return metadata or {}, content
            except yaml.YAMLError as e:
                raise Exception(f"Error parsing YAML front matter: {str(e)}")
        return {}, markdown_text
    except Exception as e:
        raise Exception(f"Error extracting front matter: {str(e)}")

def check_get_deck_name(front_matter: dict) -> Optional[str]:
    if 'deck' in front_matter:
        return front_matter['deck']
    if 'title' in front_matter:
        return front_matter['title']
    return None

def extract_cards_from_markdown(content: str, root_deck_name: str, obsidian_url: Optional[str] = None) -> List[Card]:
    """
    Parse markdown content and extract cards.

    Args:
        content: Markdown content to parse
        root_deck_name: Root name of the deck to assign cards to
        obsidian_url: Optional URL to the source in Obsidian

    Returns:
        List of Card objects extracted from the markdown
    """
    from ankify.anki import Card

    cards = []
    lines = content.split('\n')

    # States for the state machine
    OUTSIDE = 0
    INSIDE_CARD = 1
    QUESTION_HEADER_SEEN = 2
    IN_QUESTION_BLOCK = 3
    ANSWER_HEADER_SEEN = 4
    IN_ANSWER_BLOCK = 5

    state = OUTSIDE
    current_card = {
        'title': '',
        'uuid': None,
        'question': '',
        'answer': '',
        'backtick_count': 0,
        'deck_name': root_deck_name  # Initialize with root deck name
    }

    # Track the closest h1 and h2 headings
    current_h1 = None
    current_h2 = None

    i = 0
    while i < len(lines):
        line = lines[i]

        # Check for level 1 headings (# heading)
        if re.match(r'^# (?!#)', line):
            current_h1 = line[2:].strip()
            current_h2 = None  # Reset h2 when new h1 is found

        # Check for level 2 headings (## heading)
        elif re.match(r'^## (?!#)', line):
            current_h2 = line[3:].strip()

        # New card starts with level 3 header
        elif line.startswith('### '):
            # Save the previous card if it was being processed
            if state != OUTSIDE and current_card['question'] and current_card['answer']:
                if current_card['uuid']:
                    print('Card', current_card)
                    cards.append(Card(
                        id=current_card['uuid'],  # None will trigger auto-generation
                        deck_name=current_card['deck_name'],
                        obsidian_url=obsidian_url,
                        question=current_card['question'].strip(),
                        answer=current_card['answer'].strip(),
                        tags=[]
                    ))
                else:
                    print('Card', current_card)
                    cards.append(Card(
                        deck_name=current_card['deck_name'],
                        obsidian_url=obsidian_url,
                        question=current_card['question'].strip(),
                        answer=current_card['answer'].strip(),
                        tags=[]
                    ))

            # Build the deck name based on current h1 and h2 context
            deck_components = [root_deck_name]
            if current_h1 is not None:
                deck_components.append(current_h1)
            if current_h2 is not None:
                deck_components.append(current_h2)
            computed_deck_name = "::".join(deck_components)

            # Reset for new card
            current_card = {
                'title': line[4:].strip(),
                'uuid': None,
                'question': '',
                'answer': '',
                'backtick_count': 0,
                'deck_name': computed_deck_name
            }
            state = INSIDE_CARD

        # Look for UUID in the lines between card title and question header
        elif state == INSIDE_CARD and line.startswith('^'):
            current_card['uuid'] = line[1:].strip()

        # Question header
        elif state in (INSIDE_CARD, QUESTION_HEADER_SEEN) and line.startswith('#### Question'):
            state = QUESTION_HEADER_SEEN

        # Answer header
        elif state in (IN_QUESTION_BLOCK, ANSWER_HEADER_SEEN) and line.startswith('#### Answer'):
            state = ANSWER_HEADER_SEEN

        # Start of question code block
        elif state == QUESTION_HEADER_SEEN and line.strip().startswith('`'):
            backticks = re.match(r'^(`+)', line.strip())
            if backticks:
                current_card['backtick_count'] = len(backticks.group(1))
                state = IN_QUESTION_BLOCK
                # Skip the opening backticks line

        # Start of answer code block
        elif state == ANSWER_HEADER_SEEN and line.strip().startswith('`'):
            backticks = re.match(r'^(`+)', line.strip())
            if backticks:
                current_card['backtick_count'] = len(backticks.group(1))
                state = IN_ANSWER_BLOCK
                # Skip the opening backticks line

        # Content within question code block
        elif state == IN_QUESTION_BLOCK:
            close_pattern = r'^`{' + str(current_card['backtick_count']) + r'}$'
            if re.match(close_pattern, line.strip()):
                # End of question block, but stay in this state until we see Answer header
                pass
            else:
                current_card['question'] += line + '\n'

        # Content within answer code block
        elif state == IN_ANSWER_BLOCK:
            close_pattern = r'^`{' + str(current_card['backtick_count']) + r'}$'
            if re.match(close_pattern, line.strip()):
                # End of answer block detected – finalize card immediately
                if current_card['question'].strip() and current_card['answer'].strip():
                    if current_card['uuid']:
                        cards.append(Card(
                            id=current_card['uuid'],
                            deck_name=current_card['deck_name'],
                            obsidian_url=obsidian_url,
                            question=current_card['question'].strip(),
                            answer=current_card['answer'].strip(),
                            tags=[]
                        ))
                    else:
                        cards.append(Card(
                            deck_name=current_card['deck_name'],
                            obsidian_url=obsidian_url,
                            question=current_card['question'].strip(),
                            answer=current_card['answer'].strip(),
                            tags=[]
                        ))
                state = OUTSIDE
                current_card = {
                    'title': '',
                    'uuid': None,
                    'question': '',
                    'answer': '',
                    'backtick_count': 0,
                    'deck_name': current_card['deck_name']
                }
            else:
                current_card['answer'] += line + '\n'

        i += 1

    # Don't forget to add the last card if we were processing one
    if state != OUTSIDE and current_card['question'] and current_card['answer']:
        if current_card['uuid']:
            cards.append(Card(
                id=current_card['uuid'],
                deck_name=current_card['deck_name'],
                obsidian_url=obsidian_url,
                question=current_card['question'].strip(),
                answer=current_card['answer'].strip(),
                tags=[]
            ))
        else:
            cards.append(Card(
                deck_name=current_card['deck_name'],
                obsidian_url=obsidian_url,
                question=current_card['question'].strip(),
                answer=current_card['answer'].strip(),
                tags=[]
            ))

    return cards


def validate_cards_count(content: str, cards: List[Card]) -> bool:
    """
    Validate that the number of cards matches the number of level 3 headings.

    Args:
        content: Markdown content to analyze
        cards: List of extracted Card objects

    Returns:
        True if the number of cards matches the number of level 3 headings,
        False otherwise
    """
    # Count level 3 headings
    lines = content.split('\n')
    level3_count = 0

    for line in lines:
        if line.startswith('### '):
            level3_count += 1

    cards_count = len(cards)

    if level3_count != cards_count:
        raise Exception(f"Mismatch between level 3 headers ({level3_count}) and extracted cards ({cards_count})")

    return True

def process_markdown_file(file_path: str, default_deck_name: str = "Default") -> List['Card']:
    """
    Process a markdown file and extract cards.

    Args:
        file_path: Path to the markdown file
        default_deck_name: Default deck name to use if not specified in front matter

    Returns:
        List of Card objects extracted from the file
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract front matter
        metadata, content_without_front_matter = extract_front_matter(content)

        # Get deck name from front matter, or use default
        root_deck_name = check_get_deck_name(metadata) or default_deck_name

        # Construct obsidian URL if needed (can be customized further)
        obsidian_url = f"obsidian://open?path={file_path}" if file_path else None

        # Extract cards
        results = extract_cards_from_markdown(content_without_front_matter, root_deck_name, obsidian_url)
        validate_cards_count(content_without_front_matter, results)
        return results
    except Exception as e:
        raise Exception(f"Error processing file {file_path}: {str(e)}")

def insert_missing_uuids(file_path: str, cards: List[Card]) -> None:
    """
    Add missing UUIDs to the markdown file.

    Args:
        file_path: Path to the markdown file
        cards: List of Card objects extracted from the file

    This function analyzes the markdown file and inserts UUID identifiers
    for any card that doesn't already have one specified.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract front matter if present
        metadata, content_to_process = extract_front_matter(content)

        lines = content_to_process.split('\n')
        modified_lines = []

        # Find all level 3 headings
        heading3_indices = [i for i, line in enumerate(lines) if line.startswith('### ')]

        if len(heading3_indices) != len(cards):
            raise Exception(f"Mismatch between level 3 headers ({len(heading3_indices)}) and cards ({len(cards)})")

        # Process each section between headings
        for i, start_idx in enumerate(heading3_indices):
            card = cards[i]
            end_idx = heading3_indices[i+1] if i < len(heading3_indices) - 1 else len(lines)

            # Check if there's already a UUID
            has_uuid = False
            question_header_idx = None

            for j in range(start_idx + 1, end_idx):
                if lines[j].startswith('^'):
                    has_uuid = True
                    break
                if lines[j].startswith('#### Question'):
                    question_header_idx = j
                    break

            # Add all lines up to the card heading
            if i == 0:
                modified_lines.extend(lines[:start_idx + 1])
            else:
                modified_lines.append(lines[start_idx])

            # If no UUID was found and we did find the question header, insert UUID
            if not has_uuid and question_header_idx is not None:
                modified_lines.append(f"^{card.id}")
                modified_lines.extend(lines[start_idx + 1:end_idx])
            else:
                modified_lines.extend(lines[start_idx + 1:end_idx])

        # Reconstruct the file content
        if metadata:
            # Reconstruct with front matter
            updated_content = "---\n"
            for key, value in metadata.items():
                updated_content += f"{key}: {value}\n"
            updated_content += "---\n\n"
            updated_content += '\n'.join(modified_lines)
        else:
            # No front matter
            updated_content = '\n'.join(modified_lines)

        # Write the updated content back to the file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)

    except Exception as e:
        raise Exception(f"Error updating UUIDs in file {file_path}: {str(e)}")

def import_to_anki(file_path: str, default_deck_name: str = "Default") -> None:
    """
    Import cards from a markdown file into Anki with progress display.

    Args:
        file_path: Path to the markdown file
        default_deck_name: Default deck name to use if not specified in front matter
    """
    async def _import_to_anki(file_path: str, default_deck_name: str) -> None:
        try:
            # Process the markdown file
            cards = process_markdown_file(file_path, default_deck_name)

            if not cards:
                raise Exception(f"No cards found in {file_path}")

            # Update the file with missing UUIDs
            insert_missing_uuids(file_path, cards)

            # Connect to Anki
            async with AnkiConnect() as anki:
                # Ensure the model template exists
                await anki.ensure_model_template_exists()

                # Limit concurrency with a semaphore (adjust the number if needed)
                sem = Semaphore(10)

                async def create_and_update(card):
                    async with sem:
                        return await anki.create_or_update_card(card)

                # Create tasks for all cards
                tasks = [asyncio.create_task(create_and_update(card)) for card in cards]

                # Use tqdm with asyncio.as_completed to update progress bar
                with tqdm(total=len(tasks), desc="Importing cards") as pbar:
                    for coro in asyncio.as_completed(tasks):
                        try:
                            anki_id = await coro
                            pbar.update(1)
                            pbar.set_postfix({'last_id': anki_id})
                        except Exception as e:
                            raise Exception(f"Failed to add card: {str(e)}")

        except Exception as e:
            raise Exception(f"Error during import: {str(e)}")
    # Run the async function
    asyncio.run(_import_to_anki(file_path, default_deck_name))
def main():
    parser = argparse.ArgumentParser(description="Convert Markdown notes to Anki flashcards")
    parser.add_argument("path", help="Path to a Markdown file or directory")
    parser.add_argument("--root-deck-name", help="Root deck name to use (overrides frontmatter)", default="Ankify")
    parser.add_argument("--dry-run", action="store_true", help="Print cards without importing to Anki")
    parser.add_argument("--limit", type=int, help="Limit processing to first N cards")

    args = parser.parse_args()

    # Check if path exists
    if not os.path.exists(args.path):
        print(f"Error: Path '{args.path}' does not exist")
        sys.exit(1)

    # Process a single file
    if os.path.isfile(args.path):
        try:
            cards = process_markdown_file(args.path, args.root_deck_name)
            if args.limit:
                cards = cards[:args.limit]

            if args.dry_run:
                print(f"Found {len(cards)} cards in {args.path}")
                for i, card in enumerate(cards, 1):
                    print(f"\nCard {i}/{len(cards)}:")
                    print(card)
            else:
                import_to_anki(args.path, args.root_deck_name)
                print(f"Successfully imported {len(cards)} cards from {args.path}")
        except Exception as e:
            print(f"Error: {str(e)}")
            sys.exit(1)

    # Process a directory
    elif os.path.isdir(args.path):
        md_files = list(Path(args.path).glob("**/*.md"))
        print(f"Found {len(md_files)} Markdown files")

        total_cards = 0
        for file_path in md_files:
            try:
                cards = process_markdown_file(str(file_path), args.root_deck_name)
                if args.limit:
                    cards = cards[:args.limit]

                if args.dry_run:
                    print(f"\nFound {len(cards)} cards in {file_path}")
                    for i, card in enumerate(cards, 1):
                        print(f"\nCard {i}/{len(cards)}:")
                        print(card)
                else:
                    import_to_anki(str(file_path), args.root_deck_name)
                    print(f"Successfully imported {len(cards)} cards from {file_path}")

                total_cards += len(cards)
            except Exception as e:
                print(f"Error processing {file_path}: {str(e)}")

        print(f"\nTotal: {total_cards} cards processed")

if __name__ == "__main__":
    main()
