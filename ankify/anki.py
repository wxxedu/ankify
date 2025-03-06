from typing import Match, Optional, Dict, Any, Tuple
from uuid import uuid4
from pydantic import BaseModel, Field
import aiohttp
import asyncio
import re
import markdown2

from pydantic.types import List

# TODO: this part is not added yet.
MERMAID_SCRIPT = r'''
<script type="module" defer>
  import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@9/dist/mermaid.esm.min.mjs';
  mermaid. Initialize({
    securityLevel: 'loose',
    startOnLoad: true
  });
  let observer = new MutationObserver(mutations => {
    for(let mutation of mutations) {
      mutation.target.style.visibility = "visible";
    }
  });
  document.querySelectorAll("pre.mermaid-pre div.mermaid").forEach(item => {
    observer.observe(item, {
      attributes: true,
      attributeFilter: ['data-processed'] });
  });
</script>
'''

ANKIFY_CARD_CSS = r'''
.card {
    font-family: 'Arial', sans-serif;
    font-size: 16px;
    text-align: left;
    color: #333;
    background-color: #f9f9f9;
    padding: 20px;
    max-width: 800px;
    margin: 0 auto;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
    border-radius: 8px;
}

.ankify-question {
    font-size: 1.2em;
    font-weight: bold;
    color: #2c3e50;
    margin-bottom: 15px;
}

.ankify-answer {
    color: #27ae60;
    margin-bottom: 15px;
}

.ankify-comments {
    font-size: 0.9em;
    color: #7f8c8d;
    font-style: italic;
    margin-bottom: 15px;
}

.ankify-obsidian-link a {
    color: #6b7cff;
    text-decoration: none;
    font-weight: bold;
}

.ankify-obsidian-link a:hover {
    text-decoration: underline;
}

hr {
    border: 0;
    height: 1px;
    background-color: #ddd;
    margin: 15px 0;
}

.codehilite .hll { background-color: #49483e }
.codehilite  { background: #272822; color: #f8f8f2 }
.codehilite .c { color: #75715e } /* Comment */
.codehilite .err { color: #960050; background-color: #1e0010 } /* Error */
.codehilite .k { color: #66d9ef } /* Keyword */
.codehilite .l { color: #ae81ff } /* Literal */
.codehilite .n { color: #f8f8f2 } /* Name */
.codehilite .o { color: #f92672 } /* Operator */
.codehilite .p { color: #f8f8f2 } /* Punctuation */
.codehilite .ch { color: #75715e } /* Comment.Hashbang */
.codehilite .cm { color: #75715e } /* Comment.Multiline */
.codehilite .cp { color: #75715e } /* Comment.Preproc */
.codehilite .cpf { color: #75715e } /* Comment.PreprocFile */
.codehilite .c1 { color: #75715e } /* Comment.Single */
.codehilite .cs { color: #75715e } /* Comment.Special */
.codehilite .gd { color: #f92672 } /* Generic.Deleted */
.codehilite .ge { font-style: italic } /* Generic.Emph */
.codehilite .gi { color: #a6e22e } /* Generic.Inserted */
.codehilite .gs { font-weight: bold } /* Generic.Strong */
.codehilite .gu { color: #75715e } /* Generic.Subheading */
.codehilite .kc { color: #66d9ef } /* Keyword.Constant */
.codehilite .kd { color: #66d9ef } /* Keyword.Declaration */
.codehilite .kn { color: #f92672 } /* Keyword.Namespace */
.codehilite .kp { color: #66d9ef } /* Keyword.Pseudo */
.codehilite .kr { color: #66d9ef } /* Keyword.Reserved */
.codehilite .kt { color: #66d9ef } /* Keyword.Type */
.codehilite .ld { color: #e6db74 } /* Literal.Date */
.codehilite .m { color: #ae81ff } /* Literal.Number */
.codehilite .s { color: #e6db74 } /* Literal.String */
.codehilite .na { color: #a6e22e } /* Name.Attribute */
.codehilite .nb { color: #f8f8f2 } /* Name.Builtin */
.codehilite .nc { color: #a6e22e } /* Name.Class */
.codehilite .no { color: #66d9ef } /* Name.Constant */
.codehilite .nd { color: #a6e22e } /* Name.Decorator */
.codehilite .ni { color: #f8f8f2 } /* Name.Entity */
.codehilite .ne { color: #a6e22e } /* Name.Exception */
.codehilite .nf { color: #a6e22e } /* Name.Function */
.codehilite .nl { color: #f8f8f2 } /* Name.Label */
.codehilite .nn { color: #f8f8f2 } /* Name.Namespace */
.codehilite .nx { color: #a6e22e } /* Name.Other */
.codehilite .py { color: #f8f8f2 } /* Name.Property */
.codehilite .nt { color: #f92672 } /* Name.Tag */
.codehilite .nv { color: #f8f8f2 } /* Name.Variable */
.codehilite .ow { color: #f92672 } /* Operator.Word */
.codehilite .w { color: #f8f8f2 } /* Text.Whitespace */
.codehilite .mb { color: #ae81ff } /* Literal.Number.Bin */
.codehilite .mf { color: #ae81ff } /* Literal.Number.Float */
.codehilite .mh { color: #ae81ff } /* Literal.Number.Hex */
.codehilite .mi { color: #ae81ff } /* Literal.Number.Integer */
.codehilite .mo { color: #ae81ff } /* Literal.Number.Oct */
.codehilite .sa { color: #e6db74 } /* Literal.String.Affix */
.codehilite .sb { color: #e6db74 } /* Literal.String.Backtick */
.codehilite .sc { color: #e6db74 } /* Literal.String.Char */
.codehilite .dl { color: #e6db74 } /* Literal.String.Delimiter */
.codehilite .sd { color: #e6db74 } /* Literal.String.Doc */
.codehilite .s2 { color: #e6db74 } /* Literal.String.Double */
.codehilite .se { color: #ae81ff } /* Literal.String.Escape */
.codehilite .sh { color: #e6db74 } /* Literal.String.Heredoc */
.codehilite .si { color: #e6db74 } /* Literal.String.Interpol */
.codehilite .sx { color: #e6db74 } /* Literal.String.Other */
.codehilite .sr { color: #e6db74 } /* Literal.String.Regex */
.codehilite .s1 { color: #e6db74 } /* Literal.String.Single */
.codehilite .ss { color: #e6db74 } /* Literal.String.Symbol */
.codehilite .bp { color: #f8f8f2 } /* Name.Builtin.Pseudo */
.codehilite .fm { color: #a6e22e } /* Name.Function.Magic */
.codehilite .vc { color: #f8f8f2 } /* Name.Variable.Class */
.codehilite .vg { color: #f8f8f2 } /* Name.Variable.Global */
.codehilite .vi { color: #f8f8f2 } /* Name.Variable.Instance */
.codehilite .vm { color: #f8f8f2 } /* Name.Variable.Magic */
.codehilite .il { color: #ae81ff } /* Literal.Number.Integer.Long */
'''
class AnkiConnect:
    def __init__(self):
        self.session = None
        self.anki_connect_url = 'http://localhost:8765'
        self.default_version = 6
        self.max_retries = 3
        self.retry_delay = 1  # seconds
        self.existing_decks = set()

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            self.session = None

    async def send_request(self, data: Dict[str, Any], retries: Optional[int] = None):
        retries = self.max_retries if retries is None else retries
        data = self._prepare_request_data(data)
        last_exception = None

        for attempt in range(retries):
            try:
                # Always use the existing session if we're in a context manager
                if self.session is None:
                    async with aiohttp.ClientSession() as session:
                        response = await self._make_request(session, data)
                        response_data = await response.json()
                        self._validate_response(response_data)
                        return response_data['result']
                else:
                    # Use the existing session that will be closed by __aexit__
                    response = await self._make_request(self.session, data)
                    response_data = await response.json()
                    self._validate_response(response_data)
                    return response_data['result']
            except Exception as e:
                last_exception = e
                if attempt < retries - 1:
                    # Wait before retrying
                    await asyncio.sleep(self.retry_delay * (attempt + 1))

        # If we've exhausted all retries, raise the last exception
        if last_exception:
            raise last_exception

    def _prepare_request_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if 'version' not in data:
            data['version'] = self.default_version
        return data

    async def _make_request(self, session: aiohttp.ClientSession, data: Dict[str, Any]):
        try:
            # Add timeout to avoid hanging indefinitely
            response = await session.post(
                self.anki_connect_url,
                json=data,
                timeout=aiohttp.ClientTimeout(total=10)  # 10 second timeout
            )
            if response.status != 200:
                raise Exception(f'Failed to connect to Anki: HTTP {response.status}')
            return response
        except aiohttp.ClientConnectorError:
            raise Exception('Failed to connect to Anki: Is Anki running with AnkiConnect plugin installed?')
        except asyncio.TimeoutError:
            raise Exception('Failed to connect to Anki: Request timed out')
        except aiohttp.ServerDisconnectedError:
            raise Exception('Failed to connect to Anki: Server disconnected - Anki may be busy or not responding')
        except aiohttp.ClientError as e:
            raise Exception(f'Failed to connect to Anki: {str(e)}')

    def _validate_response(self, response_data: Dict[str, Any]) -> None:
        if len(response_data) != 2:
            raise Exception('Response has an unexpected number of fields')
        if 'error' not in response_data:
            raise Exception('Response is missing required error field')
        if 'result' not in response_data:
            raise Exception('Response is missing required result field')
        if response_data['error'] is not None:
            raise Exception(response_data['error'])

    async def ensure_model_template_exists(self) -> bool:
        """Ensure the ObsidianCard model template exists, create it if not."""
        try:
            # First check if Anki is running and AnkiConnect is available
            try:
                await self.send_request({"action": "version"})
            except Exception as _:
                raise Exception("Make sure Anki is running and AnkiConnect plugin is installed.")

            # Check if model exists
            models = await self.send_request({
                "action": "modelNames"
            })

            # Create the model if it doesn't exist
            if models and "ObsidianCard" not in models:
                model_template = Card.template()
                await self.send_request({
                    "action": "createModel",
                    "params": model_template
                })
                return True
            return False
        except Exception as e:
            raise Exception(f"Failed to ensure model template exists: {str(e)}")

    async def get_anki_id_by_card_id(self, card_id: str):
        """
        Finds the Anki note ID that contains the given card_id in its id field.

        Args:
            card_id: The unique identifier of the card stored in the 'id' field

        Returns:
            The Anki note ID if found, None otherwise
        """
        try:
            # Search for notes with the given card_id in the id field
            note_ids = await self.send_request({
                "action": "findNotes",
                "params": {
                    "query": f"id:{card_id}"
                }
            })

            if not note_ids:
                return None

            if len(note_ids) > 1:
                raise Exception(f"Found multiple notes ({len(note_ids)}) with id field: {card_id}")

            # Return the first matching note ID
            return note_ids[0]
        except Exception as e:
            raise Exception(f"Error finding note by card_id {card_id}: {str(e)}")

    async def ensure_deck_created(self, deck_name: str):
        """
        Ensures that a deck with the given name exists in Anki, creating it if needed.

        Args:
            deck_name: The name of the deck to check/create

        Returns:
            True if the deck was created, False if it already existed
        """
        try:
            if len(self.existing_decks) <= 0:
                # Get all existing deck names
                existing_decks = await self.send_request({
                    "action": "deckNames"
                })
                if (existing_decks):
                    self.existing_decks = set(existing_decks)

            # Check if the deck already exists
            if deck_name in self.existing_decks:
                return False

            # Create the deck if it doesn't exist
            await self.send_request({
                "action": "createDeck",
                "params": {
                    "deck": deck_name
                }
            })
            self.existing_decks.add(deck_name)
            return True
        except Exception as e:
            raise Exception(f"Failed to create deck '{deck_name}': {str(e)}")

    async def create_or_update_card(self, card: 'Card'):
        """
        Creates a new card or updates an existing one in Anki.

        Args:
            card: The Card object to create or update

        Returns:
            The Anki note ID
        """
        try:
            # First check if the card already exists
            await self.ensure_deck_created(card.deck_name)
            anki_id = await self.get_anki_id_by_card_id(card.id)

            if anki_id is None:
                # Card doesn't exist, create a new one
                result = await self.send_request({
                    "action": "addNote",
                    "params": {
                        "note": card.to_anki_create()
                    }
                })
                return result
            else:
                # Card exists, update it
                await self.send_request({
                    "action": "updateNote",
                    "params": {
                        "note": card.to_anki_update(anki_id)
                    }
                })
                return anki_id
        except Exception as e:
            raise Exception(f"Failed to create or update card: {str(e)}")


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
    html = markdown2.markdown(text_without_equations, extras={'fenced-code-blocks': {}, 'tables': {}, 'codehilite': {}, 'code-friendly': {}, 'breaks': {'on_newline': True, 'on_backslash': False}})

    # Reinsert equations
    html = reinsert_equations(html, inline_equations, block_equations)

    return html



