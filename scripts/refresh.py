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

Run locally the same way the GitHub Action runs it:
    python3 scripts/refresh.py
Optional: parse a saved registry dump instead of fetching live:
    python3 scripts/refresh.py --registry /tmp/registry.txt
"""
import re, json, sys, html, pathlib, datetime, urllib.request, urllib.parse
from collections import defaultdict

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
    s = s.strip()
    for fmt in ("%a, %d %b %Y %H:%M:%S %Z", "%a, %d %b %Y %H:%M:%S"):
        try:
            return datetime.datetime.strptime(s[:31].strip(), fmt).replace(tzinfo=None)
        except Exception:
            continue
    return None


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
        dt = parse_pubdate(d.group(1)) if d else None
        items.append({"title": title, "source": source, "url": l.group(1).strip(),
                      "date": dt.date().isoformat() if dt else "", "dt": dt})
    return items


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


def destination_countries(title):
    low = title.lower()
    out = []
    for m in COUNTRY_RE.finditer(title):
        canon = _CANON_LOOKUP.get(m.group(1).lower())
        if not canon or canon == "India" or canon in out:
            continue
        window = low[max(0, m.start() - 34): m.end() + 34]
        if DEST_CUE_RE.search(window):
            out.append(canon)
    return out


def articles_out(items, limit=6):
    return [{"title": a["title"], "source": a["source"], "url": a["url"], "date": a["date"]}
            for a in items[:limit]]


def fetch_news_for(query, limit=6):
    return articles_out(google_news(query), limit)


def detect_reported_trip(min_sources=3, recency_days=3):
    """A trip credible news corroborates but the registry hasn't published yet.

    A country is only treated as a trip leg when it appears with a destination
    cue (arrives/visits/welcomes…), in >= min_sources independent recent
    articles, with its freshest mention within recency_days of the newest signal.
    These guards keep out framing noise (e.g. 'counter China') and stale recaps.
    """
    now = datetime.datetime.utcnow()
    window = now - datetime.timedelta(days=6)
    queries = ["Narendra Modi arrives", "PM Modi visit", "Narendra Modi lands",
               "PM Modi foreign visit", "Modi bilateral summit"]
    seen, items = set(), []
    for q in queries:
        for it in google_news(q):
            key = it["title"].lower()
            if key in seen or not it["dt"] or it["dt"] < window:
                continue
            seen.add(key)
            items.append(it)
    if not items:
        return None

    hits = defaultdict(list)
    for it in items:
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
    tour_items = sorted(
        [a for a in items if any(c in cand for c in destination_countries(a["title"]))],
        key=lambda x: x["dt"], reverse=True)
    return {
        "countries": countries,
        "primary": primary,
        "asOf": freshest.date().isoformat(),
        "sourceCount": len(tour_items),
        "articles": articles_out(tour_items, 6),
    }


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

    # Only look for a news-reported trip when the registry has none in progress.
    reported = detect_reported_trip() if reg_status != "ongoing" else None

    if reported:
        status = "reported"
        trip_block = {"label": human_join(reported["countries"]), "start": None, "end": None,
                      "countries": reported["countries"]}
        articles = reported["articles"]
        print(f"Reported trip (unofficial): {', '.join(reported['countries'])} · {reported['sourceCount']} sources")
    else:
        status = reg_status
        trip_block = ({"label": reg_trip["label"], "start": reg_trip["start"], "end": reg_trip["end"],
                       "countries": split_countries(reg_trip["label"])} if reg_trip else None)
        focus = reg_trip["label"].split(",")[0].split(" & ")[0] if reg_trip else "Narendra Modi"
        articles = fetch_news_for(f"Narendra Modi {focus} visit")

    news = {
        "generated": datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "status": status,
        "reported": ({"countries": reported["countries"], "primary": reported["primary"],
                      "asOf": reported["asOf"], "sourceCount": reported["sourceCount"]}
                     if reported else None),
        "trip": trip_block,
        "articles": articles,
    }
    (ROOT / "data" / "news.json").write_text(json.dumps(news, indent=2, ensure_ascii=False) + "\n")
    print(f"Wrote {len(articles)} articles to data/news.json (focus: {status})")


if __name__ == "__main__":
    main()
