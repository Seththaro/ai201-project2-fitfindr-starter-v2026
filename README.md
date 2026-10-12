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

**Unit 4 changes to the loop:** `search_listings` and `compare_price` are now called over MCP (`mcp_client.call_tool` to `mcp_server.py`). An empty search that had a size filter retries once without it before the branch above fires (stretch), and the size regex in `parse_query` now needs a word boundary. See Loop Trace and The Improvement.

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

**Moment 3 (unit 4)**

- *What I asked for:* I had Claude run the whole unit 4 workflow against my repo, then I read what it produced against the brief: the MCP move, the three failures, the scenarios, the five-by-five runs.
- *What came back:* Two things I had to check rather than accept. First, its empty-wardrobe test did not return advice: the model asked for a wardrobe, because my own style-memory stretch had added an item to the "empty" wardrobe. Second, its first retry scorer reported 5 FAILs on runs that had worked, because the checker read the trace before `run_eval.py` had saved it.
- *What I changed:* I kept the empty-wardrobe finding as a real bug and fixed it in the agent, and I fixed the scorer's ordering and re-ran. I also kept the case where Claude predicted the retry would not affect criterion 2 and was wrong, and reported the miss instead of changing the query.

<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════

     Don't fill these in during unit 3.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Unit 4 Stretch Features (declared before building)

Declared before any unit 4 code was written:

1. **A second tool moved onto MCP**: `compare_price` (no model call), alongside `search_listings`.
2. **Retry with looser constraints**: an empty search retries once without the size filter, and the agent says what it dropped.
3. **A second measured improvement** from the diagnosis, with a third run log in the same table format.

---

## Run Log — Before

Produced by `python run_eval.py --label before` (`run_eval.py::main`, scored by the `check_*` functions in `scenarios.py`). Five tries per criterion, caching off, temperature 0.9. The full raw output, including the trace of every try, is committed in `results/run_2026-10-12_0109_before.md`.

State of the agent for this run: `search_listings` and `compare_price` already run over MCP, and the three failure handlers from Milestone 2 are in. Nothing else had changed. The tries are different inputs, not the same input five times, because that is what each criterion in `criteria.md` asks for: criterion 4 says "5 different items" and criterion 5 says "across 5 different size values". Criteria 1, 2 and 3 use five different queries so that the target is not decided by one lucky phrasing.

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. Matching query completes all three tools | 4 of 5 | PASS | FAIL | PASS | PASS | PASS | MET (4/5) |
| 2. Impossible query stops before tool 2 | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. Selected item is the item passed on | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. Fit card has the price once, 2-4 sentences | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 5. Every result matches the requested size | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

The queries behind each row (try 1 to try 5):

1. `vintage graphic tee under $30` / `oversized flannel under $25` / `y2k mesh top` / `cozy cardigan` / `90s windbreaker size L`
2. `designer ballgown size XXS under $5` / `wedding tuxedo` / `snowboard goggles` / `denim jacket under $5` / `leather bomber size XXS`
3. `denim jacket under $50` / `linen blazer` / `band tee size L` / `silk dress` / `leather belt`
4. `butterfly baby tee` / `levi's 501 jeans` / `track jacket` / `chelsea boots` / `bucket hat` (five different items: lst_002, lst_001, lst_004, lst_028, lst_034)
5. `top size M` / `tee size L` / `jacket size S` / `sweatshirt size XL` / `sneakers size 9`

**A diagnostic row added after seeing the table above.** Five MET out of five looked too good for a keyword matcher, so I probed it with five more natural phrasings that I could see had a matching listing in the data. This is not one of my five criteria and it does not change any verdict. It is scored like criterion 1 (did all three tools complete?) and it was run on the unchanged code right after the first run (`results/run_2026-10-12_0110_before-variants.md`).

| Diagnostic | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Result |
|---|---|---|---|---|---|---|---|
| Phrasing variants: `oversized sweatshirt` / `sweatshirts` / `sneaker size 9` / `graphic tees under $30` / `denim jackets` | none | FAIL | FAIL | FAIL | PASS | PASS | 2/5 |

**Real output from one try per criterion** (pasted as text; each names the file and function that produced it).

Criterion 1, try 1 (a PASS). Fit card from `tools.py::create_fit_card`, run by `agent.py::run_agent`:

```
Obsessed is an understatement for this Y2K butterfly baby tee I just scored on Depop for only $18! It’s giving major early-2000s off-duty model energy, especially paired with low-rise baggies and chunky sneakers. Thrift gods have officially blessed me. ✨🦋
```

