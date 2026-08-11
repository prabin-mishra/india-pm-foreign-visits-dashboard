#!/usr/bin/env python3
"""Regression tests for news article dating and trip-window filtering.

Covers the logic that keeps stale coverage from being presented as current
reporting. Google News re-dates the same article URL between runs, so these
guards are invisible in normal operation and easy to regress silently.

Stdlib only, no network. Run:
    python3 scripts/test_news_dates.py
"""
import sys, pathlib, datetime

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import refresh as R

FAILS = []


def check(name, got, want):
    if got != want:
        FAILS.append(f"{name}\n     got:  {got!r}\n     want: {want!r}")


def art(title, date, url=None, source="Test"):
    return {"title": title, "source": source, "url": url or "https://x/" + title[:20],
            "date": date, "dt": datetime.datetime.strptime(date, "%Y-%m-%d")}


# --- parse_pubdate: RFC 2822 in, naive UTC out -------------------------------
check("GMT", R.parse_pubdate("Sun, 09 Aug 2026 03:52:24 GMT"),
      datetime.datetime(2026, 8, 9, 3, 52, 24))
# +0530 must convert to UTC, not be dropped — this crosses a date boundary.
check("+0530 crosses midnight", R.parse_pubdate("Mon, 10 Aug 2026 01:00:00 +0530"),
      datetime.datetime(2026, 8, 9, 19, 30))
check("-0400", R.parse_pubdate("Mon, 10 Aug 2026 20:00:00 -0400"),
      datetime.datetime(2026, 8, 11, 0, 0))
check("UTC literal", R.parse_pubdate("Tue, 04 Aug 2026 07:13:08 UTC"),
      datetime.datetime(2026, 8, 4, 7, 13, 8))
check("leap day", R.parse_pubdate("Tue, 29 Feb 2028 12:00:00 GMT"),
      datetime.datetime(2028, 2, 29, 12, 0))
for bad in ("", "   ", "not a date", "9 Aug 2026"[:4], None):
    check(f"invalid {bad!r}", R.parse_pubdate(bad), None)

# --- collect_news: same URL, disagreeing feeds -> earliest wins --------------
SAME = "https://news.google.com/rss/articles/SAME"
feeds = {
    "q1": [art("6-day visit to UAE, Netherlands, Sweden, Norway & Italy", "2026-08-10", SAME)],
    "q2": [art("6-day visit to UAE, Netherlands, Sweden, Norway & Italy", "2026-05-29", SAME)],
}
R.google_news = lambda q: [dict(a) for a in feeds[q]]
merged = R.collect_news(["q1", "q2"])
check("earliest wins (later seen second)", [a["date"] for a in merged], ["2026-05-29"])
merged = R.collect_news(["q2", "q1"])
check("earliest wins (order independent)", [a["date"] for a in merged], ["2026-05-29"])
check("deduped by URL", len(merged), 1)

# --- apply_ledger: dates only ever revise downward ---------------------------
items = [art("Sweden diaspora welcome", "2026-08-10", "u1")]
ledger = {R.url_key("u1"): "2026-07-12"}
R.apply_ledger(items, ledger, "2026-08-11")
check("ledger lowers date", items[0]["date"], "2026-07-12")
check("ledger dateSource", items[0]["dateSource"], "first-seen")
check("ledger dt follows date", items[0]["dt"], datetime.datetime(2026, 7, 12))

items = [art("Genuinely new", "2026-08-10", "u2")]
ledger = {R.url_key("u2"): "2026-08-30"}  # a later record must not raise the date
R.apply_ledger(items, ledger, "2026-08-11")
check("ledger never raises", items[0]["date"], "2026-08-10")
check("unchanged dateSource", items[0]["dateSource"], "rss")

items = [art("Feed claims tomorrow", "2026-12-25", "u3")]
ledger = R.apply_ledger(items, {}, "2026-08-11")
check("future date clamped to today", items[0]["date"], "2026-08-11")
check("clamped dateSource", items[0]["dateSource"], "clamped")
check("ledger records the floor", ledger[R.url_key("u3")], "2026-08-11")

