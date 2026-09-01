# Ideas log

One entry per daily improvement cycle. Newest last.

## 2026-08-02 — CSV export of the filtered trip registry

**Shipped.** A "Download CSV" button in the Registry section head exports exactly the rows
currently in view, honouring every active filter. Columns: `start_date`, `end_date`,
`itinerary`, `countries`, `country_count`, `visit_type`, `days`, `prime_minister`,
`source_tier`. RFC 4180 quoting, CRLF line endings, UTF-8 BOM so Excel renders accented
country names. Filename carries the export date and a `_filtered` marker when filters are
active. Button disables itself with an explanatory `aria-label` when the view is empty.

Why this one: the site's audience is journalists and researchers, and it promised "open data"
while only offering raw JSON. CSV is the format that audience actually works in, and the
filter state was already computed — the feature is pure read-side leverage on existing code.

**Runners-up**
- *Drawer focus trap* — the trip drawer sets `aria-modal="true"` but Tab still escapes to the
  page behind it. A genuine a11y defect and a strong candidate for a near-term day; lost only
  because it fixes a smaller surface than the export opens up.
- *Defer the Plotly load* — a ~3.5 MB CDN script blocks first render in `<head>`. Real perf
  win, but chart init ordering makes it riskier than a one-day slot should carry. Deserves its
  own cycle.
- *Screen-reader data tables behind each chart* — charts expose `role="img"` labels but no
  underlying numbers. High a11y value, bigger job than one day.
- *Sortable registry columns* — the six charts already cover most analytical questions.
- *robots.txt + sitemap.xml + canonical* — 10 minutes of work, marginal payoff for a
  single-page site.
- *"Copy link to this view"* — URL state already syncs to the address bar; low added value.

**Noted, not acted on:** `normalizeTrips` splits itineraries on `&` and `and`, so
"Trinidad & Tobago" becomes two countries. This predates today's work and affects the charts,
tags, and now the export equally — the export deliberately mirrors what the site displays.
Worth its own cycle, and it touches data interpretation, so it needs a deliberate decision.

**Files touched:** `index.html`

## 2026-08-04 — Make the trip drawer a real modal dialog

**Shipped.** The drawer declared `role="dialog"` and `aria-modal="true"` but did none of what
that promises: measured with the drawer open, **71 focusable elements behind it were still
reachable by Tab**, the page scrolled behind the scrim, and the background stayed in the
accessibility tree. Now, while the drawer is open, every direct child of `<body>` except the
drawer and its overlay gets `inert` (removing it from tab order, pointer events, and the a11y
tree), body scroll is locked with a scrollbar-width gutter so nothing shifts, and Tab /
Shift+Tab cycle within the drawer. Un-inerting happens before focus returns to the triggering
row, since `focus()` inside an inert subtree is silently ignored.

Why this one: it was the top runner-up on day one and it is a defect, not a wishlist item —
the markup was making an accessibility promise the behaviour didn't keep. Fixing a broken
contract beats adding a fourth feature on top of it. It also unblocks a per-trip permalink
later; deep-linking into a dialog that leaks focus would have compounded the problem.

**Runners-up**
- *Per-trip permalink (`?trip=<id>` opens the drawer)* — genuinely useful for journalists
  citing a specific trip, and the strongest feature idea in the list. Deliberately sequenced
  after this fix rather than before it.
- *Defer the blocking Plotly CDN load* — still the biggest perf win available (~3.5 MB in
  `<head>`); chart init ordering makes it its own cycle.
- *Screen-reader data tables behind each chart* — charts expose `role="img"` labels but no
  numbers. Bigger than one day.
- *Sortable registry columns* — the six charts already answer most analytical questions.
- *Print stylesheet for the registry* — the deliberate opposite of the obvious pick; real but
  niche demand.
- *robots.txt + sitemap.xml + canonical* — quick, low payoff for a single-page site.

**Verification:** focus leakage 71 → 0; forward and backward Tab wrap confirmed, mid-list tabs
not intercepted; Escape and overlay-click both close and fully clean up; three open/close
cycles leave no residual `inert` or scroll lock; CSV export, filters, and all six charts
unaffected; no horizontal scroll at 375px; console clean. Three fallback tiers untouched.

**Files touched:** `index.html`

## 2026-08-07 — Per-trip permalink (`?trip=<slug>` deep-links the drawer) + copy-link button

**Shipped.** Opening a trip's drawer now pushes `?trip=<slug>` to the address bar; loading that
URL directly (or via back/forward) opens the same drawer, honouring the focus trap and
background-inert behaviour shipped on 08-04. A "Copy link to this trip" button was added next
to the existing registry link so journalists citing a specific trip don't have to rely on
spotting the address bar on mobile — it copies via the Clipboard API with a `document.execCommand`
fallback, and confirms via both a visible label change and an `aria-live` region.

The identifier is a content-derived slug (`start-date--slugified-label`), not the existing
positional `id` (`array-index + 1`). Checked: `id` is assigned during `normalizeTrips` from each
trip's position in `data/visits.json`, which is already newest-first — so a new trip landing at
the top of tomorrow's pipeline refresh would shift every other trip's `id` down by one, silently
retargeting any `id`-based permalink shared today. The slug is immune to that: it's derived from
the trip's own immutable `start`/`label` fields, so it survives any reordering or insertion
elsewhere in the array. `id` itself is untouched for any other future use.

Why this one: called "the strongest feature idea in the list" in both prior logs, and
deliberately sequenced after the 08-04 focus-trap fix so a deep link wouldn't open into a
dialog that leaked focus. It's pure read-side logic over data already in memory — no new
dependency, no data-provenance touch — and directly serves the site's stated audience
(journalists citing a specific trip).

**Runners-up**
- *Defer the blocking Plotly CDN load* — still the biggest perf win (~3.5 MB in `<head>`);
  chart-init ordering makes it risky enough to want its own cycle, not a rider on today's idea.
- *Screen-reader data tables behind each chart* — charts expose `role="img"` labels but no
  underlying numbers. High a11y value, bigger than one day.
- *Sortable registry table columns* — real, but the six charts already answer most of the
  analytical questions a sort would serve.
- *robots.txt + sitemap.xml + canonical link* — quick, but marginal payoff for a single-page
  site with one real URL.
- *"Days since last foreign trip" / longest-gap stat* — a genuinely new way to read the data,
  but a fresh analytical claim needs more care before shipping than a one-day slot affords.

**Verification:** row click → drawer opens, URL gains `?trip=<slug>`; copy-link button places
the exact permalink on the clipboard and announces it via the live region; Escape/overlay-click
closes and strips the param, restoring focus to the triggering row; loading the captured
permalink cold opens the correct drawer with the background properly inert and focus on the
close button; browser back/forward correctly open and close the drawer in step with the URL;
an unknown `?trip=` slug loads the page normally with no error and no drawer. All six charts
render, CSV export and filters unaffected, no horizontal scroll at 375px, console clean (bar an
unrelated Plotly world-topojson CDN fetch this sandbox's network policy blocks — pre-existing,
untouched by this change, will resolve on the real network). Three fallback tiers untouched;
tested against tier 1 (`data/visits.json`) since tiers 2/3 weren't reachable in this sandbox,
but the deep-link/copy-link logic runs identically after any tier populates `trips`.

**Files touched:** `index.html`

## 2026-08-08 — Accessible data tables behind each chart

**Shipped.** All six analysis charts get a collapsed `<details>` disclosure — "View data table
(N rows)" — holding the exact numbers Plotly is plotting: country + visit count for the map,
month/trips/countries for the timeline, the top-15 list for the ranking bar, PM/trips/countries
for the comparison, year/single/multi/total for the year-over-year bars, and a full year×month
grid for the calendar heatmap. The charts kept `role="img"` with a one-line `aria-label`, but
that label was the entire experience for a screen-reader user or anyone whose browser doesn't
run the ~3.5 MB Plotly bundle — no route to the underlying numbers existed at all. Each table
reuses the same array already computed for its chart, so there's no new data derivation, just a
second render target for numbers already in memory. Tables regenerate on every filter change
like the charts do, and an open table stays open across a filter change instead of silently
re-collapsing.

This was flagged as high-value and passed over as "bigger than one day" in the 08-02, 08-04, and
08-07 logs. Re-scoped down to exactly this — no chart redesign, no new toggle-button UI system,
just a native `<details>` + a plain `<table>` per panel using data the charts already have — it
fit in a day.

**Bug caught in verification, fixed in the same commit:** the calendar-heatmap table has 13
columns (year + 12 months) and, once opened at 375px, pushed the *whole page* into horizontal
scroll even though its own wrapper had `overflow-x: auto`. Cause: CSS Grid items default to
`min-width: auto`, so a wide child can force its grid track wider than the viewport before the
child's own overflow rule ever gets a chance to contain it. Added `min-width: 0` to `.panel`;
confirmed the page-level scroll disappears while the table's own internal scroll still works.

**Runners-up**
- *Defer the blocking Plotly CDN load* — still the biggest perf win (~3.5 MB in `<head>`);
  chart-init ordering makes it its own cycle, not a rider on today's idea.
- *Sortable registry table columns* — real, but the six charts (now with number tables) already
  answer most of the analytical questions a sort would serve.
- *robots.txt + sitemap.xml + canonical link* — quick, marginal payoff for a single-page site.
- *Registry column visibility toggle for narrow screens* — mobile polish, but the table already
  scrolls horizontally inside its own container; lower urgency than the a11y gap.

**Verification:** this sandbox's network policy blocks `cdn.plot.ly` outright (confirmed via
the proxy status endpoint — same class of restriction noted for `r.jina.ai` in the 08-07 log),
so Plotly itself can't load here. Verified the new code by stubbing `Plotly.react`/`newPlot`
locally and driving the real page through Playwright: all six wrap containers get a populated
`<details>`/`<table>` with correct headers, row counts, and captions; toggling one table open
and then changing a filter leaves it open (state-preservation works); no page-level horizontal
scroll at 375px before or after opening the widest (13-column) table; dark mode renders the
disclosure and table with the same tokens as the rest of the page; `node --check` on the
extracted inline script confirms no syntax errors; console clean of anything but the
pre-existing, sandbox-only CDN blocks. Both other fallback tiers (live mirror, embedded
snapshot) are untouched — this change only reads from `rows`, the already-normalized in-memory
trip list, regardless of which tier populated it.

**Files touched:** `index.html`

## 2026-08-09 — Defer the blocking Plotly CDN script, gate chart renders on readiness

**Shipped.** The ~3.5MB Plotly bundle was loaded synchronously via a plain `<script src>` in
`<head>`, blocking first paint on every visit. This was named the single biggest performance
win in the 08-02, 08-04, and 08-07 logs and passed over each time because a naive fix looked
risky: the page's main inline script runs (and calls into Plotly) during initial parsing,
*before* a deferred external script gets a chance to execute, so simply adding `defer` without
more would call `Plotly.react` before `Plotly` exists.

