#!/usr/bin/env python3
"""
Refresh the PM foreign-visits dataset and the live-trip news feed.

Writes two files consumed by the static site:
  - data/visits.json : every foreign visit parsed from the official PM India
                       registry. Authoritative; drives the dataset, charts, table.
  - data/news.json   : third-party news coverage for the current/most-recent trip,
                       plus an optional "reported" block for a trip that credible
                       news corroborates but the registry has not yet published.

The reported block NEVER enters visits.json — it only powers the live status
band, clearly labelled as unofficial, and disappears once the registry catches
up or the news goes quiet.

Article dating — why this is more careful than it looks
------------------------------------------------------
Google News search feeds do NOT return a stable per-article publication time.
The same article URL is served with different <pubDate> values on different
days, and sometimes with two dates 70+ days apart *within a single run* across
two query feeds. Observed on one URL:
    fetched 2026-08-03 -> 2026-08-02
    fetched 2026-08-10 -> 2026-08-09
    fetched 2026-08-11 -> 2026-08-10  and  2026-05-29  (same run)
Its pubDate tracks cluster freshness, not publication. Trusting it verbatim is
what made week-old coverage of a finished tour appear as today's reporting on
the next one.

So a published date is only ever revised *downward*:
  1. dedupe by URL and keep the EARLIEST pubDate seen across all query feeds;
  2. carry a first-seen ledger (news.json -> "seen": url digest -> earliest date
     ever recorded) so a date Google later inflates cannot drift upward again.
     An article cannot have been published after we first saw it.
Disagreement between observations is itself proof the feed's date is unreliable,
so the conservative bound is the honest one; articles it ages out simply drop.
The ledger was seeded from this file's own git history (58 URLs, Jun–Aug 2026).

Recency alone cannot separate consecutive tours (PM tours often fall less than
two weeks apart), so trip membership is also gated on relevance: an article must
name a country of the current trip as a destination, and must not name more
non-trip destinations than trip ones — which is how a five-nation-tour headline
stops being filed under a two-country trip that merely shares one leg.

What a headline actually claims
-------------------------------
Matching a country name near a travel word is not the same as reading the news.
Three kinds of story name a country beside a travel cue while saying the PM is
*not* abroad, and each one produced a false "reportedly abroad" band:
    reversed  "Bangladesh PM Likely To Visit India Next Week"  (someone else,
              travelling the other way — this one shipped as a Bangladesh trip)
    negated   "Bangladesh PM Refuses to Visit India Until …"
    prospective "… India visit uncertain as Dhaka, Delhi discuss dates"
So a country mention that is really a person ("Bangladesh PM") is not a
destination, travel *to India* by a foreign leader disqualifies the headline
outright, and the live band additionally requires headlines that assert a trip
in progress — with at least one report placing him on the ground.

Run locally the same way the GitHub Action runs it:
    python3 scripts/refresh.py
Optional: parse a saved registry dump instead of fetching live:
    python3 scripts/refresh.py --registry /tmp/registry.txt
"""
import re, json, sys, html, hashlib, pathlib, datetime, email.utils, urllib.request, urllib.parse
from collections import defaultdict

# Article-dating and trip-window tuning. The window is deliberately tight: a
# generous window (e.g. +/- 14 days) is wider than the gap between consecutive
# tours, so it would re-admit exactly the cross-trip coverage this guards against.
FIRST_SEEN_KEEP_DAYS = 120  # ledger retention; keeps news.json small
FIRST_SEEN_MAX_ENTRIES = 800  # hard cap so the browser's news.json stays small
NEWS_LEAD_IN_DAYS = 3       # pre-departure previews ("PM leaves Friday")
NEWS_LAG_DAYS = 4           # post-return wrap-ups and readouts
REPORTED_SPAN_DAYS = 6      # matches detect_reported_trip's detection window

ROOT = pathlib.Path(__file__).resolve().parent.parent
REGISTRY_URL = "http://www.pmindia.gov.in/en/details-of-foreigndomestic-visits/"
JINA_URL = "https://r.jina.ai/" + REGISTRY_URL

