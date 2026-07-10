#!/usr/bin/env python3
"""
Refresh the PM foreign-visits dataset and the live-trip news feed.

Writes two files consumed by the static site:
  - data/visits.json : every foreign visit parsed from the PM India registry
  - data/news.json   : third-party news coverage for the current/most-recent trip

Run locally the same way the GitHub Action runs it:
    python3 scripts/refresh.py
Optional: parse a saved registry dump instead of fetching live:
    python3 scripts/refresh.py --registry /tmp/registry.txt
"""
import re, json, sys, html, pathlib, datetime, urllib.request, urllib.parse

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
# The trailing date expression begins at a "day-range month" or "day month" run.
ANCHOR = re.compile(r"\d{1,2}\s*[–—-]\s*\d{1,2}\s+(?:%s)|\d{1,2}\s+(?:%s)" % (_MONTH_ALT, _MONTH_ALT))


def month_num(name):
    return MONTHS.get(name, MONTHS.get(name[:3].title(), "01"))


def fetch(url, timeout=45):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (pm-visits-tracker)"})
    return urllib.request.urlopen(req, timeout=timeout).read().decode("utf-8", "replace")


def parse_date_range(ds):
    """Return (start_iso, end_iso) for a trailing date string, or None."""
    ds = ds.replace("–", "-").replace("—", "-")
    # 27-29 June, 2026  (shared month, day range)
    m = re.match(r"\s*(\d{1,2})\s*-\s*(\d{1,2})\s+([A-Za-z]+)\s*,?\s*(\d{4})", ds)
    if m:
        y, mm = m.group(4), month_num(m.group(3))
        return f"{y}-{mm}-{m.group(1).zfill(2)}", f"{y}-{mm}-{m.group(2).zfill(2)}"
    # 07 Feb - 08 Feb, 2026   OR   28 Aug - 1 Sep, 2025  (day month - day month, year)
    m = re.match(r"\s*(\d{1,2})\s+([A-Za-z]+)\s*-\s*(\d{1,2})\s+([A-Za-z]+)\s*,?\s*(\d{4})", ds)
    if m:
        y = m.group(5)
        return f"{y}-{month_num(m.group(2))}-{m.group(1).zfill(2)}", f"{y}-{month_num(m.group(4))}-{m.group(3).zfill(2)}"
    # 22 April 2025 -22 April 2025  (full date - full date, each with year)
    m = re.match(r"\s*(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})\s*-\s*(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", ds)
    if m:
        return (f"{m.group(3)}-{month_num(m.group(2))}-{m.group(1).zfill(2)}",
                f"{m.group(6)}-{month_num(m.group(5))}-{m.group(4).zfill(2)}")
    return None


def parse_trips(text):
    trips = []
    for line in text.splitlines():
        line = line.strip()
        m = re.match(r"^(\d+)\s+(.+)$", line)  # leading serial number + rest
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
    """Mirror the client's country splitting so news queries match trip cards."""
    s = re.sub(r"\s+and\s+", ", ", label, flags=re.I)
    s = s.replace(" & ", ", ")
    return [c.strip() for c in s.split(",") if c.strip()]


def pick_focus_trip(trips, today):
    """Return (trip, status): ongoing → upcoming → most-recent completed."""
    ongoing = [t for t in trips if t["start"] <= today <= t["end"]]
    if ongoing:
        return ongoing[0], "ongoing"
    upcoming = sorted([t for t in trips if t["start"] > today], key=lambda t: t["start"])
    if upcoming:
        return upcoming[0], "upcoming"
    past = [t for t in trips if t["end"] < today]  # trips are sorted desc, so first is most recent
    if past:
        return past[0], "recent"
    return (trips[0], "recent") if trips else (None, None)


def fetch_news(trip, max_items=6):
    """Third-party coverage via Google News RSS (no API key). Best-effort."""
    if not trip:
        return []
    countries = split_countries(trip["label"])
    focus = countries[0] if countries else trip["label"]
    q = f'Narendra Modi {focus} visit'
    url = ("https://news.google.com/rss/search?q=" + urllib.parse.quote(q)
           + "&hl=en-IN&gl=IN&ceid=IN:en")
    try:
        xml = fetch(url, timeout=30)
    except Exception as e:
        print(f"[news] fetch failed: {e!r}", file=sys.stderr)
        return []
    articles, seen = [], set()
    for block in re.findall(r"<item>(.*?)</item>", xml, re.S):
        t = re.search(r"<title>(.*?)</title>", block, re.S)
        l = re.search(r"<link>(.*?)</link>", block, re.S)
        s = re.search(r"<source[^>]*>(.*?)</source>", block, re.S)
        d = re.search(r"<pubDate>(.*?)</pubDate>", block, re.S)
        if not t or not l:
            continue
        title = html.unescape(re.sub(r"<[^>]+>", "", t.group(1))).strip()
        source = html.unescape(s.group(1)).strip() if s else ""
        # Google News titles end with " - Publisher"; drop it when we have <source>.
        if source and title.endswith(" - " + source):
            title = title[: -(len(source) + 3)].strip()
        iso = ""
        if d:
            try:
                iso = datetime.datetime.strptime(d.group(1).strip()[:25], "%a, %d %b %Y %H:%M:%S").date().isoformat()
            except Exception:
                iso = ""
        key = title.lower()
        if not title or key in seen:
            continue
        seen.add(key)
        articles.append({"title": title, "source": source, "url": l.group(1).strip(), "date": iso})
        if len(articles) >= max_items:
            break
    return articles


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

    trip, status = pick_focus_trip(trips, today)
    articles = fetch_news(trip)
    news = {
        "generated": datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "status": status,
        "trip": {"label": trip["label"], "start": trip["start"], "end": trip["end"],
                 "countries": split_countries(trip["label"])} if trip else None,
        "articles": articles,
    }
    news_path = ROOT / "data" / "news.json"
    news_path.write_text(json.dumps(news, indent=2, ensure_ascii=False) + "\n")
    print(f"Wrote {len(articles)} articles to data/news.json (focus: {status})")


if __name__ == "__main__":
    main()
