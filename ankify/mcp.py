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

    # Formatting for both Question and Answer

    When writing questions and answers containing mathematical content, follow
    these formatting rules to ensure consistency and readability:

    ## Basic Formatting Rules

    - Use MathJax for ALL mathematical expressions:
    - Enclose inline math in `\(` and `\)`
    - Enclose block math (displayed equations) in `\[` and `\]`
    - Never use Unicode special symbols for mathematical notation

    ## Common Mistakes and Correct Alternatives

    ### Not properly enclosing inline math in math environment:

    ❌ INCORRECT: "Consider the variable X and constant c."
    ✅ CORRECT: "Consider the variable \(X\) and constant \(c\)."

    ❌ INCORRECT: "The number 5 is prime, and f(x) is a function."
    ✅ CORRECT: "The number \(5\) is prime, and \(f(x)\) is a function."

    ❌ INCORRECT: "Let A ∩ B be the intersection of sets A and B."
    ✅ CORRECT: "Let \(A \cap B\) be the intersection of sets \(A\) and \(B\)."

    ❌ INCORRECT: "The formula a² + b² = c² is the Pythagorean theorem."
    ✅ CORRECT: "The formula \(a^2 + b^2 = c^2\) is the Pythagorean theorem."

    ❌ INCORRECT: "The derivative d/dx of x² is 2x."
    ✅ CORRECT: "The derivative \(d/dx\) of \(x^2\) is \(2x\)."

    ❌ INCORRECT: "If P(A) = 0.3 and P(B) = 0.5, then P(A∪B) = ?"
    ✅ CORRECT: "If \(P(A) = 0.3\) and \(P(B) = 0.5\), then \(P(A \cup B) = ?\)"

    ### Not Using MathJax for subscripts and superscripts

    ❌ INCORRECT: "The sequence x₁, x², x₃..."
    ✅ CORRECT: "The sequence \(x_1\), \(x^2\), \(x_3\)..."

    ### Not using latex for greek letters and special characters

    ❌ INCORRECT: "If α < β and x ≤ y, then δ = μ·σ"
    ✅ CORRECT: "If \(\alpha < \beta\) and \(x \leq y\), then \(\delta = \mu \cdot \sigma\)"

    ❌ INCORRECT: "The sum Σⁿᵢ₌₁ aᵢ equals 10"
    ✅ CORRECT: "The sum \(\sum_{i=1}^{n} a_i\) equals \(10\)"

    ❌ INCORRECT: "The integral ∫₀¹ f(x)dx"
    ✅ CORRECT: "The integral \(\int_{0}^{1} f(x)dx\)"

    ### Not using the correct statistical notations

    ❌ INCORRECT: "The expected value E[X] with probability P(X > 3)"
    ✅ CORRECT: "The expected value \(\mathbb{E}[X]\) with probability \(P(X > 3)\)"

    ❌ INCORRECT: "The variance Var(X) is 5"
    ✅ CORRECT: "The variance \(\text{Var}(X)\) is \(5\)"

    ### Not correctly labeling matrices and vectors

    ❌ INCORRECT: "The vector v and matrix A"
    ✅ CORRECT: "The vector \(\vec{v}\) and matrix \(\mathbf{A}\)"

    ### Not using the correct environments for MathJax

    ❌ INCORRECT: Using align* environment directly
    ✅ CORRECT: Use aligned environment within block math:

    \[
    \begin{aligned}
    f(x) &= ax^2 + bx + c \\
    &= a(x - h)^2 + k
    \end{aligned}
    \]

    ## Additional Formatting Examples

    - Fractions: Use \(\frac{a}{b}\) instead of a/b when appropriate
    - Square roots: Use \(\sqrt{x}\) instead of √x
    - 𝓧: Use \(\mathcal{X}\) instead of 𝓧
    - ε: Use \(\epsilon\) instead of ε
    - Set notation: Use \(\{x \in \mathbb{R} \mid x > 0\}\) instead of {x ∈ ℝ | x > 0}
    - Limits: Use \(\lim_{x \to \infty} f(x)\) instead of lim(x→∞) f(x)
    """
    card = Card(deck_name=deck_name, question=question, answer=answer)
    try:
        async with AnkiConnect() as anki:
            await anki.create_or_update_card(card)
            return 'Successful'
    except Exception as e:
        return f'Failed to add card due to {str(e)}'