MONTHS = {
    "Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04", "May": "05", "Jun": "06",
    "Jul": "07", "Aug": "08", "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12",
    "January": "01", "February": "02", "March": "03", "April": "04", "June": "06",
    "July": "07", "August": "08", "September": "09", "October": "10",
    "November": "11", "December": "12",
}
_MONTH_ALT = "|".join(sorted(MONTHS.keys(), key=len, reverse=True))
ANCHOR = re.compile(r"\d{1,2}\s*[–—-]\s*\d{1,2}\s+(?:%s)|\d{1,2}\s+(?:%s)" % (_MONTH_ALT, _MONTH_ALT))

# Country gazetteer for detecting a reported trip from news headlines. Aliases map
# to a display name. Ordered longest-first at match time so multiword names win.
COUNTRY_ALIASES = {
    "United States of America": "USA", "United States": "USA", "U.S.": "USA", "USA": "USA", "America": "USA",
    "United Kingdom": "UK", "U.K.": "UK", "UK": "UK", "Britain": "UK",
    "United Arab Emirates": "UAE", "UAE": "UAE", "Abu Dhabi": "UAE", "Dubai": "UAE",
    "New Zealand": "New Zealand", "Papua New Guinea": "Papua New Guinea", "Sri Lanka": "Sri Lanka",
    "South Africa": "South Africa", "South Korea": "South Korea", "North Korea": "North Korea",
    "Saudi Arabia": "Saudi Arabia", "Trinidad and Tobago": "Trinidad & Tobago", "Trinidad & Tobago": "Trinidad & Tobago",
    "Czech Republic": "Czechia", "Czechia": "Czechia",
}
COUNTRY_SIMPLE = [
    "Indonesia", "Australia", "Japan", "China", "Russia", "France", "Germany", "Italy", "Spain",
    "Portugal", "Netherlands", "Belgium", "Sweden", "Norway", "Denmark", "Finland", "Poland",
    "Austria", "Switzerland", "Greece", "Croatia", "Slovakia", "Slovenia", "Hungary", "Ireland",
    "Cyprus", "Malta", "Ukraine", "Canada", "Mexico", "Brazil", "Argentina", "Chile", "Peru",
    "Colombia", "Guyana", "Egypt", "Ethiopia", "Kenya", "Nigeria", "Ghana", "Tanzania", "Uganda",
    "Namibia", "Mozambique", "Rwanda", "Mauritius", "Seychelles", "Comoros", "Madagascar",
    "Israel", "Jordan", "Oman", "Qatar", "Kuwait", "Bahrain", "Iran", "Iraq", "Turkey", "Turkiye",
    "Lebanon", "Palestine", "Nepal", "Bhutan", "Bangladesh", "Maldives", "Pakistan", "Afghanistan",
    "Myanmar", "Thailand", "Malaysia", "Singapore", "Brunei", "Vietnam", "Cambodia", "Laos",
    "Philippines", "Mongolia", "Kazakhstan", "Uzbekistan", "Kyrgyzstan", "Tajikistan",
    "Turkmenistan", "Azerbaijan", "Armenia", "Georgia", "Fiji", "Samoa", "Tonga", "Bahamas",
    "Jamaica", "Cuba", "Venezuela", "Ecuador", "Bolivia", "Uruguay", "Paraguay", "Panama",
    "Morocco", "Tunisia", "Algeria", "Angola", "Zambia", "Zimbabwe", "Botswana", "Senegal",
    "Romania", "Bulgaria", "Serbia", "Estonia", "Latvia", "Lithuania", "Iceland", "Luxembourg",
    "Vatican", "Kuwait", "Yemen", "Syria",
]
COUNTRY_MAP = dict(COUNTRY_ALIASES)
for c in COUNTRY_SIMPLE:
    COUNTRY_MAP.setdefault(c, c)
