#!/usr/bin/env python3
"""
Refresh the outcome-indicator feed: data/outcomes.json.

Companion to refresh.py, deliberately separate from it. refresh.py owns the
registry (data/visits.json) and the news feed; this script only *reads*
visits.json to learn which countries were visited, then collects public
statistics for those countries from the sources shortlisted in
docs/outcome-indicators.md:

  documents     MEA "List of Outcomes" entries for PM visits, matched to a
                registry trip by country tag and date, with the number of
                items each list carries.                    (per visit)
  trade         Merchandise exports to / imports from each partner, plus
                India's world total for the baseline.       (UN Comtrade, annual + monthly)
  coauthorship  Works with at least one India-affiliated and one partner-
                affiliated author, plus India's total.      (OpenAlex, annual)
  unga          Share of UN General Assembly recorded votes where India and
                the partner voted the same way.             (Harvard Dataverse, per session)
  loc           Government of India lines of credit signed with, and operative
                in, each partner.                           (EXIM Bank, per LoC)

Design rules, shared with refresh.py:
  - stdlib only; no keys, no accounts. Every source is a keyless public endpoint.
  - one source failing must not blank the others. Each section is fetched
    independently; on failure the previous run's section is carried forward
    and marked "cached" with the error, and the script still exits 0.
  - the file is only rewritten when at least one section fetched successfully.
  - nothing here is causal. The "note" in meta is copied onto the site
    verbatim; keep it there.

Politeness: Comtrade's keyless preview endpoint rate-limits hard (429s on
back-to-back calls), so trade fetches are incremental — periods already in
the file are not refetched except the trailing months, which Comtrade revises.

Run locally exactly as the Action runs it:
    python3 scripts/refresh_outcomes.py
Skip slow sections while developing:
    OUTCOMES_SKIP=unga,trade python3 scripts/refresh_outcomes.py
"""
import re, json, sys, os, io, csv, html, time, zipfile, pathlib, datetime
import urllib.request, urllib.parse, urllib.error
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parent.parent
VISITS_PATH = ROOT / "data" / "visits.json"
OUT_PATH = ROOT / "data" / "outcomes.json"

UA = "india-pm-foreign-visits-dashboard/outcomes (+https://github.com/prabin-mishra/india-pm-foreign-visits-dashboard)"
BROWSER_UA = "Mozilla/5.0 (compatible; india-pm-foreign-visits-dashboard outcomes refresh)"

SCHEMA = 1
NOTE = ("These figures describe what changed in public statistics around the time of a visit. "
        "They do not show that a visit caused any of it. Each series is shown beside India's "
        "overall figure so movement specific to one country can be told apart from movement "
        "everywhere. Flat and negative changes are reported exactly like positive ones.")

FIRST_YEAR = 2017          # three years of history before the earliest registry trip (2021)
MONTHLY_FROM = "2019-01"   # monthly trade history start
TRAILING_MONTHS = 3        # monthly periods refetched every run because Comtrade revises them
UNGA_MIN_SESSION = 70      # 2015 onward

# --- country identity --------------------------------------------------------
# Mirrors COUNTRY_CANON / COMPOUND_COUNTRIES in index.html so this file keys its
# countries exactly the way the page does.
COUNTRY_CANON = {
    'usa': 'United States', 'us': 'United States', 'united states': 'United States',
    'united states of america': 'United States', 'america': 'United States',
    'uk': 'United Kingdom', 'britain': 'United Kingdom', 'great britain': 'United Kingdom',
    'uae': 'United Arab Emirates', 'dubai': 'United Arab Emirates', 'abu dhabi': 'United Arab Emirates',
    'samarkand': 'Uzbekistan', 'holland': 'Netherlands', 'czechia': 'Czech Republic',
    'russian federation': 'Russia', 'republic of korea': 'South Korea', 'korea': 'South Korea',
    'burma': 'Myanmar', 'brunei darussalam': 'Brunei', 'ivory coast': "Cote d'Ivoire",
    'the netherlands': 'Netherlands', 'vatican': 'Vatican City',
}
COMPOUND_COUNTRIES = [
    'Trinidad and Tobago', 'Antigua and Barbuda', 'Bosnia and Herzegovina',
    'Saint Kitts and Nevis', 'Sao Tome and Principe', 'Turks and Caicos Islands',
    'Saint Vincent and the Grenadines', 'Wallis and Futuna',
]