Criterion 1, try 2 (the FAIL). Trace printed by `trace.py` from `agent.py::run_agent`, and the message the branch returned:

```
[1] parse_query
      in:  'oversized flannel under $25'
      out: description='over flannel', size='d', max_price=25.0
[2] search_listings (via MCP)
      in:  description='over flannel', size='d', max_price=25.0
      out: [] (empty)
      →    branch: empty, stopping
No listings matched your search. Try loosening the size, raising the price ceiling, or using a broader description.
```

Criterion 2, try 1. Message set in `session["error"]` by the branch in `agent.py::run_agent`; `scenarios.py::check_empty_stops` confirmed `suggest_outfit` was never called and no outfit or fit card was produced:

```
query: designer ballgown size XXS under $5
No listings matched your search. Try loosening the size, raising the price ceiling, or using a broader description.
```

Criterion 3, try 1. The `suggest_outfit` call as traced by `agent.py::run_agent`, and the verdict from `scenarios.py::check_state`, which compares `session["selected_item"]["id"]` with the id a spy in `run_eval.py::run_once` saw `suggest_outfit` being called with:

```
query: denim jacket under $50
check: PASS - both lst_007
```

Criterion 4, try 2. Fit card from `tools.py::create_fit_card`, scored by `scenarios.py::check_fit_card`:

```
Scored the holy grail of denim: these vintage Levi's 501 jeans in the dreamiest medium wash for just $38.00 on Depop! I’m already styling them with a chunky white sneakers-and-tank combo for daytime, or dressing them down with an oversized grey crewneck and combat boots. Nothing beats finding broken-in, perfect-fitting denim that feels this effortlessly cool.
check: PASS - lst_001: one $38.00, 3 sentences
```

Criterion 5, try 1. `tools.py::search_listings` results through MCP, checked by `scenarios.py::check_sizes`:

```
query: top size M
check: PASS - size M: all 2 results match      (lst_017 size "S/M", lst_023 size "S/M")
```

---

## Verdicts and Diagnoses

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 | Matching query completes all three tools | 4 of 5 | MET (4/5) | Four PASS cells against a target of 4. It met the number with no slack, and the one FAIL was a real defect (below). |
| 2 | Impossible query stops before tool 2 | 5 of 5 | MET (5/5) | Five of five stopped with `suggest_outfit` never called and a message naming the size, price or description. |
| 3 | Selected item is the item passed on | 5 of 5 | MET (5/5) | The spy saw the same id as `session["selected_item"]` on all five. |
| 4 | Fit card has the price once, 2-4 sentences | 4 of 5 | MET (5/5) | Every card had exactly one `$` price equal to the item's price and 3 or 4 sentences. |
| 5 | Every result matches the requested size | 5 of 5 | MET (5/5) | All results in all five runs had the requested size as a whole token. No run returned an empty list. |

**No criterion was MISSED by its verdict, so there is no miss to diagnose in the strict sense. Three things are still worth saying plainly.**

**1. The one failing try (criterion 1, try 2) is a real defect, and my own criterion predicted the wrong cause.** The query `oversized flannel under $25` stopped early. Place: the query parsing in `agent.py::parse_query` (it runs before any tool, so this is the loop, not a tool and not the model). Mechanism: the size regex was `size\s*[:\-]?\s*([A-Za-z0-9/]+)` with no word boundary, so it matched the "size" inside "over**size**d", took the following "d" as the size, and removed those characters from the description. The search then ran with `description='over flannel', size='d'`, which matches nothing, and the branch (correctly) stopped. In `criteria.md` I justified 4 of 5 by saying a phrasing could miss because the keyword match is not semantic. That was the wrong guess. The keyword match was not the cause here, and the same bug affects any word containing "size" (`sizeable`, `oversized sweatshirt`, `oversized hoodie`).

**2. The diagnostic row shows the all-MET table was partly luck of my query choice.** Of the three phrasing failures, one is the parse bug above. The other two are in `tools.py::search_listings`, step "score by keyword overlap": the match compares whole words, so `sweatshirts` finds nothing for a listing titled "Sweatshirt", and `sneaker` finds nothing for "Sneakers". The five criterion 1 queries happened to use words that appear in the data in the same singular or plural form. I did not change those queries after seeing the diagnostic; the diagnostic is reported next to them.