# --- prune_ledger ------------------------------------------------------------
today = datetime.date(2026, 8, 11)
led = {"keep": "2026-07-01", "drop": "2025-01-01", "edge":
       (today - datetime.timedelta(days=R.FIRST_SEEN_KEEP_DAYS)).isoformat()}
pruned = R.prune_ledger(led, today)
check("prunes past retention", sorted(pruned), ["edge", "keep"])
big = {f"k{i}": "2026-08-01" for i in range(R.FIRST_SEEN_MAX_ENTRIES + 50)}
check("caps entries", len(R.prune_ledger(big, today)), R.FIRST_SEEN_MAX_ENTRIES)

# --- trip_window ------------------------------------------------------------
check("registry trip window", R.trip_window("2026-05-15", "2026-05-20", None),
      ("2026-05-12", "2026-05-24"))
check("reported trip window", R.trip_window(None, None, "2026-08-09"),
      ("2026-08-03", "2026-08-13"))
check("window crosses month", R.trip_window("2026-03-01", "2026-03-02", None),
      ("2026-02-26", "2026-03-06"))
check("window crosses leap day", R.trip_window("2028-03-01", "2028-03-02", None),
      ("2028-02-27", "2028-03-06"))
check("no dates at all", R.trip_window(None, None, None), (None, None))

# --- article_matches_trip: relevance, not just recency ----------------------
ok, why = R.article_matches_trip(
    "PM Modi to be on 6-day visit to UAE, Netherlands, Sweden, Norway & Italy beginning Friday",
    ["Israel", "Sweden"])
check("five-nation tour rejected for two-country trip", ok, False)
ok, _ = R.article_matches_trip(
    "Shalom Modi: PM Modi arrives in Israel for two-day visit", ["Israel", "Sweden"])
check("on-trip article kept", ok, True)
ok, why = R.article_matches_trip("PM Modi's foreign visits cost Rs 557 crore", ["Israel"])
check("no destination named -> rejected", (ok, why), (False, "no destination country named"))
ok, _ = R.article_matches_trip("PM Modi lands in Russia, red carpet welcome", ["Israel"])
check("other trip's destination rejected", ok, False)
ok, _ = R.article_matches_trip("PM Modi visits Israel to counter China influence", ["Israel"])
check("framing mention is not a destination", ok, True)

# --- select_trip_articles: window boundaries, dedup, ordering ---------------
window = ("2026-08-03", "2026-08-13")
pool = [
    art("PM Modi arrives in Israel for talks", "2026-08-09", "a1"),
    art("PM Modi concludes Israel visit", "2026-08-10", "a2"),
    art("PM Modi arrives in Israel for talks", "2026-08-08", "a3"),   # duplicate headline
    art("PM Modi visit to Israel marks milestone", "2026-08-03", "a4"),  # lower boundary
    art("PM Modi visit to Israel a milestone moment", "2026-08-13", "a5"),  # upper boundary
    art("PM Modi begins Israel visit preparations", "2026-08-02", "a6"),  # just outside
    art("PM Modi Israel visit review", "2026-08-14", "a7"),           # just outside
]
kept = R.select_trip_articles(pool, ["Israel"], window)
check("boundaries inclusive, outsiders dropped, deduped",
      [a["date"] for a in kept], ["2026-08-13", "2026-08-10", "2026-08-09", "2026-08-03"])
check("sorted newest first", [a["date"] for a in kept] == sorted(
    [a["date"] for a in kept], reverse=True), True)
check("open window keeps everything relevant",
      len(R.select_trip_articles(pool, ["Israel"], (None, None))), 6)

# --- articles_out ------------------------------------------------------------
out = R.articles_out(kept, limit=2)
check("respects display limit", len(out), 2)
check("emits the fields the page needs", sorted(out[0]), ["date", "dateSource", "source", "title", "url"])

if FAILS:
    print(f"FAILED {len(FAILS)} check(s):", file=sys.stderr)
    for f in FAILS:
        print("  - " + f, file=sys.stderr)
    sys.exit(1)
print("All news-date checks passed.")