# ISO codes for canonical names. Comtrade's numeric partner codes and the UNGA
# dataset's Correlates-of-War codes are both resolved through ISO3 at run time
# from the sources' own reference tables, so only ISO2/ISO3 are hard-coded.
ISO = {
    'Afghanistan': ('AFG', 'AF'), 'Algeria': ('DZA', 'DZ'), 'Argentina': ('ARG', 'AR'),
    'Australia': ('AUS', 'AU'), 'Austria': ('AUT', 'AT'), 'Bahrain': ('BHR', 'BH'),
    'Bangladesh': ('BGD', 'BD'), 'Barbados': ('BRB', 'BB'), 'Belgium': ('BEL', 'BE'),
    'Bhutan': ('BTN', 'BT'), 'Brazil': ('BRA', 'BR'), 'Brunei': ('BRN', 'BN'),
    'Bulgaria': ('BGR', 'BG'), 'Cambodia': ('KHM', 'KH'), 'Canada': ('CAN', 'CA'),
    'Chile': ('CHL', 'CL'), 'China': ('CHN', 'CN'), 'Colombia': ('COL', 'CO'),
    "Cote d'Ivoire": ('CIV', 'CI'), 'Croatia': ('HRV', 'HR'), 'Cuba': ('CUB', 'CU'),
    'Cyprus': ('CYP', 'CY'), 'Czech Republic': ('CZE', 'CZ'), 'Denmark': ('DNK', 'DK'),
    'Egypt': ('EGY', 'EG'), 'Estonia': ('EST', 'EE'), 'Ethiopia': ('ETH', 'ET'),
    'Fiji': ('FJI', 'FJ'), 'Finland': ('FIN', 'FI'), 'France': ('FRA', 'FR'),
    'Germany': ('DEU', 'DE'), 'Ghana': ('GHA', 'GH'), 'Greece': ('GRC', 'GR'),
    'Guyana': ('GUY', 'GY'), 'Hungary': ('HUN', 'HU'), 'Indonesia': ('IDN', 'ID'),
    'Iran': ('IRN', 'IR'), 'Ireland': ('IRL', 'IE'), 'Israel': ('ISR', 'IL'),
    'Italy': ('ITA', 'IT'), 'Jamaica': ('JAM', 'JM'), 'Japan': ('JPN', 'JP'),
    'Jordan': ('JOR', 'JO'), 'Kazakhstan': ('KAZ', 'KZ'), 'Kenya': ('KEN', 'KE'),
    'Kuwait': ('KWT', 'KW'), 'Kyrgyzstan': ('KGZ', 'KG'), 'Laos': ('LAO', 'LA'),
    'Latvia': ('LVA', 'LV'), 'Lithuania': ('LTU', 'LT'), 'Luxembourg': ('LUX', 'LU'),
    'Malaysia': ('MYS', 'MY'), 'Maldives': ('MDV', 'MV'), 'Mauritius': ('MUS', 'MU'),
    'Mexico': ('MEX', 'MX'), 'Mongolia': ('MNG', 'MN'), 'Morocco': ('MAR', 'MA'),
    'Mozambique': ('MOZ', 'MZ'), 'Myanmar': ('MMR', 'MM'), 'Namibia': ('NAM', 'NA'),
    'Nepal': ('NPL', 'NP'), 'Netherlands': ('NLD', 'NL'), 'New Zealand': ('NZL', 'NZ'),
    'Nigeria': ('NGA', 'NG'), 'Norway': ('NOR', 'NO'), 'Oman': ('OMN', 'OM'),
    'Palestine': ('PSE', 'PS'), 'Papua New Guinea': ('PNG', 'PG'), 'Peru': ('PER', 'PE'),
    'Philippines': ('PHL', 'PH'), 'Poland': ('POL', 'PL'), 'Portugal': ('PRT', 'PT'),
    'Qatar': ('QAT', 'QA'), 'Romania': ('ROU', 'RO'), 'Russia': ('RUS', 'RU'),
    'Rwanda': ('RWA', 'RW'), 'Saudi Arabia': ('SAU', 'SA'), 'Senegal': ('SEN', 'SN'),
    'Serbia': ('SRB', 'RS'), 'Seychelles': ('SYC', 'SC'), 'Singapore': ('SGP', 'SG'),
    'Slovakia': ('SVK', 'SK'), 'Slovenia': ('SVN', 'SI'), 'South Africa': ('ZAF', 'ZA'),
    'South Korea': ('KOR', 'KR'), 'Spain': ('ESP', 'ES'), 'Sri Lanka': ('LKA', 'LK'),
    'Sweden': ('SWE', 'SE'), 'Switzerland': ('CHE', 'CH'), 'Tajikistan': ('TJK', 'TJ'),
    'Tanzania': ('TZA', 'TZ'), 'Thailand': ('THA', 'TH'), 'Trinidad and Tobago': ('TTO', 'TT'),
    'Turkey': ('TUR', 'TR'), 'Turkmenistan': ('TKM', 'TM'), 'Uganda': ('UGA', 'UG'),
    'Ukraine': ('UKR', 'UA'), 'United Arab Emirates': ('ARE', 'AE'),
    'United Kingdom': ('GBR', 'GB'), 'United States': ('USA', 'US'),
    'Uzbekistan': ('UZB', 'UZ'), 'Vatican City': ('VAT', 'VA'), 'Vietnam': ('VNM', 'VN'),
}