**3. Targets that were too low.** Criterion 4 was set at 4 of 5 and scored 5 of 5, and every card has the shape the criterion describes, so that target left room I never needed. I would tighten it to 5 of 5 across 10 items. Criterion 1 at 4 of 5 is the one that hid a deterministic bug behind a "tolerance for phrasing" argument; a tighter version is 5 of 5 on queries a user could type whose words appear in the data. What the criterion 4 pass does not show: 19 of the 24 fit cards in this run open with the word "Scored", and no criterion of mine measures that.

**Limits of what my scorers measured** (so the MET verdicts are not over-read):
- Criterion 3 is a wiring check. The session-only evidence could not show what `suggest_outfit` was called with (the trace printed the title, not the id), so I measured it with a spy on the call and, during this unit, added `item_id` to the trace line.
- Criterion 5's queries all return a non-empty list. An empty list would pass vacuously, so the scorer treats it as a FAIL. Waist sizes (`W30`, `W28`) cannot be searched with `size 30`, which no criterion 5 query tried (see What's Still Broken).
- Criterion 4's sentence count splits on `.`, `!` and `?` followed by whitespace, so a decimal price like `$38.00` is not counted as a sentence end.

I did not revise any criterion. `criteria.md` is unchanged.

---

## Failure Modes Triggered on Purpose

All three were triggered by hand, one at a time, in Milestone 2.

**1. Empty search.** `python app.py ask 'designer ballgown size XXS under $5' --trace`. Already handled by the branch from unit 3. It stops after the search and `suggest_outfit` is never called. Message:

```
No listings matched your search. Try loosening the size, raising the price ceiling, or using a broader description.
```

**2. Empty wardrobe.** `python app.py ask 'corduroy pants under $40' --empty-wardrobe --trace`. This one did **not** behave. It did not crash and it was not an empty string, but it was not advice either. Output before the fix:

```
Outfit:   It looks like you forgot to include the list of pieces in your current wardrobe! Reply with the items you already own (tops, shoes, and accessories), and I'll gladly put together 2-3 outfit combinations for those rust corduroy pants.
Fit card: Obsessed is an understatement for these rust corduroy wide-leg pants. Snagged them on Depop for just $32 [...] Now I just need to decide how to style them—drop your favorite outfit ideas below!
```

Cause: the style-memory stretch in `agent.py::run_agent` appends a synthetic "Remembered style preferences" item to the wardrobe, so the wardrobe passed to `suggest_outfit` was no longer empty. `tools.py::suggest_outfit` therefore skipped its general-advice branch, and the model answered the malformed wardrobe prompt by asking for a wardrobe. The fit card was then built on that non-answer. (The trace line said `wardrobe_items=0`, because it counts the original wardrobe. That mismatch is how I noticed.) Handler: style memory is now only folded in when the wardrobe has items. After the fix, `knit vest under $30 --empty-wardrobe`:

```
Outfit:   Layer this argyle vest over a crisp, oversized white or baby blue button-down shirt to lean into the preppy, dark academia aesthetic. Pair it with high-waisted pleated trousers in chocolate brown, charcoal grey, or plaid, and finish the look with chunky loafers or leather oxfords. [...]
```

**3. Model unavailable.** I changed the last character of `GEMINI_API_KEY` in `.env`, ran a query I had not asked before (`low rise cargo under $30`, so it could not be served from cache), then restored the key from a backup copy and confirmed `python test.py` passed again. `generate.py` already raised `ModelUnavailable` and `agent.py` already caught it, but the message was a single line and did not say what had worked. Message now:

```
The search worked (best match: Low-Rise Cargo Pants — Khaki) but the model couldn't be reached, so no outfit or fit card was made. The model rejected your API key. Check GEMINI_API_KEY in your .env file, or create a fresh key at aistudio.google.com. Fix that, then run the same query again.
```

An `MCPError` handler was added in the same place, for when the MCP server cannot start: it says nothing was searched and tells the user to run `python mcp_server.py` on its own.

**Did each message leave the user something to try?** I checked this myself against the three messages rather than in a group. The model message passes (it names the file and the setting). The empty search message passes, but it is generic: it lists size, price and description even when the user gave no size or price. The empty wardrobe case has no message at all because the agent now answers with general advice; the honest limit is that the advice does not tell the user it is general.

---

## Loop Trace

