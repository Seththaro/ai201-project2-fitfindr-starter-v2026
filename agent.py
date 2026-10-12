"""
The FitFindr planning loop.

This is the file that makes FitFindr an agent rather than a script. It decides
which tool to run next based on what the last one returned.

If your loop calls all three tools no matter what comes back, you have a list
of function calls. A loop looks at the last result before it picks the next
step. **That branch is the graded part of this unit.**

Build and test your three tools in `tools.py` first. Then come here.

    python agent.py          runs both example paths below
"""

import re

import config
import trace
from tools import suggest_outfit, create_fit_card
from generate import ModelUnavailable
from mcp_client import call_tool, MCPError
from utils.data_loader import remember_style, load_style_memory


# ── session state ─────────────────────────────────────────────────────────────

def new_session(query: str, wardrobe: dict) -> dict:
    """
    A fresh session for one user interaction.

    The session is the single source of truth for a run. Every tool result goes
    in here, and the next tool reads it back out.

    You could pass values straight from one call to the next. It would work,
    and you would not be able to test it — you can't print a variable you have
    already overwritten. Going through the session is what makes the state
    visible, and unit 4 has you write a criterion about exactly that.

    Add fields if you need them.
    """
    return {
        "query": query,              # what the user typed
        "parsed": {},                # description / size / max_price you pulled out of it
        "search_results": [],        # everything search_listings returned
        "selected_item": None,       # the one you chose — goes into suggest_outfit
        "wardrobe": wardrobe,        # the user's wardrobe
        "outfit_suggestion": None,   # what suggest_outfit returned
        "fit_card": None,            # what create_fit_card returned
        "price_comparison": None,    # what compare_price returned (stretch — 2nd branch)
        "error": None,               # set when the run ended early
    }


# ── query parsing ─────────────────────────────────────────────────────────────

def parse_query(query: str) -> dict:
    """
    Pull a size and a price ceiling out of free text with regex, and use
    whatever's left as the search description.

    "vintage graphic tee under $30, size M" ->
        {"description": "vintage graphic tee", "size": "M", "max_price": 30.0}
    """
    remaining = query

    max_price = None
    price_match = re.search(r"(?:under|below|less than)\s*\$?\s*(\d+(?:\.\d+)?)", remaining, re.I)
    if price_match:
        max_price = float(price_match.group(1))
        remaining = remaining[: price_match.start()] + remaining[price_match.end():]

    size = None
    size_match = re.search(r"size\s*[:\-]?\s*([A-Za-z0-9/]+)", remaining, re.I)
    if size_match:
        size = size_match.group(1)
        remaining = remaining[: size_match.start()] + remaining[size_match.end():]

    description = re.sub(r"[,]+", " ", remaining)
    description = re.sub(r"\s+", " ", description).strip()

    return {"description": description, "size": size, "max_price": max_price}


def _fmt(values: dict) -> str:
    """key=value text for a trace line. trace.py shows only the keys of a dict,
    and a trace that hides the inputs can't be used to diagnose anything."""
    return ", ".join(f"{k}={v!r}" for k, v in values.items())


# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Run the loop once and return the finished session.

    Args:
        query:    what the user asked for, in plain language
                  (e.g. "vintage graphic tee under $30, size M").
        wardrobe: a wardrobe dict — get_example_wardrobe() or
                  get_empty_wardrobe() from utils/data_loader.py.

    Returns:
        The session dict. **Check session["error"] first** — if it isn't None,
        the run ended early and the later fields will still be None.

    ─────────────────────────────────────────────────────────────────────────
    TODO — build this, following the branch rule you wrote in Milestone 2.

      1. Start a session with new_session().

      2. Count the times round the loop, and call trace.check_iterations(count)
         on each one before you go again. It raises when the count passes
         MAX_ITERATIONS in config.py — see trace.py.

      3. Parse the query into a description, a size, and a max_price. Regex,
         string splitting, or asking the model are all fine — say which you
         chose in your README. Put the result in session["parsed"].

      4. Call search_listings() with what you parsed.
         Put the results in session["search_results"].

         ⚠️ THIS IS THE BRANCH. If nothing came back:
              - put a message in session["error"] saying what the user could
                change — "No results" is not that message
              - return the session
              - do NOT call suggest_outfit with nothing

      5. Choose an item — the first result is fine. Put it in
         session["selected_item"].

      6. Call suggest_outfit() with the selected item and the wardrobe.
         Put the result in session["outfit_suggestion"].

      7. Call create_fit_card() with the outfit and the item.
         Put the result in session["fit_card"].

      8. Return the session.

    ─────────────────────────────────────────────────────────────────────────
    IN UNIT 4 you come back and add two things:

      • Trace calls. One per step. `trace.step("search_listings", inputs=...,
        returned=...)` — see trace.py. Your README needs the output.

      • A handler for ModelUnavailable, so a bad key produces a message rather
        than a stack trace. The import is already at the top of this file.
    """
    session = new_session(query, wardrobe)
    iteration = 0

    try:
        iteration += 1
        trace.check_iterations(iteration)
        parsed = parse_query(query)
        session["parsed"] = parsed
        trace.step("parse_query", inputs=repr(query), returned=_fmt(parsed))

        iteration += 1
        trace.check_iterations(iteration)
        # Unit 4: search_listings now runs on the MCP server (mcp_server.py).
        results = call_tool("search_listings", {
            "description": parsed["description"],
            "size": parsed["size"],
            "max_price": parsed["max_price"],
        })
        session["search_results"] = results
        trace.step(
            "search_listings (via MCP)",
            inputs=_fmt(parsed),
            returned=results,
            note="" if results else "branch: empty, stopping",
        )

        # ── THE BRANCH ──
        if not results:
            session["error"] = (
                "No listings matched your search. Try loosening the size, "
                "raising the price ceiling, or using a broader description."
            )
            return session

        selected_item = results[0]
        session["selected_item"] = selected_item

        # Style memory (stretch): fold remembered style tags from past runs
        # into the wardrobe as a lightweight synthetic "preferences" item, so
        # suggest_outfit sees taste built up over previous sessions, not just
        # what's in the static wardrobe file.
        remembered_tags = load_style_memory()["style_tags"]
        wardrobe_with_memory = dict(wardrobe)
        # Unit 4 handler: only fold memory into a wardrobe that has items. Adding
        # the synthetic item to an EMPTY wardrobe made suggest_outfit skip its
        # general-advice branch, and the model replied "you forgot your wardrobe".
        if remembered_tags and wardrobe.get("items"):
            wardrobe_with_memory["items"] = wardrobe.get("items", []) + [{
                "id": "style_memory",
                "name": "Remembered style preferences",
                "category": "accessories",
                "colors": [],
                "style_tags": remembered_tags,
                "notes": "Styles the user has gravitated toward in past finds.",
            }]

        iteration += 1
        trace.check_iterations(iteration)
        outfit = suggest_outfit(selected_item, wardrobe_with_memory)
        session["outfit_suggestion"] = outfit
        remember_style(selected_item.get("style_tags", []))
        trace.step(
            "suggest_outfit",
            inputs=_fmt({
                "new_item": selected_item.get("title"),
                "item_id": selected_item.get("id"),
                "wardrobe_items": len(wardrobe.get("items", [])),
            }),
            returned=outfit,
        )

        iteration += 1
        trace.check_iterations(iteration)
        fit_card = create_fit_card(outfit, selected_item)
        session["fit_card"] = fit_card
        trace.step(
            "create_fit_card",
            inputs=_fmt({"outfit": outfit[:60] + "…", "new_item": selected_item.get("title")}),
            returned=fit_card,
        )

        # ── SECOND BRANCH (stretch) ──
        # If the selected item's price is at or above its category average,
        # run a price comparison so the fit card isn't the only signal about
        # whether it's a good find.
        iteration += 1
        trace.check_iterations(iteration)
        comparison = call_tool("compare_price", {"item": selected_item})
        if comparison["verdict"] != "good deal":
            session["price_comparison"] = comparison
            trace.step(
                "compare_price (via MCP)",
                inputs=_fmt({"item": selected_item.get("title")}),
                returned=_fmt(comparison),
                note=f"branch: {comparison['verdict']}, flagging price",
            )
        else:
            trace.step(
                "compare_price (via MCP)",
                inputs=_fmt({"item": selected_item.get("title")}),
                returned=_fmt(comparison),
                note="branch: good deal, no flag needed",
            )

        return session

    except ModelUnavailable as exc:
        found = (session["selected_item"] or {}).get("title")
        session["error"] = (
            (f"The search worked (best match: {found}) but " if found else "")
            + f"the model couldn't be reached, so no outfit or fit card was made. "
            f"{exc} Fix that, then run the same query again."
        )
        trace.step("model unavailable", returned=str(exc), note="stopping, no outfit or fit card")
        return session
    except MCPError as exc:
        session["error"] = (
            f"The search tool couldn't be reached over MCP, so nothing was searched. "
            f"{exc}\n"
            f"What to try: run `python mcp_server.py` on its own to see "
            f"why it won't start, then run the query again."
        )
        trace.step("MCP error", returned=str(exc).splitlines()[0], note="stopping")
        return session


# ── running it directly ───────────────────────────────────────────────────────

def _show(session: dict) -> None:
    if session["error"]:
        print(f"  stopped: {session['error']}")
        print(f"  fit_card is {session['fit_card']!r} — it should still be None here")
        return

    item = session["selected_item"] or {}
    print(f"  found:    {item.get('title')} — ${item.get('price')} on {item.get('platform')}")
    print(f"  outfit:   {session['outfit_suggestion']}")
    print(f"  fit card: {session['fit_card']}")


if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe

    print("=== A query the data can match ===")
    _show(run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    ))

    print("\n=== A query it can't ===")
    _show(run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    ))

    print(
        "\nThe second one should stop before the fit card. If both paths look "
        "the same,\nthe branch isn't doing anything yet."
    )