# Regex alternation, longest phrase first so "New Zealand" beats "Zealand", etc.
_COUNTRY_PATTERNS = sorted(COUNTRY_MAP.keys(), key=len, reverse=True)
COUNTRY_RE = re.compile(r"\b(" + "|".join(re.escape(p) for p in _COUNTRY_PATTERNS) + r")\b", re.I)
_CANON_LOOKUP = {k.lower(): v for k, v in COUNTRY_MAP.items()}


def month_num(name):
    return MONTHS.get(name, MONTHS.get(name[:3].title(), "01"))


def fetch(url, timeout=45):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (pm-visits-tracker)"})
    return urllib.request.urlopen(req, timeout=timeout).read().decode("utf-8", "replace")


def parse_date_range(ds):
    ds = ds.replace("–", "-").replace("—", "-")
    m = re.match(r"\s*(\d{1,2})\s*-\s*(\d{1,2})\s+([A-Za-z]+)\s*,?\s*(\d{4})", ds)
    if m:
        y, mm = m.group(4), month_num(m.group(3))
        return f"{y}-{mm}-{m.group(1).zfill(2)}", f"{y}-{mm}-{m.group(2).zfill(2)}"
    m = re.match(r"\s*(\d{1,2})\s+([A-Za-z]+)\s*-\s*(\d{1,2})\s+([A-Za-z]+)\s*,?\s*(\d{4})", ds)
    if m:
        y = m.group(5)
        return f"{y}-{month_num(m.group(2))}-{m.group(1).zfill(2)}", f"{y}-{month_num(m.group(4))}-{m.group(3).zfill(2)}"
    m = re.match(r"\s*(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})\s*-\s*(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", ds)
    if m:
        return (f"{m.group(3)}-{month_num(m.group(2))}-{m.group(1).zfill(2)}",
                f"{m.group(6)}-{month_num(m.group(5))}-{m.group(4).zfill(2)}")
    return None


def parse_trips(text):
    trips = []
    for line in text.splitlines():
        line = line.strip()
        m = re.match(r"^(\d+)\s+(.+)$", line)
        if not m:
            continue
        rest = m.group(2)
        a = ANCHOR.search(rest)
        if not a:
            continue
        label = rest[:a.start()].strip()
        if not label:
            continue
        r = parse_date_range(rest[a.start():])
        if not r:
            continue
        trips.append({"label": label, "start": r[0], "end": r[1], "pm": "Narendra Modi"})
    trips.sort(key=lambda t: t["start"], reverse=True)
    return trips


def split_countries(label):
    s = re.sub(r"\s+and\s+", ", ", label, flags=re.I)
    s = s.replace(" & ", ", ")
    return [c.strip() for c in s.split(",") if c.strip()]


def human_join(names):
    if len(names) <= 1:
        return names[0] if names else ""
    return ", ".join(names[:-1]) + " & " + names[-1]


def pick_focus_trip(trips, today):
    ongoing = [t for t in trips if t["start"] <= today <= t["end"]]
    if ongoing:
        return ongoing[0], "ongoing"
    upcoming = sorted([t for t in trips if t["start"] > today], key=lambda t: t["start"])
    if upcoming:
        return upcoming[0], "upcoming"
    past = [t for t in trips if t["end"] < today]
    if past:
        return past[0], "recent"
    return (trips[0], "recent") if trips else (None, None)


def parse_pubdate(s):
    """RFC 2822 -> naive UTC datetime, or None.

    Uses the stdlib RFC 2822 parser so numeric offsets (+0530) and named zones
    both work, then normalises to UTC so every comparison and the date we
    publish share one timezone. Previously this only handled GMT/UTC literals
    and truncated the string at 31 chars.
    """
    if not s or not s.strip():
        return None
    try:
        dt = email.utils.parsedate_to_datetime(s.strip())
    except (TypeError, ValueError):
        return None
    if dt is None:
        return None
    if dt.tzinfo is not None:
        dt = dt.astimezone(datetime.timezone.utc).replace(tzinfo=None)
    return dt


