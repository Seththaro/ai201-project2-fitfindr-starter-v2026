# FitFindr

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first** — setup, every
> command, and what to do when something breaks.
>
> Once `python test.py` passes:
>
> ```bash
> python app.py listings --full -n 6      # read the data (Milestone 1)
> python app.py fields                    # what you can filter on
> python app.py ask 'vintage graphic tee under $30'
> ```
>
> All three tools are stubs, so that last command will do nothing useful yet.
> That's the starting position.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     HOW TO USE THIS FILE

     This is your submission. Fill each section in as you finish the milestone
     it belongs to — don't leave it all to the end.

     Unit 3 asks for the first five sections. Unit 4 adds the five below them.
     Leave the unit 4 sections alone until then; they're here so you know
     what's coming.

     Everything is pasted as TEXT. No screenshots, no images, no video links.
     A typed block of output gets full credit; a picture of the same output
     gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 3 — THE BUILD ═══════════════════════ -->

## What This Does

A user types a free-text request like `"vintage graphic tee under $30, size M"`.
FitFindr parses out a description, a size, and a price ceiling; searches the
listings data for matches; picks the best one; asks the model how to style it
with the user's existing wardrobe; and writes a short social-caption-style
"fit card" for the find. If nothing matches the search, the agent stops and
tells the user what to change instead of guessing. It also checks the chosen
item's price against similar listings and remembers style tags from past
finds so later outfit suggestions build on earlier ones.

---

## Stretch Features Implemented

- **A fourth tool, `compare_price`** (`tools.py`). See Tool Inventory below.
- **A second branch**: the loop takes a different path depending on whether
  the found item's price is at/above its category average. See Planning Loop
  below.
- **Style memory**: the agent remembers style tags across runs. See Sample
  Run below for two runs where the second is shaped by the first.

---

## Tool Inventory

<!-- Four lines per tool. This is worth 2 points and it's the single most
     common place students lose them.

     "Returns a list" earns NOTHING. The description has to say what is IN
     the list.

     The empty case isn't optional either — it's the thing your loop branches
     on, and if you don't decide it here you'll discover it as a crash in
     Milestone 5. -->

### `search_listings`

- **What it does:** Filters the listings data by price and size, scores what's left by keyword overlap with a description, and returns the best matches.
- **Inputs:** `description` (str): keywords describing what the user wants; `size` (str or None): a size token to match, or None to skip size filtering; `max_price` (float or None): inclusive price ceiling, or None to skip price filtering.
- **Returns:** A list of listing dicts (best match first), each with `id, title, description, category, style_tags (list), size, condition, price (float), colors (list), brand (str or None), platform`. Capped at `config.SEARCH_RESULT_LIMIT`.
- **When it has nothing:** Returns `[]`, an empty list, never `None` and never an exception.

### `suggest_outfit`

- **What it does:** Asks the model for one or two outfit ideas pairing a new item with the user's wardrobe.
- **Inputs:** `new_item` (dict): a listing dict; `wardrobe` (dict): a wardrobe dict with an `items` key (list of wardrobe item dicts), which may be empty.
- **Returns:** A non-empty `str`, 2-3 sentences, naming specific wardrobe pieces by name when the wardrobe isn't empty.
- **When it has nothing:** When `wardrobe["items"]` is empty, returns general styling advice (a string) instead of raising or returning `""`.

### `create_fit_card`

- **What it does:** Writes a short, caption-style post about the item using the outfit suggestion.
- **Inputs:** `outfit` (str): the string from `suggest_outfit`; `new_item` (dict): the listing dict.
- **Returns:** A 2-4 sentence `str` caption mentioning the item, its price, and its platform once each.
- **When it has nothing:** When `outfit` is empty or whitespace-only, returns a descriptive message string (naming the item) instead of raising.

### `compare_price` (stretch, 4th tool)