Produced by `python run_eval.py` (`trace.py` called from `agent.py::run_agent`; full copy in `results/run_2026-10-12_0122_after2.md`). `search_listings` and `compare_price` are labelled `(via MCP)` because the calls go through `mcp_client.call_tool` to `mcp_server.py`. `suggest_outfit` and `create_fit_card` are still direct calls.

**Happy path** (`vintage graphic tee under $30`, 5 steps):

```
[1] parse_query
      in:  'vintage graphic tee under $30'
      out: description='vintage graphic tee', size=None, max_price=30.0
[2] search_listings (via MCP)
      in:  description='vintage graphic tee', size=None, max_price=30.0
      out: 10 items: Y2K Baby Tee — Butterfly Print, Graphic Tee — 2003 Tour Bootleg Style, Vintage Band Tee — Faded Grey … +7 more
[3] suggest_outfit
      in:  new_item='Y2K Baby Tee — Butterfly Print', item_id='lst_002', wardrobe_items=10
      out: Pair the Y2K butterfly baby tee with your baggy straight-leg dark wash jeans and chunky white sneakers for an …
[4] create_fit_card
      in:  outfit='Pair the Y2K butterfly baby tee with your baggy straight-leg…', new_item='Y2K Baby Tee — Butterfly Pri…
      out: Found my ultimate Y2K grail on Depop for just $18! Obsessed with the butterfly print and already planning to s…
[5] compare_price (via MCP)
      in:  item='Y2K Baby Tee — Butterfly Print'
      out: average_price=22.0, percent_of_average=81.8, verdict='fair price', compared_to=14
      →    branch: fair price, flagging price
```

**Empty search** (`designer ballgown size XXS under $5`; it has a size, so the retry stretch fires once before the loop stops):

```
[1] parse_query
      in:  'designer ballgown size XXS under $5'
      out: description='designer ballgown', size='XXS', max_price=5.0
[2] search_listings (via MCP)
      in:  description='designer ballgown', size='XXS', max_price=5.0
      out: [] (empty)
      →    branch: empty, retrying without the size filter
[3] search_listings (via MCP), retry
      in:  description='designer ballgown', size=None, max_price=5.0
      out: [] (empty)
      →    retry: still empty without the size filter
No listings matched your search. Try loosening the size, raising the price ceiling, or using a broader description.
```

Without a size in the query the empty trace is 2 steps (parse, search) and then stops. Either way it is visibly shorter than the happy path, and no model step appears.

**On the MCP move:** `mcp_server.py` registers `search_listings` (and, for the stretch, `compare_price`) with a description written for a reader who cannot see the code, typed inputs that match the Tool Inventory (`description: str`, `size: str | None`, `max_price: float | None`), and the empty case stated in the description. `python mcp_client.py` lists both tools. In `agent.py::run_agent` the two direct calls were replaced with `call_tool("search_listings", {...})` and `call_tool("compare_price", {"item": ...})`, and the `(via MCP)` label was added to their trace steps.

Did anything behave differently? The return values did not. Before wiring it, I called the direct function and the MCP tool on four queries (including one with no results) and compared with `==`: all four were identical, an empty result arrives as `[]` rather than `None`, a `None` brand stays `None`, and `compare_price` matched for all 40 listings. The differences I did see are in cost and in errors: every MCP call starts a fresh server process, so each run is slower than the direct call, and there is a new failure mode (the server not starting), which is why I added the `MCPError` handler. The other two tools were left as direct calls.

---

## The Improvement

**What I changed (improvement 1):** `agent.py::parse_query`, one line. The size regex now starts with a word boundary: `\bsize\b\s*[:\-]?\s*([A-Za-z0-9/]+)`. Nothing else was changed for this run. Checked by hand: `oversized sweatshirt` and `sizeable hoodie` now parse to no size, while `tee size M under $20`, `tee, size: L`, `jacket size S/M` and `Size 9 sneakers` still parse as before.

**Which failure it was meant to fix:** criterion 1, try 2 of the before run (`oversized flannel under $25` parsed as `size='d'` and the search came back empty). That was the one failing try in the table, and the same mechanism accounts for the first diagnostic failure (`oversized sweatshirt`). I picked it because it was the only observed failure on a criterion, it had a clear mechanism, and it was a one-line fix.

### Run Log — After

`python run_eval.py --label after` (`results/run_2026-10-12_0115_after.md`). Same scenarios, same queries, same scorers.

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. Matching query completes all three tools | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. Impossible query stops before tool 2 | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. Selected item is the item passed on | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. Fit card has the price once, 2-4 sentences | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 5. Every result matches the requested size | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