def google_news(query):
    url = "https://news.google.com/rss/search?q=" + urllib.parse.quote(query) + "&hl=en-IN&gl=IN&ceid=IN:en"
    items = []
    try:
        xml = fetch(url, timeout=30)
    except Exception as e:
        print(f"[news] fetch failed for {query!r}: {e!r}", file=sys.stderr)
        return items
    for block in re.findall(r"<item>(.*?)</item>", xml, re.S):
        t = re.search(r"<title>(.*?)</title>", block, re.S)
        l = re.search(r"<link>(.*?)</link>", block, re.S)
        s = re.search(r"<source[^>]*>(.*?)</source>", block, re.S)
        d = re.search(r"<pubDate>(.*?)</pubDate>", block, re.S)
        if not t or not l:
            continue
        title = html.unescape(re.sub(r"<[^>]+>", "", t.group(1))).strip()
        source = html.unescape(s.group(1)).strip() if s else ""
        if source and title.endswith(" - " + source):
            title = title[: -(len(source) + 3)].strip()
        raw = d.group(1).strip() if d else ""
        dt = parse_pubdate(raw)
        if raw and dt is None:
            print(f"[news] unparseable pubDate {raw!r} — skipping {title[:60]!r}", file=sys.stderr)
            continue
        if dt is None:
            print(f"[news] no pubDate — skipping {title[:60]!r}", file=sys.stderr)
            continue
        items.append({"title": title, "source": source, "url": l.group(1).strip(),
                      "date": dt.date().isoformat(), "dt": dt, "rawDate": raw})
    return items


def collect_news(queries):
    """Fetch every query and merge by URL, keeping the earliest pubDate seen.

    Cross-feed disagreement about one URL is the feed telling on itself; the
    earliest observation is the only defensible bound on publication time.
    """
    merged, conflicts = {}, 0
    for q in queries:
        for it in google_news(q):
            prev = merged.get(it["url"])
            if prev is None:
                merged[it["url"]] = it
                continue
            if it["dt"] < prev["dt"]:
                conflicts += 1
                print(f"[news] feed disagreement on one URL: {prev['date']} vs {it['date']} "
                      f"-> keeping {it['date']} | {it['title'][:60]!r}", file=sys.stderr)
                merged[it["url"]] = it
            elif it["dt"] > prev["dt"]:
                conflicts += 1
                print(f"[news] feed disagreement on one URL: {prev['date']} vs {it['date']} "
                      f"-> keeping {prev['date']} | {it['title'][:60]!r}", file=sys.stderr)
    if conflicts:
        print(f"[news] {conflicts} cross-feed date conflict(s) resolved to the earliest date",
              file=sys.stderr)
    return list(merged.values())


def url_key(url):
    """Short digest of an article URL — the ledger's key.

    Google News URLs are ~250-character blobs and the ledger holds hundreds of
    them; storing them verbatim made news.json 220 KB, which the browser then
    fetched on every page load. A 12-hex digest keeps it a few KB. The ledger is
    pipeline bookkeeping only — the page never reads it.
    """
    return hashlib.sha1(url.encode("utf-8")).hexdigest()[:12]


def load_ledger(news_path):
    """First-seen ledger from the previous news.json: url digest -> earliest date."""
    if not news_path.exists():
        return {}
    try:
        prev = json.loads(news_path.read_text())
    except (ValueError, OSError) as e:
        print(f"[news] could not read existing news.json for the ledger: {e!r}", file=sys.stderr)
        return {}
    seen = prev.get("seen")
    return dict(seen) if isinstance(seen, dict) else {}


def apply_ledger(items, ledger, today_iso):
    """Clamp each article's date to the earliest we have ever recorded for it.

    Publication cannot post-date our first sighting, so the ledger only ever
    lowers a date. Mutates items and returns the updated ledger.
    """
    for it in items:
        k = url_key(it["url"])
        floor = min([d for d in (ledger.get(k), it["date"], today_iso) if d])
        if floor == it["date"]:
            it["dateSource"] = "rss"
        elif floor == ledger.get(k):
            it["dateSource"] = "first-seen"
        else:
            it["dateSource"] = "clamped"  # feed claimed a future date
        if floor != it["date"]:
            print(f"[news] date revised down {it['date']} -> {floor} (first seen) | "
                  f"{it['title'][:60]!r}", file=sys.stderr)
            it["date"] = floor
            it["dt"] = datetime.datetime.strptime(floor, "%Y-%m-%d")
        ledger[k] = floor
    return ledger