class Card(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    deck_name: str
    obsidian_url: Optional[str]
    question: str
    answer: str
    tags: List[str] = Field(default_factory=list)

    def __str__(self) -> str:
        """
        Returns a string representation of the card with formatted sections.

        Returns:
            str: A formatted string representation of the card
        """
        line_width = 80
        top_bottom_border = "=" * line_width
        section_separator = "-" * line_width

        # Format the card content
        card_str = f"{top_bottom_border}\n"
        card_str += f"ID: {self.id}\n"
        card_str += f"Deck: {self.deck_name}\n"
        if self.obsidian_url:
            card_str += f"Obsidian URL: {self.obsidian_url}\n"
        card_str += f"{section_separator}\n"
        card_str += f"QUESTION:\n{self.question}\n"
        card_str += f"{section_separator}\n"
        card_str += f"ANSWER:\n{self.answer}\n"
        if self.tags:
            card_str += f"{section_separator}\n"
            card_str += f"Tags: {', '.join(self.tags)}\n"
        card_str += f"{top_bottom_border}"
        return card_str

    @staticmethod
    def template():
        return {
            "modelName": "ObsidianCard",
            "inOrderFields": ["id", "question", "answer", "comments", "obsidian_url"],
            "css": ANKIFY_CARD_CSS,
            "isCloze": False,
            "cardTemplates": [
                {
                    "Name": "Card",
                    "Front": "<div class='ankify-question'>{{question}}</div>",
                    "Back": "{{FrontSide}}\n\n<hr id=answer>\n\n<div class='ankify-answer'>{{answer}}</div>\n\n<hr>\n\n<div class='ankify-comments'>{{comments}}</div>\n\n<hr>\n\n<div class='ankify-obsidian-link'><a href='{{obsidian_url}}'>Open in Obsidian</a></div>\n\n<div class='ankify-card-id' style='display:none;'>{{id}}</div>"
                }
            ]
        }

    def to_anki_create(self):
        """
        Converts the Card object to a dictionary format expected by Anki Connect.

        Returns:
            dict: A dictionary containing the card data formatted for Anki Connect
        """
        return {
            "deckName": self.deck_name,
            "modelName": "ObsidianCard",
            "fields": {
                "id": self.id,
                "question": markdown_to_html(self.question),
                "answer": markdown_to_html(self.answer),
                "comments": "",
                "obsidian_url": self.obsidian_url or ""
            },
            "options": {
                "allowDuplicate": False,
                "duplicateScope": "deck"
            },
            "tags": self.tags
        }

    def to_anki_update(self, anki_id: str):
        """
        Converts the Card object to a dictionary format for updating an existing note in Anki.
        Ignores the comments field during update.

        Returns:
            dict: A dictionary containing the note data formatted for Anki Connect update
        """
        return {
            "id": anki_id,
            "fields": {
                "question": markdown_to_html(self.question),
                "answer": markdown_to_html(self.answer),
            },
            "tags": self.tags
        }

if __name__ == "__main__":
    import asyncio

    async def test_ensure_model_template():
        async with AnkiConnect() as anki:
            try:
                created = await anki.ensure_model_template_exists()
                if created:
                    print("ObsidianCard template was created.")
                else:
                    print("ObsidianCard template already exists.")
            except Exception as e:
                print(f"Error: {e}")

    asyncio.run(test_ensure_model_template())
