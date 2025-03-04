import re
import yaml
import requests
import markdown2
import json
import logging
from pathlib import Path
import argparse
from tqdm import tqdm
from typing import Dict, List, Tuple, Optional, Any, Match

# Configure logging
logging.basicConfig(
    level=logging.WARN,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('anki_importer')

def extract_equations(text: str) -> Tuple[str, Dict[str, str], Dict[str, str]]:
    """Extract LaTeX equations from text and replace with placeholders"""
    inline_equations: Dict[str, str] = {}
    block_equations: Dict[str, str] = {}
    inline_count: int = 0
    block_count: int = 0

    # Extract inline equations \( ... \)
    def replace_inline(match: Match[str]) -> str:
        nonlocal inline_count
        inline_count += 1
        placeholder = f"%%INLINE-EQ-{inline_count}%%"
        inline_equations[placeholder] = match.group(1)
        return placeholder

    # Extract block equations \[ ... \]
    def replace_block(match: Match[str]) -> str:
        nonlocal block_count
        block_count += 1
        placeholder = f"%%BLOCK-EQ-{block_count}%%"
        block_equations[placeholder] = match.group(1)
        return placeholder

    # Replace equations with placeholders
    text = re.sub(r'\\\((.*?)\\\)', replace_inline, text, flags=re.DOTALL)
    text = re.sub(r'\\\[(.*?)\\\]', replace_block, text, flags=re.DOTALL)

    return text, inline_equations, block_equations

def escape_equation(input: str) -> str:
    """Escape special sequences in equation text"""
    # Handle double curly braces
    result = input
    while '{{' in result:
        result = result.replace('{{', '{ {')
    while '}}' in result:
        result = result.replace('}}', '} }')
    return result

def reinsert_equations(html: str, inline_equations: Dict[str, str], block_equations: Dict[str, str]) -> str:
    """Reinsert equations into HTML with proper escaping"""
    # Fix the regex pattern to properly match placeholders in HTML
    inline_pattern = r'%%INLINE-EQ-(\d+)%%'
    block_pattern = r'%%BLOCK-EQ-(\d+)%%'

    # Find all inline equation placeholders
    for match in re.finditer(inline_pattern, html):
        placeholder = match.group(0)
        if placeholder in inline_equations:
            equation = inline_equations[placeholder]
            replacement = f"\\({escape_equation(equation)}\\)"
            html = html.replace(placeholder, replacement)

    # Find all block equation placeholders
    for match in re.finditer(block_pattern, html):
        placeholder = match.group(0)
        if placeholder in block_equations:
            equation = block_equations[placeholder]
            replacement = f"\\[{escape_equation(equation)}\\]"
            html = html.replace(placeholder, replacement)

    return html

def markdown_to_html(text: str) -> str:
    """Convert markdown to HTML, preserving LaTeX equations"""
    # Extract equations
    text_without_equations, inline_equations, block_equations = extract_equations(text)

    # Convert to HTML
    html = markdown2.markdown(text_without_equations, extras=['fenced-code-blocks', 'codehilite'])

    # Reinsert equations
    html = reinsert_equations(html, inline_equations, block_equations)

    return html

def extract_front_matter(markdown_text: str) -> Dict[str, Any]:
    """Extract YAML front matter from markdown text"""
    pattern = r'^---\s*\n(.*?)\n---\s*\n'
    match = re.search(pattern, markdown_text, re.DOTALL)
    if match:
        return yaml.safe_load(match.group(1))
    return {}

def read_markdown_content(file_path: Path) -> str:
    """Read markdown file and return its content"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def write_markdown_content(file_path: Path, content: str) -> None:
    """Write content back to markdown file"""
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

def extract_title_from_front_matter(front_matter: Dict[str, Any]) -> str:
    """Extract title from front matter"""
    return front_matter.get('title', 'Untitled')

def remove_front_matter(content: str) -> str:
    """Remove front matter from content"""
    return re.sub(r'^---\s*\n.*?\n---\s*\n', '', content, flags=re.DOTALL)

def extract_heading2(line: str) -> Optional[str]:
    """Extract heading2 from line if present"""
    heading2_match = re.match(r'^##\s+(.*?)$', line)
    return heading2_match.group(1) if heading2_match else None

def extract_heading3(line: str) -> Optional[str]:
    """Extract heading3 from line if present"""
    heading3_match = re.match(r'^###\s+(.*?)$', line)
    return heading3_match.group(1) if heading3_match else None

def is_question_heading(line: str) -> bool:
    """Check if line is a question heading"""
    return bool(re.match(r'^\s*####\s+Question\s*$', line))

def is_answer_heading(line: str) -> bool:
    """Check if line is an answer heading"""
    return bool(re.match(r'^\s*####\s+Answer\s*$', line))

def get_fence_marker(line: str) -> Optional[str]:
    """Extract the fence marker from a line if present"""
    match = re.match(r'^(\s*`{3,})\s*(.*)$', line)
    return match.group(1) if match else None

def extract_anki_id(line: str) -> Optional[str]:
    """Extract the Anki note ID from a line if present"""
    match = re.match(r'^<!--\s*anki-id:\s*(\d+)\s*-->$', line)
    return match.group(1) if match else None

def is_heading(line: str) -> bool:
    """Check if line is any type of heading"""
    return line.startswith('#')

def find_anki_id_after_heading3(lines: List[str], start_index: int) -> Optional[str]:
    """Look for anki ID after heading3 but before the next heading of any level"""
    i = start_index
    while i < len(lines):
        line = lines[i]
        # Stop if we encounter a new heading
        if is_heading(line):
            break

        # Check if this line contains an anki ID
        anki_id = extract_anki_id(line)
        if anki_id:
            logger.debug(f"Found anki_id {anki_id} after heading3")
            return anki_id

        i += 1

    return None

def extract_code_block_content(lines: List[str], start_index: int) -> Tuple[int, Optional[str], Optional[str]]:
    """Extract content from a code block starting at start_index and any Anki ID"""
    content = ""
    i = start_index
    fence_marker = None
    anki_id = None

    # Check for Anki ID before the code block
    while i < len(lines) and not fence_marker:
        id_match = extract_anki_id(lines[i])
        if id_match:
            anki_id = id_match
            i += 1
        else:
            marker = get_fence_marker(lines[i])
            if marker:
                fence_marker = marker
                i += 1  # Skip the opening fence
            else:
                i += 1

    if not fence_marker or i >= len(lines):
        return i, None, anki_id  # No code block found or reached end of file

    # Collect content until matching closing fence
    while i < len(lines):
        # Check if the current line starts with the same fence marker
        if lines[i].startswith(fence_marker):
            i += 1  # Skip the closing fence
            break
        content += lines[i] + "\n"
        i += 1

    return i, content.strip() if content else None, anki_id

def create_card(question: str, answer: str, heading2: str, heading3_text: Optional[str] = None,
                anki_id: Optional[str] = None) -> Dict[str, Any]:
    """Create a card dictionary from question, answer, heading2, heading3 and optional IDs"""
    # Convert markdown to HTML
    question_html = markdown_to_html(question)
    answer_html = markdown_to_html(answer)

    card: Dict[str, Any] = {
        'question': question_html,
        'answer': answer_html,
        'heading2': heading2,
        'raw_question': question,
        'raw_answer': answer
    }

    if heading3_text:
        card['heading3_text'] = heading3_text

    if anki_id:
        card['anki_id'] = anki_id
        logger.debug(f"Card with heading3 '{heading3_text}' has existing anki_id: {anki_id}")

    return card

def parse_markdown_file(file_path: Path, from_scratch: bool = False) -> Tuple[str, List[Dict[str, Any]]]:
    """Parse markdown file and extract cards with their context"""
    content = read_markdown_content(file_path)

    # Extract front matter and title
    front_matter = extract_front_matter(content)
    title = extract_title_from_front_matter(front_matter)

    # Remove front matter for further processing
    content_without_front_matter = remove_front_matter(content)

    cards: List[Dict[str, Any]] = []
    current_heading2 = "General"
    current_heading3_text = None  # Track text of the most recent heading3
    current_heading3_idx = -1     # Track index where heading3 was found
    current_question = None
    current_question_anki_id = None

    lines = content_without_front_matter.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]

        # Check for heading2
        heading2 = extract_heading2(line)
        if heading2:
            current_heading2 = heading2
            i += 1
            continue

        # Check for heading3
        heading3 = extract_heading3(line)
        if heading3:
            current_heading3_text = heading3
            current_heading3_idx = i

            # Look ahead for anki ID after this heading3 if not starting from scratch
            heading3_anki_id = None if from_scratch else find_anki_id_after_heading3(lines, i + 1)
            if heading3_anki_id:
                logger.debug(f"Found anki_id {heading3_anki_id} for heading3 '{heading3}'")

            i += 1
            continue

        # Check for Question block
        if is_question_heading(line):
            i += 1
            # If from_scratch, ignore existing anki_ids
            if from_scratch:
                i, current_question, _ = extract_code_block_content(lines, i)
            else:
                i, current_question, current_question_anki_id = extract_code_block_content(lines, i)
            continue

        # Check for Answer block
        if is_answer_heading(line) and current_question:
            i += 1
            i, current_answer, _ = extract_code_block_content(lines, i)

            # Create a card if we have both question and answer
            if current_question and current_answer:
                # If we're starting from scratch, don't use any existing IDs
                anki_id_to_use = None
                if not from_scratch:
                    anki_id_to_use = current_question_anki_id
                    if not anki_id_to_use and current_heading3_idx >= 0:
                        anki_id_to_use = find_anki_id_after_heading3(lines, current_heading3_idx + 1)
                        if anki_id_to_use:
                            logger.debug(f"Using anki_id {anki_id_to_use} found after heading3 '{current_heading3_text}'")

                cards.append(create_card(
                    current_question, current_answer, current_heading2,
                    current_heading3_text, anki_id_to_use
                ))
                current_question = None
                current_question_anki_id = None
            continue

        i += 1

    logger.debug(f"Parsed {len(cards)} cards from file {file_path}")
    return title, cards

def create_anki_deck_request(deck_name: str) -> Dict[str, Any]:
    """Create the JSON request to create an Anki deck"""
    return {
        "action": "createDeck",
        "version": 6,
        "params": {
            "deck": deck_name
        }
    }

def create_add_note_request(deck_name: str, question: str, answer: str) -> Dict[str, Any]:
    """Create the JSON request to add a note to Anki"""
    return {
        "action": "addNote",
        "version": 6,
        "params": {
            "note": {
                "deckName": deck_name,
                "modelName": "Basic",
                "fields": {
                    "Front": question,
                    "Back": answer
                },
                "options": {
                    "allowDuplicate": False
                },
                "tags": []
            }
        }
    }

def create_update_note_request(note_id: str, question: str, answer: str) -> Dict[str, Any]:
    """Create the JSON request to update an existing note in Anki"""
    return {
        "action": "updateNoteFields",
        "version": 6,
        "params": {
            "note": {
                "id": int(note_id),
                "fields": {
                    "Front": question,
                    "Back": answer
                }
            }
        }
    }

def create_find_notes_request(query: str) -> Dict[str, Any]:
    """Create the JSON request to find notes by query"""
    return {
        "action": "findNotes",
        "version": 6,
        "params": {
            "query": query
        }
    }

def create_notes_info_request(note_ids: List[int]) -> Dict[str, Any]:
    """Create the JSON request to get notes info by note IDs"""
    return {
        "action": "notesInfo",
        "version": 6,
        "params": {
            "notes": note_ids
        }
    }

def update_anki_id_in_file(file_path: Path, heading3_text: str, old_id: str, new_id: str) -> None:
    """Update the Anki ID in markdown file"""
    content = read_markdown_content(file_path)
    lines = content.split('\n')

    heading3_idx = find_heading3_position(file_path, heading3_text)
    if heading3_idx is None:
        logger.warning(f"Could not update anki_id for heading3 '{heading3_text}' - heading not found")
        return

    # Look for the old ID and replace it
    i = heading3_idx + 1
    while i < len(lines) and not (is_question_heading(lines[i]) or extract_heading3(lines[i]) or extract_heading2(lines[i])):
        if extract_anki_id(lines[i]) == old_id:
            lines[i] = f"<!-- anki-id: {new_id} -->"
            logger.debug(f"Updated anki_id from {old_id} to {new_id} for heading3 '{heading3_text}'")
            # Write the updated content back to the file
            updated_content = '\n'.join(lines)
            write_markdown_content(file_path, updated_content)
            return
        i += 1

    # If we didn't find the old ID, insert the new one
    insert_id_in_markdown(file_path, heading3_text, new_id)

def find_matching_note_by_content(question: str, deck_name: str, dry_run: bool = False) -> Optional[str]:
    """Find a note ID by matching its front content"""
    if dry_run:
        return None

    # Create a search query to find notes with similar content
    # First try to find an exact match
    escaped_question = question.replace('"', '\\"')
    query = f'deck:"{deck_name}" "front:{escaped_question}"'
    find_request = create_find_notes_request(query)
    result = send_anki_request(find_request)

    if result.get('error'):
        logger.error(f"Error finding notes: {result.get('error')}")
        return None

    note_ids = result.get('result', [])
    if not note_ids:
        # Try more flexible search
        words = re.findall(r'\w+', question)
        if len(words) > 3:  # Use a few significant words
            search_words = ' '.join(words[:3])
            query = f'deck:"{deck_name}" front:{search_words}'
            find_request = create_find_notes_request(query)
            result = send_anki_request(find_request)
            if result.get('error'):
                logger.error(f"Error finding notes with relaxed search: {result.get('error')}")
                return None
            note_ids = result.get('result', [])

    if note_ids:
        # Get detailed info for the found notes
        notes_info_request = create_notes_info_request(note_ids)
        info_result = send_anki_request(notes_info_request)
        if info_result.get('error'):
            logger.error(f"Error getting notes info: {info_result.get('error')}")
            return None

        notes_info = info_result.get('result', [])

        # Find the note that best matches our content
        best_match = None
        for note_info in notes_info:
            if 'fields' in note_info and 'Front' in note_info['fields']:
                front_value = note_info['fields']['Front']['value']
                # Simple text comparison (could be improved)
                if front_value == question:
                    # Found exact match
                    best_match = str(note_info['noteId'])
                    break

        if best_match:
            logger.debug(f"Found matching note ID: {best_match}")
            return best_match

    logger.debug("No matching note found in Anki")
    return None

def send_anki_request(request: Dict[str, Any], dry_run: bool = False) -> Dict[str, Any]:
    """Send a request to the Anki Connect API"""
    if dry_run:
        logger.debug(f"Would send request: {json.dumps(request, indent=2)}")
        return {"result": None, "error": None}

    logger.debug(f"Sending request to Anki: {json.dumps(request)}")
    response = requests.post('http://localhost:8765', json=request)
    response.raise_for_status()
    result = response.json()
    logger.debug(f"Received response from Anki: {json.dumps(result)}")
    return result

def find_heading3_position(file_path: Path, heading3_text: str) -> Optional[int]:
    """Find the line number of a heading3 in the file"""
    content = read_markdown_content(file_path)
    lines = content.split('\n')

    for i, line in enumerate(lines):
        if extract_heading3(line) == heading3_text:
            return i
    logger.warning(f"Could not find heading3 '{heading3_text}' in file {file_path}")
    return None

def insert_id_in_markdown(file_path: Path, heading3_text: str, id_value: str) -> None:
    """Insert an ID as a comment after the heading3"""
    content = read_markdown_content(file_path)
    lines = content.split('\n')

    heading3_idx = find_heading3_position(file_path, heading3_text)
    if heading3_idx is None:
        logger.warning(f"Could not insert anki_id for heading3 '{heading3_text}' - heading not found")
        return

    # Determine where to insert the ID
    insert_at = heading3_idx + 1

    # Check if the ID is already there to avoid duplicates
    i = heading3_idx + 1
    while i < len(lines) and not (is_question_heading(lines[i]) or extract_heading3(lines[i]) or extract_heading2(lines[i])):
        if extract_anki_id(lines[i]):
            # ID already exists, no need to insert
            logger.debug(f"anki_id for heading3 '{heading3_text}' already exists in file, skipping insert")
            return
        i += 1

    id_marker = f"<!-- anki-id: {id_value} -->"
    lines.insert(insert_at, id_marker)
    logger.debug(f"Inserted anki_id {id_value} for heading3 '{heading3_text}'")

    # Write the updated content back to the file
    updated_content = '\n'.join(lines)
    write_markdown_content(file_path, updated_content)

def validate_file_path(file_path: Path) -> bool:
    """Validate that the file exists"""
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        print(f"File not found: {file_path}")
        return False
    return True

def add_or_update_note_in_anki(file_path: Path, deck_name: str, title: str, card: Dict[str, Any], dry_run: bool = False) -> Optional[str]:
    """Add a new note to Anki or update an existing one"""
    full_deck_name = f"{deck_name}::{title}::{card['heading2']}"
    heading3_text = card.get('heading3_text', 'Unknown heading')

    # Create the deck if it doesn't exist
    create_deck_request = create_anki_deck_request(full_deck_name)
    send_anki_request(create_deck_request, dry_run)

    if dry_run:
        print("\n--- CARD CONTENT (DRY RUN) ---")
        print(f"Deck: {full_deck_name}")
        print(f"Question: {card['question']}")
        print(f"Answer: {card['answer']}")
        print("-----------------------------\n")

    if 'anki_id' in card:
        logger.debug(f"Updating existing note with ID {card['anki_id']} for heading3 '{heading3_text}'")
        update_request = create_update_note_request(card['anki_id'], card['question'], card['answer'])
        logger.debug(f"Update request: {json.dumps(update_request)}")
        result = send_anki_request(update_request, dry_run)

        error_msg = result.get('error')
        if error_msg and isinstance(error_msg, str) and "Note was not found" in error_msg:
            # Note ID not found - try to find the right note by content
            logger.warning(f"Note ID {card['anki_id']} not found, trying to find matching note by content")
            matching_note_id = find_matching_note_by_content(card['raw_question'], full_deck_name, dry_run)

            if matching_note_id:
                # Found matching note - update the ID in our card and in the file
                logger.info(f"Found matching note with ID {matching_note_id}, updating reference")
                old_id = card['anki_id']
                card['anki_id'] = matching_note_id

                # Update the ID in the markdown file
                if not dry_run:
                    update_anki_id_in_file(file_path, heading3_text, old_id, matching_note_id)

                # Try update again with the new ID
                update_request = create_update_note_request(matching_note_id, card['question'], card['answer'])
                result = send_anki_request(update_request, dry_run)

                if result.get('error'):
                    logger.error(f"Error updating note with new ID for heading3 '{heading3_text}': {result.get('error')}")
                    print(f"Error updating note: {result.get('error')}")
                    return None

                logger.debug(f"Successfully updated note with new ID for heading3 '{heading3_text}'")
                return matching_note_id
            else:
                # No matching note found - create a new one
                logger.info("No matching note found, creating a new one")
                add_note_request = create_add_note_request(full_deck_name, card['question'], card['answer'])
                result = send_anki_request(add_note_request, dry_run)

                if result.get('error'):
                    logger.error(f"Error adding new note for heading3 '{heading3_text}': {result.get('error')}")
                    return None

                new_id = result.get('result') if not dry_run else "dry-run-id"
                if new_id:
                    logger.info(f"Created new note with ID {new_id}, updating reference")
                    # Update the ID in the markdown file
                    if not dry_run:
                        update_anki_id_in_file(file_path, heading3_text, card['anki_id'], str(new_id))

                    return str(new_id)
                else:
                    logger.warning(f"No new ID returned when adding note for heading3 '{heading3_text}'")
                    return None
        elif result.get('error'):
            logger.error(f"Error updating note for heading3 '{heading3_text}': {result.get('error')}")
            print(f"Error updating note: {result.get('error')}")
            return None

        logger.debug(f"Successfully updated note for heading3 '{heading3_text}'")
        return card['anki_id']
    else:
        # Add new card
        logger.debug(f"Adding new note for heading3 '{heading3_text}'")
        add_note_request = create_add_note_request(full_deck_name, card['question'], card['answer'])
        logger.debug(f"Add request: {json.dumps(add_note_request)}")
        result = send_anki_request(add_note_request, dry_run)
        if result.get('error'):
            logger.error(f"Error adding note for heading3 '{heading3_text}': {result.get('error')}")
            return None

        anki_id = result.get('result') if not dry_run else "dry-run-id"
        if anki_id:
            logger.debug(f"Successfully added note for heading3 '{heading3_text}' with ID {anki_id}")
            return str(anki_id)
        else:
            logger.warning(f"No anki_id returned when adding note for heading3 '{heading3_text}'")
            return None


def process_cards(file_path: Path, deck_name: str, title: str, cards: List[Dict[str, Any]], dry_run: bool = False, limit: Optional[int] = None) -> int:
    """Process cards and add them to Anki"""
    if dry_run:
        logger.info("Running in dry-run mode - no changes will be made to Anki")
        print("Running in dry-run mode - no changes will be made to Anki")

    if limit is not None and limit > 0:
        cards = cards[:limit]
        logger.info(f"Limiting to the first {limit} cards")
        print(f"Limiting to the first {limit} cards")

    success_count = 0
    logger.info(f"Processing {len(cards)} cards from file {file_path}")
    for card in tqdm(cards, desc="Processing cards"):
        # Get the heading3 text from the card
        heading3_text = card.get('heading3_text', 'Unknown heading')

        # If the card has an anki_id, make sure it's in the file too
        if heading3_text and not dry_run and 'anki_id' in card:
            logger.debug(f"Ensuring anki_id {card['anki_id']} is in file for heading3 '{heading3_text}'")
            insert_id_in_markdown(file_path, heading3_text, card['anki_id'])

        # Now try to add/update the Anki note
        logger.debug(f"Processing card with heading3 '{heading3_text}'")
        note_id = add_or_update_note_in_anki(file_path, deck_name, title, card, dry_run)

        if note_id:
            success_count += 1
            logger.debug(f"Card with heading3 '{heading3_text}' was successfully processed")
            # If there's no anki_id in the card and we got a note_id, insert it in the markdown
            if not dry_run and 'anki_id' not in card and heading3_text:
                logger.debug(f"Inserting new anki_id {note_id} for heading3 '{heading3_text}'")
                insert_id_in_markdown(file_path, heading3_text, note_id)
        else:
            logger.warning(f"Failed to process card with heading3 '{heading3_text}'")

    logger.info(f"Successfully {'processed' if dry_run else 'added/updated'} {success_count} out of {len(cards)} cards")
    print(f"Successfully {'processed' if dry_run else 'added/updated'} {success_count} out of {len(cards)} cards")
    return success_count

def process_file(file_path: Path, deck_name: str, dry_run: bool = False, limit: Optional[int] = None, from_scratch: bool = False) -> int:
    """Process a single markdown file"""
    logger.info(f"Processing file: {file_path}")

    if not validate_file_path(file_path):
        return 0

    title, cards = parse_markdown_file(file_path, from_scratch=from_scratch)
    return process_cards(file_path, deck_name, title, cards, dry_run, limit)


def parse_command_line_args() -> argparse.Namespace:
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Import markdown flashcards to Anki')
    parser.add_argument('path', type=str, help='Path to markdown file or directory containing markdown files')
    parser.add_argument('--dry-run', action='store_true', help='Print requests instead of sending them to Anki')
    parser.add_argument('--limit', type=int, help='Limit processing to the first N cards')
    parser.add_argument('--from-scratch', action='store_true', help='Discard all local IDs and create new cards')
    parser.add_argument('--root-deck-name', type=str, help='Root deck name in Anki (also can be set via ANKI_ROOT_DECK_NAME env var)')
    return parser.parse_args()


def get_root_deck_name(args: argparse.Namespace) -> str:
    """Get the root deck name from args or environment"""
    # Check command line argument first
    if args.root_deck_name:
        return args.root_deck_name

    # Then check environment variable
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        logger.warning("python-dotenv not installed, not loading .env file")

    import os
    deck_name = os.environ.get("ANKI_ROOT_DECK_NAME")
    if deck_name:
        return deck_name

    # If no deck name is found, show error and exit
    logger.error("No deck name specified. Please provide --root-deck-name or set ANKI_ROOT_DECK_NAME environment variable")
    print("Error: No deck name specified. Please provide --root-deck-name or set ANKI_ROOT_DECK_NAME environment variable")
    exit(1)


def main() -> None:
    args = parse_command_line_args()
    path = Path(args.path)
    logger.info(f"Starting processing of path: {path}")

    if not validate_file_path(path):
        return

    # Get the root deck name
    deck_name = get_root_deck_name(args)
    logger.info(f"Using root deck name: {deck_name}")

    if args.from_scratch:
        logger.info("Running in from-scratch mode - discarding all local IDs")
        print("Running in from-scratch mode - discarding all local IDs")

    total_processed = 0

    if path.is_dir():
        # Process all markdown files in the directory
        logger.info(f"Processing directory: {path}")
        print(f"Processing directory: {path}")

        markdown_files = list(path.glob("*.md"))
        logger.info(f"Found {len(markdown_files)} markdown files")

        for file in tqdm(markdown_files, desc="Processing files"):
            processed = process_file(file, deck_name, args.dry_run, args.limit, args.from_scratch)
            total_processed += processed

        logger.info(f"Processed a total of {total_processed} cards from {len(markdown_files)} files")
        print(f"Processed a total of {total_processed} cards from {len(markdown_files)} files")
    else:
        # Process a single file
        total_processed = process_file(path, deck_name, args.dry_run, args.limit, args.from_scratch)

    logger.info("Processing complete")

if __name__ == "__main__":
    main()