def prune_ledger(ledger, today):
    """Drop entries past retention, newest first, capped — bounds news.json size."""
    cutoff = (today - datetime.timedelta(days=FIRST_SEEN_KEEP_DAYS)).isoformat()
    fresh = [(k, d) for k, d in ledger.items() if d >= cutoff]
    fresh.sort(key=lambda kv: kv[1], reverse=True)
    return dict(fresh[:FIRST_SEEN_MAX_ENTRIES])


def trip_window(start, end, as_of):
    """Inclusive ISO date window of coverage that belongs to this trip.

    Registry trips have real dates, so the window hugs the trip itself. A
    news-reported trip has none, so it anchors on the freshest signal and spans
    the same lookback the detector used.
    """
    def shift(iso, days):
        return (datetime.date.fromisoformat(iso) + datetime.timedelta(days=days)).isoformat()
    if start and end:
        return shift(start, -NEWS_LEAD_IN_DAYS), shift(end, NEWS_LAG_DAYS)
    if as_of:
        return shift(as_of, -REPORTED_SPAN_DAYS), shift(as_of, NEWS_LAG_DAYS)
    return None, None


def article_matches_trip(title, trip_countries):
    """True when the headline reads as coverage of *this* trip.

    Requires a named destination on the itinerary, and rejects headlines whose
    destinations are mostly elsewhere — that is a different tour's article that
    happens to share a leg.
    """
    if not trip_countries:
        return True, ""
    dests = destination_countries(title)
    if not dests:
        return False, "no destination country named"
    inside = [d for d in dests if d in trip_countries]
    outside = [d for d in dests if d not in trip_countries]
    if not inside:
        return False, f"destinations {'/'.join(dests)} not on this trip"
    if len(outside) > len(inside):
        return False, f"mostly other destinations ({'/'.join(outside)})"
    return True, ""


def select_trip_articles(items, trip_countries, window, limit=6):
    """Date- and relevance-filter articles for one trip, newest first, deduped.

    Returns every qualifying article (the caller's articles_out applies the
    display limit) so a corroboration count can reflect all of them.
    """
    lo, hi = window
    kept, seen_titles = [], set()
    for a in sorted(items, key=lambda x: x["dt"], reverse=True):
        reason = ""
        key = a["title"].lower()
        if key in seen_titles:
            reason = "duplicate headline"
        elif lo and a["date"] < lo:
            reason = f"published before window ({lo})"
        elif hi and a["date"] > hi:
            reason = f"published after window ({hi})"
        else:
            ok, why = article_matches_trip(a["title"], trip_countries)
            if not ok:
                reason = why
        if reason:
            print(f"[news] FILTERED {a['date']} | {reason} | {a['title'][:70]!r}", file=sys.stderr)
            continue
        seen_titles.add(key)
        kept.append(a)
        print(f"[news] INCLUDED {a['date']} | {a['source'][:18]} | {a['title'][:70]!r}", file=sys.stderr)
    print(f"[news] {len(items)} candidate(s) -> {len(kept)} kept -> {min(len(kept), limit)} published",
          file=sys.stderr)
    return kept


def find_countries(text):
    found = []
    for m in COUNTRY_RE.finditer(text):
        canon = _CANON_LOOKUP.get(m.group(1).lower())
        if canon and canon != "India" and canon not in found:
            found.append(canon)
    return found


# Travel/destination cues. A country only counts as a trip leg when one of these
# sits near it in the headline — so "arrives in Australia" credits Australia, but
# "counter China" / "amid China rivalry" (framing, not a destination) does not.
DEST_CUE_RE = re.compile(
    r"arriv|\bland(?:s|ed|ing)?\b|reach(?:es|ed)?|\bvisit|\btour|welcom|receiv|\bhost|"
    r"greet|bilateral|\bsummit|\bties\b|new chapter|upgrade|state visit|three-nation|two-nation|"
    r"nation (?:trip|tour|visit)|touches down|\ben route", re.I)


