"""
The runs my test needs. ← UNIT 4, MILESTONE 3

One scenario per criterion in criteria.md. `run_eval.py` runs each scenario
five times (five tries, caching off). A scenario with a `queries` list uses a
different query on each try; a scenario with only `query` repeats it.

Each scenario's `check(record, try_number, scenario)` returns (passed, reason).
The checks are written from the wording in criteria.md, not from what the agent
happens to do. `record` holds the finished session, the trace, and `calls`: the
item ids that `suggest_outfit` was actually called with (a spy installed by
run_eval.py, because the session alone can't show what a tool was called with).
"""

import re

# What each criterion needs to read as MET (passes out of five). From criteria.md.
TARGETS = {1: 4, 2: 5, 3: 5, 4: 4, 5: 5}


# ── scoring helpers ───────────────────────────────────────────────────────────

def _session(record):
    return record.get("session") or {}


def _crashed(record):
    return f"crashed: {record['crashed']}" if record.get("crashed") else None


def check_full_run(record, n, scenario):
    """Criterion 1: all three tools ran and a fit card came back."""
    if (why := _crashed(record)):
        return False, why
    s = _session(record)
    if s.get("error"):
        return False, f"stopped early: {str(s['error'])[:70]}"
    if not s.get("search_results"):
        return False, "search returned nothing"
    if not (s.get("outfit_suggestion") or "").strip():
        return False, "no outfit suggestion"
    if not (s.get("fit_card") or "").strip():
        return False, "no fit card"
    return True, "search, outfit and fit card all present"


def check_empty_stops(record, n, scenario):
    """Criterion 2: nothing matched, suggest_outfit never called, message names what to change."""
    if (why := _crashed(record)):
        return False, why
    s = _session(record)
    if record.get("calls"):
        return False, f"suggest_outfit was called with {record['calls']}"
    if s.get("outfit_suggestion") or s.get("fit_card"):
        return False, "outfit or fit card was produced"
    err = (s.get("error") or "").lower()
    if not err:
        return False, "no message in session['error']"
    if not any(word in err for word in ("size", "price", "description")):
        return False, f"message names nothing to change: {err[:60]}"
    return True, "stopped before suggest_outfit with an actionable message"


def check_state(record, n, scenario):
    """Criterion 3: selected_item id == id of the item suggest_outfit was called with."""
    if (why := _crashed(record)):
        return False, why
    s = _session(record)
    item = s.get("selected_item")
    if not item:
        return False, "no selected_item in session"
    if len(record.get("calls") or []) != 1:
        return False, f"suggest_outfit called {len(record.get('calls') or [])} times"
    if record["calls"][0] != item.get("id"):
        return False, f"selected {item.get('id')} but suggest_outfit got {record['calls'][0]}"
    return True, f"both {item.get('id')}"


_PRICE = re.compile(r"\$\s?(\d[\d,]*(?:\.\d+)?)")


def _sentences(text):
    return [p for p in re.split(r"(?<=[.!?])\s+", text.strip()) if p.strip()]


def check_fit_card(record, n, scenario):
    """Criterion 4: item's price as $<numeral> exactly once, 2-4 sentences."""
    if (why := _crashed(record)):
        return False, why
    s = _session(record)
    card, item = (s.get("fit_card") or ""), s.get("selected_item")
    if not card or not item:
        return False, "no fit card or no item"
    prices = _PRICE.findall(card)
    right = [p for p in prices if abs(float(p.replace(",", "")) - float(item["price"])) < 0.005]
    n_sent = len(_sentences(card))
    problems = []
    if len(prices) != 1 or len(right) != 1:
        problems.append(f"$-prices in card: {prices} (item price {item['price']})")
    if not 2 <= n_sent <= 4:
        problems.append(f"{n_sent} sentences")
    if problems:
        return False, f"{item['id']}: " + "; ".join(problems)
    return True, f"{item['id']}: one ${right[0]}, {n_sent} sentences"


def check_sizes(record, n, scenario):
    """Criterion 5: every returned listing has the requested size as a whole token."""
    if (why := _crashed(record)):
        return False, why
    wanted = scenario["sizes"][n - 1].lower()
    results = _session(record).get("search_results") or []
    if not results:
        return False, "search returned nothing, so nothing to verify"
    bad = [
        f"{r['id']} ({r['size']})"
        for r in results
        if wanted not in re.split(r"[\s/\-]+", r["size"].lower())
    ]
    if bad:
        return False, f"size {wanted.upper()}: wrong sizes returned: {', '.join(bad)}"
    return True, f"size {wanted.upper()}: all {len(results)} results match"


# ── the scenarios ─────────────────────────────────────────────────────────────

SCENARIOS = [
    {
        # Criterion 1: five different natural phrasings, because the "why 4 of
        # 5" reasoning is about phrasing the keyword match might not cover.
        "name": "matching query completes all three tools",
        "queries": [
            "vintage graphic tee under $30",
            "oversized flannel under $25",
            "y2k mesh top",
            "cozy cardigan",
            "90s windbreaker size L",
        ],
        "wardrobe": "example",
        "criterion": 1,
        "check": check_full_run,
    },
    {
        # Criterion 2: five different queries the data cannot match.
        "name": "impossible query stops before tool 2",
        "queries": [
            "designer ballgown size XXS under $5",
            "wedding tuxedo",
            "snowboard goggles",
            "denim jacket under $5",
            "leather bomber size XXS",
        ],
        "wardrobe": "example",
        "criterion": 2,
        "check": check_empty_stops,
    },
    {
        # Criterion 3: ordinary queries; what is checked is the session.
        "name": "selected item is the item passed on",
        "queries": [
            "denim jacket under $50",
            "linen blazer",
            "band tee size L",
            "silk dress",
            "leather belt",
        ],
        "wardrobe": "example",
        "criterion": 3,
        "check": check_state,
    },
    {
        # Criterion 4: five queries that select five different items.
        "name": "fit card has the price once, 2-4 sentences",
        "queries": [
            "butterfly baby tee",
            "levi's 501 jeans",
            "track jacket",
            "chelsea boots",
            "bucket hat",
        ],
        "wardrobe": "example",
        "criterion": 4,
        "check": check_fit_card,
    },
    {
        # Criterion 5: five different sizes.
        "name": "every result matches the requested size",
        "queries": [
            "top size M",
            "tee size L",
            "jacket size S",
            "sweatshirt size XL",
            "sneakers size 9",
        ],
        "sizes": ["M", "L", "S", "XL", "9"],
        "wardrobe": "example",
        "criterion": 5,
        "check": check_sizes,
    },
    {
        # Diagnostic (not one of the five): a user with nothing saved.
        "name": "empty wardrobe",
        "query": "denim jacket under $50",
        "wardrobe": "empty",
        "criterion": None,
    },
]

WARDROBES = ("example", "empty")


def query_for(scenario, n):
    """The query for try number n (1-based)."""
    queries = scenario.get("queries")
    return queries[(n - 1) % len(queries)] if queries else scenario["query"]


def validate() -> list[str]:
    """Complain about anything malformed, before a long run rather than during."""
    problems = []
    for i, scenario in enumerate(SCENARIOS, 1):
        if not (scenario.get("query") or scenario.get("queries")):
            problems.append(f"scenario {i} has no query")
        if scenario.get("wardrobe") not in WARDROBES:
            problems.append(
                f"scenario {i} has wardrobe {scenario.get('wardrobe')!r} — "
                f"it should be one of {WARDROBES}"
            )
    return problems