| Diagnostic | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Result |
|---|---|---|---|---|---|---|---|
| Phrasing variants | none | PASS | FAIL | FAIL | PASS | PASS | 3/5 |

**Did it help, and how do I know:** Yes, for the thing it targeted. Criterion 1 went from 4/5 to 5/5, and the query that failed before (`oversized flannel under $25`) now completes. The diagnostic row went from 2/5 to 3/5, and the try that changed is `oversized sweatshirt`; the other two failures in that row (`sweatshirts`, `sneaker size 9`) are unchanged, which is what I expected because they have a different cause. Criteria 2 to 5 were unchanged at the same scores. Caveat: it is five tries per row with a model in the loop for the later steps, but the part this change touches (parsing and search) has no model in it, so the 4/5 to 5/5 move is not noise. The change did not make the keyword-matching failures any better, and the criterion 1 queries were not rewritten between runs.

---

## Stretch Features: What Was Built and Measured

Declared in the "Unit 4 Stretch Features" section above before any unit 4 code existed (commit `e571c40`).

### Stretch 1: a second tool moved onto MCP (`compare_price`)

`mcp_server.py` registers `compare_price` alongside `search_listings`, and `agent.py::run_agent` calls it with `call_tool("compare_price", {"item": selected_item})`. A run through the MCP path is the happy path trace above, step 5, `compare_price (via MCP)`. In every run log the compare step ran through MCP without an error. The result matched the direct function for all 40 listings before I wired it.

### Stretch 2: retry with looser constraints

An empty search that had a size filter now retries once without the size (`agent.py::run_agent`, before the branch). The constraint that is dropped is the size filter. The retry shows up in the trace as `search_listings (via MCP), retry` with a note, and the user is told what was dropped (`session["dropped"]`, printed by `app.py`): "Note: nothing matched at first, so I retried without the size filter (nothing was listed in size XXL, so these may be other sizes)." A search with no size does not retry, and an empty retry still stops with the original message.

Run log for it (`results/run_2026-10-12_0117_retry.md`, via `python run_eval.py --label retry --only retry`), scored by `scenarios.py::check_retry` (the run completed, `session["dropped"]` names the size, and a retry step is in the trace):

| Retry scenario | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Result |
|---|---|---|---|---|---|---|---|
| `band tee size XXL` / `denim jacket size XXL` / `flannel size XS` / `cargo pants size XL` / `bucket hat size L` | none | PASS | PASS | PASS | PASS | PASS | 5/5 |

Real output (`python app.py ask 'band tee size XXL under $30' --trace`):

```
[2] search_listings (via MCP)
      in:  description='band tee', size='XXL', max_price=30.0
      out: [] (empty)
      →    branch: empty, retrying without the size filter
[3] search_listings (via MCP), retry
      in:  description='band tee', size=None, max_price=30.0
      out: 5 items: Graphic Tee — 2003 Tour Bootleg Style, Vintage Band Tee — Faded Grey, Y2K Baby Tee — Butterfly Print … +2 more
      →    retry: dropped the size filter (XXL)
  Note: nothing matched at first, so I retried without the size filter (nothing was listed in size XXL, so these may be other sizes).
```

**It has a cost, and it cost me a criterion.** See the third run log below: this stretch is what turned criterion 2 from 5/5 into 4/5.

### Stretch 3: a second measured improvement

**What I changed (improvement 2):** `tools.py::search_listings` now compares words by singular form: a small `_singular()` helper strips a trailing "s" from words longer than three letters that do not end in "ss", on both the description words and the listing words. It is inside the tool that is exposed over MCP, so the MCP tool changed with it.

**Which failure it was meant to fix:** the two keyword-match failures in the phrasing-variants diagnostic that improvement 1 did not touch: `sweatshirts` (listing titled "Sweatshirt") and `sneaker size 9` (listing titled "Sneakers"). Mechanism from the diagnosis: whole-word overlap, no plural handling.

### Run Log — After (improvement 2, third run log)

`python run_eval.py --label after2` (`results/run_2026-10-12_0122_after2.md`). This run includes the retry stretch as well as improvement 2, because the retry was built before it.

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. Matching query completes all three tools | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. Impossible query stops before tool 2 | 5 of 5 | PASS | PASS | PASS | PASS | FAIL | MISSED (4/5) |
| 3. Selected item is the item passed on | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. Fit card has the price once, 2-4 sentences | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 5. Every result matches the requested size | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

