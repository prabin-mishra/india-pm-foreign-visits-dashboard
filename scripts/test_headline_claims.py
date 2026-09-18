#!/usr/bin/env python3
"""Regression tests for reading what a headline actually claims.

A country name sitting next to a travel word is not evidence the PM travelled.
These cover the three ways that assumption failed in production: coverage of
someone else's inbound visit, of a refused/cancelled trip, and of one that is
still only proposed. Stdlib only, no network. Run:
    python3 scripts/test_headline_claims.py
"""
import sys, pathlib, datetime

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import refresh as R

FAILS = []


def check(name, got, want):
    if got != want:
        FAILS.append(f"{name}\n     got:  {got!r}\n     want: {want!r}")


def art(title, date, url=None, source="Test"):
    return {"title": title, "source": source, "url": url or "https://x/" + title[:24],
            "date": date, "dt": datetime.datetime.strptime(date, "%Y-%m-%d")}


# The three headlines that put "Reportedly abroad now — Bangladesh" on the site
# on 2026-08-17. Every one is about Bangladesh's PM travelling to India.
BANGLADESH = [
    "Another Diplomatic Setback for Modi Government as Bangladesh PM Refuses to "
    "Visit India Until Sheikh Hasina’s Extradition",
    "Bangladesh PM Tarique Rahman’s India visit uncertain as Dhaka, Delhi discuss "
    "dates amid Hasina row: Report",
    "Bangladesh PM Likely To Visit India Next Week, 1st Trip Since Assuming Power",
]

# --- direction: whose trip is this? -----------------------------------------
for t in BANGLADESH:
    check(f"inbound not a destination | {t[:44]}", R.destination_countries(t), [])
check("foreign leader is a person, not a place",
      R.destination_countries("Sri Lanka President arrives for talks with PM Modi"), [])
check("leader hosting the PM still places him there",
      R.destination_countries("Israel President welcomes Modi at Ben Gurion airport"), ["Israel"])
check("the PM's own trip is unaffected",
      R.destination_countries("PM Modi arrives in Israel for two-day visit"), ["Israel"])
check("multi-leg tour still reads in order",
      R.destination_countries("PM Modi lands in Japan after concluding France visit"),
      ["Japan", "France"])

# --- claim strength: is he there now? ---------------------------------------
for t in BANGLADESH:
    ok, _ = R.presence_claim(t)
    check(f"cannot support a live trip | {t[:44]}", ok, False)
for t in ["PM Modi's Israel visit postponed amid regional tensions",
          "PM Modi cancels Sweden leg of European tour",
          "PM Modi skips G7 summit in Canada",
          "PM Modi rules out visit to Pakistan",
          "PM Modi likely to visit Israel next month",
          "PM Modi may travel to Russia for summit",
          "PM Modi to visit Bhutan, dates awaited"]:
    ok, _ = R.presence_claim(t)
    check(f"negated/prospective rejected | {t[:44]}", ok, False)
for t in ["Shalom Modi: PM Modi arrives in Israel for two-day visit",
          "PM Modi concludes landmark Israel visit, Netanyahu sees him off",
          "PM Modi’s visit to Israel marks a significant milestone in relations",
          "PM Modi holds talks with Japanese counterpart in Tokyo",
          "PM Modi lands in Moscow, likely to meet Putin on Thursday"]:
    ok, why = R.presence_claim(t)
    check(f"current coverage kept | {t[:44]}", (ok, why), (True, ""))

# --- detect_reported_trip end to end ----------------------------------------
today = datetime.datetime.utcnow().date()
d = lambda n: (today - datetime.timedelta(days=n)).isoformat()

pool = [art(BANGLADESH[0], d(1), "b1"), art(BANGLADESH[1], d(2), "b2"),
        art(BANGLADESH[2], d(4), "b3")]
check("no live band from inbound/cancelled coverage", R.detect_reported_trip(pool), None)