- **What it does:** Compares a listing's price against other listings in the same category and returns a verdict.
- **Inputs:** `item` (dict): the listing dict to evaluate; `category` (str or None): which category to compare against, defaults to `item["category"]`.
- **Returns:** A dict `{"average_price": float, "percent_of_average": float, "verdict": str, "compared_to": int}`, where `verdict` is one of `"good deal"`, `"fair price"`, `"above average"`.
- **When it has nothing:** When no other listings exist in the category, returns `{"average_price": None, "percent_of_average": None, "verdict": "no comparison data", "compared_to": 0}`.

---

## Planning Loop

<!-- Your branch rule, stated as a rule — the condition AND both paths — plus
     the file and function that holds it.

     Like this:
       "If search_listings returns an empty list, put a message in the session
        and stop. Otherwise take the first result and go to suggest_outfit."
        — agent.py::run_agent

     The grader checks your code against what you claim here, so the file and
     function have to be real. -->

**Branch rule (required branch):** If `search_listings` returns an empty list, put a message in `session["error"]` naming what the user could change (loosen size, raise price, broaden description) and stop; do not call `suggest_outfit`. Otherwise, take the first result as `session["selected_item"]` and continue to `suggest_outfit`.

**Branch rule (stretch, 2nd branch):** After `create_fit_card`, call `compare_price` on the selected item. If its `verdict` is not `"good deal"` (i.e. it's `"fair price"` or `"above average"`), store the comparison in `session["price_comparison"]` and note it in the trace as a flag; if it *is* a good deal, the comparison still runs (so the trace always shows the check) but nothing is flagged.

**Where it lives:** `agent.py::run_agent`

**How the query is parsed:** Regex (`agent.py::parse_query`). One regex pulls a price ceiling from phrases like "under $30"/"below 30"/"less than 30"; a second pulls a size from "size M" style phrases; whatever text is left (with the matched spans removed) becomes the search description.

**What moves through the session:** `query` -> `parsed` (from `parse_query`) -> `search_results` (from `search_listings`) -> `selected_item` (first result) -> `outfit_suggestion` (from `suggest_outfit`, called with `selected_item` and the wardrobe merged with style memory) -> `fit_card` (from `create_fit_card`, called with `outfit_suggestion` and `selected_item`) -> `price_comparison` (from `compare_price`, called with `selected_item`). `error` is set instead, and the rest stay `None`, when the branch triggers.

---

## Sample Run

<!-- Two things go here.

     1. One FULL query and its output, pasted as text.
     2. Your three per-tool terminal tests — the command and what it printed. -->

**One full query**

```
$ python app.py ask 'vintage graphic tee under $30' --trace

[1] parse_query
      in:  dict with keys: query
      out: dict with keys: description, size, max_price
[2] search_listings
      in:  dict with keys: description, size, max_price
      out: 10 items: Y2K Baby Tee — Butterfly Print, Graphic Tee — 2003 Tour Bootleg Style, Vintage Band Tee — Faded Grey … +7 more
[3] suggest_outfit
      in:  dict with keys: new_item, wardrobe_items
      out: Pair the Y2K baby tee with your baggy straight-leg jeans and brown leather belt for a classic early-2000s silh…
[4] create_fit_card
      in:  dict with keys: outfit, new_item
      out: Scored this absolute dream of a butterfly print baby tee for just $18 on Depop! Throwing it back to the early …
[5] compare_price
      in:  dict with keys: item
      out: dict with keys: average_price, percent_of_average, verdict, compared_to
      →    branch: fair price, flagging price

  Found:    Y2K Baby Tee — Butterfly Print — $18.0 on depop

  Outfit:   Pair the Y2K baby tee with your baggy straight-leg jeans and brown leather belt for a classic early-2000s silhouette, finished off with chunky white sneakers. To lean into the juxtaposition of fitted and oversized styles, layer your vintage black denim jacket on top and accessorize with your black crossbody bag.

  Fit card: Scored this absolute dream of a butterfly print baby tee for just $18 on Depop! Throwing it back to the early 2000s today by pairing it with baggy straight-leg denim, a chunky belt, and my favorite vintage jacket. Such a nostalgic little find that I'm never taking off. 🦋✨

2 model calls this session, 353 prompt + 135 output tokens
```

**Empty-search branch, same command shape**

```
$ python app.py ask 'designer ballgown size XXS under $5' --trace

[1] parse_query
      in:  dict with keys: query
      out: dict with keys: description, size, max_price
[2] search_listings
      in:  dict with keys: description, size, max_price
      out: [] (empty)
      →    branch: empty, stopping

  No listings matched your search. Try loosening the size, raising the price ceiling, or using a broader description.

0 model calls this session
```

**The three required tools, tested one at a time**

```
$ python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"

[{'id': 'lst_002', 'title': 'Y2K Baby Tee — Butterfly Print', ..., 'size': 'S/M', 'price': 18.0, 'platform': 'depop', ...}, {'id': 'lst_006', 'title': 'Graphic Tee — 2003 Tour Bootleg Style', ..., 'price': 24.0, ...}, ... 6 results total]
```

```
$ python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"

Pair the new vintage Levi's 501 jeans with the white ribbed tank top and chunky white sneakers for a classic, effortless 90s-inspired look, pulling it together with the black crossbody bag. For cooler weather, layer the oversized grey crewneck sweatshirt over the tank and swap the sneakers for the black combat boots to add an edgy, streetwear vibe.
```

```
$ python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"

Scored these vintage Levi's 501 jeans on Depop for just $38 and I am never taking them off. They've got that *exact* broken-in medium wash that looks impossible to replicate. Just paired 'em with crisp white sneakers for the ultimate effortless weekend fit.
```

**Stretch: 4th tool, `compare_price`**

```
$ python -c "from tools import compare_price; from utils.data_loader import load_listings; print(compare_price(load_listings()[0]))"

{'average_price': 28.44, 'percent_of_average': 133.6, 'verdict': 'above average', 'compared_to': 9}
```

**Stretch: style memory across two runs**

Run 1 (`vintage graphic tee under $30`) finds the Y2K Baby Tee, whose
`style_tags` are `["y2k", "vintage", "graphic tee", "cottagecore"]`. After that
run, `data/style_memory.json` contains:

```
{
  "style_tags": ["y2k", "vintage", "graphic tee", "cottagecore"]
}
```

Run 2 (`90s track jacket in size M`) then calls `suggest_outfit` with a
wardrobe that includes a synthetic "Remembered style preferences" item
carrying those four tags, folded in on top of the static wardrobe, so the
second run's outfit suggestion is shaped by what the first run found, not
just the fixed wardrobe file. See `agent.py::run_agent` for where this is
wired (`load_style_memory` / `remember_style` in `utils/data_loader.py`).

---

## How I Used AI

<!-- Two specific moments. What you asked, what came back, what you changed.

     "I used Claude to help me code" is not enough.

     "I gave Claude my search_listings spec. It returned None on no match
     instead of an empty list, so I changed it" is the level we want. -->

**Moment 1**

- *What I asked for:* I asked Claude to implement `search_listings`'s size filter and flagged the warning already in the docstring about substring matching on size strings (e.g. `"s" in "us 9"`).
- *What came back:* A first pass that split each listing's size string on any non-alphanumeric character (`re.split(r"[^a-z0-9]+", ...)`) and checked for an exact token match. That fixed the "s" in "us 9" problem, but I then tested it against `"US 8.5"` myself and found that splitting on `.` too turned `"8.5"` into separate tokens `"8"` and `"5"`, so searching for size `"8"` incorrectly matched `"US 8.5"`.
- *What I changed:* I changed the split pattern to `r"[\s/\-]+"` (whitespace, slash, hyphen only) so decimal sizes stay intact as one token, and re-verified against the listings data that `"8"` now matches only `"US 8"` and not `"US 8.5"`.

**Moment 2**

- *What I asked for:* I wrote criterion 5 myself first, "size filtering works correctly across different size values," then asked Claude to read it back and tell me, using only that sentence, exactly how it would test it.
- *What came back:* It said it couldn't test it from that sentence alone. "Works correctly" doesn't say what correct means, so it would have to ask me what counts as a match.
- *What I changed:* I rewrote the criterion myself to name the exact tokenization rule (whitespace/slash/hyphen-separated tokens) and the concrete counterexample it has to avoid (`"M"` matching `"S/M"` but not `"XL"`), with a 5-of-5 target across 5 different size values: something a reader could actually run and check without asking me what I meant.

<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════

     Don't fill these in during unit 3.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Run Log — Before

<!-- Five criteria, five tries each, in this exact format.

     Five, because your criteria are written out of five. Mark each try PASS
     or FAIL, count the passes, and read that count against your target — a
     row targeting 4 of 5 with three PASS cells is MISSED (3/5).

     `python run_eval.py --label before` runs everything and writes the table
     into results/. Paste it here and fill in the verdicts. -->

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Real output from one try**, pasted as text, naming the file and function
that produced it:

```

```

---

## Verdicts and Diagnoses

<!-- MET or MISSED per criterion against LAST UNIT's target, plus a sentence on
     how you decided.

     Then, for every miss: which of the four places it happened — a tool, the
     loop's branch, the session, or the model's output — AND the mechanism.

     Not a diagnosis:  "The fit card was bad."
     A diagnosis:      "The fit card criterion missed on 2 of 5 items. Both had
                        an empty brand field. My prompt puts the brand in the
                        first sentence, so the card opened with a blank and read
                        like a fragment. The tool worked; the prompt assumed a
                        field that isn't always there."

     Look for a pattern. Three misses on the same tool is one problem, not
     three. -->

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 |  |  |  |  |
| 2 |  |  |  |  |
| 3 |  |  |  |  |
| 4 |  |  |  |  |
| 5 |  |  |  |  |

**Diagnoses**



---

## Loop Trace

<!-- One full run, printed step by step, with the MCP call visible in it.

     `python app.py ask '...' --trace` once you've added the trace.step()
     calls in Milestone 2.

     Worth pasting BOTH the happy path and the empty-search path. The empty
     one should be visibly shorter, because it stops. If your two traces are
     the same length, your branch isn't working — and this is the fastest way
     anyone will ever find that out. -->

**Happy path**

```

```

**Empty search**

```

```

**On the MCP move:** <!-- what changed in your code, and whether anything
behaved differently afterwards. If the rewire didn't work, say exactly where it
broke — the error text and the last thing that worked. That earns the point in
full. -->



---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:**

**Which failure it was meant to fix:**

### Run Log — After

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Did it help, and how do I know:**

<!-- If it made things worse, say that. Honestly reported, that earns full
     credit and is more interesting than one that worked. -->



---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->



<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 3

       [ ] criteria.md has five numbered criteria, each with a target
       [ ] Each criterion has a reason underneath it
       [ ] All five unit 3 sections above have real content
       [ ] Tool Inventory: all three tools, inputs WITH TYPES, a specific
           return value, and the empty case
       [ ] Planning Loop names the branch rule and agent.py::run_agent
       [ ] Sample Run: one full query plus the three per-tool tests, as text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN, you submit the same one
           next unit

     SUBMISSION CHECKLIST — unit 4

       [ ] mcp_server.py exists with one tool registered
           (or a written record of exactly where the rewire broke)
       [ ] Run Log — Before, five criteria, five tries each
       [ ] Real output pasted underneath, naming file and function
       [ ] A verdict on every criterion
       [ ] A diagnosis for every miss, naming a place AND a mechanism
       [ ] Loop Trace, with the MCP call visible in it
       [ ] All three failure modes triggered and handled
       [ ] One improvement, with Run Log — After in the same format
       [ ] What's Still Broken
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository. Your commit history is what
     shows your criteria existed before your results did.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