# A country named beside a travel cue is still not proof the PM went there.
# Three classes of headline read as a trip to a naive match and are not one:
#   direction   "Bangladesh PM to visit India"  - inbound travel by someone else
#   negation    "refuses to visit", "trip called off", "visit postponed"
#   prospect    "likely to visit", "may travel next week", "dates uncertain"
# Direction decides *whose* trip a story is about, so it is filtered everywhere.
# Negation and prospect bear only on whether a trip is happening *now*, so they
# gate the reported-trip banner while remaining valid coverage of a real trip.

# "<Country> PM/President/…" names a person, not a destination.
LEADER_TITLE_RE = re.compile(
    r"^(?:['’]s)?\s+(?:PM\b|Prime Minister|President|King\b|Queen\b|Chancellor|Premier|"
    r"Emir\b|Sultan|Crown Prince|Foreign Minister|Foreign Secretary|Ambassador|Envoy|"
    r"Minister|Delegation|Government|Govt\b|Cabinet|Counterpart|Leader\b)", re.I)

# …unless that leader is receiving the PM — "Israel President welcomes Modi"
# still places him in Israel.
PM_AS_GUEST_RE = re.compile(r"(?:welcom|receiv|host|greet)\w*[^.]{0,24}\bModi\b", re.I)

# Travel *towards* India. Paired with a foreign leader as the subject, the story
# is about someone else's inbound visit, not about the PM being abroad.
INBOUND_INDIA_RE = re.compile(
    r"\bIndia (?:visit|trip|tour)\b|\bvisits? (?:to )?India\b|\bvisiting India\b|"
    r"\b(?:trip|tour) to India\b|"
    r"\b(?:arriv|land|reach|head|travel|fly|flies|com)\w*\s+(?:in|to)\s+India\b", re.I)


def destination_countries(title):
    low = title.lower()
    inbound = INBOUND_INDIA_RE.search(title)
    pm_is_guest = PM_AS_GUEST_RE.search(title)
    out = []
    for m in COUNTRY_RE.finditer(title):
        canon = _CANON_LOOKUP.get(m.group(1).lower())
        if not canon or canon == "India" or canon in out:
            continue
        if LEADER_TITLE_RE.match(title[m.end():m.end() + 40]) and not pm_is_guest:
            if inbound:
                return []  # that leader is travelling to India — not the PM's trip
            continue       # a person, not a place; other mentions may still count
        window = low[max(0, m.start() - 34): m.end() + 34]
        if DEST_CUE_RE.search(window):
            out.append(canon)
    return out


NEGATED_RE = re.compile(
    r"refus\w*|cancel\w*|call(?:s|ed)? off|postpon\w*|defer(?:s|red)?|scrapp?\w*|shelv\w*|"
    r"snub\w*|\bskips?\b|declin\w*|rules? out|ruled out|no plans|won['\u2019]?t\b|will not\b|"
    r"pull(?:s|ed)? out|abandon\w*|denies?\b|\bnot (?:to )?visit\b", re.I)

SPECULATIVE_RE = re.compile(
    r"\b(?:likely|expected|set|slated|due|poised|planning|planned|proposed|scheduled)\s+to\b|"
    r"\b(?:may|might|could|will|would|to)\s+(?:soon\s+)?"
    r"(?:visit|travel|arrive|land|head|fly|tour|go|embark|attend)\b|"
    r"\buncertain\b|\bin talks\b|\bmull\w*|\bweigh(?:s|ing)\b|\bconsider(?:s|ing)\b|"
    r"\bahead of\b|\bnext (?:week|month)\b|\bplans? (?:a |an |his )?(?:visit|trip|tour)\b|"
    r"\bawait\w*", re.I)

