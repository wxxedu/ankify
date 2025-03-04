# ANKIFY - Markdown to Anki Flashcard Converter

Ankify is a powerful tool for converting Markdown notes into Anki flashcards.
It helps you maintain a consistent knowledge base in Markdown format while
seamlessly syncing with Anki for effective spaced repetition learning.

## Features

- **Markdown to Anki Integration**: Convert structured Markdown files into
  Anki flashcards
- **Bidirectional Syncing**: Keep track of Anki IDs in your Markdown files for
  future updates
- **LaTeX Support**: Properly handles both inline `\(x^2\)` and block
  `\[E=mc^2\]` equations
- **Hierarchical Organization**: Cards are organized into decks based on file
  and heading structure
- **Batch Processing**: Process individual files or entire directories at once
- **Dry Run Mode**: Preview changes without modifying your Anki collection

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

```markdown
---
title: Your Document Title
---

## Section Heading

### Subsection Heading

#### Question

```
Your question goes here.
Markdown formatting is supported!
Lists work too:
- Item 1
- Item 2

Math works: \(E = mc^2\)
```

#### Answer

```
Your answer here. Full markdown support!

\[
\int_{a}^{b} f(x) \, dx
\]
```
```

Each file should have:
- YAML frontmatter with a title (optional)
- Level 2 headings (`##`) for main sections
- Level 3 headings (`###`) for subsections (optional)
- Question/Answer pairs using Level 4 headings (`####`) and code blocks

## Usage

```bash
# Process a single file
ankify path/to/your/notes.md --root-deck-name "Your Deck"

# Process an entire directory
ankify path/to/your/notes/ --root-deck-name "Your Deck"

# Dry run (no changes to Anki)
ankify path/to/your/notes.md --dry-run --root-deck-name "Your Deck"

# Limit to first N cards
ankify path/to/your/notes.md --limit 10 --root-deck-name "Your Deck"

# Start fresh (ignore existing Anki IDs)
ankify path/to/your/notes.md --from-scratch --root-deck-name "Your Deck"
```

You can set the root deck name in an environment variable to avoid specifying it each time:
```bash
export ANKI_ROOT_DECK_NAME="Your Deck"
```

Or create a `.env` file:
```
ANKI_ROOT_DECK_NAME=Your Deck
```

## How It Works

1. Ankify parses your Markdown files, extracting questions and answers
2. It creates a hierarchical deck structure in Anki: `RootDeck::FileTitle::Section`
3. When cards are added to Anki, their IDs are stored as HTML comments in your Markdown
4. On subsequent runs, Ankify updates existing cards instead of creating duplicates

## Troubleshooting

- **Connection errors**: Ensure Anki is running and AnkiConnect addon is installed
- **Missing cards**: Check your Markdown structure follows the expected format
- **LaTeX issues**: Verify your LaTeX syntax is correct

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

[AGPL-3.0](LICENSE)
