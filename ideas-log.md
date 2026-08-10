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
