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
