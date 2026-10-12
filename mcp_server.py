"""
Your MCP server. ← UNIT 4, MILESTONE 1

Right now your tools only exist inside your own program. Nothing else can reach
them. MCP is an agreed shape you wrap a tool in so that anything speaking the
same protocol can call it — your agent today, a different agent tomorrow,
someone else's app after that.

**You're moving one tool. Not three.** The point is to see the seam.
`search_listings` is the one to move: it doesn't call the model, so nothing is
slow and nothing changes between runs while you're learning the shape.

    python mcp_server.py        starts the server (it will just sit there — that's right)
    python mcp_client.py        asks the server what it offers

─────────────────────────────────────────────────────────────────────────────
TODO — register one tool.

Uncomment the block below and fill it in. Three things matter:

  1. **The name.** Exactly what your agent will ask for.

  2. **The description.** This is the part that isn't code and matters most.
     Write it before you look at the example. You are not writing it for your
     agent — you're writing it for an agent someone else builds, that will
     never see your implementation. That isn't hypothetical; it's what every
     MCP server on the registry is.

     Two things to get right: name units and types ("price" is ambiguous,
     "max_price, in whole dollars" isn't), and state the empty case. Last unit
     the empty case was on your spec sheet for your loop's benefit. Here it's
     part of a published contract.

  3. **The typed inputs.** These come straight from your Tool Inventory. If the
     types here don't match your README, one of the two is wrong — fix it.

Then point your agent at it. In `run_agent()`, swap the direct call:

    results = search_listings(description, size, max_price)

for the MCP one:

    from mcp_client import call_tool
    results = call_tool("search_listings", {
        "description": description,
        "size": size,
        "max_price": max_price,
    })

**What comes back should not change.** If it does, that difference is your
first clue about what your tool was really returning before.

🛑 Stop rule: if this isn't connecting after 40 minutes, stop. Keep your direct
call, and write down in your README exactly where it broke — the error text and
the last thing that worked. Then carry on to Milestone 2. Everything after this
works with a direct call, and **a documented failure earns the point in full.**
─────────────────────────────────────────────────────────────────────────────
"""

from mcp.server.fastmcp import FastMCP

from tools import compare_price as _compare_price_impl
from tools import search_listings as _search_listings_impl

# log_level="WARNING" keeps the server from printing an INFO line for every
# request. Without it your terminal fills with "Processing request of type
# CallToolRequest" and the output you actually care about scrolls away.
mcp = FastMCP("fitfindr", log_level="WARNING")


@mcp.tool()
def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search secondhand clothing listings by keyword. `description` is free-text
    keywords (e.g. "vintage graphic tee"); `size` is an optional single size
    token such as "M", "XL" or "9", matched case-insensitively against whole
    size tokens (so "M" matches "S/M" but not "XL" or "US 9"); `max_price` is
    an optional inclusive price ceiling in US dollars. Returns up to 10 listing
    objects, best match first, each with id, title, description, category,
    style_tags, size, condition, price, colors, brand (may be null) and
    platform. Returns an empty list (never an error) when nothing matches.
    """
    return _search_listings_impl(description, size, max_price)


@mcp.tool()
def compare_price(item: dict, category: str | None = None) -> dict:
    """
    Compare one listing's price to the average price of the other listings in
    the same category. `item` is a listing object as returned by
    search_listings (it needs `id`, `category` and `price`, in US dollars);
    `category` optionally overrides which category to compare against.
    Returns {average_price, percent_of_average, verdict, compared_to}, where
    verdict is "good deal" (80% of average or less), "fair price" (up to 115%)
    or "above average". When the category has no other listings it returns
    average_price null, percent_of_average null, verdict "no comparison data"
    and compared_to 0.
    """
    return _compare_price_impl(item, category)


if __name__ == "__main__":
    mcp.run()
