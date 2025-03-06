from mcp.server.fastmcp import FastMCP

from ankify.anki import AnkiConnect, Card

ANKIFY_INSTRUCTIONS = r'''
'''

mcp = FastMCP(
    name='Ankify',
    instructions=ANKIFY_INSTRUCTIONS
)

@mcp.tool()
async def list_deck_names() -> str:
    """
    Lists the all deck names that the user has. Invoke this tool once to know
    which deck the user has and thereby decide which whether if a new deck
    should be created for some cards or that they should be inserted into some
    existing decks.
    """
    try:
        async with AnkiConnect() as anki:
            names = await anki.list_decks()
            names.sort()
            names = list(map(lambda x: f'- {x}', names))
            return '# Decks: \n' + '\n'.join(names)
    except Exception:
        return 'Fail to retrieve decks, notify user if anki has properly been started'

@mcp.tool()
async def insert_card(deck_name: str, question: str, answer: str):
    r"""
    Adds a card to the deck with `deck_name`. The `question` is the question
    asked, and the `answer` is the answer provided. Please make sure that the
    question along provides enough context to the user, as it would be shuffled
    and reviewed among other questions.

    For the `deck_name`, make sure that you've invoked the `list_deck_names`
    before, and decide whether if you want to insert the card into an existing
    deck, or to insert it into some new deck. To create subdecks, use the ::
    as a separator.

    For your return, for all math formulas / symbols / equations / numbers, use
    mathjax enclosed in `\(` and `\)` for inline math and `\[` and `\]` for
    block math. Do not use any unicode special symbols for math things, do not
    use special symbols for subscripts/ superscripts. For example, if you say
    "variable X", it's not correct. You should say "variable \(X\)". You should
    also always use mathjax for subscripts/superscripts, i.e. you should
    use \(x_1\) instead of x₁. Do not use δ, ≤, μ etc. Instead, use mathjax
    enclosed in math environments. For summation, use latex but not the sigma
    letter in unicode. For expectation, do not just use E but use \mathbb{E}
    in the math environment. Do not use align*, for that, always use aligned.
    we are using mathjax so they have to be inside the mathjax environment, be
    it block or inline.
    """
    card = Card(deck_name=deck_name, question=question, answer=answer)
    try:
        async with AnkiConnect() as anki:
            await anki.create_or_update_card(card)
            return 'Successful'
    except Exception as e:
        return f'Failed to add card due to {str(e)}'
