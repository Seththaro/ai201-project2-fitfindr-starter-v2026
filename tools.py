"""
The three FitFindr tools.

Each one is a standalone function you can call and test on its own, before any
of them are wired into the loop. Build and test them one at a time — three
untested tools joined by a loop is one problem that looks like six, because you
can't tell which layer is lying to you.

    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)             → str
    create_fit_card(outfit, new_item)              → str
    compare_price(item, category)                  → dict   (stretch — 4th tool)

⚠️ Before you write any of them, fill in the **Tool Inventory** section of your
README (Milestone 2). Four lines per tool: what it does, each input with its
type, exactly what it returns, and what it returns when it has nothing to give.
That last line is what your loop branches on. "Returns a list" earns nothing —
the description has to say what is *in* the list.
"""

import re

import config
from generate import generate
from utils.data_loader import load_listings


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the listings data for items matching a description, and optionally a
    size and a price ceiling.

    This is the tool that doesn't call the model, which makes it the easiest one
    to test and the one to move onto MCP in unit 4.

    Args:
        description: keywords describing what the user wants
                     (e.g. "vintage graphic tee").
        size:        a size string to filter by, or None to skip size filtering.
                     Match case-insensitively — "M" should match "S/M".

                     ⚠️ Read the sizes in the data before you reach for a plain
                     substring test. `"s" in "us 9"` is True, and so is
                     `"l" in "xl"`. A filter that returns shoes when someone
                     asked for a small top reads like a broken search, and it
                     will quietly cost you in unit 4 when you test criterion 1.
                     What counts as a size match is part of your spec — decide
                     it and write it into your Tool Inventory.
        max_price:   maximum price, inclusive, or None to skip price filtering.

    Returns:
        A list of matching listing dicts, best match first.
        **Returns an empty list when nothing matches — an empty list, not None,
        and not an exception.** Your loop branches on this.

    Each listing dict has these fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand (str or None), platform

    Note that `brand` is None for most listings. That is deliberate and
    realistic — thrift listings often have no brand. If something you write
    assumes a brand is always there, you will find out in unit 4.

    TODO:
        1. Load every listing with load_listings().
        2. Filter by max_price and by size, when each is provided.
        3. Score what's left by keyword overlap with `description`.
        4. Drop anything scoring zero.
        5. Sort by score, highest first, and return the listing dicts —
           at most config.SEARCH_RESULT_LIMIT of them.

    Test it from a terminal before you move on:
        python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"
    """
    listings = load_listings()

    if max_price is not None:
        listings = [item for item in listings if item["price"] <= max_price]

    if size is not None:
        size_lower = size.strip().lower()
        matched = []
        for item in listings:
            item_size = item["size"].lower()
            # Size tokens are compared whole, not with substring matching —
            # "s" in "us 9" and "l" in "xl" are both true and both wrong.
            # Split on non-alphanumeric separators ("S/M" -> ["s", "m"]) and
            # require an exact token match.
            tokens = re.split(r"[\s/\-]+", item_size)
            if size_lower in tokens:
                matched.append(item)
        listings = matched

    description_words = set(re.findall(r"[a-z0-9]+", description.lower()))

    scored = []
    for item in listings:
        haystack = " ".join(
            [item["title"], item["description"], item["category"]]
            + item["style_tags"]
        ).lower()
        haystack_words = set(re.findall(r"[a-z0-9]+", haystack))
        score = len(description_words & haystack_words)
        if score > 0:
            scored.append((score, item))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [item for _, item in scored[: config.SEARCH_RESULT_LIMIT]]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest one or two outfits.

    This one calls the model, through `generate()`. You don't need to think
    about rate limits — the adapter handles pacing for you.

    Args:
        new_item: a listing dict — the item the user is considering.
        wardrobe: a wardrobe dict with an 'items' key holding a list of items.
                  **It may be empty.** Handle that.

    Returns:
        A non-empty string with outfit suggestions.
        With an empty wardrobe, return general styling advice rather than
        raising or returning "". Unit 4 has you trigger the empty wardrobe on
        purpose, so decide now what it should do.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If it is, ask the model for general styling ideas for this item.
        3. If it isn't, format the wardrobe items into the prompt and ask for
           specific combinations naming pieces the user already owns.
        4. Return the model's response.

    Test it from a terminal before you move on:
        python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"
    """
    item_desc = (
        f"{new_item['title']} ({new_item['category']}), "
        f"colors: {', '.join(new_item['colors'])}, "
        f"style: {', '.join(new_item['style_tags'])}"
    )

    wardrobe_items = wardrobe.get("items", [])

    if not wardrobe_items:
        prompt = (
            f"Someone is considering thrifting this item: {item_desc}.\n"
            f"They don't have a wardrobe on file yet. Give general styling "
            f"advice for what kinds of pieces would go well with this item — "
            f"2-3 sentences, specific about colors and styles, not generic."
        )
    else:
        wardrobe_text = "\n".join(
            f"- {w['name']} ({w['category']}, {', '.join(w['colors'])})"
            for w in wardrobe_items
        )
        prompt = (
            f"Someone is considering thrifting this item: {item_desc}.\n"
            f"Here is their current wardrobe:\n{wardrobe_text}\n\n"
            f"Suggest one or two specific outfits using pieces they already "
            f"own alongside the new item. Name the actual pieces from their "
            f"wardrobe by name. 2-3 sentences."
        )

    return generate(prompt)


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Write a short caption someone would actually post about the find.

    This calls the model too.

    Args:
        outfit:   the outfit suggestion string from suggest_outfit().
        new_item: the listing dict for the item.

    Returns:
        A two-to-four sentence caption.
        If `outfit` is empty or whitespace, return a descriptive message rather
        than raising.

    The caption should read like a real post rather than a product description,
    mention the item and its price and platform once each, and be specific about
    the vibe.

    It should also come out **differently for different inputs**. If you run
    this three times on the same item and get three word-for-word identical
    strings, it's one of two things, and both are near the top of `config.py`:

        • CACHE_ENABLED — the adapter handed back an answer it already had
        • TEMPERATURE   — at 0.0 the model gives the same words every time

    TODO:
        1. Guard against an empty or whitespace-only `outfit`.
        2. Build a prompt with the item details and the outfit.
        3. Call generate() and return the response.

    Test it from a terminal before you move on:
        python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"
    """
    if not outfit or not outfit.strip():
        return (
            f"No outfit suggestion to caption yet — {new_item.get('title', 'this item')} "
            f"needs an outfit idea before a fit card can be written."
        )

    prompt = (
        f"Write a short social media caption (2-4 sentences) for a thrifted "
        f"find someone is posting about.\n\n"
        f"Item: {new_item['title']}\n"
        f"Price: ${new_item['price']} on {new_item['platform']}\n"
        f"Outfit idea: {outfit}\n\n"
        f"Mention the item, the price, and the platform once each. Write it "
        f"like a real post — specific about the vibe, not like a product "
        f"listing."
    )

    return generate(prompt)


# ── Tool 4 (stretch): compare_price ───────────────────────────────────────────

def compare_price(item: dict, category: str | None = None) -> dict:
    """
    Compare a listing's price against other listings in the same category.

    Doesn't call the model — it's a plain stats lookup over the listings data,
    same as search_listings.

    Args:
        item:     the listing dict to evaluate (e.g. session["selected_item"]).
        category: which category to compare against, or None to use
                  item["category"].

    Returns:
        A dict: {"average_price": float, "percent_of_average": float,
        "verdict": str, "compared_to": int}, where "compared_to" is how many
        other listings in the category were used and "verdict" is one of
        "good deal", "fair price", "above average".
        **Returns {"average_price": None, "percent_of_average": None,
        "verdict": "no comparison data", "compared_to": 0}** when no other
        listings exist in that category.

    Test it from a terminal before you move on:
        python -c "from tools import compare_price; from utils.data_loader import load_listings; print(compare_price(load_listings()[0]))"
    """
    category = category or item.get("category")
    others = [
        listing
        for listing in load_listings()
        if listing["category"] == category and listing["id"] != item.get("id")
    ]

    if not others:
        return {
            "average_price": None,
            "percent_of_average": None,
            "verdict": "no comparison data",
            "compared_to": 0,
        }

    average_price = sum(listing["price"] for listing in others) / len(others)
    percent_of_average = (item["price"] / average_price) * 100

    if percent_of_average <= 80:
        verdict = "good deal"
    elif percent_of_average <= 115:
        verdict = "fair price"
    else:
        verdict = "above average"

    return {
        "average_price": round(average_price, 2),
        "percent_of_average": round(percent_of_average, 1),
        "verdict": verdict,
        "compared_to": len(others),
    }
