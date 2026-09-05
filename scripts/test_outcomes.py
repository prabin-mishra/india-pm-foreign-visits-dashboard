#!/usr/bin/env python3
"""Regression tests for the outcome-indicator feed's parsing and matching.

Stdlib only, no network. Run:
    python3 scripts/test_outcomes.py
"""
import sys, pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import refresh_outcomes as O

FAILS = []


def check(name, got, want):
    if got != want:
        FAILS.append(f"{name}\n     got:  {got!r}\n     want: {want!r}")


# --- country splitting must agree with the page's canonicalisation -----------
check("compound country kept whole", O.split_label("Ghana, Trinidad and Tobago, Argentina & Brazil"),
      ["Ghana", "Trinidad and Tobago", "Argentina", "Brazil"])
check("aliases canonicalised", O.split_label("USA and United Arab Emirates (UAE)"),
      ["United States", "United Arab Emirates"])
check("city resolves to country", O.split_label("Samarkand, Uzbekistan"), ["Uzbekistan"])

# --- EXIM signing dates come as Excel serials or dd-mm-yyyy text ---------------
check("excel serial", O.excel_serial_to_iso("40385"), "2010-07-26")
check("serial with decimals", O.excel_serial_to_iso("38210.0"), "2004-08-11")
check("dd-mm-yyyy", O.excel_serial_to_iso("22-07-2026"), "2026-07-22")
check("garbage", O.excel_serial_to_iso("N.A."), None)

# --- amounts: USD million numbers vs 'INR 4100 crore' text -------------------
check("numeric amount", O.amount_fields("15"), (15.0, "15"))
check("text amount", O.amount_fields("INR 4100 crore"), (None, "INR 4100 crore"))

# --- MEA listing fragment ------------------------------------------------------
LISTING = '''
<div class="pressRelesastBox"><div class="d-flex"><span class="date">30 August, 2026</span></div>
<h3 class="pressTitle"><a href="/bilateral-documents?dtl/41712/List_of_Outcomes">
  List of Outcomes: Prime Minister&#8217;s State Visit to Uzbekistan (August 29 &#8211; 30, 2026)
</a></h3><div class="d-flex tags"><a onclick="redirectWithTag('Uzbekistan')">Uzbekistan</a>
<a onclick="redirectWithTag('Prime Minister')">Prime Minister</a></div></div>
<div class="pressRelesastBox"><div class="d-flex"><span class="date">03 September, 2026</span></div>
<h3 class="pressTitle"><a href="/bilateral-documents?dtl/41738/x">List of Outcomes: Visit of the Prime Minister of the Kingdom of Belgium to India (September 03, 2026)</a></h3>
<div class="d-flex tags"><a onclick="redirectWithTag('Belgium')">Belgium</a></div></div>
'''
entries = O.parse_mea_listing(LISTING)
check("two entries parsed", [(e["id"], e["date"], e["tags"][0]) for e in entries],
      [(41712, "2026-08-30", "Uzbekistan"), (41738, "2026-09-03", "Belgium")])
check("entities unescaped", "Prime Minister’s State Visit" in entries[0]["title"], True)

trips = [{"start": "2026-08-29", "end": "2026-08-30", "label": "Uzbekistan", "countries": ["Uzbekistan"]},
         {"start": "2026-09-02", "end": "2026-09-04", "label": "Belgium", "countries": ["Belgium"]}]
check("outgoing list matched by tag and date", O.match_document_to_trip(entries[0], trips)[1], "Uzbekistan")
check("inbound leader visit rejected even on a matching date", O.match_document_to_trip(entries[1], trips), None)
check("date outside trip window rejected",
      O.match_document_to_trip(dict(entries[0], date="2026-09-10"), trips), None)

DETAIL = '''<table><tr><th>Sl. No.</th><th>Title</th></tr>
<tr><td>1.</td><td>Cultural Exchange Programme</td></tr>
<tr><td>2.</td><td>Letter of Intent</td></tr></table>
<table><tr><td>Sl.</td><td>Announcements</td></tr><tr><td>1</td><td>Handover of restored site</td></tr></table>'''
check("numbered rows counted, headers skipped", O.count_list_items(DETAIL), 3)

PLAIN = '<p>List of Outcomes: State visit to Egypt Agreement / MoUs 1. Strategic Partnership Agreement. 2. MOU between the Ministry of Agriculture. 3. MoU on Antiquities. Announcements 4. Direct flight Cairo-Delhi. 5. Centre of Excellence.</p>'
check("plain-text numbering counted", O.count_list_items(PLAIN), 5)
check("<li> layout counted", O.count_list_items("<ul><li>a</li><li>b</li><li>c</li></ul>"), 3)
check("uncountable layout is None, not zero", O.count_list_items("<p>Joint statement text only.</p>"), None)
check("older title convention accepted",
      O.match_document_to_trip({"id": 1, "date": "2022-05-03", "tags": [],
                                "title": "List of agreements signed/announced during the visit of Prime Minister to Denmark"},
                               [{"start": "2022-05-02", "end": "2022-05-04", "label": "Germany, Denmark & France",
                                 "countries": ["Germany", "Denmark", "France"]}])[1], "Denmark")

# --- EXIM link discovery ---------------------------------------------------------
PAGE = '''<a href="/sites/default/files/2026-08/GOILOC%20Statistics_31.07.2026.xlsx">signed</a>
<a href="/sites/default/files/2026-08/Pipeline%20LOCs_31.07.2026.xlsx">pipeline</a>
<a href="/sites/default/files/2026-08/Operative%20LOCs_31.07.2026.xlsx">operative</a>'''
links = O.exim_links(PAGE)
check("signed and operative links found, pipeline ignored", sorted(links),
      ["operative", "signed"])
check("absolute url", links["signed"].startswith("https://www.eximbankindia.in/sites/"), True)

# --- month iteration ---------------------------------------------------------------
check("month range crosses a year", list(O.month_iter("2025-11", "2026-02")),
      ["2025-11", "2025-12", "2026-01", "2026-02"])

if FAILS:
    print(f"{len(FAILS)} failure(s):")
    for f in FAILS:
        print("  -", f)
    sys.exit(1)
print("all outcome tests passed")
