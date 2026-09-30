"""
Utility functions for loading the mock listings dataset and wardrobe schema.
Use these in your tool implementations to access the data without re-reading
the files each time.
"""

import json
import os
from typing import Optional

# Resolve the path to the data directory relative to this file
_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def load_listings() -> list[dict]:
    """
    Load all mock listings from the dataset.

    Returns:
        A list of listing dictionaries. Each listing has the following fields:
        - id (str)
        - title (str)
        - description (str)
        - category (str): one of tops, bottoms, outerwear, shoes, accessories
        - style_tags (list[str])
        - size (str)
        - condition (str): excellent, good, or fair
        - price (float)
        - colors (list[str])
        - brand (str or None)
        - platform (str): depop, thredUp, or poshmark
    """
    path = os.path.join(_DATA_DIR, "listings.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_wardrobe_schema() -> dict:
    """
    Load the wardrobe schema, including the example wardrobe and empty template.

    Returns:
        A dictionary containing:
        - schema: the field definitions for a wardrobe item
        - example_wardrobe: a sample wardrobe with 10 items
        - empty_wardrobe: a starting template for a new user
    """
    path = os.path.join(_DATA_DIR, "wardrobe_schema.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _wardrobe(name: str) -> dict:
    """
    Pull one wardrobe out of the schema file, without the documentation keys.

    The JSON uses underscore-prefixed keys (_description, _note) to explain
    itself to a human reader. Those are notes about the file, not part of a
    wardrobe, and stripping them here means both wardrobes below come back
    the same shape. Otherwise the empty one carries an extra _note key, and a
    tool that formats the whole dict into a prompt would send the model a
    sentence about templates.
    """
    wardrobe = load_wardrobe_schema()[name]
    return {k: v for k, v in wardrobe.items() if not k.startswith("_")}


def get_example_wardrobe() -> dict:
    """
    Convenience function — returns just the example wardrobe items list.

    Returns:
        A wardrobe dict with an 'items' key containing a list of wardrobe items.
    """
    return _wardrobe("example_wardrobe")


def get_empty_wardrobe() -> dict:
    """
    Convenience function — returns an empty wardrobe template.

    Returns:
        A wardrobe dict with an empty 'items' list. Same shape as the example
        wardrobe — the only difference is that 'items' is empty.
    """
    return _wardrobe("empty_wardrobe")


def load_style_memory() -> dict:
    """
    Load remembered style tags from previous runs (stretch — style memory).

    Returns:
        A dict {"style_tags": list[str]} — tags seen across past finds, most
        recent last. Empty if no memory file exists yet.
    """
    path = os.path.join(_DATA_DIR, "style_memory.json")
    if not os.path.exists(path):
        return {"style_tags": []}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_style_memory(memory: dict) -> None:
    """Persist the style memory dict to disk so it's there on the next run."""
    path = os.path.join(_DATA_DIR, "style_memory.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(memory, f, indent=2)


def remember_style(style_tags: list[str], limit: int = 20) -> dict:
    """
    Add newly-seen style tags to memory and persist it.

    Args:
        style_tags: tags from the item the user just looked at.
        limit: how many tags to keep, most recent kept when trimming.

    Returns:
        The updated memory dict.
    """
    memory = load_style_memory()
    seen = memory["style_tags"]
    for tag in style_tags:
        if tag in seen:
            seen.remove(tag)
        seen.append(tag)
    memory["style_tags"] = seen[-limit:]
    save_style_memory(memory)
    return memory


# --- Quick sanity check ---
if __name__ == "__main__":
    listings = load_listings()
    print(f"Loaded {len(listings)} listings.")
    print(f"First listing: {listings[0]['title']} — ${listings[0]['price']}")

    wardrobe = get_example_wardrobe()
    print(f"\nExample wardrobe has {len(wardrobe['items'])} items.")
    print(f"First item: {wardrobe['items'][0]['name']}")
