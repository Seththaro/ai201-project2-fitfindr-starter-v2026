# Acceptance criteria — FitFindr

Five criteria that say what "working" means for this agent, written in unit 3
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"The agent handles errors"* is an opinion.
*"When search returns nothing, the agent stops before calling the second tool,
in 5 of 5 tries"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter one. A reason that says something about your tools, your loop, or the
data earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

**Two are written for you. You write three.**

---

## 1. A matching query completes all three tools

Given a query that matches at least one listing, the agent completes all three
tool calls and returns a fit card — in at least 4 of 5 tries.

**Why this target:**
<!-- Why 4 of 5 and not 5 of 5? Something about your search, probably —
     "my search is a plain keyword match and some phrasings will miss" is a
     real answer. -->

---

## 2. An impossible query stops before the second tool

Given a query that matches no listings, the agent stops before calling
`suggest_outfit` and returns a message naming what to change — 5 of 5 tries.

**Why this target:**
<!-- Why is 5 of 5 reasonable here when criterion 1 isn't? What's different
     about this path? -->

---

## 3. Something about state

`session["selected_item"]["id"]` matches the `id` of the listing dict named in
`session["outfit_suggestion"]` (i.e. the item `suggest_outfit` was actually
called with, confirmed via `trace.step`'s `in:` line for that call) — 5 of 5
tries.

**Why this target:**
This is a wiring check, not a model-quality check — either the id that went
into `suggest_outfit` matches `selected_item` or it doesn't, there's no partial
credit and no run-to-run variance to account for, so 5 of 5 is the only
honest target. `agent.py::run_agent` reads `selected_item` out of the session
and passes that same object into `suggest_outfit`, so a failure here would
mean the session plumbing itself is broken, not that the model did something
unexpected.

---

## 4. Something about the fit card

For 5 different items run through `create_fit_card`, each caption mentions
the item's price (as `$` followed by the numeral) exactly once and is between
2 and 4 sentences — 4 of 5 tries.

**Why this target:**
4 of 5 and not 5 of 5 because the prompt *asks* the model to mention the price
once, but doesn't force it structurally — at TEMPERATURE 0.9 the model has
room to phrase things in a way that drops the numeral (e.g. spelling out
"eighteen dollars") or run a sentence long enough to blur the count. The
content is allowed to vary every run — that's the point of temperature — but
the structural shape (price present, sentence count in range) is what's
actually checkable and worth holding to a near-perfect target.

---

## 5. Your choice

Given a query with an explicit `size` token (e.g. "size M"), every listing in
`search_listings`'s returned list has that size token as one of its
whitespace/slash/hyphen-separated size tokens (e.g. "M" matches "S/M" but not
"US 9" or "XL") — 5 of 5 tries, across 5 different size values.

**Why this target:**
I picked this because the size-matching logic is the one place in
`search_listings` where a naive implementation (plain substring matching)
silently produces wrong results without ever raising an error — `"s" in "us 9"`
is `True` in Python, so an unguarded filter would return shoes when someone
asked for a small top. Since my implementation tokenizes the size string
instead of substring-matching, this should be exactly correct every time with
no model variance involved, so 5 of 5 is the honest target.



---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 4 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 4. Something about the fit card

         The fit card is different every time.

         **Why this target:** ...

         > **Revised in unit 4:** For 5 different items, the 5 fit cards share
         > no opening sentence.
         >
         > **Why revised:** "different" wasn't checkable — two cards that
         > differed by one word still counted. The new version is something I
         > can actually score.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said the empty search stops it 5 of 5 times, but I got 3 of 5,
            so 3 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->
