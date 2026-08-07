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
