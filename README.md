# ANKIFY - Markdown to Anki Flashcard Converter

Ankify is a powerful tool for converting Markdown notes into Anki flashcards.
It helps you maintain a consistent knowledge base in Markdown format while
seamlessly syncing with Anki for effective spaced repetition learning.

## Features

- **Markdown to Anki Integration**: Convert structured Markdown files into
  Anki flashcards
- **Bidirectional Syncing**: Keep track of Anki IDs in your Markdown files for
  future updates
- **Hierarchical Organization**: Cards are organized into decks based on file
  and heading structure
- **Batch Processing**: Process individual files or entire directories at once
- **Dry Run Mode**: Preview changes without modifying your Anki collection
- **Model Context Protocol Support**: Integrate directly with AI assistants like Claude

## Prerequisites

- Python 3.6+
- Anki with [AnkiConnect](https://ankiweb.net/shared/info/2055492159) addon
  installed
- Anki must be running when you use Ankify

## Installation

```bash
# Install from source
pip install .

# Or install in development mode
pip install -e .
```

## Markdown Format

Ankify expects Markdown files structured as follows:

````markdown
---
title: Your Document Title
deck: root_deck::some_deck
---

# Main Section

## Subsection

### Card Title
^unique_card_id  # Optional, will be auto-generated if missing

#### Question

```
Your question goes here.
Markdown formatting is supported!
Lists work too:
- Item 1
- Item 2
```

#### Answer

```
Your answer here. Full markdown support!
```
````

Each file should have:
- YAML frontmatter with a title (optional) and a deck (optional). Deck will
  have higher precedence than title. If neither is provided, then you will need
  to specify the `--root-deck-name` flag.
- Level 1 headings (`#`) for main sections
- Level 2 headings (`##`) for subsections
- Level 3 headings (`###`) for individual cards
- Optional card ID line starting with `^` after the card title
- Question/Answer pairs using Level 4 headings (`####`) and code blocks

## Usage

```bash
# Process a single file
ankify path/to/your/notes.md

# Process a single file with custom root deck name
ankify path/to/your/notes.md --root-deck-name "Your Deck"

# Process an entire directory
ankify path/to/your/notes/

# Dry run (no changes to Anki), but prints out each card in the console.
ankify path/to/your/notes.md --dry-run

# Limit to first N cards
ankify path/to/your/notes.md --limit 10
```

### Model Context Protocol (MCP) Integration

To use Ankify with AI assistants that support the Model Context Protocol:

1. Create an MCP configuration file with the following format:
   ```json
   {
     "globalShortcut": "Ctrl+Space",
     "mcpServers": {
       "ankify": {
         "command": "/Users/yourusername/path/to/ankify/.venv/bin/ankify",
         "args": ["--mcp"]
       }
     }
   }
   ```

2. Replace the command path with the path to your Ankify installation (you can find this with `which ankify`)

3. Add this configuration file to your AI assistant that supports MCP (such as Claude Desktop)

## How It Works

1. Ankify parses your Markdown files, extracting questions and answers
2. It creates a hierarchical deck structure in Anki based on headings: `RootDeck::H1::H2`
3. When cards are added to Anki, their IDs are stored in the Markdown with a `^` prefix
4. On subsequent runs, Ankify updates existing cards instead of creating duplicates

## Troubleshooting

- **Connection errors**: Ensure Anki is running and AnkiConnect addon is installed
- **Missing cards**: Check your Markdown structure follows the expected format
- **Card count mismatch**: Ensure each level 3 heading has corresponding Question and Answer sections

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

[AGPL-3.0](LICENSE)