# Hard evidence of the PM on the ground, as opposed to a trip being discussed.
ON_GROUND_RE = re.compile(
    r"\barriv\w+|\bland(?:s|ed|ing)\b|\breach(?:es|ed)\b|touch(?:es|ed)? down|\bis in\b|"
    r"\bbegins?\b|\bkick(?:s|ed)? off|\bconclude\w*|\bwrap(?:s|ped)? up|\bholds? talks\b|"
    r"\bwelcomed\b|\breceiv\w+ (?:a )?(?:ceremonial|guard|red[- ]carpet|grand|warm) welcome|"
    r"\bstate visit to\b|\bon (?:a )?(?:two|three|four|five|six|seven)[- ]day\b", re.I)


def presence_claim(title):
    """Can this headline support the claim that the PM is abroad *now*?

    Returns (ok, reason). A negated trip never can. A prospective one can only
    when the same headline also reports him on the ground — "arrives in X,
    likely to meet Y" is a current trip; "likely to visit X" is not.
    """
    m = NEGATED_RE.search(title)
    if m:
        return False, f"trip negated ({m.group(0).lower()})"
    m = SPECULATIVE_RE.search(title)
    if m and not ON_GROUND_RE.search(title):
        return False, f"prospective, not current ({m.group(0).lower()})"
    return True, ""


def articles_out(items, limit=6):
    return [{"title": a["title"], "source": a["source"], "url": a["url"],
             "date": a["date"], "dateSource": a.get("dateSource", "rss")}
            for a in items[:limit]]


REPORTED_QUERIES = ["Narendra Modi arrives", "PM Modi visit", "Narendra Modi lands",
                    "PM Modi foreign visit", "Modi bilateral summit"]


def detect_reported_trip(pool, min_sources=3, recency_days=3):
    """A trip credible news corroborates but the registry hasn't published yet.

    A country is only treated as a trip leg when it appears with a destination
    cue (arrives/visits/welcomes…), in >= min_sources independent recent
    articles, with its freshest mention within recency_days of the newest signal.
    These guards keep out framing noise (e.g. 'counter China') and stale recaps.

    Corroborating headlines must also assert a trip in progress — see
    presence_claim — and at least one must place the PM on the ground, so a
    cancelled or merely proposed trip cannot raise the live band.

    `pool` is already deduped by URL with dates clamped by the ledger, so a
    re-dated week-old article no longer counts as corroboration for today.
    """
    now = datetime.datetime.utcnow()
    since = now - datetime.timedelta(days=REPORTED_SPAN_DAYS)
    seen, items = set(), []
    for it in sorted(pool, key=lambda x: x["dt"], reverse=True):
        key = it["title"].lower()
        if key in seen or it["dt"] < since:
            continue
        seen.add(key)
        items.append(it)
    print(f"[news] reported-trip detection: {len(pool)} unique article(s), "
          f"{len(items)} within {REPORTED_SPAN_DAYS}d of {now.date()}", file=sys.stderr)
    if not items:
        return None

    # Only headlines that actually assert a trip in progress may corroborate one.
    credible = []
    for it in items:
        ok, why = presence_claim(it["title"])
        if ok:
            credible.append(it)
        else:
            print(f"[news] NOT-CURRENT {it['date']} | {why} | {it['title'][:70]!r}", file=sys.stderr)
    print(f"[news] {len(items)} recent -> {len(credible)} assert a trip in progress", file=sys.stderr)
    if not credible:
        return None

    hits = defaultdict(list)
    for it in credible:
        for c in destination_countries(it["title"]):
            hits[c].append(it)
    cand = {c: v for c, v in hits.items() if len(v) >= min_sources}
    if not cand:
        return None

    latest = lambda c: max(x["dt"] for x in cand[c])
    freshest = max(latest(c) for c in cand)
    # Keep only legs still "current": freshest mention within recency_days of newest.
    cand = {c: v for c, v in cand.items() if (freshest - latest(c)).days <= recency_days}
    if not cand:
        return None

    countries = sorted(cand, key=lambda c: min(x["dt"] for x in cand[c]))  # tour order
    primary = countries[-1]  # most recently begun leg = current location
    # Corroboration by count is not enough: at least one report must place him on
    # the ground there, not merely discuss the leg.
    if not any(ON_GROUND_RE.search(x["title"]) for x in cand[primary]):
        print(f"[news] no on-the-ground report for {primary} — not claiming a live trip",
              file=sys.stderr)
        return None
    as_of = freshest.date().isoformat()
    window = trip_window(None, None, as_of)
    articles = select_trip_articles(credible, countries, window)
    return {
        "countries": countries,
        "primary": primary,
        "asOf": as_of,
        "sourceCount": len(articles),
        "window": window,
        "articles": articles_out(articles),
    }