pool = [art("Shalom Modi: PM Modi arrives in Israel for two-day visit", d(1), "i1", "A"),
        art("PM Modi concludes landmark Israel visit, Netanyahu sees him off", d(1), "i2", "B"),
        art("PM Modi’s visit to Israel marks a significant milestone", d(3), "i3", "C")]
got = R.detect_reported_trip(pool)
check("genuine trip still detected", got and got["countries"], ["Israel"])
check("corroboration counted", got and got["sourceCount"], 3)

# Three sources, none of which puts him on the ground.
pool = [art("PM Modi’s Israel visit marks a milestone, says envoy", d(1), "s1"),
        art("PM Modi Israel visit signals deeper defence ties", d(2), "s2"),
        art("PM Modi Israel visit reshapes West Asia policy", d(3), "s3")]
check("talked about is not the same as there", R.detect_reported_trip(pool), None)

# --- India as host: the 2026-09-17 "Russia & China" band --------------------
# India hosted the BRICS Summit in New Delhi; Xi came to him. Putin sent birthday
# wishes. Nine such headlines raised "Reportedly abroad now — Russia & China".
HOSTED = [
    ("Prez Putin extends birthday wishes to PM Modi; lauds his contribution to "
     "strengthening India-Russia ties", "Shillong Times"),
    ("President Putin extends birthday wishes to PM Modi, lauds contribution to "
     "India-Russia ties", "DD News"),
    ('"Impossible to overstate your personal contribution": Putin wishes PM Modi on '
     "birthday; highlights role in strengthening", "ANI"),
    ('China says Modi-Xi reached "most important consensus" at BRICS Summit', "PGurus"),
    ("Can a 20-second Modi-Xi handshake at the BRICS summit break years of India-China ice?",
     "Asia News Network"),
    ("BRICS Summit 2026 Highlights: Xi Says India-China Ties On Path Of Steady "
     "Improvement In Meeting With PM Modi", "News18"),
    ("Modi at BRICS 2026: Between US Ties and China’s Rise", "Mint"),
    ("PM Modi holds bilateral with Uganda Vice President Jessica Alupo on BRICS "
     "sidelines in New Delhi", "PIB"),
]
for t, _ in HOSTED[:2]:
    check(f"bilateral pair is not a place | {t[:44]}", R.destination_countries(t), [])
check("country as speaker is not a place", R.destination_countries(HOSTED[3][0]), [])
check("summit in New Delhi is at home", R.destination_countries(HOSTED[7][0]), [])
check("reached a consensus is not arrival", bool(R.ON_GROUND_RE.search(HOSTED[3][0])), False)
check("reached a city still is", bool(R.ON_GROUND_RE.search("PM Modi reached Tokyo late on Friday")), True)
check("someone else on the ground is not the PM",
      R.destination_countries("EAM Jaishankar arrives in Bhutan, holds talks with counterpart") == ["Bhutan"]
      and not R.PM_SUBJECT_RE.search("EAM Jaishankar arrives in Bhutan, holds talks with counterpart"), True)

pool = [art(t, d(i % 5), f"h{i}", src) for i, (t, src) in enumerate(HOSTED)]
check("no live band while India hosts", R.detect_reported_trip(pool), None)

# A lone stale "arrives" headline is not enough to call a live trip.
pool = [art("PM Modi Arrives in Seychelles for Three-Day State Visit", d(1), "y1", "A"),
        art("PM Modi Seychelles visit to deepen maritime ties", d(1), "y2", "B"),
        art("PM Modi Seychelles visit: what’s on the agenda", d(2), "y3", "C")]
check("one on-the-ground source is not corroboration", R.detect_reported_trip(pool), None)

if FAILS:
    print(f"FAILED {len(FAILS)} check(s):", file=sys.stderr)
    for f in FAILS:
        print("  - " + f, file=sys.stderr)
    sys.exit(1)
print("All headline-claim checks passed.")
