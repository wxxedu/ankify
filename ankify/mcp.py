from mcp.server.fastmcp import FastMCP

from ankify.anki import AnkiConnect

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