def build_news(reg_trip, reg_status, today, news_path):
    """Collect and date-validate coverage for the focus trip; write data/news.json.

    Separated from main() so the news path can be exercised on its own without
    re-writing the authoritative visits.json.
    """
    ledger = load_ledger(news_path)
    print(f"[news] first-seen ledger: {len(ledger)} known URL(s)", file=sys.stderr)

    # Only look for a news-reported trip when the registry has none in progress.
    reported = None
    if reg_status != "ongoing":
        pool = collect_news(REPORTED_QUERIES)
        ledger = apply_ledger(pool, ledger, today)
        reported = detect_reported_trip(pool)

    if reported:
        status = "reported"
        trip_block = {"label": human_join(reported["countries"]), "start": None, "end": None,
                      "countries": reported["countries"]}
        articles = reported["articles"]
        window = reported["window"]
        print(f"Reported trip (unofficial): {', '.join(reported['countries'])} · {reported['sourceCount']} sources")
    else:
        status = reg_status
        countries = split_countries(reg_trip["label"]) if reg_trip else []
        trip_block = ({"label": reg_trip["label"], "start": reg_trip["start"], "end": reg_trip["end"],
                       "countries": countries} if reg_trip else None)
        focus = countries[0] if countries else "Narendra Modi"
        window = trip_window(reg_trip["start"], reg_trip["end"], None) if reg_trip else (None, None)
        pool = collect_news([f"Narendra Modi {focus} visit"])
        ledger = apply_ledger(pool, ledger, today)
        articles = articles_out(select_trip_articles(pool, countries, window))

    news = {
        "generated": datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "status": status,
        "reported": ({"countries": reported["countries"], "primary": reported["primary"],
                      "asOf": reported["asOf"], "sourceCount": reported["sourceCount"]}
                     if reported else None),
        "trip": trip_block,
        # The window the articles below were filtered against; the page re-checks
        # it client-side so a stale news.json cannot render mislabelled coverage.
        "window": {"from": window[0], "to": window[1]},
        "articles": articles,
        "seen": prune_ledger(ledger, datetime.date.today()),
    }
    news_path.write_text(json.dumps(news, indent=2, ensure_ascii=False) + "\n")
    print(f"Wrote {len(articles)} articles to data/news.json (focus: {status}, "
          f"window {window[0]}..{window[1]})")
    return news


def main():
    registry_path = None
    if "--registry" in sys.argv:
        registry_path = sys.argv[sys.argv.index("--registry") + 1]

    text = pathlib.Path(registry_path).read_text(errors="replace") if registry_path else fetch(JINA_URL)
    trips = parse_trips(text)
    if not trips:
        print("No trips parsed — keeping existing data.", file=sys.stderr)
        sys.exit(0)

    today = datetime.date.today().isoformat()

    visits_path = ROOT / "data" / "visits.json"
    current = json.loads(visits_path.read_text()) if visits_path.exists() else {}
    current["meta"] = {
        "updated": today,
        "source": "PM India registry (auto-refreshed daily via GitHub Actions)",
        "source_url": "https://www.pmindia.gov.in/en/details-of-foreigndomestic-visits/",
        "count": len(trips),
    }
    current["trips"] = trips
    visits_path.write_text(json.dumps(current, indent=2, ensure_ascii=False) + "\n")
    print(f"Wrote {len(trips)} trips to data/visits.json")

    reg_trip, reg_status = pick_focus_trip(trips, today)
    build_news(reg_trip, reg_status, today, ROOT / "data" / "news.json")


if __name__ == "__main__":
    main()