Solved it at the actual dependency edge instead of guessing at load order: the script tag now
carries `defer`, and a `plotlyReady` promise (resolved by the script's `load` or `error` event)
gates `renderCharts()` — the single function every one of the 6 charts and their data tables
already funnels through. Two lines at that one choke point were enough; no chart-by-chart
changes, no new dependency.

**Runners-up**
- *Sortable registry table columns* — real, but the six charts (with number tables since 08-08)
  already answer most of what a sort would serve.
- *robots.txt + sitemap.xml + canonical link* — quick, marginal payoff for a single-URL site;
  rejected on the same grounds twice already (08-04, 08-07).
- *"Days since last foreign trip" stat* — a genuinely new way to read the data, but a fresh
  analytical claim needs more design care than a one-day slot affords; still open.
- *Registry column visibility toggle for narrow screens* — mobile polish, but the table already
  scrolls horizontally in its own container; lower urgency than the perf fix.
- *Drawer Tab focus trap* — checked the code before brainstorming further; this shipped
  silently as part of the 08-04/08-07 modal work (`trapDrawerTab`, wired to the drawer's
  `keydown`) and is no longer an open item.

**Verification:** `node --check` on both inline scripts. Playwright against the real page
(`cdn.plot.ly` is blocked in this sandbox, so its requests were routed to a stub) at 1280px and
375px: page chrome (KPIs, filters, registry) renders before Plotly has loaded, proving the load
is genuinely non-blocking; all 6 charts and their accessible data tables populate correctly once
Plotly loads, including under a simulated 400ms slow load; a filter change after Plotly is
already loaded still re-renders correctly; no horizontal scroll at either width. Simulated a
total CDN failure (`route.abort`) — the page now fails loudly with one clear console error
(`Plotly is not defined`) and the rest of the page (KPIs, registry, filters) keeps working,
which is *more* correct than the old blocking script's failure mode: previously a CDN failure
threw synchronously inside tier 1's `render()` call, inside its `try` block, so it would've been
misdiagnosed as a data-fetch failure and cascaded into tier 2 needlessly. That's a side effect
of gating on the promise, not a scope change — the fallback-tier logic itself is untouched.
Console clean of anything but the pre-existing, sandbox-only Google Fonts network block (unrelated
to this change, same class of restriction noted for `cdn.plot.ly`/`r.jina.ai` in prior logs).

**Files touched:** `index.html`

## 2026-08-10 — Fix compound country names being split into two countries

**Shipped.** `normalizeTrips`'s itinerary-label splitter treated every "and"/"&" as a
separator between destinations. Official country names that contain "and"/"&" — e.g.
"Trinidad and Tobago" — got torn in two. Confirmed this isn't hypothetical: `data/visits.json`
already carries "Ghana, Trinidad & Tobago, Argentina, Brazil & Namibia" (2025-07-02), and the
site was silently counting it as 6 countries instead of 5, listing bogus "Trinidad" and
"Tobago" entries in the country filter and registry tags, inflating the "Unique countries" KPI,
and (since Plotly's choropleth uses `locationmode: 'country names'`, which doesn't recognize
"Trinidad" or "Tobago" alone) almost certainly dropping that leg from the map entirely. The
`COORD_ALIAS` table for the flight-globe visual already had a band-aid mapping `trinidad` and
`tobago` back together — evidence this was known-broken in one view and silently wrong
everywhere else.

Fix: a small allowlist of official compound-name countries (Trinidad and Tobago, Antigua and
Barbuda, Bosnia and Herzegovina, Saint Kitts and Nevis, Sao Tome and Principe, Turks and Caicos
Islands, Saint Vincent and the Grenadines, Wallis and Futuna) is protected before the splitter
runs and restored after, in the canonical "and" form Plotly's country-name matching expects.
Updated the one `COORDS`/`COORD_ALIAS` entry that had been hand-patching around the bug. Pure
display-layer parsing fix — reads `data/visits.json`, doesn't touch it or the refresh pipeline.

Flagged in the 2026-08-02 log ("Noted, not acted on... worth its own cycle") and left alone
since — today's brainstorm turned up nothing more urgent, and finding it live in the current
data made the case concrete rather than theoretical.

**Runners-up**
- *Sortable registry table columns* — real, but named a lower-value analytical aid than
  correctness in the underlying counts feeding every chart, KPI, and export; still open.
- *robots.txt + sitemap.xml + canonical link* — rejected on the same "marginal payoff for a
  single-page site" grounds as the 08-04/08-07 logs.
- *Registry column visibility toggle for narrow screens* — mobile polish; the table already
  scrolls horizontally in its own container.
- *"Copy as citation" button on the trip drawer* — fresh idea, genuinely useful for
  journalists, but a live correctness bug in the numbers themselves outranks a new convenience
  feature.

**Verification:** unit-tested the new splitter against every real itinerary label currently in
`data/visits.json` plus synthetic compound-name cases — the Trinidad trip now yields exactly
`["Ghana","Trinidad and Tobago","Argentina","Brazil","Namibia"]` (5, not 6); every other label
(multi-country tours joined by "&", "and", and Oxford-comma "and") splits identically to before.
Playwright against the served page: country filter dropdown now offers "Trinidad and Tobago"
with no stray "Trinidad"/"Tobago" entries; KPI "Unique countries" and the trip's registry tags,
drawer ("Destinations: 5"), and CSV export (`country_count` column) all agree; CSV `countries`
field renders `Trinidad and Tobago` as one semicolon-delimited entry. `node --check` on both
inline scripts. No horizontal scroll at 375px, dark-mode toggle unaffected, console clean bar
the pre-existing sandbox-only `cdn.plot.ly`/Google Fonts network blocks. All three fallback
tiers untouched — the fix sits in `normalizeTrips`, shared by every tier.

**Files touched:** `index.html`

## 2026-08-11 — Sortable registry table columns

**Shipped.** The six "Dates / Itinerary / Countries / Type / Days / PM" registry headers are
now click-to-sort buttons: first click sorts descending for numeric-feeling columns (Dates,
Countries, Days — "biggest/newest first") and ascending for text columns (Itinerary, Type, PM
— A→Z); a second click on the same header flips direction. Each `<th>` carries a live
`aria-sort` (`ascending`/`descending`/`none`) and a `▲`/`▼`/`↕` indicator, and because the
control is a real `<button>`, Enter/Space activation and focus styling come for free — no new
keydown handler needed. `Source` stays unsortable (a status tag, not a data dimension). Sort
state persists across filter changes and survives "Reset filters" (that button resets filters,
not table order — the two are independent controls). Default state (`start`, descending)
reproduces the table's pre-existing order exactly, so nothing changes until a user clicks a
header.

This is the single most-repeated open item in this log — named a real, valuable idea and passed
over as a runner-up in the 08-02, 08-04, 08-07, 08-08, and 08-09 entries, each time because
something else (a correctness bug, an a11y defect, a perf fix) edged it out on that day's
priority call. Nothing in today's fresh brainstorm out-ranked it, so it finally got its slot.

**Runners-up**
- *"Copy citation" button on the trip drawer* — flagged fresh in the 08-10 log; a real
  trust/citation win for the stated journalist/researcher audience, but the sort backlog is now
  five logs deep and outranks a new convenience feature. Still open.
- *"Longest gap between trips" fact* — a genuinely new way to read the data, but (as noted in
  08-07) a fresh analytical claim needs more definitional care (what counts as a "gap"?) than a
  header-sort mechanic does. Still open.
- *robots.txt + sitemap.xml + canonical link* — rejected a fourth time on the same "marginal
  payoff for a single-URL site" grounds as 08-02/08-04/08-07/08-08.
- *Registry column visibility toggle for narrow screens* — mobile polish; the table already
  scrolls horizontally in its own container, so lower urgency than clearing the sort backlog.
- *Data-caveats/limitations panel* (documenting known parsing edge cases like the 08-10 compound-
  country fix) — genuine trust value, but passive documentation ranks below a working feature
  the log has wanted for nine days.

**Verification:** Playwright against the served page (Plotly stubbed; `cdn.plot.ly` is blocked
in this sandbox) at 1280px and 375px. Clicking `Days` sorts descending first (`[8,7,7,6,6,…]`),
a second click reverses to ascending; clicking `PM` (a fresh column) defaults to ascending, and
that state survives a subsequent filter change (`aria-sort="ascending"` persists after switching
Visit type to Multi-country). Focusing the `Itinerary` header via keyboard and pressing Enter
sorts alphabetically and updates `aria-sort` — confirms the native `<button>` needs no bespoke
keydown code. Clicking "Reset filters" clears filters but leaves the active sort untouched, as
intended. All 6 charts still initialize via `Plotly.react`, all 5 KPI cards render, dark-mode
toggle and re-render leave the active sort intact, and the drawer still opens correctly from a
re-sorted row. No horizontal scroll at 375px. `node --check` on both inline scripts. Console
clean bar the pre-existing, sandbox-only Google Fonts network block. All three fallback tiers
untouched — sorting is a pure display-layer step applied in `render()`/`handleSortClick()` on
`rows`, the already-normalized in-memory trip list, regardless of which tier populated it.

**Files touched:** `index.html`, `ideas-log.md`

## 2026-08-11 — Fix article dating in Latest coverage (directed fix, not a cycle pick)

**Problem, and it was not the one reported.** The brief assumed dates were hardcoded and RSS
`pubDate` parsing was missing. Neither was true — the pipeline already parsed `pubDate` and the
page already rendered each article's own date. The real fault is upstream: **Google News search
feeds serve a different `pubDate` for the same article URL on different days.** One URL, measured:

| fetched | Google's pubDate |
|---|---|
| 2026-08-03 | 2026-08-02 |
| 2026-08-10 | 2026-08-09 |
| 2026-08-11 | 2026-08-10 **and** 2026-05-29 — both, same run, two query feeds |

`pubDate` tracks cluster freshness, not publication. That is how a finished tour's coverage
appeared as today's reporting on the next one: "PM Modi to be on 6-day visit to UAE, Netherlands,
Sweden, Norway & Italy" was filed under an Israel/Sweden trip a week later. The two "Sweden"
articles corroborating that trip were first seen 2026-07-12 — a month old, restamped as current.

**Consequently the requested 14-day window would not have fixed it** and is not what shipped: a
14-day window is wider than the gap between consecutive PM tours, so it re-admits exactly the
stale coverage in question. Two mechanisms shipped instead:

1. *Dates only ever revise downward.* Dedupe by URL keeping the earliest `pubDate` across feeds,
   plus a first-seen ledger (`news.json` → `seen`, url digest → earliest date ever recorded), so a
   date Google later inflates cannot drift up. Seeded from this file's own git history (58 URLs).
   Cross-feed disagreement is itself proof the date is unreliable, so the conservative bound is the
   honest one. Where a date was revised, the card shows `*` with the reason on hover/`aria-label`
   rather than printing a confident guess.
2. *Relevance, not just recency.* An article must name a country of the current trip as a
   destination and must not name more non-trip destinations than trip ones — which is what stops a
   five-nation-tour headline being filed under a two-country trip sharing one leg.

`parse_pubdate` now uses the stdlib RFC 2822 parser, so `+0530` offsets convert to UTC instead of
being dropped (it previously handled only GMT/UTC literals and truncated at 31 chars). Client-side
re-validation is a second line of defence over a stale or hand-edited `news.json`: window re-check,
ISO-string comparison (no `Date`, no timezone drift), dedupe, invalid dates skipped, newest first,
`data-article-date`/`data-date-source`/`data-trip` attributes, an empty state, and a collapsed
console group logging every INCLUDED/FILTERED decision with counts.

**Effect on today's output:** 6 articles → 3, all genuine 9 Aug Israel coverage; the trip reads
"Israel" rather than "Israel & Sweden", because Sweden's corroboration was entirely re-dated
month-old articles. Trip detection is date-driven, so correcting dates necessarily changes it.
The ledger keyed on full URLs would have made `news.json` 220 KB — a file the browser fetches on
every load — so it keys on a 12-hex digest, retained 120 days and capped: 18.8 KB.

**Not done, deliberately:** per-trip coverage for historical trips. The brief's "Feb trip shows
only Feb articles" implies a news archive per trip; the site has one coverage block for the current
focus trip and no per-trip news exists to filter. Building that means fetching news per trip across
100+ trips — its own cycle, not a rider on a date fix.

**Guardrail note:** this touched `scripts/refresh.py`, which CLAUDE.md fences off. The request
explicitly asked for the news-fetching fix, and the change is confined to the news path — registry
parsing, `visits.json`, the workflow, and the three fallback tiers are untouched.

**Verification:** 38 assertions in `scripts/test_news_dates.py` (offsets, leap day, invalid dates,
earliest-wins, ledger direction, future-date clamping, window boundaries inclusive, relevance
gate, dedupe, ordering) all pass; in-browser checks of the reported scenario (Feb + stale-Aug-2
articles under an Aug-9 trip → both dropped), a May 15–20 registry trip, malformed payloads
(nulls, `2026-02-30`, missing URLs) with no console errors, empty state, derived window for an
older `news.json`; 44 trip rows, 5 KPIs, 6 charts, filters, reset and CSV all unaffected; no
horizontal scroll at 375px; dark mode verified.

**Files touched:** `scripts/refresh.py`, `scripts/test_news_dates.py` (new), `index.html`,
`data/news.json`

## 2026-08-12 — "Copy citation" button on the trip drawer

**Shipped.** The trip drawer's action list gets a second button next to "Copy link to this
trip": "Copy citation", which copies a ready-to-paste, Chicago-style web citation to the
clipboard — publisher, quoted trip label and date range, access date, the trip's existing
permalink, and the underlying source (`pmindia.gov.in`). E.g.:

> India PM Foreign Visits Tracker, "France & Slovakia, 13–18 Jun 2026," accessed 12 August
> 2026, https://…?trip=2026-06-13--france-and-slovakia. Source data: PM India
> Foreign/Domestic Visits registry (pmindia.gov.in).

Plain text, not a formatted `<cite>` block — it needs to survive a paste into a footnote, a
Slack message, or a terminal alike. Confirms via the same visible label-swap + `aria-live`
pattern as the existing copy-link button, and reuses its clipboard-with-textarea-fallback
logic (extracted into a shared `copyToClipboard`/`flashCopied` pair rather than duplicated).

This is the most-repeated open item in the log after the sort backlog cleared 08-11: flagged
fresh in 08-10 ("genuinely useful for journalists... a live correctness bug... outranks a new
convenience feature") and again in 08-11 ("a real trust/citation win for the stated
journalist/researcher audience... still open"). Nothing fresher outranked it today, and it's
pure read-side logic over data already in memory plus the permalink infrastructure shipped
08-07 — no new dependency, no data-provenance touch, and a citation string is inherently
neutral (label, dates, PM name, source) so it carries no non-partisan-framing risk.

**Runners-up**
- *Data-caveats/limitations panel* (documenting parsing edge cases like the 08-10 compound-
  country fix) — genuine trust value, flagged again in the 08-11 log, but passive
  documentation still ranks below a working feature two logs have asked for by name.
- *"Longest gap between trips" fact* — a genuinely new way to read the data, open since 08-07,
  but still needs more definitional care (what counts as a "gap" — same PM only? any PM?) than
  a one-day slot affords cleanly.
- *Missing favicon / apple-touch-icon* — fresh find: the page has OG/Twitter images and a
  JSON-LD dataset block but no `<link rel="icon">` at all, so every browser tab and bookmark
  is unbranded. Real, but smaller and lower-stakes than the citation backlog.
- *Registry column visibility toggle for narrow screens* — mobile polish; the table already
  scrolls horizontally in its own container, unchanged priority from prior logs.
- *robots.txt + sitemap.xml + canonical link* — rejected on the same "marginal payoff for a
  single-URL site" grounds as every prior log (08-02/04/07/08).

**Verification:** `node --check` on both inline scripts. Playwright against the served page
(Plotly stubbed; `cdn.plot.ly` blocked in this sandbox) at 1280px, 375px, and both themes:
opening a trip and clicking "Copy citation" places the exact expected string on the clipboard,
flips the button label to "Citation copied" and the `aria-live` region to match, and reverts
after 1.8s — independently of the adjacent "Copy link" button (clicking one doesn't touch the
other's label or timer, confirming the per-button timer fix in the shared helper). All 44
registry rows render, all 6 charts initialize, filters/sort/CSV unaffected, no horizontal
scroll at 375px, dark mode renders both drawer buttons identically to light. Console clean bar
the pre-existing, sandbox-only Google Fonts block. All three fallback tiers untouched — the
citation is built entirely from the in-memory `trip` object already used by the open drawer.

**Files touched:** `index.html`

## 2026-08-13 — Data-caveats panel documenting parsing rules

**Shipped.** The Methodology section gets a new "Reading the numbers correctly" subsection: five
collapsed `<details>` disclosures explaining how the page turns registry text into the counts
everything else is built on — how "Multi-country" vs "Single-country" is decided (itinerary
country count > 1), how itineraries are split into countries (`&`/"and", with the compound-name
allowlist from the 08-10 fix), how trip duration is counted (inclusive of both stated dates),
how "Reportedly abroad now" trips are excluded from every KPI/chart/export until the official
registry lists them, and the conservative-only-revise-earlier rule for "Latest coverage" article
dates (from the 08-11 news-dating fix). Reuses the existing `.chart-data` disclosure-triangle CSS
pattern for visual consistency; pure documentation of parsing logic already in `normalizeTrips`
and the news pipeline — no new derivation, no code-path changes, no data touch.

This is the single most-repeated open item in the log after the sort and citation backlogs
cleared: flagged in 08-10 ("worth its own cycle"), 08-11 ("still open"), and 08-12 ("still ranks
below a working feature two logs have asked for by name") — three separate days named it "genuine
trust value" and passed it over. Nothing fresher in today's brainstorm outranked it, it directly
serves "trust and credibility signals" (one of CLAUDE.md's named dimensions), and it carries zero
non-partisan risk since it only documents factual parsing decisions already made in code.

**Runners-up**
- *Favicon / apple-touch-icon* — flagged fresh in 08-12 ("real, but smaller and lower-stakes than
  the citation backlog"); still true relative to the caveats backlog. Still open.
- *"Longest gap between trips" fact* — open since 08-07, still needs more definitional care (same
  PM only? any PM?) than a one-day slot affords cleanly.
- *Registry column visibility toggle for narrow screens* — mobile polish; the table already
  scrolls horizontally in its own container, unchanged priority from prior logs.
- *robots.txt + sitemap.xml + canonical link* — rejected on the same "marginal payoff for a
  single-URL site" grounds as every prior log (08-02/04/07/08/10/11).
- *Active-filter chip summary (removable pills)* — fresh idea; URL state already syncs and Reset
  already clears everything in one click, so the added value over the existing filter bar is
  thin.

**Verification:** `node --check` on both inline scripts. Playwright against the served page
(Plotly stubbed with the correct string-id call signature; `cdn.plot.ly` blocked in this sandbox)
at 1280px and 375px: all 5 caveat disclosures present, open/close correctly on click, and read the
intended copy; no horizontal scroll at either width; dark mode renders the new section with the
same tokens as the rest of the page (screenshot-verified, all 5 open simultaneously). All 6 charts
initialize via `Plotly.react` (fixed the stub to resolve by element id, matching how the real code
calls it), all 5 KPI cards render, all 44 registry rows render. Console clean bar the pre-existing,
sandbox-only `cdn.plot.ly`/Google Fonts network blocks noted in every prior log. All three fallback
tiers untouched — this is a static content addition to the existing Methodology section, reading
nothing from `trips`/`news.json` at all.

**Files touched:** `index.html`

## 2026-08-14 — Favicon + apple-touch-icon

**Shipped.** The page had no icon at all — confirmed via a head scan, not just a hunch — so every
browser tab, bookmark, and iOS "Add to Home Screen" was unbranded despite the page already carrying
full OG/Twitter cards and a JSON-LD dataset block. Added a plain map-pin mark (a place marker, on
theme for a visits tracker) in the site's accent teal (`#0e6b70`) on a solid square: an inline SVG
data URI for `rel="icon"` so modern browsers get a crisp icon with zero extra network request, plus
two small PNGs (`favicon.png` 48×48, `apple-touch-icon.png` 180×180) for iOS home-screen icons and
any older browser or search crawler that expects a conventional favicon file rather than a data URI.
No image library is installed in this environment, so the PNGs are generated by a small pure-stdlib
script (manual pixel rasterization + `zlib`-compressed PNG chunks) — no new dependency, just a
one-time asset-generation step, the same way `preview.png` already sits in the repo as a committed
static asset.

Two design misfires caught before shipping, worth noting because both were symbol collisions, not
rendering bugs: a first pass (globe ring + diagonal flight path through the center) rendered as an
international "no entry" sign; a second pass (ring + diagonal line to a corner dot) read as the ♂
symbol at small sizes. Settled on a plain, solid map-pin silhouette instead — unambiguous at 16px
and carries no unintended meaning.

This is the single most-repeated "real but smaller" runner-up in the log — named open in 08-12
("real, but smaller and lower-stakes than the citation backlog") and again in 08-13 ("still true
relative to the caveats backlog. Still open") — and today's fresh brainstorm turned up nothing that
clearly outranked it: no live correctness bug, no open a11y defect (focus trap, chart data tables,
and sortable columns all shipped already), and the perf/SEO backlog items (robots.txt/sitemap) have
been rejected on marginal-payoff grounds five times running with nothing new to change that call.

**Runners-up**
- *robots.txt + sitemap.xml + canonical link* — rejected a sixth time on the same "marginal payoff
  for a single-URL site" grounds as every prior log (08-02/04/07/08/10/11/13).
- *"Longest gap between trips" fact* — open since 08-07, still needs more definitional care (same
  PM only? any PM?) than a one-day slot affords cleanly.
- *Registry column visibility toggle for narrow screens* — mobile polish; the table already scrolls
  horizontally in its own container, unchanged priority from prior logs.
- *Per-chart "download as PNG" button* — fresh idea, genuine value for journalists reusing a chart,
  but Plotly's modebar is deliberately disabled (`displayModeBar: false`) for a cleaner look, so this
  needs its own UI rather than just flipping a flag — bigger than today's slot next to the icon work.
- *Skeleton loaders for the KPI/chart panels* — fresh idea, real perceived-performance polish, but
  thinner value than a missing brand asset that's been on the runners-up list for two straight days.

**Verification:** `node --check` on both inline scripts. Playwright against the served page (Plotly
stubbed; `cdn.plot.ly` blocked in this sandbox) at 1280px and 375px: both new PNGs resolve `200` over
HTTP, all three `<link>` tags (`icon` SVG, `icon` PNG, `apple-touch-icon`) are present with correct
hrefs, all 6 charts initialize, all 5 KPI cards render, all 44 registry rows render, no horizontal
scroll at either width. Full-page screenshots at both widths confirm no visual regression elsewhere
on the page. Console clean bar the pre-existing, sandbox-only Google Fonts network block noted in
every prior log. All three fallback tiers untouched — icons are static assets referenced from
`<head>`, entirely independent of which data tier populates `trips`.

**Files touched:** `index.html`, `favicon.png` (new), `apple-touch-icon.png` (new)

## 2026-08-20 — Empty-state message on all six charts when filters match zero trips

**Shipped.** Filtering or searching to a combination with zero matches (e.g. a PM/year pair that
never happened, or a search term matching nothing) is a real, reachable state — the registry
table already handled it with an explicit "No trips match the current filters" message and a
reset button, but every one of the six analysis charts above it just rendered its empty axes
with no explanation at all: a blank world map, an axis-only line chart, empty bars. A user
scanning top-down would hit six unexplained blank panels before reaching the one message, further
down the page, that actually tells them what happened. Added one shared Plotly annotation —
"No trips match the current filters," centered in the panel, using the chart's own theme-aware
axis color — computed once at the top of `renderChartsInner` from `rows.length` and passed into
each of the six chart layouts via the existing `baseLayout(c, {...})` merge point. Empty when
there are matches (unchanged behaviour, verified byte-identical to before), populated only when
there are none. One array literal, six one-line additions, no new dependency, no chart redesign.

Fresh find, not a repeat of any logged item: checked the backlog (registry column toggle,
per-chart PNG export, robots.txt/sitemap, og:image dimensions) and none of them describe this gap.
It's a clean fit for the "interactivity" dimension — closing a visible inconsistency in the site's
own existing empty-state handling — sized to one choke point, fully reversible, and carries zero
non-partisan risk (a loading/empty UI state, not content or commentary).

**Runners-up**
- *Registry column visibility toggle for narrow screens* — mobile polish, open since 08-08; the
  table already scrolls horizontally in its own container, unchanged low priority from every
  prior log.
- *robots.txt + sitemap.xml + canonical link* — rejected a thirteenth time on the same "marginal
  payoff for a single-URL site" grounds as every prior log.
- *`og:image:width`/`og:image:height` meta tags* — flagged 08-18; real but thinner value than a
  visible, confirmable UX inconsistency between the charts and the table right below them.
- *Per-chart "download as PNG" button* — flagged 08-14 through 08-19; Plotly's modebar is
  deliberately disabled, so this needs its own UI, bigger than today's slot.
- *Debounce the search input* — checked the code; the dataset is 44 rows, so a full re-render per
  keystroke is not a measurable perf problem here. Correctly not a perf idea.

**Verification:** `node --check` on both real inline scripts (the JSON-LD block is not JS and
correctly fails a syntax check; ignored). `cdn.plot.ly` is blocked in this sandbox (confirmed via
`curl`, same as every prior log), so verified via Playwright against the served page with a
call-capturing `Plotly.react` stub at 1280px and 375px, light and dark: unfiltered baseline — all
6 charts called with `annotations: []` (no change from current behaviour); filling the search box
with a no-match term — all 6 re-render with `annotations: [{text: "No trips match the current
filters", x: 0.5, y: 0.5, xref: "paper", yref: "paper", font: {color: <theme axis color>}}]`,
matching the registry's own "No trips match the current filters." message and the "0 of 44 trips"
live-region text word-for-word; clicking Reset clears every chart's annotations again. Dark mode
resolves the annotation to the theme's dark axis color, no console errors. No horizontal scroll at
either viewport. The two console-level resource failures present in both runs
(`cdn.plot.ly`, Google Fonts) are the same pre-existing sandbox-only network blocks noted in every
prior log, confirmed by name via `requestfailed`. All three fallback tiers untouched — the change
reads only `rows.length`, already computed identically regardless of which tier populated `trips`.

**Files touched:** `index.html`, `ideas-log.md`

## 2026-08-15 — "Longest gap without a trip" fact

**Shipped.** The hero's existing `facts` row (which already surfaces "Most visited" and "Longest
trip") gets a third, computed fact: the longest stretch, among the trips currently in view, between
one trip ending and the next one starting — e.g. "Longest gap without a trip · 184 days (16 Nov 2022
– 19 May 2023)". This is CLAUDE.md's "a new way to read the data" dimension, and no prior cycle had
shipped one yet.

This exact idea has been named open since 08-07 and repeatedly passed over "because a fresh
analytical claim needs more definitional care... than a one-day slot affords" — specifically the
question "same PM only? any PM?" (08-07, 08-11, 08-12). Resolved it today by not inventing new
scoping rules at all: the fact operates on `rows`, the already-filtered array every other KPI and
fact on the page already reads, so PM/year/country/search scope is whatever the user's existing
filters already show — identical mechanics to "Most visited" and "Longest trip" today. No new
filter semantics, so no new ambiguity. Pure display-layer computation over data already normalized
in memory (sorts a copy of the filtered rows by `start`, diffs consecutive `end`→`start` pairs,
keeps the max); no data-provenance touch, no new dependency, no new CSS (reuses the existing `.fact`
class). The fact only counts gap length, never which PM was or wasn't traveling during it, so it
carries no partisan-scoring risk.

**Runners-up**
- *robots.txt + sitemap.xml + canonical link* — rejected an eighth time on the same "marginal
  payoff for a single-URL site" grounds as every prior log.
- *Registry column visibility toggle for narrow screens* — mobile polish; the table already
  scrolls horizontally in its own container, unchanged priority from prior logs.
- *Per-chart "download as PNG" button* — flagged 08-14; Plotly's modebar is deliberately disabled,
  so this needs its own UI, bigger than today's slot.
- *Skeleton loaders for KPI/chart panels* — flagged 08-14; real perceived-performance polish, but
  thinner value than finally closing the oldest open item in the log.
- *Active-filter chip summary (removable pills)* — rejected 08-13 on the same "URL state already
  syncs, Reset already clears everything" grounds; nothing changed that call today.

**Verification:** `node --check` on the extracted inline script; unit-checked the gap logic in
isolation (single-trip view → no gap fact; adjacent/overlapping trips → 0-day gap correctly
suppressed, not shown as a negative or zero-day "fact"; tied max gaps → first occurrence wins
deterministically). Playwright against the served page (Plotly stubbed; `cdn.plot.ly` blocked in
this sandbox) at 1280px and 375px: fact renders correctly, all 6 charts initialize, all 5 KPIs and
44 registry rows render, no horizontal scroll at either width. Narrowing the view to 2 trips
(search "Bhutan") recomputes the gap correctly for that subset; narrowing further to 1 trip hides
it (confirmed via the isolated logic test, since no live single-row filter combination existed in
today's dataset). Dark mode renders the new fact with the same themed color as the other two.
Console clean bar the pre-existing, sandbox-only Google Fonts network block noted in every prior
log. All three fallback tiers untouched — the fact reads only `rows`, the already-normalized
in-memory trip list, identically regardless of which tier populated `trips`.

**Files touched:** `index.html`

## 2026-08-16 — Announce filter/search results to screen readers

**Shipped.** The registry's "N trips" result-count span (`#tableSubtitle`) updates visibly on every
change to the five filter controls (PM, Year, Country, Visit type, Search) and on sort, but carried
no `aria-live` — a screen-reader user changing a filter got no signal at all that the registry and
all six charts had just changed, and no route to "how many trips does this view now show" short of
manually re-navigating into the table. Added `aria-live="polite" aria-atomic="true"` to the span so
every filter/search change is announced automatically. Also tightened the announced text itself:
when a filter actually narrows the view it now reads "23 of 44 trips" instead of just "23 trips" —
context a sighted user gets for free from the surrounding filter bar, but a screen-reader user
hearing the span in isolation would otherwise miss entirely. The unfiltered baseline ("44 trips")
is untouched, so the visible label doesn't grow when nothing is filtered.

A fresh find, not a repeat of any backlogged item: I checked the log's existing a11y list (drawer
focus trap, chart data tables, sortable columns) and all three are shipped; this is a different gap
in the same family — visible-but-silent state changes — that nothing in the log had named before.
Small, isolated to two lines (one HTML attribute, one text-branch), and carries the standard ARIA
"live region announces results count" pattern, so no new UI, dependency, or design decision.

**Runners-up**
- *Registry column visibility toggle for narrow screens* — mobile polish, open since 08-08; the
  table already scrolls horizontally in its own container, unchanged priority from every prior log.
- *Per-chart "download as PNG" button* — flagged 08-14/08-15; Plotly's modebar is deliberately
  disabled, so this needs its own UI, bigger than today's slot.
- *Skeleton loaders for KPI/chart panels* — flagged 08-14/08-15; real perceived-performance polish,
  but thinner value than a live, unflagged accessibility gap.
- *robots.txt + sitemap.xml + canonical link* — rejected a ninth time on the same "marginal payoff
  for a single-URL site" grounds as every prior log.
- *"On this day" historical-trips callout* — fresh idea (trips that started on today's month/day in
  past years), but most calendar days have zero matches in a 44-trip dataset, so the feature would
  be empty or hidden more often than not — inconsistent value for a permanent UI slot.
- *Lazy-render below-the-fold charts via IntersectionObserver* — fresh idea, but Plotly's already
  deferred (08-09) and first paint is already unblocked; the marginal gain didn't clearly outweigh
  adding a second render-gating path alongside the existing `plotlyReady` one.

**Verification:** `node --check` on both inline scripts. Playwright against the served page (Plotly
stubbed; `cdn.plot.ly` blocked in this sandbox) at 1280px and 375px: `#tableSubtitle` carries
`aria-live="polite"`/`aria-atomic="true"`; unfiltered load reads "44 trips"; selecting Visit type →
Multi-country updates it live to "23 of 44 trips"; searching "Bhutan" updates it to "2 of 44 trips";
Reset restores "44 trips". All 6 charts initialize, all 5 KPI cards render, all 44 registry rows
render, no horizontal scroll at either width. Console clean bar the pre-existing, sandbox-only
Google Fonts network block noted in every prior log. All three fallback tiers untouched — the
change reads only `rows.length` and `trips.length`, both already in memory regardless of which tier
populated `trips`.

**Files touched:** `index.html`

## 2026-08-17 — Print stylesheet

**Shipped.** A `@media print` block makes the page produce a clean, citable printout instead of
whatever the screen chrome happens to render onto paper. Hidden: site nav, dark-mode toggle,
filter form controls, CSV/download buttons, "Latest coverage" (third-party, image-heavy, not core
to the dataset), the trip drawer, and the sort-arrow glyphs. Kept: hero, KPIs, facts, live-trip
status, the result-count text (so an active filter is still legible on the page), the registry
table, and Methodology. The six Plotly canvases — interactive chrome and on-screen-only colours
that don't survive paper — are replaced by their existing accessible data tables (shipped 08-08):
`beforeprint`/`afterprint` handlers force every `<details class="chart-data">` open for the print
pass and restore each one's exact prior open/closed state afterward, so a reader who had a table
open on screen doesn't lose that state and one who hadn't isn't left with six tables sprung open
after printing. Dark mode's CSS variables are overridden back to the light palette specifically
under `@media print`, regardless of the on-screen toggle, so printing in dark mode doesn't burn
ink on a near-black background. A small byline (site name, URL, "printed \<date\>") appears only
in print, at the top of page one, giving a paper copy the same citation trail the 08-07 permalink
and 08-12 copy-citation features already give a shared link.

Named once, on day one (08-04: "the deliberate opposite of the obvious pick... real but niche
demand") and never repeated or explicitly rejected since — genuinely fresh, not a repeat pick.
Chosen over the day's other candidates because it's the only one that's both fully open (no
existing accessibility, correctness, or trust defect currently outranks it) and cleanly one-day:
pure CSS plus two small event listeners, no new dependency, no data-provenance touch, and it
leans on data tables and citation infrastructure the site already has rather than building new
UI. It also serves the stated journalist/researcher audience directly — a page designed to be
cited benefits from being printable without dragging a UI shell onto the page.

**Runners-up**
- *robots.txt + sitemap.xml + canonical link* — rejected a tenth time on the same "marginal
  payoff for a single-URL site" grounds as every prior log.
- *Registry column visibility toggle for narrow screens* — mobile polish, open since 08-08; the
  table already scrolls horizontally in its own container, unchanged priority from prior logs.
- *Skeleton loaders for KPI/chart panels* — flagged 08-14/08-15; real perceived-performance
  polish, but the print gap was older (open since 08-04, not 08-14) and fully unaddressed.
- *Per-chart "download as PNG" button* — flagged 08-14/08-15; Plotly's modebar is deliberately
  disabled, so this needs its own UI, bigger than today's slot.
- *WCAG contrast audit of `--text-3`/`--gold-text` against both themes* — fresh idea, genuine
  accessibility value, but scoping "which pairs, which threshold, what changes" cleanly enough
  for one day needs more definitional work than today's brainstorm gave it. Worth a dedicated
  cycle rather than a rushed pass today.

**Verification:** `node --check` on both inline scripts. Playwright against the served page
(Plotly stubbed; `cdn.plot.ly` blocked in this sandbox) at 1280px and 375px: normal screen
rendering unaffected — all 6 charts initialize, all 5 KPIs and 44 registry rows render, the
`.print-byline` stays `display:none`, no horizontal scroll at either width, console clean bar the
pre-existing, sandbox-only Google Fonts network block noted in every prior log. Under
`emulateMedia('print')`: nav, theme toggle, CSV button, and news block report `display:none`;
the six chart canvases (`[role="img"]` under `.charts`) report `display:none` while their
`.chart-data-scroll` wrappers report `overflow:visible`; the registry table and result-count
stay visible; toggling dark mode on and re-emulating print shows the light background colour
(`rgb(246,244,239)`), confirming the theme override, and reverts to the dark background on
returning to screen media. Directly dispatching `beforeprint`/`afterprint` (Chromium's headless
print pipeline doesn't reliably fire `afterprint` without a real dialog, so this isolates the
handler logic itself) against a mixed baseline (two tables pre-opened by the "user," four
closed) confirms all six force open on `beforeprint` and the exact original per-table
open/closed pattern — not a blanket collapse — is restored on `afterprint`; the print byline
shows the correct stamped date. Full-page print screenshots confirm the layout: hero/KPIs render
cleanly, each analysis panel shows its data table instead of a chart canvas with no visual
breakage, and the registry table reads cleanly with the header row and action buttons gone.
All three fallback tiers untouched — the change is a screen/print CSS split plus two `window`
event listeners operating on DOM already built from whichever tier populated `trips`.

**Files touched:** `index.html`

## 2026-08-18 — Fix dark-mode `--text-3` WCAG AA contrast failure

**Shipped.** Measured every color-token pair in both themes against the WCAG 2.1 relative-luminance
formula, applied to the actual backgrounds each token is used against in the CSS (not just `--bg`).
Every pair passed AA except one: dark-mode `--text-3` (`#837e6f`), used throughout for small
secondary text (filter labels, panel subtitles, drawer detail labels, news source lines — all under
`0.9rem`, so the 4.5:1 "normal text" floor applies, not the 3:1 "large text" one). Against `--bg` it
scraped by at 4.58:1, but against the panel backgrounds it actually sits on in real markup it failed:
4.30:1 on `--surface` (most panel/card subtitles), and 3.97:1 on `--surface-2` — the background of
`.drawer-grid > div`, i.e. every "Dates / Duration / Countries" label in the trip drawer, the site's
most-used piece of chrome. Lightened to `#908b7c` (same hue/saturation, `+5` lightness in HSL),
verified to clear 4.5:1 against all three realistic backgrounds (5.46 / 5.12 / 4.73:1). Light-mode
`--text-3` and `--gold-text` in both themes were already comfortably passing (5.00–8.52:1) and are
untouched. One CSS custom-property value, no other change.

Named fresh in the 08-17 log ("genuine accessibility value, but scoping... needs more definitional
work... worth a dedicated cycle") — today *was* that dedicated cycle: doing the actual per-background
contrast math (not just spot-checking against `--bg`) is what turned a vague "audit this" into a
one-line, fully-verified fix. Directly serves CLAUDE.md's named "accessibility fix" dimension, carries
zero non-partisan risk (a color value, not content), and is trivially reversible.

**Runners-up**
- *Registry column visibility toggle for narrow screens* — mobile polish, open since 08-08; the table
  already scrolls horizontally in its own container, unchanged priority from every prior log.
- *Skeleton loaders for KPI/chart panels* — flagged 08-14 through 08-17; real perceived-performance
  polish, but a measured contrast failure in the site's most-used chrome (the drawer) outranks it.
- *Per-chart "download as PNG" button* — flagged 08-14 through 08-17; Plotly's modebar is deliberately
  disabled, so this needs its own UI, bigger than today's slot.
- *robots.txt + sitemap.xml + canonical link* — rejected an eleventh time on the same "marginal payoff
  for a single-URL site" grounds as every prior log.
- *`og:image:width`/`og:image:height` meta tags* — fresh, minor SEO polish (lets social crawlers skip
  a fetch-and-measure round trip); real but strictly smaller than a live contrast failure.

**Verification:** computed WCAG 2.1 relative-luminance contrast for every `--text-3`/`--gold-text`/
`--text-2`/link/status-color pair in both themes against every background each token is actually
composited over in the CSS (not just `--bg`) — confirmed dark `--text-3` was the only failure (3.59–
4.30:1 depending on background; `--surface-3` isn't used as a real background so its 3.59:1 worst case
never fires in practice, but `--surface`/`--surface-2` at 4.30/3.97:1 do). Re-ran the same formula
against the replacement `#908b7c` for all three real backgrounds: 5.46:1 (`--bg`), 5.12:1 (`--surface`),
4.73:1 (`--surface-2`) — all clear 4.5:1. `node --check` on both inline scripts (no JS touched, sanity
check only). Playwright against the served page (Plotly stubbed; `cdn.plot.ly` blocked in this
sandbox) at 1280px and 375px: 5 KPIs and 44 registry rows render, dark-mode toggle applies the new
token (`getComputedStyle` confirms `#908b7c`; the drawer's `.drawer-grid .l` label resolves to
`rgb(144,139,124)`), opening/closing the trip drawer works, no horizontal scroll at 375px. Full-page
screenshots at both themes show no visual regression — the new value is a subtle, still-clearly-
tertiary lightening, not a jump to `--text-2`. Light mode is byte-for-byte untouched (diff confirms
only the one dark-mode line changed). Console clean bar the pre-existing, sandbox-only Google Fonts
network block noted in every prior log. All three fallback tiers untouched — this is a static CSS
token read by every element regardless of which tier populated `trips`.

**Files touched:** `index.html`

---

## 2026-08-18 — Read what the headline claims, not just which country it names (directed fix, not a cycle pick)

**Problem.** The live band read "Reportedly abroad now — Bangladesh", corroborated by three
sources, on a day the PM was in Delhi. All three headlines were about *Bangladesh's* PM
travelling *to India*, and none described a trip that was happening:

| headline | what it actually says |
|---|---|
| "…Bangladesh PM **Refuses to Visit India** Until Sheikh Hasina's Extradition" | refused |
| "Bangladesh PM Tarique Rahman's **India visit uncertain** as Dhaka, Delhi discuss dates" | not agreed |
| "Bangladesh PM **Likely To Visit India Next Week**" | not yet happened |

`detect_reported_trip` matched "Bangladesh" beside a travel cue ("visit") in three independent
recent articles and concluded the PM was there. The detector had no concept of *who* was
travelling, *which direction*, or *whether the trip was real* — country proximity was the whole
test. Three distinct failure classes, all live at once: reversed direction, negation, and
speculation.

**Shipped.** Two layers, mirroring the existing date-validation design (pipeline filters at
source, page re-checks what it is served).

*Direction* — `scripts/refresh.py`, applies to all coverage since it decides which trip a story
belongs to. A country immediately followed by a leader title ("Bangladesh PM", "Sri Lanka
President") names a person, not a destination, so it no longer counts as a trip leg — unless the
same headline shows the PM as the guest ("Israel President welcomes Modi", which does place him
there). If such a leader is also travelling *to India*, the headline is discarded outright.

*Claim strength* — gates the reported band only, so registry-confirmed trips keep their previews
and wrap-ups. A headline can corroborate "abroad now" only if it is not negated (refuses, cancels,
postpones, skips, rules out, won't) and not merely prospective (likely to, may visit, next week,
uncertain, in talks, ahead of) — with the exception that a prospective clause is fine alongside
on-the-ground reporting, since "lands in Moscow, likely to meet Putin" is a current trip. On top
of the existing 3-source threshold, at least one source must place him on the ground; three
articles that only *discuss* a visit no longer raise the band.

*Client-side* — `corroboratesLiveTrip()` repeats the negation/speculation/on-ground test over the
served articles before rendering the band, and drops the country from the "Latest coverage"
heading when it fails, so a stale or hand-edited `news.json` cannot revive a false claim.

**Non-partisan check:** the change only makes the site slower to assert an unofficial claim; it
adds no commentary and cannot state anything the registry does not, in either direction.

**Verification:** new `scripts/test_headline_claims.py` (26 checks, stdlib, no network) pins all
three production headlines plus negated/prospective/current variants, an inbound foreign leader,
a leader hosting the PM, and end-to-end `detect_reported_trip` — asserting both that the false
Bangladesh band disappears and that the genuine Israel band from 2026-08-09 still detects at 3
sources. Existing `test_news_dates.py` still passes unchanged. Re-ran the live news path against
today's feeds: 21 recent articles → 15 assert a trip in progress, 6 correctly rejected (including
"Bangladesh PM … 'has no plans' to visit India" and "India and Bangladesh in talks for visit by PM
Tarique Rahman next week"), no reported trip detected, `data/news.json` regenerated to the
registry's most recent trip. In-browser: served page renders "No trip in progress. Latest —
Indonesia, Australia & New Zealand", console clean, no horizontal scroll at 375px; injecting the
old Bangladesh `news.json` suppresses the band and the coverage heading, injecting the Israel one
still renders "Reportedly abroad now — Israel". `visits.json` and all three fallback tiers
untouched.

**Files touched:** `scripts/refresh.py`, `scripts/test_headline_claims.py` (new), `index.html`,
`data/news.json` (regenerated output)

## 2026-08-19 — Skeleton loaders for the KPI strip and the six chart panels

**Shipped.** Before today, `#kpis` and the six `role="img"` chart divs sat completely empty from
first paint until, respectively, the tier-1 `data/visits.json` fetch resolved and the deferred
~3.5 MB Plotly bundle (08-09) finished loading and drawing — on a slow connection, a page that
looks broken rather than loading. Two changes, no new dependency:

1. The five `.stat` cards in `#kpis` now ship as static shimmer-bar markup in the page's own HTML
   (confirmed via raw `curl`, so it's present before any JS runs at all). `renderKpis()` already
   overwrites `#kpis.innerHTML` wholesale, so the moment real data lands the skeleton is replaced
   with zero extra JS — no new render path.
2. Each chart div gets a `chart-loading` class (shimmer background via CSS) in its initial markup;
   `renderCharts()` now removes that class right after that specific panel's own `Plotly.react()`
   call, so panels reveal progressively as each chart actually draws rather than all six flipping
   at once. Wrapped in a try/catch: a total CDN failure (Plotly undefined) clears all six skeletons
   immediately instead of shimmering forever — strictly better than the old blank-panel failure
   mode, and still logs the one clear `[charts]` error the 08-09 log established. Shimmer uses
   `background-position` animation only; the existing global `prefers-reduced-motion` rule already
   flattens all `animation-duration` to `.01ms`, so no separate reduced-motion CSS was needed.

Named as a runner-up five days running (08-14 through 08-18) and never rejected on the merits —
only ever outranked by something more urgent that day (a11y defects, a live correctness bug, a
contrast failure). Today's fresh brainstorm turned up nothing that outranked it again, so it
finally got the slot: genuine perceived-performance value, one-day scope (CSS + ~10 lines of JS,
no chart-by-chart redesign), fully reversible, and carries zero non-partisan risk (a loading
state, not content).

**Runners-up**
- *Registry column visibility toggle for narrow screens* — mobile polish, open since 08-08; the
  table already scrolls horizontally in its own container, unchanged priority from every prior log.
- *Per-chart "download as PNG" button* — flagged 08-14 through 08-18; Plotly's modebar is
  deliberately disabled, so this needs its own UI, bigger than today's slot.
- *`og:image:width`/`og:image:height` meta tags* — flagged fresh 08-18; real but strictly smaller
  than a five-times-repeated perceived-performance gap.
- *robots.txt + sitemap.xml + canonical link* — rejected a twelfth time on the same "marginal
  payoff for a single-URL site" grounds as every prior log.
- *"Trips by weekday started" fact* — fresh idea (a new way to read the data, in the spirit of the
  08-15 gap fact), but registry dates record only day/month/year with no time-of-day meaning
  beyond the calendar date, and weekday-of-departure isn't a claim the underlying data actually
  supports distinguishing from noise at 44 rows — dropped rather than shipped a thin stat.

**Verification:** `node --check` on both inline scripts. Confirmed via raw `curl` that the served
HTML (pre-JS) already contains the 5 KPI skeleton cards and all 6 `chart-loading` chart divs.
Playwright against the served page (`cdn.plot.ly` blocked in this sandbox, routed to a stub) at
1280px and 375px, both themes: with the data fetch and Plotly script artificially delayed
(900 ms / 1500 ms respectively) and polled every 150ms — 15 KPI skeleton bars + 6 chart skeletons
visible while both are pending; KPI skeletons clear and show real values (e.g. "44") the instant
the data fetch resolves, while chart skeletons persist until Plotly also resolves; all 6 clear
together right after Plotly loads. Screenshots at both viewports/themes confirm the shimmer reads
correctly and matches the site's existing tokens, no layout shift, no horizontal scroll at 375px.
Simulated total CDN failure (`route.abort()` on `cdn.plot.ly`): all 6 chart skeletons clear instead
of shimmering forever, KPIs and all 44 registry rows still render correctly, console shows exactly
one new `[charts] ReferenceError: Plotly is not defined` plus the pre-existing blocked-resource
errors — no new failure mode introduced. Un-delayed run: all 6 charts draw, 5 KPIs and 44 registry
rows render, dark-mode toggle re-renders charts correctly with skeleton classes already cleared,
no horizontal scroll at either width, console clean bar the pre-existing, sandbox-only Google Fonts
block noted in every prior log. Filters, sort, CSV export, drawer, permalinks, and print stylesheet
are untouched (no code in those paths was touched). All three fallback tiers untouched — the
skeleton is a screen-only, tier-agnostic loading state that clears on however `trips` gets
populated.

**Files touched:** `index.html`

## 2026-08-21 — Restore in-page navigation on mobile instead of hiding it

**Shipped.** At ≤640px, `.site-nav { display: none; }` removed the four in-page nav links
(Analysis, Registry, Methodology, Data) from the header entirely, with nothing put in their
place — confirmed via a real 375px screenshot, not just reading the CSS: below 640px a mobile
visitor had no way to jump to a section short of scrolling the whole page, and the theme toggle
sat oddly close to the wordmark instead of pinned to the right edge (a side effect of the same
missing element, since `.site-nav`'s `margin-left: auto` was what pushed it there). Measuring
the actual header at 375px showed the wordmark alone (`India PM Foreign Visits` + the
`TRACKER` badge) was 256px wide against 343px of available space — there was never room to
just un-hide the full-size nav next to it.

Fix, CSS only: the decorative `TRACKER` badge drops and the wordmark's name shrinks slightly
(1.06rem → .92rem) to free real space; both wordmark and the theme toggle become fixed-size
flex items (`flex: none`) so they stay fully visible; the nav becomes the one flexible,
horizontally-scrollable item between them (`flex: 1 1 auto; overflow-x: auto`) — the same
"tab bar" pattern used in countless mobile apps, with slightly tighter link padding so more of
it fits before scrolling is needed. No markup, JS, or data changed — the four links are the
same `<a href="#analysis">`-style anchors as before, including `Data`'s existing
`target="_blank"`.

Fresh find, not a repeat: the log's mobile-polish backlog (registry column toggle, open since
08-08) never named the nav itself, and no prior entry mentions `site-nav`. Chosen over that
backlog item because a completely absent navigation control is a functional gap, not polish,
and it's the more foundational mobile issue — the registry table's horizontal scroll is at
least usable today, this had zero mobile affordance at all.

**Runners-up**
- *Registry column visibility toggle for narrow screens* — mobile polish, open since 08-08; the
  table already scrolls horizontally in its own container, a real workaround the nav never had.
- *Per-chart "download as PNG" button* — flagged 08-14 through 08-19; Plotly's modebar is
  deliberately disabled, so this needs its own UI, bigger than today's slot.
- *robots.txt + sitemap.xml + canonical link* — rejected a fourteenth time on the same
  "marginal payoff for a single-URL site" grounds as every prior log.
- *`og:image:width`/`og:image:height` meta tags* — flagged 08-18/08-19; real but strictly
  smaller than a mobile visitor having zero way to jump to a section.
- *"Trips by season" fact* — fresh idea (which quarter/season the PM travels most), but 44 trips
  split across 4 seasons is thin enough that the "top" season is likely noise, not signal —
  same class of concern that shelved "trips by weekday" on 08-19.

**Verification:** measured the real header at 375px before the fix (Playwright, Plotly
CDN stubbed since this sandbox blocks `cdn.plot.ly`): wordmark 256px vs. 343px available,
nav rendered at 1px wide — confirming the gap was structural, not cosmetic. After the fix, at
320px/375px/390px (iPhone-SE through iPhone-12 widths): all four nav links present in the DOM,
nav is horizontally scrollable (`scrollLeft` reaches 183px, revealing `Methodology`/`Data`),
clicking a visible link (`Analysis`) navigates to `#analysis` correctly, `Data` keeps its
`target="_blank"`, no page-level horizontal scroll at any of the three widths, theme toggle
sits flush right. Desktop (1280px) screenshot confirms the nav, badge, and toggle are
byte-identical to before — the changes are entirely inside the `max-width: 640px` media query
plus two harmless additive properties (`white-space: nowrap`, `flex: none`) in the base rules
that only matter once the nav is actually squeezed. Dark mode at 375px renders the same layout
with correct theme tokens. `node --check` on both inline scripts (untouched, sanity check
only). All 5 KPIs, 44 registry rows, and the full page render with no console errors. All three
fallback tiers untouched — this is a pure CSS change with no JS or data-path touched at all.

**Files touched:** `index.html`, `ideas-log.md`

## 2026-08-22 — "Compact columns" toggle for the trip registry

**Shipped.** The registry's 7-column table (Dates, Itinerary, Countries, Type, Days, PM,
Source) has relied on the `table-wrap`'s own horizontal scroll to be usable on a phone since
day one — real, but a workaround, not a fix. Added a "Compact columns" button next to
Download CSV that hides Type, Days, and Source with one tap, leaving the four columns that
matter for a quick scan (Dates, Itinerary, Countries, PM); a second tap ("All columns")
restores the rest. All three hidden fields are still one row-tap away in the trip drawer,
which already shows every field in full, so nothing is lost, just decluttered. It's a pure
CSS `display:none` toggle keyed off `data-col` attributes added to each `<th>`/`<td>` — the
cells stay in the DOM, so sorting (keys unaffected) and CSV export (reads `filtered()` trip
data directly, never the table markup) both work exactly as before regardless of which mode
is active. The preference persists in `localStorage` the same way the theme toggle already
does, is a real `<button aria-pressed>` (not a checkbox list, so no new form semantics), and
works identically on desktop for anyone who prefers a denser table.

This is the single most-repeated backlog item in this log, named open in every entry from
08-08 through 08-21 (14 entries) and never once rejected on the merits — only ever outranked
by something more urgent that day. Today's fresh brainstorm (a `rel="noopener"` gap on two
`data/visits.json` links, `og:image` width/height meta, a per-chart PNG export, a new
"average trip length" stat, a page-level "back to top" control) turned up nothing that
outranked a mobile-experience gap open for two full weeks, so it finally got the slot.

**Bug caught in verification, fixed in the same change:** adding a second button to
`.registry-actions` meant three flex items (helper text + 2 buttons) no longer fit one line
at 375px — the row silently overflowed its container and dragged the *whole page* into
horizontal scroll (confirmed via `scrollWidth` before/after: 375px clean before this change,
406px after, isolated to `.registry-actions`, not the table). Fixed by adding `flex-wrap: wrap`
to the existing 640px breakpoint rule for `.registry-actions` and letting the helper text take
its own line — the same class of "flex row silently overflows its box" defect the 08-08 log
hit with CSS Grid, different layout mode.

**Runners-up**
- `rel="noopener"` missing on two `target="_blank"` links to `data/visits.json` (footer,
  Methodology) — a genuine, tiny defect (reverse-tabnabbing risk, low severity since the link
  is same-origin JSON), but thinner than a 14-times-repeated mobile gap.
- `og:image:width`/`og:image:height` meta tags — flagged 08-18/08-19, real but minor SEO
  polish, same reasoning as every prior log that passed on it.
- Per-chart "download as PNG" button — flagged 08-14 through 08-19; Plotly's modebar is
  deliberately disabled, so this still needs its own UI, bigger than today's slot.
- "Average trip length by PM" fact — a new way to read the data, but it's a cross-PM
  comparison, and CLAUDE.md's non-partisan guardrail means any new stat that ranks or
  compares PMs needs more deliberate framing than a one-day slot affords; the existing PM
  comparison chart already carries that risk carefully, a fresh one shouldn't be rushed.
- Page-level "back to top" control — real but niche; the in-page nav (fixed 08-21) already
  covers jumping between sections including back to the hero.

**Verification:** `node --check` on both real inline scripts (JSON-LD block fails as always,
expected — not JS). Playwright against the served page (Plotly stubbed; `cdn.plot.ly` blocked
in this sandbox) at 1280px and 375px, light and dark: default state is unpressed/"all columns"
(byte-identical to before); one click sets `aria-pressed="true"`, flips the label to "All
columns", hides Type/Days/Source across every row while Dates/Itinerary/Countries/PM stay
visible, and persists through a full page reload via `localStorage`; a second click restores
all 7 columns. `document.documentElement.scrollWidth` confirms no page-level horizontal
scroll at 375px in either mode (the pre-fix regression measured 406px vs. a 375px viewport;
the flex-wrap fix brought it back to 375px). All 6 charts still initialize
(`.chart-loading` clears on all of them), 5 KPIs and 44 registry rows render, sort arrows and
click-to-sort still work with compact mode on, CSV export unaffected (reads trip data, not
table markup). Full-page screenshots at both viewports and both themes confirm the toggle's
pressed/unpressed styling and the wrapped mobile action row read correctly. Console clean bar
the pre-existing, sandbox-only Google Fonts network block (`ERR_CONNECTION_RESET`) noted in
every prior log. All three fallback tiers untouched — the change is a display-only toggle
over the DOM `render()` already builds from `rows`, identical regardless of which tier
populated `trips`.

**Files touched:** `index.html`, `ideas-log.md`

## 2026-08-23 — Per-chart "download as PNG" button

**Shipped.** Each of the six analysis panels gets a small download-icon button next to its
subtitle, reproducing exactly what Plotly's own modebar camera icon would do —
`Plotly.downloadImage(chartId, {format: 'png', scale: 2})` — since `displayModeBar: false`
(shipped for a cleaner look) leaves journalists and researchers with no way to pull a chart
out of the page for reuse. Descriptive per-chart filenames (`trip-frequency-map.png`,
`pm-comparison.png`, etc.) and per-chart `aria-label`s. Ships `disabled` in the raw HTML
(confirmed via `curl`, before any JS runs) and is enabled the instant that panel's own
`revealChart()` fires — the same choke point the 08-19 skeleton loaders already clear through,
so no new render-gating path. No new dependency: `downloadImage` is a built-in Plotly method,
not a custom modebar rebuild.

Named a runner-up six times running (08-14 through 08-19) and passed over each time as
"needs its own UI, bigger than today's slot" — re-examined that assumption today: since
`downloadImage` already does the actual export work, the real scope is one small button per
panel plus a single delegated click handler, not a rebuilt modebar. That reframing is what
moved it from backlog to shippable. Chosen over this cycle's fresh finds because it's a
complete, self-contained capability (not a partial fix like the `rel="noopener"` gap), it's
squarely CLAUDE.md's "interactivity" dimension, and it carries zero non-partisan risk — a
chart export button changes nothing about what any chart shows.

**Runners-up**
- `rel="noopener"` missing on two `target="_blank"` links to `data/visits.json` (Methodology
  body copy, footer) — confirmed still open (flagged 08-22); real but a smaller, single-line
  fix next to a capability six logs deep on the backlog.
- `og:image:width`/`og:image:height` meta tags — flagged 08-18/08-19/08-22 every time as
  "real but minor," same reasoning holds again.
- "Longest gap between trips, same PM only" as a second variant of the 08-15 fact — checked and
  dropped: the existing gap fact already reads as "in the current filtered view," and a
  same-PM-only variant would need its own UI slot to coexist rather than replace it, more scope
  than a fresh variant on an existing fact should carry.
- `robots.txt` + `sitemap.xml` + canonical link — rejected a fifteenth time on the same
  "marginal payoff for a single-URL site" grounds as every prior log.
- Preconnect (not just `dns-prefetch`) to `cdn.plot.ly` — real but marginal now that Plotly's
  load is already deferred (08-09) and off the critical path for first paint.

**Verification:** `node --check` on both extracted inline scripts. `curl` of the raw served
HTML confirms all six buttons ship `disabled` before any JS runs. Playwright against the served
page (Plotly stubbed with a capturing `react`/`downloadImage`; `cdn.plot.ly` blocked in this
sandbox) at 1280px and 375px, light and dark: all six buttons enabled immediately after their
chart renders, correct per-chart `data-filename`/`aria-label`; clicking each fires
`Plotly.downloadImage` with the exact expected `{format:'png', filename, scale:2}`; buttons stay
enabled and continue to work correctly after a filter change, a sort, Reset, Compact-columns
toggle, CSV export, dark-mode toggle, and opening/closing the trip drawer — none of those paths
touched. No page-level horizontal scroll at either width (`scrollWidth === clientWidth`).
Screenshots confirm the button reads correctly inline with each panel's subtitle in both themes
and wraps cleanly at 375px alongside the existing panel-head layout. All 5 KPIs and 44 registry
rows render. Console clean bar the pre-existing, sandbox-only Google Fonts network block
(`ERR_CONNECTION_RESET`) noted in every prior log. All three fallback tiers untouched — the
button reads only `window.Plotly` and the chart div already drawn by whichever tier populated
`trips`.

**Files touched:** `index.html`, `ideas-log.md`

## 2026-08-24 — Mobile browser chrome tinted to match the active theme

**Shipped.** The page had no `<meta name="theme-color">` at all — confirmed via a head scan,
not just a hunch — so on Android Chrome and iOS Safari the address/status bar around the page
stayed the browser's default white or black regardless of which theme was active, an unbranded
seam right at the top of the screen on the exact devices the 08-21/08-22 mobile-polish work was
aimed at. Added a single `<meta name="theme-color" id="themeColorMeta">` tag, defaulting to the
light `--bg` value (`#f6f4ef`) in the static markup, and one line in the existing `applyTheme()`
choke point — already the single place both the manual toggle and the saved/system-preference
initial load funnel through — that sets its `content` to `#14130f` (dark `--bg`) or `#f6f4ef`
(light `--bg`) in lockstep with `data-theme`. No new choke point, no CSS media-query duplicate
logic: it reuses the exact same "saved preference else system, else manual toggle" resolution
the rest of the theme system already has, so the browser chrome can never disagree with what's
on screen.

Fresh find, not a repeat: checked the log's trust/branding items (favicon 08-14, caveats panel
08-13) and neither mentions browser-chrome color. Chosen today over a keyboard-shortcut search
focus ("/") idea and a `rel="noopener"` fix because recent cycles (08-19 through 08-23) leaned
heavily on interactivity and mobile-layout work; this is the first trust/branding-adjacent pick
since 08-14 and closes a real, visible gap on the mobile devices the last two cycles targeted,
for a one-line, fully reversible change.

**Runners-up**
- *Keyboard shortcut ("/") to focus the search field* — genuine, fresh interactivity value for
  repeat users re-filtering the registry, but the site shipped three interactivity/mobile
  features in the last four cycles (08-20 through 08-23); a trust/branding gap open since launch
  was the better balance for today.
- `rel="noopener"` missing on two `target="_blank"` links to `data/visits.json` (Methodology
  body copy, footer) — confirmed still open (flagged 08-22/08-23); real but low severity since
  both links are same-origin JSON, and thinner than a visible cross-device branding gap.
- *Canonical `<link>` tag* — reconsidered fresh given the `?trip=<slug>` permalinks shipped
  08-07 (a real new argument beyond the "marginal payoff" grounds this was rejected on 15 times
  running), but the permalinks differ only in query string on the same path, which search
  engines already consolidate without help, and `og:url`/JSON-LD already declare the bare URL —
  the SEO case is real but marginal, so still not the best use of today's slot.
- `og:image:width`/`og:image:height` meta tags — flagged 08-18 through 08-22 every time as
  "real but minor," same reasoning holds again.
- `robots.txt` + `sitemap.xml` — rejected a sixteenth time on the same "marginal payoff for a
  single-URL site" grounds as every prior log.
- *Trip-duration histogram (a new way to read the data)* — genuinely fresh, but a seventh chart
  would need to replicate the skeleton loader, empty-state annotation, accessible data table, and
  PNG-download infrastructure every existing chart now carries — a mini-epic, not a one-day idea.

**Verification:** `node --check` on both extracted inline scripts. `curl` of the raw served HTML
confirms the meta tag ships with the light-mode default (`#f6f4ef`) before any JS runs. Playwright
against the served page (Plotly stubbed; `cdn.plot.ly` blocked in this sandbox, confirmed via
`requestfailed` — same class of restriction as every prior log) at 1280px and 375px: initial
`theme-color` matches the resolved `data-theme` on load; clicking the theme toggle flips both
`data-theme` and `theme-color` together (`#f6f4ef` ↔ `#14130f`) in the same click; toggling back
returns both to their original values. All 5 KPI cards and all 44 registry rows render at both
widths, no horizontal scroll (`scrollWidth === clientWidth`), console clean bar the pre-existing,
sandbox-only `cdn.plot.ly`/Google Fonts network blocks noted in every prior log. All three
fallback tiers untouched — the change is a static meta tag plus one line inside the theme system,
entirely independent of which tier populates `trips`.

**Files touched:** `index.html`, `ideas-log.md`


## 2026-08-25 — "Other trips to the same destinations" cross-links in the trip drawer

**Shipped.** Opening a trip's drawer now shows a section, right below the country tags, listing
up to five other trips that share at least one destination country — e.g. opening "France &
Slovakia" surfaces "France & USA," "France & United Arab Emirates (UAE)," and "Germany, Denmark &
France," each a clickable button showing the trip's label and date range. Clicking one re-opens
the drawer on that trip in place (same `openDrawer()` call the registry table and permalinks
already use), updating the URL slug so the new trip is itself shareable, and the section is
absent entirely for a trip whose destinations don't recur elsewhere (verified live: Seychelles,
and the three-country Jordan/Ethiopia/Oman trip, both render zero related links and no stray
heading). Matching reads `trip.countries`, the same normalized array the drawer's own country tags
and the 08-10 compound-name fix already produce, so "Trinidad and Tobago"-style names match
correctly with no new parsing logic. Capped at 5 with a "+N more" note if a country ever recurs
more than that (no country does yet in the live 44-trip dataset — max is France at 4 — but the
cap keeps the drawer from growing unbounded as the pipeline adds more years of data).

This is a genuinely new way to read the data — no prior entry lets a reader follow one country's
visit history across trips without leaving the drawer to re-filter and re-scroll the registry —
and CLAUDE.md names that dimension explicitly. Chosen over the standing "/" search-shortcut
runner-up (itself deferred once already, 08-24, purely for dimension balance) because this ranks
higher on user impact for the stated journalist/researcher audience and had never been named in
the log before, while "/" remains a smaller, still-open convenience item. Pure read-side logic
over `trips`, already in memory regardless of which fallback tier populated it — no new
dependency, no data-provenance touch, and a factual cross-reference by shared country carries no
scoring or comparison risk between PMs or parties.

**Runners-up**
- *Keyboard shortcut ("/") to focus the search field* — flagged fresh 08-24, genuine interactivity
  value, deferred there for dimension balance; today a "new way to read the data" idea with no
  prior log entry outranked it on impact, not on staleness. Still open.
- `rel="noopener"` missing on two `target="_blank"` links to `data/visits.json` (Methodology body
  copy, footer) — confirmed still open (flagged 08-22 through 08-24); real but a single-line fix,
  thinner than a new cross-reading capability.
- `og:image:width`/`og:image:height` meta tags — flagged 08-18 through 08-22 every time as "real
  but minor," same reasoning holds again.
- `robots.txt` + `sitemap.xml` + canonical link — rejected a seventeenth time on the same
  "marginal payoff for a single-URL site" grounds as every prior log.
- *Trip-duration histogram (a new way to read the data)* — flagged fresh 08-24 as "a mini-epic, not
  a one-day idea" since a seventh chart needs the full skeleton/empty-state/data-table/PNG-export
  infrastructure every existing chart carries; still true today, and the drawer cross-link idea
  gets at the same "new way to read the data" dimension without that overhead.

**Verification:** `node --check` on both extracted inline scripts (the JSON-LD block fails as
always, expected — not JS). Playwright against the served page (Plotly stubbed; `cdn.plot.ly`
blocked in this sandbox) at 1280px and 375px, light and dark: opening "France & Slovakia" shows
exactly 3 related links in newest-first order with correct labels/date ranges; clicking one
re-renders the drawer for that trip (title updates, URL `?trip=` slug changes), keeps the drawer
open and the background `inert`, and Escape still closes it and restores focus correctly —
confirming the existing focus trap and background-inert behavior survive a nested in-drawer
navigation. Opening "Seychelles" (a country appearing once) and the three-country "Jordan,
Ethiopia, and Oman" trip (no repeats among the three) both render zero related links and omit the
section heading entirely, not an empty list. All 6 charts initialize, all 5 KPI cards and all 44
registry rows render, no horizontal scroll at either width (`scrollWidth <= clientWidth`).
Screenshots confirm the new section reads correctly against both themes' tokens and wraps cleanly
on a 375px viewport alongside the existing drawer-action buttons. Console clean bar the
pre-existing, sandbox-only Google Fonts network block noted in every prior log. Print stylesheet
untouched — `#drawer`/`#drawer-overlay` were already in its hide-list from the 08-17 log, so the
new section is already excluded from print output with no additional rule needed. All three
fallback tiers untouched — the feature reads only `trips`, the already-normalized in-memory list,
identically regardless of which tier populated it.

**Files touched:** `index.html`, `ideas-log.md`

## 2026-08-26 — Earlier/Later chronological trip navigation in the drawer

**Shipped.** Opening any trip's drawer now shows a two-button nav bar at the top — "← Earlier"
and "Later →" — that steps to the chronologically adjacent trip in the full historical record
(not just the current filter view), one click at a time, without closing the drawer or
returning to the registry. Each button's `aria-label` names the target trip and its date range
for screen-reader users; the boundary trips (newest and oldest in the dataset) render the
far-side button `disabled` rather than hidden, so the timeline's edges are visually legible
rather than silently absent. Reuses `openDrawer()` for the actual step — same focus trap,
background-inert, and URL-permalink update as every other in-drawer navigation (row click,
permalink load, the 08-25 related-trips links) — so no new interaction model, just a new entry
point into it. `trips` is already sorted newest-first (08-07), so "earlier"/"later" is a plain
index walk with no new data derivation or PM-scoping question to resolve.

This is a genuinely new way to read the data — no prior entry lets a reader move along the
timeline itself, trip to trip, the way the 08-25 cross-links let them move sideways by shared
destination. Checked the backlog first: the "/" search-shortcut runner-up (open since 08-24,
deferred twice) and the `rel="noopener"` gap (open since 08-22, deferred four times) are both
smaller, already-scoped fixes; this ranked higher today on user impact for the stated
journalist/researcher audience and, like the 08-25 pick, had never been named in the log before.
Pure read-side logic over `trips`, already in memory regardless of which fallback tier populated
it — no new dependency, no data-provenance touch, and stepping through trips in date order
carries no scoring or comparison risk between PMs or parties.

**Runners-up**
- *Keyboard shortcut ("/") to focus the search field* — flagged 08-24, deferred again 08-25 for
  dimension balance; still open, still smaller than a new way to read the data.
- `rel="noopener"` missing on two `target="_blank"` links to `data/visits.json` (Methodology body
  copy, footer) — confirmed still open (flagged 08-22 through 08-25); real but a single-line fix.
- `og:image:width`/`og:image:height` meta tags — flagged 08-18 through 08-22 every time as "real
  but minor," same reasoning holds again.
- *Highlight the matched search term in registry rows* — fresh idea, real UX polish for the
  search box, but thinner value than a new drawer-browsing capability with no prior log mention.
- `robots.txt` + `sitemap.xml` + canonical link — rejected an eighteenth time on the same
  "marginal payoff for a single-URL site" grounds as every prior log.

**Verification:** `node --check` on both extracted inline scripts. Playwright against the served
page (Plotly stubbed; `cdn.plot.ly` blocked in this sandbox) at 1280px and 375px, light and dark:
opening a mid-list trip shows both buttons enabled with correct `aria-label`s naming the neighbor
trip and dates; clicking "Earlier" changes the drawer title, keeps the drawer open and background
`inert`, and updates the URL `?trip=` slug; clicking "Later" returns to the exact original trip
(round-trip verified). Boundary trips confirmed correctly: the newest trip renders "Later"
`disabled` with "Earlier" enabled, the oldest renders the reverse. The focus trap's focusable-item
query picks up the enabled chrono buttons alongside the existing controls. Confirmed the 08-25
related-trips section and the chrono nav coexist and both remain functional in the same drawer
(searched "France", opened a match, clicked a related-trip link, verified the chrono nav updates
to the new trip's neighbors). Copy-link, copy-citation buttons, click-to-sort (`aria-sort` on the
Days column flips to descending), and the CSV export button are all unaffected. No horizontal
scroll at either width, with or without the drawer open. Console clean bar the pre-existing,
sandbox-only Google Fonts network block noted in every prior log. All three fallback tiers
untouched — the feature reads only `trips`, the already-normalized in-memory list, identically
regardless of which tier populated it.

**Files touched:** `index.html`, `ideas-log.md`

## 2026-08-29 — "/" keyboard shortcut to jump to the registry search field

**Shipped.** Pressing `/` anywhere on the page now moves focus straight to the registry search
box, the same convention GitHub, Slack, and most search-heavy sites use. Guarded so it never
steals a keystroke: it's ignored while focus is already in an `input`, `textarea`, `select`, or
any `contenteditable`, and ignored with any modifier held (`Ctrl`/`Cmd`/`Alt`), so typing a
literal "/" into the search box itself, or into any other field, behaves exactly as before. A
small `/` hint sits inside the field, right-aligned — visible only when the field is empty and
unfocused (`:not(:placeholder-shown)`/`:focus` both hide it via a pure-CSS sibling selector, no
JS state) and hidden entirely on touch-only devices (`@media (hover: none)`), since there's no
physical key to press there. An `aria-describedby` span carries the same instruction for
screen-reader users, who don't get the visual hint. No new dependency, no data-provenance touch.

Named open five times running (08-24 through 08-28) — genuine interactivity value, deferred each
time only for dimension balance against that day's higher-impact pick, never on the merits.
Nothing in today's fresh brainstorm (the `rel="noopener"` gap, `og:image` dimensions, a
per-year "days abroad" fact) outranked closing the oldest surviving item in the backlog, and the
last five cycles already covered trust (08-24, 08-28) and new-ways-to-read-the-data (08-25,
08-26) twice each, with interactivity itself absent since 08-27's search highlight — today's pick
balances that mix rather than adding a third trust or data-reading feature in a row.

**Runners-up**
- *`rel="noopener"` missing on two `target="_blank"` links to `data/visits.json`* (Methodology
  body copy, footer) — confirmed still open (flagged 08-22 through 08-28, now eight logs
  running); real, a two-attribute fix, but thinner than the interactivity backlog's oldest item.
- *"Days abroad this year" cumulative fact* — flagged fresh 08-28 as a genuine new way to read
  the data; still open, and the site already shipped two data-reading features in the last four
  cycles (08-25, 08-26), so it lost on dimension balance today rather than merit.
- `og:image:width`/`og:image:height` meta tags — flagged 08-18 through 08-26 every time as "real
  but minor," same reasoning holds again.
- `robots.txt` + `sitemap.xml` + canonical link — rejected a twenty-first time on the same
  "marginal payoff for a single-URL site" grounds as every prior log.
- *Trip-duration histogram (a new way to read the data)* — still a mini-epic per 08-24/08-25: a
  seventh chart needs the full skeleton/empty-state/data-table/PNG-export infrastructure every
  existing chart carries.

**Verification:** `node --check` on both real inline scripts (the JSON-LD block fails as always,
expected — not JS). Playwright against the served page (Plotly stubbed; `cdn.plot.ly` blocked in
this sandbox) at 1280px and 375px, light and dark: with nothing focused, pressing `/` moves focus
to `#q`; the `/` hint is visible beforehand and disappears the instant the field gains focus;
typing "israel" fills the field normally (the literal `/` never fires the shortcut mid-query),
filters the registry to 1 of 44 trips, and hides the hint (`:not(:placeholder-shown)`); clearing
the field and focusing the PM `<select>` first, then pressing `/`, leaves focus on the select —
confirming the guard against stealing focus from another form control. Emulated a touchscreen
device (iPhone 12 profile, `hover: none`) and confirmed the hint computes to `display: none`
there. All 6 charts initialize, all 5 KPI cards and all 44 registry rows render, no horizontal
scroll at either width (`scrollWidth === clientWidth`). Console clean bar the pre-existing,
sandbox-only Google Fonts network block noted in every prior log. All three fallback tiers
untouched — the shortcut and hint operate purely on the DOM and `#q`, identically regardless of
which tier populated `trips`.

**Files touched:** `index.html`, `ideas-log.md`

## 2026-08-28 — Stale-refresh warning when the daily pipeline hasn't run recently

**Shipped.** `data/visits.json` already carries `meta.updated`, the date the GitHub Actions
pipeline last committed a refresh, but the tier-1 status badge unconditionally read "Verified
pipeline data" regardless of that date's age — if the daily job silently broke, the site would
keep asserting full confidence in data that might be weeks stale, on a page whose own hero copy
promises "Updated daily." Added a `daysSince()` helper and a threshold check (≥2 days, since the
job runs once daily at 03:00 UTC — a single missed run doesn't fire the warning, but two does) at
the one place tier 1 already reports its status. Past the threshold, the badge switches from the
green "Verified pipeline data" to an amber "Refresh may be delayed," reusing the site's existing
`b-warn` token (the same one "Embedded snapshot" already uses), and the message names the day
count plainly: "…the daily GitHub Actions refresh hasn't run recently… updated 2026-08-15 (13
days ago)." An unparseable or missing `meta.updated` is treated as unknown, not stale — the badge
and message are left exactly as before, since a claim about staleness needs to be verifiable to
be honest. Tiers 2 and 3 are untouched: `live` is fetched at request time (so a staleness clock
doesn't apply) and `fallback` already carries its own warning badge for a different reason.

Fresh find, not a repeat: checked the log's trust/credibility entries (08-13 caveats panel, 08-14
favicon, 08-18 contrast fix, 08-24 theme-color) and none address data currency, and grepping the
log for "stale" turned up only the unrelated 08-11 news-dating work. This is the strongest trust
gap available today — CLAUDE.md names "trust and credibility signals" as a dimension, and the
site's *only* defense against a silently broken pipeline was a viewer noticing the tiny date text
themselves; now a missed refresh is visibly flagged rather than mutely presented as verified. Pure
display-layer logic reading a field the pipeline already writes — no data-provenance touch, and a
data-freshness badge carries no partisan-framing risk of any kind.

**Runners-up**
- *`rel="noopener"` missing on two `target="_blank"` links to `data/visits.json`* (Methodology
  body copy, footer) — confirmed still open (flagged 08-22 through 08-27, seven logs running); a
  real two-attribute fix, but thinner than a silent-failure gap in the site's core trust claim.
- *Keyboard shortcut ("/") to focus the search field* — open since 08-24, deferred five times now;
  still smaller in impact than today's pick.
- `og:image:width`/`og:image:height` meta tags — flagged 08-18 through 08-26 every time as "real
  but minor," same reasoning holds again.
- `robots.txt` + `sitemap.xml` + canonical link — rejected a twentieth time on the same "marginal
  payoff for a single-URL site" grounds as every prior log.
- *"Days abroad this year" cumulative fact* — a fresh "new way to read the data" idea, but a live
  correctness gap in the site's freshness claim outranks a new analytical stat today.

**Verification:** `node --check` on both extracted inline scripts. Unit-checked `daysSince()`
directly (today → 0, 5 days ago → 5, unparseable string/`null`/empty string → `null`). Playwright
against the served page (Plotly stubbed; `cdn.plot.ly` blocked in this sandbox) at 1280px and
375px, light and dark: with the live `data/visits.json` (updated one day before today) — badge
stays "Verified pipeline data," message unchanged. Against a copy of `data/visits.json` with
`meta.updated` rewritten 13 days in the past — badge switches to amber "Refresh may be delayed,"
message correctly names the pipeline gap and "(13 days ago)," screenshot-confirmed in both light
and dark. No horizontal scroll at either width in either data condition. All 5 KPI cards, all 44
registry rows, and all 6 charts (confirmed via cleared `chart-loading` class) render normally in
both conditions. Console clean bar the pre-existing, sandbox-only Google Fonts network block noted
in every prior log. Tiers 2/3 confirmed byte-unchanged via `grep` on their `setStatus()` call
sites. All three fallback tiers untouched — this reads only `data.meta.updated`, already fetched
by tier 1 regardless of the rest of the payload.

**Files touched:** `index.html`, `ideas-log.md`

## 2026-08-27 — Highlight the matched search term in registry rows

**Shipped.** Typing in the registry search box now wraps the matched text in a gold `<mark>` in
the itinerary, country-tag, and PM columns, so a reader can see *why* a row is in the filtered
view instead of just that it is. The underlying filter (`filtered()`) still checks every field
via `JSON.stringify(t)`, not only these three visible columns, so a row can still appear with no
visible highlight (e.g. a match on `visitType` or `sourceMode`) — that's an existing, unchanged
behavior, and the highlight is a "here's a visible reason" aid, not a claim of exhaustiveness.

Implementation note: the registry table previously inserted `t.label`, each country tag, and
`t.pm` unescaped, unlike every other call site in the file (drawer, live-status card), which
already run the same trip fields through `esc()`. Wrapping a match in `<mark>` safely requires
finding the match in the raw text and escaping the three resulting segments independently —
escaping first and searching after would let entity substitution shift the match offset — so the
new `highlightMatch()` helper escapes unconditionally, closing that pre-existing gap as a
byproduct of doing the highlighting correctly, not as a separate fix riding along.

This was the fresh idea flagged as a runner-up on 08-26 ("genuine UX polish for the search box");
picked over 08-26's still-open runner-up, "/" to focus search, because it acts directly on the
existing search box's biggest gap for a journalist scanning 44 rows — no visual link between what
they typed and why a row is there — while "/" only speeds reaching the box, and lost on relative
impact three cycles running (08-24, 08-25, 08-26). `mark.hit` reuses the already-established
`--gold-soft`/`--gold-text` tokens (the site's existing non-accent highlight color, used for the
"currently abroad" headline), not a new color choice.

**Runners-up**
- *`rel="noopener"` missing on two `target="_blank"` links to `data/visits.json`* (Methodology
  body copy, footer) — confirmed still open (flagged 08-22 through 08-26); real, a two-attribute
  fix, but thinner than closing the search box's biggest usability gap.
- *Keyboard shortcut ("/") to focus the search field* — open since 08-24, deferred four times now
  for dimension/impact reasons; still smaller than today's pick.
- `og:image:width`/`og:image:height` meta tags — flagged 08-18 through 08-26 every time as "real
  but minor," same reasoning holds again.
- `robots.txt` + `sitemap.xml` + canonical link — rejected a nineteenth time on the same
  "marginal payoff for a single-URL site" grounds as every prior log.
- *Upgrade `cdn.plot.ly` from `dns-prefetch` to `preconnect`* — fresh idea, real but marginal:
  the script is already `defer`red (08-09) and off the critical render path, so the connection
  warm-up saves little.

**Verification:** `node --check` on both extracted inline scripts (the JSON-LD block fails as
always, expected — not JS). Playwright against the served page (Plotly stubbed; `cdn.plot.ly`
blocked in this sandbox) at 1280px and 375px, light and dark: searching "israel" highlights
"Israel" in both the itinerary and country-tag columns; searching "russia" highlights it in a
single-country row's itinerary/tag and in the itinerary/tag of a "Russia & Austria" multi-country
row, leaving "Austria" unmarked; clearing the box removes every `<mark>`; a search matching only a
hidden field (`"pipeline"` — the field is stored as `"json"`, only rendered as the word
"Pipeline" — a pre-existing quirk, not something this change touches) returns zero rows with no
crash, confirming the helper only ever runs against real column text. Sort-by-date, compact-
columns, and the search highlight all verified working together in the same view. No horizontal
scroll at either width. Console clean bar the pre-existing, sandbox-only Google Fonts network
block noted in every prior log. Screenshots confirm the gold mark reads clearly against both
themes' surface tokens. All three fallback tiers untouched — the feature is pure display logic
over `trips` and `state.q`, already in memory regardless of which tier populated them.

**Files touched:** `index.html`, `ideas-log.md`

## 2026-08-30 — Per-trip browser tab title while the drawer is open

**Shipped.** Opening any trip's drawer — by row click, permalink load, chrono-nav step, or a
related-trips link — now sets `document.title` to that trip's own citation-style label, e.g.
`Malaysia, 7–8 Feb 2026 · India PM Foreign Visits Tracker`, reusing the exact `fmtRange()`
formatting the 08-12 copy-citation feature already established rather than inventing a new date
string. Closing the drawer (Escape, overlay click, or the close button) restores the site's
default title exactly, captured once at load (`DEFAULT_TITLE = document.title`). Before this,
every open trip — cold permalink loads included — left the tab reading the same generic
"India PM Foreign Visits Tracker" regardless of which trip was open, so a journalist with several
permalinks open in different tabs, or in browser history/bookmarks, had no way to tell them apart
without switching to each one. Three lines total: capture the default once, set it in
`openDrawer()`, restore it in `closeDrawer()` — no new helper, no new state.

Deliberately scoped to `document.title` only, not `og:title`/`twitter:title`/meta description:
this is a static single-file site with no server-side rendering, so a social-media crawler
(Twitter, Slack, Facebook) fetches the raw HTML and never runs this JS — mutating those tags
client-side would look like a fix but wouldn't change a single shared-link preview.
`document.title` is the one piece of this idea that's actually true in a static site: it's read
directly by the browser (tab title, history entry, bookmark name), so it's the only part worth
shipping.

Fresh find, not a repeat: it sits directly on the permalink (08-07), copy-citation (08-12), and
chrono-nav (08-26) infrastructure the log has built up over six weeks, but no prior entry names
tab-title identity as a gap. Chosen over the standing backlog because both remaining old items
(`rel="noopener"`, `og:image` dimensions) were re-examined and are genuinely thin — the
`noopener` gap is on two links to a same-origin JSON file, so the reverse-tabnabbing risk it
guards against doesn't actually apply, and `og:image` sizing only saves a crawler one
fetch-and-measure round trip. Neither outranks giving journalists a real way to tell open trip tabs
apart, which today's fresh brainstorm also confirmed nothing else beat.

**Runners-up**
- `rel="noopener"` missing on two `target="_blank"` links to `data/visits.json` (Methodology body
  copy, footer) — open since 08-22 (nine logs running); re-examined today and downgraded: both
  targets are the site's own same-origin JSON file, so `noopener`'s actual security purpose
  (blocking a malicious tab from reaching back via `window.opener`) doesn't apply here. Real
  correctness nit, essentially zero risk in practice — leaving it open rather than shipping a
  cosmetic-only fix.
- *"Days abroad this year" cumulative fact* — flagged fresh 08-28; on inspection, a year-scoped
  variant of the existing "Days abroad" KPI is largely redundant with just filtering Year, so it
  reads as thin rather than a genuinely new way to read the data. Not carried forward.
- `og:image:width`/`og:image:height` meta tags — flagged 08-18 through 08-26 every time as "real
  but minor," same reasoning holds again.
- `robots.txt` + `sitemap.xml` + canonical link — rejected a twenty-second time on the same
  "marginal payoff for a single-URL site" grounds as every prior log.
- *Trip-duration histogram (a new way to read the data)* — still a mini-epic per 08-24/08-25: a
  seventh chart needs the full skeleton/empty-state/data-table/PNG-export infrastructure every
  existing chart carries.

**Verification:** `node --check` on both extracted inline scripts. Playwright against the served
page (Plotly stubbed; `cdn.plot.ly` blocked in this sandbox) at 1280px and 375px, light and dark:
default tab title is the site name on load; clicking a mid-list row sets the title to that trip's
label + date range; clicking "Later" in the chrono nav updates the title to the new trip without
closing the drawer; Escape and overlay-click both revert the title to the exact default string;
loading a cold `?trip=<slug>` permalink sets the correct per-trip title immediately, before any
click. All 5 KPI cards, all 6 charts, and all 44 registry rows render at both widths; no
horizontal scroll (`scrollWidth === clientWidth`) at either. Console clean bar the pre-existing,
sandbox-only `cdn.plot.ly`/Google Fonts network blocks noted in every prior log. All three
fallback tiers untouched — the change reads only the in-memory `trip` object already used by the
open drawer, identically regardless of which tier populated `trips`.

**Files touched:** `index.html`, `ideas-log.md`

## 2026-08-31 — Enrich the Dataset JSON-LD for Google Dataset Search

**Shipped.** The page's `schema.org/Dataset` block had only the bare minimum
(`name`/`description`/`url`/`license`/`creator`/`distribution`) — nothing that helps Google Dataset
Search (datasetsearch.research.google.com), the one still-active discoverability channel this
dataset was never marked up for, actually surface or describe it. Added the fields Google's own
dataset-markup guidance calls out: `keywords` (generic terms — India, Prime Minister, foreign
visits, diplomacy, open data — deliberately no PM or party names, so the markup can't read as
promoting any administration), `inLanguage`, `spatialCoverage` ("Worldwide — bilateral and
multilateral foreign visits by India's Prime Minister", since visits span 59+ countries rather than
one place), `variableMeasured` (five `PropertyValue` entries describing the PM/country/dates/visit-
type fields the dataset actually carries), and `temporalCoverage` as an ISO 8601 interval computed
from the real min trip-start/max trip-end in `allTrips` (`2021-03-26/2026-07-11` today) — patched
in `updateSeoMeta()` alongside the `description`/`dateModified` fields that function already
updates on every load, so it stays accurate as new trips land daily. The static, non-data-dependent
fields (`keywords`, `inLanguage`, `spatialCoverage`, `variableMeasured`) are authored directly in
the JSON-LD block rather than built in JS, matching the comment already there distinguishing static
from runtime-patched fields.

Chosen over the FAQPage-schema idea for the methodology caveats section: that would target a
channel (FAQ rich results) Google restricted to authoritative government/health sites in August
2023, so the payoff for this site specifically is close to zero now — thinner than it looks. Dataset
markup, by contrast, is exactly what Google Dataset Search indexes on, and directly serves the
"researchers" audience this project is built for.

**Runners-up**
- *FAQPage JSON-LD on the caveats `<details>` section* — see above; deprioritized once checked
  against Google's actual current FAQ rich-result eligibility.
- *"Average trip duration" as a fourth registry fact* — new-way-to-read-the-data idea, but it's
  arithmetic a reader can already do from the existing "Days abroad" and "Trips" KPIs sitting next
  to each other; thinner than genuinely new metadata.
- *Copy-current-filtered-view link button* — `writeUrlState()` already keeps the browser URL bar
  live in sync with every filter change via `pushState`, so a dedicated copy button would duplicate
  what's already one Ctrl+L away.
- `robots.txt` + `sitemap.xml` + canonical link — rejected a twenty-third time on the same
  "marginal payoff for a single-URL site" grounds as every prior log.
- *Lazy-render below-the-fold charts via IntersectionObserver* — re-flagged since 08-16; Plotly's
  already deferred (08-09) and gated on `plotlyReady`, so a second render-gating path still doesn't
  clearly pay for itself.

**Verification:** the JSON-LD block parses as valid JSON (Python `json.loads`) both statically and
after runtime patching. `node --check` on both extracted inline scripts. Playwright against the
served page at 1280px and 375px: with `cdn.plot.ly` blocked (this sandbox's standing constraint),
the only console error is the expected `Plotly is not defined` from `renderChartsInner` — same as
every prior log; with Plotly stubbed, console is fully clean, all six charts reveal
(`chart-loading` count 0), all 5 KPI cards and all 44 registry rows render, no horizontal scroll at
either width. Confirmed `updateSeoMeta()` runs identically from all three fallback-tier call sites
(`data/visits.json`, Jina live mirror, embedded snapshot), so `temporalCoverage` computes correctly
regardless of which tier populated `trips`. `dateModified` and `description` continue patching as
before — this change only adds fields alongside them, touching no existing key.

**Files touched:** `index.html`, `ideas-log.md`

## 2026-08-31 — Fix the choropleth: one canonical country name per destination

**User-reported bug, not a brainstormed idea.** The map coloring was not uniform — the United
States showed as barely visited despite four trips.

**Cause:** the registry spells the same destination several ways across the years — `USA`,
`United States of America (USA)`, `UAE`, `United Arab Emirates (UAE)`, `Dubai`,
`Samarkand, Uzbekistan`. Each spelling became its own bucket in `countryCounts`, so the choropleth
handed Plotly the same country two or three times; Plotly drew one path per location and the last
one painted (the low-count alias) won, leaving the US at the pale end of the scale. `Samarkand`
also counted as a nation of its own, inflating "Unique countries" to 59 when it is 54.

**Shipped:**
- `COUNTRY_CANON` + `canonCountry()` in `normalizeTrips`: every split destination resolves to one
  canonical name (the form Plotly's country-name lookup uses), parenthetical aliases stripped,
  city rows resolved to their country, duplicates dropped per trip. Everything downstream —
  KPIs, filters, ranking, monthly countries, CSV, globe coords — reads the corrected list. The
  itinerary label itself is still displayed exactly as published.
- `geo.resolution: 50` — the default 110m world has *no polygon at all* for Seychelles, Maldives,
  Mauritius or Singapore, so those visits were uncolored no matter what the data said.
- `--ch-map-low` was within a couple of RGB points of `--ch-land` in both themes, so a
  once-visited country read as unvisited; stepped it onto the accent hue (`#cfe1de` / `#1e3c3d`).
- Methodology caveat now documents the canonicalization.

**Rejected alternatives:** switching the trace to `locationmode: 'ISO-3'` with a name→ISO3 table —
deterministic, but any future destination missing from the table would vanish from the map
silently, and it would fix only the map while leaving the counts and filters fragmented.
Canonicalizing at `normalizeTrips` fixes the defect at its source for every consumer.

**Verification:** against the served page — 54 locations, zero duplicates, zero empty-geometry
paths (was 6), United States `z=4` painted once at the dark end, `coordOf()` resolves all 54
canonical names for the globe visual, filtering by "United States" returns the expected 4 trips
with their original labels intact. Console clean at 1280px and 375px, no horizontal scroll, both
themes checked. All three fallback tiers share `normalizeTrips`, so none is privileged or altered.

**Files touched:** `index.html`, `ideas-log.md`

## 2026-09-01 — Clickable country tags in the registry table

**Shipped.** The country pills in the registry's "Countries" column (e.g. "Indonesia", "Australia",
"New Zealand" on one row) were plain, inert `<span>`s — a reader curious about one destination had
to reach up to the Country dropdown and re-select it by hand. They're now real `<button>`s: clicking
one sets the Country filter to that exact value, the same state change the dropdown's own `onchange`
makes, reusing `writeUrlState()`/`render()` unmodified — no new filter semantics, no new state shape.
Multi-country rows work per-tag (clicking "New Zealand" filters to New Zealand, not the row's first
country); the button carries `data-country` read straight from `t.countries`, so no parsing or
attribute-decoding logic was added. Visually the buttons are byte-for-byte the existing `.tag` pill
styling with UA button chrome reset off (`font/margin/appearance`) plus a hover/focus-visible tint
matching the pattern already used for `.drawer-related-link`/`.drawer-chrono-btn`.

Two correctness issues caught and fixed before shipping, not after: (1) the registry's single
delegated click/keydown listeners on `#tripTable` unconditionally opened the trip drawer for any
click/Enter inside a `tr[data-trip]` — a nested `<button>` needed an explicit early-return guard in
*both* handlers (click and keydown) or pressing Enter on a tag would filter *and* open the drawer in
the same keystroke; (2) `render()` replaces `tbody` wholesale on every filter change, destroying the
very button a keyboard user just activated — added one line moving focus to the (persistent) Country
`<select>` afterward, so a keyboard user isn't dropped back to `<body>` with no orientation.

Fresh find: grepped the log for "clickable"/tag-related entries and found only the unrelated 08-25
drawer cross-links (which navigate between whole trips, not filter by a single field). No prior entry
proposed turning the registry's own tags into filters. Chosen over the standing thin items
(`rel="noopener"`, `og:image` dimensions, `robots.txt`/sitemap — all repeatedly logged as real but
marginal) because this closes an actual passive-vs-interactive gap in the table every visitor already
scans, costs one clearly-scoped choke point (one template line, two delegated-handler guards, one new
function), and carries zero non-partisan risk — it changes how a reader *navigates* the data, not what
any chart or stat says about any PM.

**Runners-up**
- *`rel="noopener"` on the two `data/visits.json` links* — open since 08-22 (now eleven logs), and
  already downgraded 08-30 to "cosmetic-only" since both targets are same-origin JSON; the security
  rationale doesn't actually apply. Left open rather than shipped for its own sake.
- *`og:image:width`/`og:image:height` meta tags* — flagged 08-18 through 08-24 every time as "real but
  minor," same call again; a crawler saves one fetch-and-measure round trip.
- *`robots.txt` + `sitemap.xml` + canonical link* — rejected a twenty-fourth time on the same
  "marginal payoff for a single-URL site" grounds as every prior log.
- *Trip-duration histogram (a new way to read the data)* — still a mini-epic per 08-24/08-25: a
  seventh chart needs the full skeleton/empty-state/data-table/PNG-export infrastructure every
  existing chart carries.
- *Preconnect to `cdn.plot.ly`* — marginal now that the script load is already deferred (08-09) and
  off the critical render path.

**Verification:** `node --check`-equivalent (`new Function`) on both real inline script blocks passes
(the JSON-LD block fails as always, expected — not JS). Playwright against the served page (Plotly
stubbed; `cdn.plot.ly` blocked in this sandbox, per every prior log) at 1280px and 375px: country tags
render as `button.tag`; clicking one sets `#country`'s value to that exact country, pushes `?country=`
into the URL, moves focus to the select, and updates the live result count ("44 trips" → "3 of 44
trips"); a multi-country row's second tag filters to *its own* country, not the row's first; focusing
a tag and pressing Enter filters and leaves the drawer closed (confirms the click/keydown guards both
work — this was the one genuine risk in the change); clicking elsewhere in the same row still opens
the drawer as before; combining an active PM filter with a tag click produces no console error;
search-term `<mark>` still renders correctly nested inside the button; Compact-columns mode still
shows the Countries column; all 5 KPIs and all 44 registry rows render; no page-level horizontal
scroll at either width. Full-page screenshots confirm the hover/focus tint reads clearly in light mode
and the pill styling is unchanged in dark mode and on the 375px horizontally-scrolling table. Console
clean bar the pre-existing, sandbox-only `cdn.plot.ly`/Google Fonts network blocks noted in every
prior log. All three fallback tiers untouched — the change reads only `t.countries`, already produced
by `normalizeTrips` identically regardless of which tier populated `trips`.

**Files touched:** `index.html`, `ideas-log.md`