def canon_country(name):
    bare = re.sub(r"\s*\([^)]*\)\s*", " ", name)
    bare = re.sub(r"\s+", " ", bare).strip()
    key = bare.lower().replace(".", "").strip()
    return COUNTRY_CANON.get(key, bare)


def split_label(label):
    """'Indonesia, Australia & New Zealand' -> canonical country names, deduped."""
    s = label
    for name in COMPOUND_COUNTRIES:
        parts = [re.escape(p) for p in re.split(r"\s+and\s+", name, flags=re.I)]
        s = re.sub(r"\s*(?:and|&)\s*".join(parts), name.replace(" ", "\x01"), s, flags=re.I)
    s = re.sub(r"\s+and\s+", ", ", s, flags=re.I).replace(" & ", ", ")
    out = []
    for p in s.split(","):
        c = canon_country(p.strip().replace("\x01", " "))
        if c and c not in out:
            out.append(c)
    return out


def load_trips():
    d = json.loads(VISITS_PATH.read_text())
    trips = []
    for t in d["trips"]:
        trips.append({"start": t["start"], "end": t["end"], "label": t["label"],
                      "countries": split_label(t["label"])})
    return trips


# --- helpers -----------------------------------------------------------------
def log(msg):
    print(msg, flush=True)


def fetch(url, timeout=60, ua=UA, retries=3, backoff=6):
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": ua, "Accept": "*/*"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            last = e
            if e.code == 429 or e.code >= 500:
                time.sleep(backoff * (attempt + 1))
                continue
            raise
        except Exception as e:  # timeouts, resets
            last = e
            time.sleep(backoff)
    raise last


def fetch_json(url, **kw):
    return json.loads(fetch(url, **kw).decode("utf-8"))


def today_iso():
    return datetime.date.today().isoformat()


def month_iter(start_ym, end_ym):
    y, m = map(int, start_ym.split("-"))
    ey, em = map(int, end_ym.split("-"))
    while (y, m) <= (ey, em):
        yield f"{y:04d}-{m:02d}"
        m += 1
        if m == 13:
            y, m = y + 1, 1


def excel_serial_to_iso(v):
    """EXIM's signing dates are Excel serials in some rows and dd-mm-yyyy text in others."""
    s = str(v).strip()
    if re.fullmatch(r"\d{4,6}(\.0+)?", s):
        d = datetime.date(1899, 12, 30) + datetime.timedelta(days=int(float(s)))
        return d.isoformat()
    m = re.fullmatch(r"(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})", s)
    if m:
        return f"{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}"
    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2}).*", s)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    return None


def read_xlsx_rows(blob):
    """Minimal .xlsx reader (first worksheet, shared strings) so the Action needs no openpyxl."""
    z = zipfile.ZipFile(io.BytesIO(blob))
    ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    strs = []
    if "xl/sharedStrings.xml" in z.namelist():
        root = ET.fromstring(z.read("xl/sharedStrings.xml"))
        for si in root.findall("m:si", ns):
            strs.append("".join(t.text or "" for t in si.iter(f"{{{ns['m']}}}t")))
    sheet_name = sorted(n for n in z.namelist() if re.match(r"xl/worksheets/sheet\d+\.xml", n))[0]
    sheet = ET.fromstring(z.read(sheet_name))
    rows = []
    for r in sheet.findall(".//m:sheetData/m:row", ns):
        row = []
        for c in r.findall("m:c", ns):
            v = c.find("m:v", ns)
            if v is None:
                is_ = c.find("m:is", ns)
                row.append("".join(t.text or "" for t in is_.iter(f"{{{ns['m']}}}t")) if is_ is not None else "")
            elif c.get("t") == "s":
                row.append(strs[int(v.text)])
            else:
                row.append(v.text or "")
        rows.append([x.strip() if isinstance(x, str) else x for x in row])
    return rows


# --- documents: MEA "List of Outcomes" ---------------------------------------
MEA_LIST = ("https://www.mea.gov.in/FrontEnd/FetchPublicationListingData?publicationId=53"
            "&KeywordName={kw}&page={page}&PageSize=50&PLngId=1")
# Title conventions changed over the years: 2021-22 lists read "List of agreements signed/announced
# during the visit of Prime Minister to Denmark" or "List of documents ..."; from 2023 "List of Outcomes".
MEA_KEYWORDS = ["List of Outcomes", "List of agreements", "List of MoUs", "List of documents"]
MEA_DETAIL = "https://www.mea.gov.in/FrontEnd/FetchPublicationDetailData?pkid={id}&languageId=1"
MEA_PUBLIC = "https://www.mea.gov.in/bilateral-documents?dtl/{id}/"

MONTHS = {m: i for i, m in enumerate(["January", "February", "March", "April", "May", "June", "July",
                                      "August", "September", "October", "November", "December"], 1)}


def parse_mea_listing(text):
    """Yield {'id','date','title','tags'} for every entry in a listing fragment."""
    out = []
    for box in re.split(r'class="pressRelesastBox"', text)[1:]:
        m = re.search(r'class="date">\s*(\d{1,2})\s+([A-Za-z]+),?\s+(\d{4})', box)
        t = re.search(r'href="[^"]*dtl/(\d+)/[^"]*"[^>]*>\s*(.*?)\s*</a>', box, re.S)
        if not (m and t):
            continue
        mon = MONTHS.get(m.group(2).strip().title())
        if not mon:
            continue
        date = f"{m.group(3)}-{mon:02d}-{int(m.group(1)):02d}"
        tags = [html.unescape(x).strip() for x in re.findall(r"redirectWithTag\('([^']*)'\)", box)]
        out.append({"id": int(t.group(1)), "date": date,
                    "title": html.unescape(re.sub(r"\s+", " ", t.group(2))).strip(), "tags": tags})
    return out


def count_list_items(detail_html):
    """How many numbered items an outcome list carries, or None when the layout defeats counting.

    MEA publishes these in three layouts: tables with a serial-number column, <li> lists, and
    plain paragraphs numbered "1. ... 2. ..." inline. Tried in that order."""
    n = 0
    for row in re.findall(r"<tr[^>]*>(.*?)</tr>", detail_html, re.S | re.I):
        cells = [re.sub(r"\s+", " ", html.unescape(re.sub("<[^>]+>", " ", c))).strip()
                 for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, re.S | re.I)]
        if cells and re.fullmatch(r"\d{1,3}\.?", cells[0]):
            n += 1
    if n:
        return n
    n = len(re.findall(r"<li\b", detail_html, re.I))
    if n:
        return n
    text = re.sub(r"\s+", " ", html.unescape(re.sub("<[^>]+>", " ", detail_html)))
    nums = [int(x) for x in re.findall(r"(?:^|[\s>(])(\d{1,2})\.\s+(?=[A-Z\u201c\"(])", text)]
    best, run = 0, 0
    for x in nums:  # longest 1,2,3,... sequence; restarts (a second numbered block) are counted on top
        run = run + 1 if x == run + 1 else (1 if x == 1 else run)
        best = max(best, run)
    return best or None


# Outgoing lists read "Prime Minister's State Visit to Uzbekistan"; a foreign leader's
# visit reads "Visit of the Prime Minister of Belgium to India". The destination decides.
INBOUND_RE = re.compile(r"\bto India\b|\bin India\b|\bin New Delhi\b", re.I)


def match_document_to_trip(entry, trips):
    """A list is attached to a trip when its date falls inside the trip (with a 3-day tail),
    a tag or the title names one of the trip's countries, and the visit was not *to* India."""
    if not entry["title"].lower().startswith("list of"):
        return None
    if INBOUND_RE.search(entry["title"]):
        return None
    tag_countries = {canon_country(t) for t in entry["tags"]}
    for tr in trips:
        lo = (datetime.date.fromisoformat(tr["start"]) - datetime.timedelta(days=1)).isoformat()
        hi = (datetime.date.fromisoformat(tr["end"]) + datetime.timedelta(days=3)).isoformat()
        if not (lo <= entry["date"] <= hi):
            continue
        hit = [c for c in tr["countries"] if c in tag_countries or c.lower() in entry["title"].lower()]
        if hit:
            return tr, hit[0]
    return None


def fetch_documents(trips, prev):
    earliest = min(t["start"] for t in trips)
    prev_items = {}
    for c in (prev or {}).get("countries", {}).values():
        for d in c.get("documents", []):
            prev_items[d["id"]] = d.get("items")
    entries, seen, pages = [], set(), 0
    for kw in MEA_KEYWORDS:
        page = 1
        while page <= 20:
            url = MEA_LIST.format(kw=urllib.parse.quote(kw), page=page)
            batch = parse_mea_listing(fetch(url, ua=BROWSER_UA).decode("utf-8", "replace"))
            pages += 1
            if not batch:
                break
            for e in batch:
                if e["id"] not in seen:
                    seen.add(e["id"])
                    entries.append(e)
            if min(e["date"] for e in batch) < earliest:
                break
            page += 1
            time.sleep(1)
    log(f"[documents] {len(entries)} candidate lists scanned over {pages} page(s)")
    by_country = {}
    for e in entries:
        hit = match_document_to_trip(e, trips)
        if not hit:
            continue
        tr, country = hit
        items = prev_items.get(e["id"])
        if not items:  # never cache a failed or zero count; recount next run
            try:
                items = count_list_items(fetch(MEA_DETAIL.format(id=e["id"]), ua=BROWSER_UA).decode("utf-8", "replace"))
                time.sleep(1)
            except Exception as ex:
                log(f"[documents] detail {e['id']} failed: {ex}")
                items = None
        by_country.setdefault(country, []).append({
            "id": e["id"], "date": e["date"], "trip_start": tr["start"], "title": e["title"],
            "items": items, "url": MEA_PUBLIC.format(id=e["id"]),
        })
    for lst in by_country.values():
        lst.sort(key=lambda d: d["date"])
    return by_country, {"scanned": len(entries), "matched": sum(len(v) for v in by_country.values())}


# --- trade: UN Comtrade keyless preview --------------------------------------
# partner2Code=0, motCode=0 and customsCode=C00 restrict the reply to the aggregate row per partner.
# Without them India's import rows come back broken down by country of consignment and mode of
# transport, which pushes the reply past the preview endpoint's 500-record cap and silently truncates.
COMTRADE_PREVIEW = ("https://comtradeapi.un.org/public/v1/preview/C/{freq}/HS?reporterCode=699"
                    "&period={period}&cmdCode=TOTAL&flowCode={flow}&partner2Code=0&motCode=0&customsCode=C00")
COMTRADE_PREVIEW_CAP = 500
COMTRADE_PARTNERS = "https://comtradeapi.un.org/files/v1/app/reference/partnerAreas.json"
COMTRADE_PAUSE = 5.5  # the preview endpoint asks for one request every 5 seconds


def comtrade_code_map():
    ref = fetch_json(COMTRADE_PARTNERS)["results"]
    return {int(r["PartnerCode"]): r.get("PartnerCodeIsoAlpha3") for r in ref}


def comtrade_period(freq, period, flow, code_to_iso, wanted_iso):
    """Return {iso3: value} for one period and flow, 'W00' = world total."""
    d = fetch_json(COMTRADE_PREVIEW.format(freq=freq, period=period, flow=flow))
    if d.get("count", 0) >= COMTRADE_PREVIEW_CAP:
        raise ValueError(f"Comtrade preview truncated at {COMTRADE_PREVIEW_CAP} records for {freq} {period} {flow}")
    out = {}
    for rec in d.get("data", []):
        pc = int(rec.get("partnerCode", -1))
        iso = "W00" if pc == 0 else code_to_iso.get(pc)
        if iso in wanted_iso or iso == "W00":
            out[iso] = round(out.get(iso, 0) + float(rec.get("primaryValue") or 0), 3)
    return out, d.get("count", 0)


def fetch_trade(countries, prev):
    iso_of = {c: ISO[c][0] for c in countries if c in ISO}
    wanted = set(iso_of.values())
    code_to_iso = comtrade_code_map()
    now = datetime.date.today()
    annual = {c: dict(((prev or {}).get("countries", {}).get(c, {}).get("trade", {}) or {}).get("annual", {})) for c in countries}
    monthly = {c: dict(((prev or {}).get("countries", {}).get(c, {}).get("trade", {}) or {}).get("monthly", {})) for c in countries}
    world = (prev or {}).get("india_total", {}).get("trade", {}) or {}
    w_annual, w_monthly = dict(world.get("annual", {})), dict(world.get("monthly", {}))

    def store(freq, period, flow, values):
        key = "x" if flow == "X" else "m"
        for c, iso in iso_of.items():
            if iso in values:
                (annual if freq == "A" else monthly)[c].setdefault(period, {})[key] = values[iso]
        if "W00" in values:
            (w_annual if freq == "A" else w_monthly).setdefault(period, {})[key] = values["W00"]

    calls = 0
    # Annual: refetch the last two years (revisions), backfill anything missing.
    years = [str(y) for y in range(FIRST_YEAR, now.year + 1)]
    # A period counts as fetched when India's world total has both flows for it. Small partners
    # legitimately lack a flow in some periods (no trade that month), so keying on them would
    # refetch the same periods every run.
    have_year = lambda y: y in w_annual and {"x", "m"} <= set(w_annual[y])
    for y in years:
        if have_year(y) and int(y) < now.year - 1:
            continue
        for flow in ("X", "M"):
            vals, n = comtrade_period("A", y, flow, code_to_iso, wanted)
            calls += 1
            time.sleep(COMTRADE_PAUSE)
            if n:
                store("A", y, flow, vals)
    # Monthly: everything missing, plus the trailing months.
    end_ym = now.strftime("%Y-%m")
    all_months = list(month_iter(MONTHLY_FROM, end_ym))
    trailing = set(all_months[-TRAILING_MONTHS - 1:])
    known_empty = set((prev or {}).get("meta", {}).get("sources", {}).get("trade", {}).get("empty_months", []))
    empty_months = []
    for ym in all_months:
        have = ym in w_monthly and {"x", "m"} <= set(w_monthly[ym])
        if ym not in trailing and (have or ym in known_empty):
            if ym in known_empty and not have:
                empty_months.append(ym)
            continue
        got_any = False
        for flow in ("X", "M"):
            vals, n = comtrade_period("M", ym.replace("-", ""), flow, code_to_iso, wanted)
            calls += 1
            time.sleep(COMTRADE_PAUSE)
            if n:
                got_any = True
                store("M", ym, flow, vals)
        if not got_any and ym not in trailing:
            empty_months.append(ym)
    log(f"[trade] {calls} Comtrade calls")
    per_country = {c: {"annual": dict(sorted(annual[c].items())), "monthly": dict(sorted(monthly[c].items()))}
                   for c in countries}
    india_total = {"annual": dict(sorted(w_annual.items())), "monthly": dict(sorted(w_monthly.items()))}
    return per_country, india_total, {"calls": calls, "empty_months": sorted(set(empty_months))}


# --- coauthorship: OpenAlex --------------------------------------------------
OPENALEX = ("https://api.openalex.org/works?filter=institutions.country_code:in{partner}"
            "&group_by=publication_year&per-page=50")


def openalex_years(partner_iso2):
    d = fetch_json(OPENALEX.format(partner="" if not partner_iso2 else ",institutions.country_code:" + partner_iso2.lower()))
    return {g["key"]: g["count"] for g in d.get("group_by", []) if str(g["key"]) >= str(FIRST_YEAR)}


def fetch_coauthorship(countries):
    out = {}
    for c in countries:
        if c not in ISO:
            continue
        out[c] = dict(sorted(openalex_years(ISO[c][1]).items()))
        time.sleep(0.3)
    total = dict(sorted(openalex_years(None).items()))
    return out, total, {"calls": len(out) + 1}


# --- unga: Harvard Dataverse (Voeten, Bailey, Strezhnev) ---------------------
DATAVERSE_META = "https://dataverse.harvard.edu/api/datasets/:persistentId/?persistentId=doi:10.7910/DVN/LEJUQZ"
DATAVERSE_FILE = "https://dataverse.harvard.edu/api/access/datafile/{id}?format=original"
INDIA_COW = 750


def fetch_unga(countries, prev):
    meta = fetch_json(DATAVERSE_META)["data"]["latestVersion"]
    version = f"{meta['versionNumber']}.{meta.get('versionMinorNumber', 0)}"
    files = {f["dataFile"]["filename"]: f["dataFile"]["id"] for f in meta["files"]}
    prev_src = (prev or {}).get("meta", {}).get("sources", {}).get("unga", {})
    prev_ok = prev_src.get("status") == "ok" and all(
        (prev or {}).get("countries", {}).get(c, {}).get("unga") for c in countries if c in ISO)
    if prev_src.get("version") == version and prev_ok:
        log(f"[unga] version {version} unchanged, keeping cached scores")
        return {c: (prev or {})["countries"][c]["unga"] for c in countries if c in ISO}, {"version": version, "reused": True}

    ideal_name = next(n for n in files if n.startswith("Idealpointestimates") and n.endswith(".csv"))
    agree_name = next(n for n in files if n == "AgreementScores.csv")
    # ISO3 -> COW code from the ideal-point file (it carries both).
    # A country can carry two Correlates-of-War codes over time (Germany: 260 and 255), and the
    # dyadic file does not necessarily use the same one as the country-year file, so every code
    # ever attached to an ISO3 maps back to that country.
    iso_to_cows = {}
    for row in csv.DictReader(io.StringIO(fetch(DATAVERSE_FILE.format(id=files[ideal_name]), timeout=120).decode("utf-8", "replace"))):
        if row.get("iso3c") and row.get("ccode"):
            iso_to_cows.setdefault(row["iso3c"], set()).add(int(row["ccode"]))
    cow_to_country = {code: c for c in countries if c in ISO for code in iso_to_cows.get(ISO[c][0], ())}
    log(f"[unga] downloading {agree_name} (~145 MB) for version {version}")
    req = urllib.request.Request(DATAVERSE_FILE.format(id=files[agree_name]), headers={"User-Agent": UA})
    scores = {c: {} for c in cow_to_country.values()}
    with urllib.request.urlopen(req, timeout=300) as r:
        reader = csv.reader(io.TextIOWrapper(r, encoding="utf-8", errors="replace"))
        header = next(reader)
        col = {n: i for i, n in enumerate(header)}
        i1, i2, ia, isess, iyear = col["ccode1"], col["ccode2"], col["agree"], col["session.x"], col["year"]
        for row in reader:
            try:
                a, b = int(row[i1]), int(row[i2])
            except ValueError:
                continue
            if INDIA_COW not in (a, b):
                continue
            other = b if a == INDIA_COW else a
            c = cow_to_country.get(other)
            if not c:
                continue
            sess = int(row[isess])
            if sess < UNGA_MIN_SESSION or not row[ia]:
                continue
            scores[c].setdefault(str(sess), {"agree": round(float(row[ia]), 4), "year": int(float(row[iyear]))})
    out = {c: dict(sorted(scores.get(c, {}).items(), key=lambda kv: int(kv[0]))) for c in countries if c in ISO}
    return out, {"version": version, "reused": False}


# --- loc: EXIM Bank lines of credit ------------------------------------------
EXIM_PAGE = "https://www.eximbankindia.in/lines-of-credit"


def exim_links(page_html):
    links = {}
    for href in re.findall(r'href="([^"]*\.xlsx[^"]*)"', page_html):
        name = urllib.parse.unquote(href).lower()
        url = href if href.startswith("http") else "https://www.eximbankindia.in" + href
        if "goiloc" in name or "signed" in name:
            links.setdefault("signed", url)
        elif "operative" in name:
            links.setdefault("operative", url)
    return links


def header_index(rows, needle):
    for i, r in enumerate(rows):
        if any(str(x).strip().lower().startswith(needle) for x in r):
            return i, [str(x).strip().lower() for x in r]
    raise ValueError(f"header row with {needle!r} not found")


def amount_fields(v):
    s = str(v).strip()
    try:
        return float(s), s
    except ValueError:
        return None, s


def loc_country_key(name, wanted):
    n = canon_country(str(name).replace("’", "'"))
    for c in wanted:
        if c.lower() == n.lower():
            return c
    return None


def fetch_loc(countries):
    page = fetch(EXIM_PAGE, ua=BROWSER_UA).decode("utf-8", "replace")
    links = exim_links(page)
    if "signed" not in links:
        raise ValueError("signed-LoC spreadsheet link not found on EXIM page")
    vintage = None
    m = re.search(r"(\d{2})\.(\d{2})\.(\d{4})\.xlsx", urllib.parse.unquote(links["signed"]))
    if m:
        vintage = f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
    out = {c: {"signed": [], "operative": []} for c in countries}

    rows = read_xlsx_rows(fetch(links["signed"], ua=BROWSER_UA))
    hi, hdr = header_index(rows, "sr no")
    ci = {k: next(i for i, h in enumerate(hdr) if h.startswith(k)) for k in ("year", "country", "borrower", "amount", "purpose", "date")}
    for r in rows[hi + 1:]:
        if len(r) <= ci["date"] or not str(r[ci["country"]]).strip():
            continue
        c = loc_country_key(r[ci["country"]], countries)
        if not c:
            continue
        amt, txt = amount_fields(r[ci["amount"]])
        out[c]["signed"].append({"fy": str(r[ci["year"]]).strip(), "borrower": str(r[ci["borrower"]]).strip(),
                                 "amount_usd_mn": amt, "amount_text": txt, "purpose": str(r[ci["purpose"]]).strip(),
                                 "signed": excel_serial_to_iso(r[ci["date"]])})
    if "operative" in links:
        rows = read_xlsx_rows(fetch(links["operative"], ua=BROWSER_UA))
        hi, hdr = header_index(rows, "sr no")
        ci = {k: next(i for i, h in enumerate(hdr) if h.startswith(k)) for k in ("country", "amount", "projects", "total", "available", "value")}
        for r in rows[hi + 1:]:
            if len(r) <= ci["value"] or not str(r[ci["country"]]).strip():
                continue
            c = loc_country_key(r[ci["country"]], countries)
            if not c:
                continue
            amt, txt = amount_fields(r[ci["amount"]])
            out[c]["operative"].append({"amount_usd_mn": amt, "amount_text": txt,
                                        "project": str(r[ci["projects"]]).strip(),
                                        "project_value_usd_mn": amount_fields(r[ci["total"]])[0],
                                        "available_for_procurement": str(r[ci["available"]]).strip().lower().startswith("y")})
    n = sum(len(v["signed"]) + len(v["operative"]) for v in out.values())
    return out, {"vintage": vintage, "rows": n, "files": links}


# --- assembly ----------------------------------------------------------------
SOURCES = {
    "documents": {"name": "Ministry of External Affairs, Bilateral/Multilateral Documents ('List of Outcomes')",
                  "url": "https://www.mea.gov.in/bilateral-documents.htm", "licence": "Government of India; not stated",
                  "granularity": "per visit", "window": "0-12 months"},
    "trade": {"name": "UN Comtrade (India as reporter, HS total, all partners)",
              "url": "https://comtradeplus.un.org/", "licence": "UN Comtrade use policy; attribution required",
              "granularity": "partner x year, partner x month, USD", "window": "12 months before/after"},
    "coauthorship": {"name": "OpenAlex (works with an India-affiliated and a partner-affiliated author)",
                     "url": "https://openalex.org/", "licence": "CC0",
                     "granularity": "partner x publication year", "window": "3 years before/after"},
    "unga": {"name": "Voeten, Bailey and Strezhnev, United Nations General Assembly Voting Data (Harvard Dataverse)",
             "url": "https://doi.org/10.7910/DVN/LEJUQZ", "licence": "CC0 1.0",
             "granularity": "dyad x session", "window": "3 sessions before, 2 after"},
    "loc": {"name": "Export-Import Bank of India, Government of India lines of credit",
            "url": "https://www.eximbankindia.in/lines-of-credit", "licence": "Not stated",
            "granularity": "per line of credit", "window": "announced, signed, operative"},
}


def main():
    skip = {s.strip() for s in os.environ.get("OUTCOMES_SKIP", "").split(",") if s.strip()}
    trips = load_trips()
    countries = sorted({c for t in trips for c in t["countries"]})
    unknown = [c for c in countries if c not in ISO]
    if unknown:
        log(f"[warn] no ISO code for {unknown}; those countries get only document and LoC matches")
    prev = None
    if OUT_PATH.exists():
        try:
            prev = json.loads(OUT_PATH.read_text())
        except Exception as e:
            log(f"[warn] could not read previous outcomes.json: {e}")

    out = {"meta": {"schema": SCHEMA, "generated": today_iso(), "note": NOTE,
                    "registry_updated": json.loads(VISITS_PATH.read_text())["meta"].get("updated"),
                    "sources": {}},
           "countries": {c: {"iso3": ISO.get(c, (None, None))[0], "iso2": ISO.get(c, (None, None))[1]} for c in countries},
           "india_total": {}}
    ok_any = False

    def carry(section, err):
        src = dict(SOURCES[section])
        pv = (prev or {}).get("meta", {}).get("sources", {}).get(section, {})
        src.update({"status": "cached" if pv.get("fetched") else "failed", "fetched": pv.get("fetched"),
                    "error": str(err)[:300]})
        for k in ("vintage", "version", "empty_months"):
            if k in pv:
                src[k] = pv[k]
        out["meta"]["sources"][section] = src
        for c in countries:
            pc = (prev or {}).get("countries", {}).get(c, {})
            if section in pc:
                out["countries"][c][section] = pc[section]
        if section == "trade" and (prev or {}).get("india_total", {}).get("trade"):
            out["india_total"]["trade"] = prev["india_total"]["trade"]
        if section == "coauthorship" and (prev or {}).get("india_total", {}).get("coauthorship"):
            out["india_total"]["coauthorship"] = prev["india_total"]["coauthorship"]

    def done(section, extra):
        nonlocal ok_any
        ok_any = True
        src = dict(SOURCES[section])
        src.update({"status": "ok", "fetched": today_iso()})
        src.update(extra or {})
        out["meta"]["sources"][section] = src

    for section in SOURCES:
        if section in skip:
            carry(section, "skipped by OUTCOMES_SKIP")
            continue
        t0 = time.time()
        try:
            if section == "documents":
                data, extra = fetch_documents(trips, prev)
                for c in countries:
                    out["countries"][c]["documents"] = data.get(c, [])
            elif section == "trade":
                data, total, extra = fetch_trade(countries, prev)
                for c in countries:
                    out["countries"][c]["trade"] = data[c]
                out["india_total"]["trade"] = total
            elif section == "coauthorship":
                data, total, extra = fetch_coauthorship(countries)
                for c in countries:
                    out["countries"][c]["coauthorship"] = data.get(c, {})
                out["india_total"]["coauthorship"] = total
            elif section == "unga":
                data, extra = fetch_unga(countries, prev)
                for c in countries:
                    out["countries"][c]["unga"] = data.get(c, {})
            elif section == "loc":
                data, extra = fetch_loc(countries)
                for c in countries:
                    out["countries"][c]["loc"] = data[c]
            done(section, extra)
            log(f"[{section}] ok in {time.time() - t0:.0f}s")
        except Exception as e:
            log(f"[{section}] FAILED: {e!r}")
            carry(section, e)

    if not ok_any:
        log("No section fetched successfully; leaving the previous outcomes.json in place.")
        return 0
    OUT_PATH.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":"), sort_keys=False) + "\n")
    log(f"Wrote {OUT_PATH.relative_to(ROOT)} ({OUT_PATH.stat().st_size // 1024} KB, {len(countries)} countries)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