| Diagnostic | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Result |
|---|---|---|---|---|---|---|---|
| Phrasing variants | none | PASS | PASS | PASS | PASS | PASS | 5/5 |
| Retry without size (stretch) | none | PASS | PASS | PASS | PASS | PASS | 5/5 |

**Did it help, and how do I know:** The improvement did what it was for: the phrasing-variants diagnostic went from 3/5 (after improvement 1) to 5/5, and the two tries that changed are `sweatshirts` and `sneaker size 9`. I know the plural change is the cause because those two queries have no size filter or have a size that matches, so the retry cannot have helped them, and I checked directly that `sweatshirts` and `sneaker size 9` now each return 1 result. Criteria 1, 3, 4 and 5 stayed at the same scores.

**But this run also has a regression, and I am reporting it as a miss.** Criterion 2 went from MET (5/5) to **MISSED (4/5)**. The failing try was `leather bomber size XXS` (try 5). It is not caused by the plural change. It is caused by the retry stretch:

```
[2] search_listings (via MCP)
      in:  description='leather bomber', size='XXS', max_price=None
      out: [] (empty)
      →    branch: empty, retrying without the size filter
[3] search_listings (via MCP), retry
      in:  description='leather bomber', size=None, max_price=None
      out: 4 items: 90s Leather Bomber — Black, Platform Mary Janes — Black Patent, Leather Belt — Brown, Braided … +1 more
      →    retry: dropped the size filter (XXS)
[4] suggest_outfit
      in:  new_item='90s Leather Bomber — Black', item_id='lst_022', wardrobe_items=10
```

Place: the loop's branch in `agent.py::run_agent`. Mechanism: I chose that query as "impossible" because no listing is in size XXS. The retry drops exactly that constraint, finds a leather bomber in size M, and carries on through `suggest_outfit` and `create_fit_card`, so the agent does not stop before the second tool. The criterion says "a query that matches no listings", and my query matched no listings only while the size filter was hard. I predicted before building the retry that it would not affect criterion 2, and I was wrong, because one of my five impossible queries was impossible only by size. The other four are impossible by description or by price, and the retry correctly did not rescue them. I have not revised criterion 2 and I have not changed the query. The two behaviours are in tension and I kept the retry; see What's Still Broken.

---

## What's Still Broken

- **Criterion 2 is MISSED (4/5) in the current agent** (see the third run log). What I would do: make the retry visible to the criterion by treating a retry that found something as a "completed with a dropped constraint" run rather than an impossible query, or ask the user before dropping the size instead of retrying automatically, which is also the more honest behaviour (a size XXS shopper is being shown a size M jacket). I stopped because both options are a design change to the loop and the unit's rule was that the improvement and the stretches are the only changes. I think asking the user is the right fix.
- **Waist sizes cannot be searched by number.** `jeans in size 30` returns nothing because the data stores `W30`, `W28` and so on, and the size match is whole-token. I found this with a probe query, not in any criterion run. What I would do: normalise `W30` to also match `30`. I stopped because it is untested by my five criteria and I wanted one change per run log.
- **Search quality is still keyword overlap with a crude plural strip.** `sweatshirts` works now, but synonyms (`hoodie` vs `sweatshirt`, `trousers` vs `pants`) and brand misspellings (`levis` only worked because "Levi's" splits to `levi` and `s`) do not. Stop words in the description (`in`, `something`, `for`) also count toward the score. I would add a small synonym map, not a model call.
- **Fit cards are not varied.** 19 of the 24 cards in the before run open with "Scored" (26 of 36 in the last run), and the price/sentence-count criterion is blind to it. I would write a criterion for opening-sentence variety and then change the prompt; I did not, because it was not one of my five and the unit asked for a change that follows from a miss.
- **Empty wardrobe advice does not say it is general.** The fix stops the model asking for a wardrobe, but the user is not told that the advice is not based on anything they own. The fit card also sometimes mentions pieces the user does not have ("my favorite combat boots") when the wardrobe was empty.
- **The empty-search message is generic.** It lists size, price and description every time, even if the user gave no size or price.
- **My scorers can be wrong too.** `check_fit_card` splits sentences on punctuation, so a caption ending in an emoji or hashtag run is counted as part of its last sentence. Nothing in these runs hit that edge, but I have not tested it.

---

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
