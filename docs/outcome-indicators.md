# Outcome indicators for the PM foreign visits tracker

Research and design memo. Written 2026-09-05. Nothing in this memo has been built; it proposes
what to build and records what was verified.

## Summary

The site records where the Prime Minister went and for how long, and can show a reported cost
when the registry supplies one (the trip drawer has a slot for it, but the current 44 registry rows
carry no cost figure). It has no evidence-based way to show what a visit was followed by. This
memo proposes a set of **outcome indicators**: public, country-level statistics that may have
moved around a visit, shown with a fixed baseline and a fixed lag window, and with null and
negative movements rendered exactly like positive ones.

The core finding is that the honest feature is narrower than "what did the visit produce" and
wider than "FDI from the visited country". Three things are robustly populable today from
verified public sources: the documents the two governments published as the visit's outcomes,
bilateral merchandise trade by month, and research co-authorship by year. Two more are populable
with caveats: UN General Assembly voting agreement by session, and government lines of credit by
partner. FDI by source country survives only as a fiscal-year number carried with its known
distortions, and several of the indicators in the brief (defence procurement value by country,
emigration clearances by country, bilateral remittances, MoU ratification rates) cannot be
populated from any public source found and are rejected.

Two structural constraints shape everything below:

- **The registry starts in March 2021.** With a 24-month post-visit window, only 16 of the 44
  trips have a closed window today; with FDI's three-fiscal-year window, only the 2021 and early
  2022 trips do. Most panels will read "window still open" for years, and the design treats that
  as a first-class state.
- **Nothing here is causal.** Visits are scheduled when a relationship is already moving, and the
  windows contain price shocks, sanctions, elections and a pandemic. Every number is shown next to
  India's overall change and a peer-country change, and the site never uses the words "caused",
  "delivered", or "worth".

Repo facts used in this memo, from `data/visits.json` at commit `fedff71`:

| Fact | Value |
|---|---|
| Trips in registry | 44 (2021: 3, 2022: 7, 2023: 6, 2024: 11, 2025: 11, 2026 to July: 6) |
| Multi-country trips | 23 |
| Distinct countries | 54 |
| Countries visited two or more times | 13 (France and Japan 4 each; Indonesia, Italy, United States 3 each) |
| Trips ending by December 2023 | 16 |
| Trips ending by December 2024 | 27 |
## 1. Candidate indicators

The list below is deliberately wide. Each candidate is scored on four things a critic and a
supporter would both accept as fair: (a) it is a public number nobody on this project computes by
hand; (b) it is available for the visited country specifically, not just for India in aggregate;
(c) its lag is short enough that at least some of the 2021–2026 visits have a closed window
today; (d) a movement in either direction can be shown with the same sentence template, so the
indicator does not smuggle in a value judgement. "Survives" means it passed source verification in
section 2 and is worth carrying into the design; it does not mean it is in the first-build
shortlist (section 5).

### 1.1 Facts of the visit itself (near-immediate, least contestable)

| # | Indicator | What it measures | Direction-neutral? | Survives |
|---|---|---|---|---|
| F1 | Documents listed by MEA for the visit | Count of joint statements, MoUs, agreements and treaties that the two governments chose to publish as the visit's outcomes | Yes: a count, not a judgement | Yes |
| F2 | Documents from the visit traceable in the Treaties Database | Of the F1 documents, how many can be matched to a Treaties Database record, and how many of those carry an entry-into-force date, checked yearly | Yes | Partial: counts only, never a ratio (see 2.2) |
| F3 | Return visit within 12 months | Whether the partner's head of state or government visited India within a year | Yes | Partial: MEA's visits listing is script-rendered and its feed endpoint was not found; PIB releases are the fallback |
| F4 | Ministerial follow-up density | Count of incoming ministerial visits from the partner in the following 12 months | Yes | Partial, same source and risk as F3 |

F1 is the only indicator where the number is a direct product of the visit rather than something
that may have moved around it. It is also the easiest to over-read: MoUs are cheap to sign, and a
visit with twenty documents is not "better" than one with three. It is shown as a count with the
titles listed, never as a score.

### 1.2 Trade and investment flows

| # | Indicator | What it measures | Weaknesses | Survives |
|---|---|---|---|---|
| T1 | Merchandise exports to and imports from the partner, monthly | Customs-recorded goods trade, both directions, in USD | Dominated by prices and a few commodities (crude, gold, diamonds); services trade absent | Yes |
| T2 | Trade growth relative to India-wide growth | T1 change minus the change for India's total trade over the same window | Same as T1; strips out India-wide shocks only | Yes (derived) |
| T3 | FDI equity inflows from the partner, fiscal quarter | DPIIT's country-wise inflow table | Attributed to the *immediate* investing country, so Mauritius, Singapore and the Netherlands absorb money that originates elsewhere; announcement-to-realisation gap of 2+ years; lumpy (one deal moves a year); fiscal-year basis; the partner may not be broken out at all if small | Yes, with the caveats on the face of the number |
| T4 | Investment announcements made during the visit | The headline "₹X crore committed" figures in PIB releases | Not a measured flow; unverifiable; routinely restated; the archetype of boosterism | Rejected as an indicator; may be shown as a quoted claim with a "announced, not measured" label if F1 documents contain one |
| T5 | Bilateral investment treaty or DTAA status change | Whether a BIT, DTAA amendment or social-security agreement moved from signed to in force | Slow and rare; many partners have none pending | Partial: usable as a fact in F2, not as a flow |
| T6 | Services trade with the partner | IT and business services exports by destination | RBI publishes services exports only by broad region; no country-level series | Rejected: cannot be populated |

### 1.3 Defence and energy procurement

| # | Indicator | What it measures | Weaknesses | Survives |
|---|---|---|---|---|
| D1 | Arms deliveries from the partner, annual | SIPRI trend-indicator value of transfers to India by supplier | Deliveries lag contracts by 3–7 years; TIV is a volume index, not money; a single delivery batch dominates a year | Yes, as context with a 3-year window, not as a headline |
| D2 | Defence contracts signed with the partner | Contract values by supplier country | No structured public country-wise series; Lok Sabha answers give aggregates or one-offs | Rejected: cannot be populated systematically |
| E1 | Crude and LNG imports by source country, monthly | Volume and value of energy imports from the partner | Contract timing, sanctions and world prices swamp diplomacy (2022 Russian crude is the obvious case) | Yes, energy-exporting partners only, with the price caveat |
| E2 | Coal imports by source | Same for coal | Country-wise coal import data exists only in scattered answers and paid trackers | Rejected: cannot be populated reliably |

### 1.4 People: diaspora, mobility, education

| # | Indicator | What it measures | Weaknesses | Survives |
|---|---|---|---|---|
| P1 | Indian students in the partner country, annual | Outbound student counts by destination | One academic season's lag; partner visa policy is the main driver; multiple sources disagree | Yes |
| P2 | Tourist arrivals from the partner to India, annual or monthly | Foreign tourist arrivals by nationality | Slow official publication; airline capacity and visa-on-arrival policy dominate | Yes, annual |
| P3 | Emigration clearances to the partner, annual | eMigrate ECR clearances by destination | Only 18 ECR countries, mostly Gulf; the only open series is national totals with no country field | Rejected: cannot be populated |
| P4 | Remittance inflows from the partner | Estimated bilateral remittances | Estimates, not measurements; the World Bank matrix is modelled and irregular | Rejected for the panel; usable as context |
| P5 | Migration and mobility partnership agreements | Whether one was signed or entered force | It is a document (belongs in F1/F2) rather than a flow | Folded into F1/F2 |
| P6 | Visas issued to Indians by the partner | Partner-country visa statistics | Only a few partners publish by nationality (US, UK, Schengen); inconsistent definitions | Partial: per-partner where published |
| P7 | Passengers between India and the partner, quarterly | DGCA country-pair international traffic | DGCA's portal is script-rendered with no fetchable files; only a community CSV mirror is machine-readable | Deferred: revisit if DGCA exposes files |

### 1.5 Technology, science, education partnerships

| # | Indicator | What it measures | Weaknesses | Survives |
|---|---|---|---|---|
| S1 | Co-authored research papers, India × partner, annual | Count of works with at least one author affiliated in each country | 1–2 year publication lag; favours large systems; counts, not quality | Yes |
| S2 | Joint programmes or funds announced | Named initiatives (e.g. a joint research fund) | Announcement, not delivery; belongs in F1 | Folded into F1 |
| S3 | Patents co-filed | Joint patent families by inventor country | Public patent APIs exist but bilateral counts need heavy processing | Rejected for first build |

### 1.6 Multilateral and diplomatic alignment

| # | Indicator | What it measures | Weaknesses | Survives |
|---|---|---|---|---|
| M1 | UNGA voting agreement, India × partner, per session | Share of recorded votes where both cast the same vote | Structurally sticky; dominated by bloc issues (Palestine, Cuba) unrelated to the dyad; a supporter says it under-counts quiet cooperation, a critic says diplomacy should not be scored by votes at all | Yes, as context, clearly labelled as low-sensitivity |
| M2 | Machine-coded event tone (GDELT) | Average tone or Goldstein scale of media-reported India–partner events by month | English-language media bias; volume spikes on the visit itself; readers cannot audit it | Rejected for display; possibly an internal sanity check |
| M3 | Diplomatic footprint change | New consulates or missions opened in the partner | Rare; a fact for F1 | Folded into F1 |

### 1.7 Categories you did not list that belong here

- **Development lines of credit (LoCs) and their drawdown.** Amount, sanction date and
  operative status of Government of India LoCs to the partner, from EXIM Bank, and disbursement
  where Lok Sabha answers report it. Applies mainly to Africa, South Asia and island partners.
  Survives for those partners as announced amount and operative status; drawdown itself is not published (see 2.2).
- **Return and follow-up visits (F3, F4).** The cheapest, most legible reciprocity signal, and
  one both sides accept.
- **Energy and arms are procurement, but so are civil aircraft, nuclear and rail.** These do not
  have a country-wise public series beyond the HS-code trade data already in T1 and are not
  separated out.
## 2. Data sources, verified

Every source below was checked on 2026-09-05 by fetching it, not from memory. "Verified: yes"
means the checker retrieved data at the stated granularity; "partial" means the source exists but
some attribute (usually programmatic access or licence) could not be confirmed; "no" means the
source could not be reached or does not contain the claimed data. Government of India pages
generally state no licence; the Government Open Data Licence (GODL-India) applies only where a
dataset is published on data.gov.in. Several official sites (DPIIT, data.gov.in, coal.gov.in,
US State Department, UNCTAD, Income Tax Department) return 403 to non-browser fetchers, which
matters for an unattended pipeline and is noted per row.
### 2.1 Trade and investment flows

| Source | Indicator | Granularity available | Frequency | Format / programmatic access | Licence | Verified |
|---|---|---|---|---|---|---|
| DPIIT FDI statistics, quarterly fact sheet and "Table 11: country-wise FDI equity inflow" (dpiit.gov.in/publications/fdi-statistics) | FDI equity inflows by immediate investing country | ~80 countries × fiscal year (year-to-date within the year), INR crore and USD million; cumulative since April 2000 in the fact sheet annex; a full country × year matrix needs each year's Table 11 stitched | Quarterly | PDF only, text-extractable. The index page is a JavaScript shell; direct PDF links fetch with a browser user-agent but the site returns 403 to plain fetchers. No API | None stated | Yes |
| data.gov.in "Foreign Direct Investment (FDI) Equity Inflows" catalogue | FDI equity by sector, state and year | Not country-wise: only sector, state and year-wise resources were found | Irregular | CSV; resources state "The API for this resource does not exist" | GODL-India | Partial: country-wise series not found |
| RBI DBIE (data.rbi.org.in) and RBI Bulletin Table 34 / Annual Report appendix | FDI flows by country, top ~10 investors | Fiscal year, USD million, top countries only | Monthly bulletin, annual report | Manual XLS/PDF download; DBIE is a JavaScript shell; the old dbie.rbi.org.in host fails TLS. No API found | None seen | Partial |
| Ministry of Commerce Export Import Data Bank, tradestat.commerce.gov.in (EIDB country-wise export/import/total trade; MEIDB monthly module) | Merchandise exports, imports and total trade by partner | 243 partner rows × fiscal year 2017-18 to 2025-26; monthly by country 2018 to 2026; USD million or INR crore, with share and growth | Roughly monthly ("last updated 07/08/2026" at check) | HTML table returned by a plain HTTP POST after fetching a CSRF token; scrapeable without login. No API, no licence text, only a disclaimer | Not stated | Yes |
| UN Comtrade (comtradeapi.un.org) | Bilateral goods trade, HS code level | India as reporter, any partner, annual and monthly; India annual 2025 released July 2026, monthly June 2026 released August 2026 (about a 7-week lag); monthly data arrive as "reported" then get revised | Monthly releases | JSON. Preview endpoint needs no key but is limited to one period and 500 rows per call; a free registered key allows 500 calls/day and 100k rows/call | UN Comtrade use policy: free use is "internal", with an explicit exception for free visualisation tools with "UN Comtrade" attribution | Yes |
| IMF International Merchandise Trade Statistics (formerly Direction of Trade Statistics), api.imf.org SDMX 2.1 | Bilateral exports (FOB) and imports (CIF/FOB) in USD | India × ~220 counterparts, monthly and annual, through 2026-M05 at check | Monthly, around the 25th | SDMX XML without a key (the JSON variant returned HTTP 500); this is a secondary compilation of national data | Terms pages blocked (403); search snippets say all rights reserved, attribution required, no republishing on non-IMF sites. Unverified | API yes, terms partial |
| World Bank WITS (wits.worldbank.org/API) | Bilateral trade aggregates | India × partner × year from 1988, annual only | Annual | JSON, no key | WITS TradeStats aggregates fall under World Bank open data; Comtrade-sourced detail is "for internal use only" | Yes |
| UNCTAD bilateral FDI statistics | Bilateral FDI flows and stocks | Discontinued after 2012 data; only aggregate per-economy FDI remains | n/a | unctad.org returned 403 to the checker | n/a | Partial, and unusable for 2021+ |

**What this means for the FDI candidate (T3).** It survives, but only as a fiscal-year number with
its weaknesses printed beside it. The DPIIT country table for fiscal 2025-26 attributes 37% of
equity inflows to Singapore, 10% to Mauritius, 4% to the Cayman Islands and 3% to Cyprus, and even
lists "IFSC, India" as an origin. Germany, a country visited twice, shows under 1%. The tables are
equity-only, marked provisional pending reconciliation with the RBI, and carry a "country details
awaited" residual. Many visited countries in Africa, the Pacific and the Caribbean appear only as
sub-million-dollar lines. There is no monthly country series and no open-licence machine-readable
one; population means parsing a PDF each quarter.

**What this means for trade (T1, T2).** Trade is the best-instrumented flow. Three independent
routes exist: the ministry's own databank by scrape, IMF monthly by SDMX, and Comtrade by free key.
The recommended pairing is Comtrade or IMF for the machine feed and the ministry databank as the
citation readers recognise, with the site's "three-tier" habit applied to this feed as well.
Comtrade's visualisation exception is the cleanest licence for a public site; IMF's terms could not
be read and should be confirmed before it becomes the primary feed.
### 2.2 Agreements, treaties and lines of credit

| Source | Indicator | Granularity available | Frequency | Format / programmatic access | Licence | Verified |
|---|---|---|---|---|---|---|
| MEA Bilateral/Multilateral Documents, "List of Outcomes" entries (mea.gov.in/bilateral-documents.htm) | Documents the two governments published as the visit's outcomes: agreements, MoUs, inaugurations, exchanges, with signatories | Per bilateral visit. The page itself is script-rendered, but the backend it calls answers a plain GET without a key (`/FrontEnd/FetchPublicationListingData?publicationId=53&KeywordName=List%20of%20Outcomes&page=N`) and returns dated titles with detail links; the detail endpoint returns HTML tables of serial number, title and signatories. Confirmed on the Maldives state visit of 25–26 July 2025. Multilateral summit trips usually have no such list | Per visit; entries seen up to 3 September 2026 | HTML fragments by GET, paginated. No instrument-type code, no follow-up status | None stated (Government of India content) | Yes |
| MEA Indian Treaties Database (mea.gov.in/treatylist-generic.htm; the old treaties.htm is dead) | Treaty and MoU records with date of signature and date of entry into force | Per instrument, filterable by country (211 ISO-3 codes), type, subject, ministry, year of signature, year of ratification or accession, year of entry into force. Detail pages show type, signature date, entry-into-force date, country and PDF. No link to the visit at which it was signed; coverage of MoUs signed by line ministries and public enterprises is incomplete and lagged | Irregular; 2025 entries present | HTML fragments by GET (`/FrontEnd/FetchTreatyListGenericLatest`), no export | None stated | Yes |
| MEA Annual Reports (mea.gov.in/annualreports) | Narrative of visits and agreements per country chapter | Country × year, prose, not tables | Annual PDF (2024-25 published 26 June 2025) | PDF | None stated | Partial: PDF not opened |
| Press Information Bureau (pib.gov.in) | Mirrors of the "List of Outcomes" and other visit releases | Per release, with a posted timestamp; the all-releases filter is an ASP.NET postback and not URL-addressable | Daily; RSS feed works (`RssMain.aspx?ModId=6&Lang=1&Regid=3`) | RSS 2.0 and HTML, no JSON API | None stated | Yes |
| EXIM Bank of India, Government of India lines of credit (eximbankindia.in/lines-of-credit) | Signed LoCs (year approved, region, country, borrower, USD million, purpose, signing date); operative LoCs (amount, projects covered, project value, available-for-procurement flag and value); pipeline LoCs | Per LoC, per country. The three XLSX files are fetchable without login, but their filenames carry the refresh date (e.g. `GOILOC Statistics_31.07.2026.xlsx`) so the page must be scraped for the current link. No disbursement or utilisation column. A July 2025 rupee-denominated Maldives LoC did not appear, so recent or INR LoCs may be missing | Monthly | XLSX direct | None stated | Yes |
| MEA Development Partnership page | Aggregate LoC figures ("260+ LoCs, US$26 bn, 62 countries") | National narrative only | Ad hoc | HTML | None stated | Partial |
| Lok Sabha and Rajya Sabha answers on LoC utilisation (sansad.in, eparlib) | Country-wise LoC sanction and utilisation tables | Plausible per answer, but eparlib refused connections and the sansad.in question API was not found; MEA's own Q&A listing has six hits, newest March 2022 | Per session | Unreachable at check | None stated | No |
| UNCTAD International Investment Agreements Navigator | Bilateral investment treaties: signature, entry into force, termination | Per treaty | Rolling | Cloudflare 403 to fetchers | Unknown | No |
| Income Tax Department DTAA list | Double taxation agreements with dates | Per country | Rolling | Akamai access denied to fetchers | Unknown | No |
| EPFO social security agreements (epfo.gov.in/international-workers) | Partners with "agreement since YYYY" | 20 partners, year only, per-country PDFs in page attributes | Rare | HTML | None stated | Partial |

**What this means for "share of MoUs later ratified" (F2).** It cannot be computed directly.
Outcome lists carry titles and signatories only; the Treaties Database has entry-into-force dates
but no link to the visit, incomplete MoU coverage, and most MoUs enter force on signature (the
Cuba Ayurveda MoU of 18 December 2025 shows the same date for both), so "ratified" is meaningful
only for the treaty subset. A fuzzy join on country plus signature date within three days is
possible and lossy. The honest per-visit rendering is: number of documents listed, number of those
found in the Treaties Database, number with an entry-into-force date, and the number unmatched,
never a ratio framed as a success rate. LoCs are the strongest follow-through chain available
(announced in the outcome list, then appearing in EXIM's signed list, then in the operative list
with an available-for-procurement value), but they apply to roughly a third of trips and drawdown
itself is not published.
### 2.3 Defence and energy procurement

| Source | Indicator | Granularity available | Frequency | Format / programmatic access | Licence | Verified |
|---|---|---|---|---|---|---|
| SIPRI Arms Transfers Database (armstransfers.sipri.org) | Trend-indicator value (TIV) of arms deliveries to India by supplier, plus order year | Recipient × supplier × calendar year, 1950 to 2025; prior years revised each release | Annual, released in March for the previous year (10 March 2025, 9 March 2026) | CSV export from a JavaScript query UI; no API, no login. World Bank mirrors only India's total TIV, not by supplier | SIPRI copyright, not Creative Commons. Fair use is non-commercial excerpts under 10% of the dataset with the SIPRI attribution line; redistribution needs written permission | Yes |
| Ministry of Defence, PIB and Lok Sabha / Rajya Sabha answers | Value of defence imports by country | National annual totals only (e.g. PIB release 1884814, December 2022, tabulates 2017-18 to 2021-22 with no country split). The last country-wise value table found is a 2013 Lok Sabha reply covering 2010-11 to 2012-13; the standard line since is that country-wise details are withheld for strategic reasons | Ad hoc | HTML / PDF | Government of India | Yes, and the answer is negative: no country × year series exists for 2021 onward |
| Petroleum Planning and Analysis Cell (ppac.gov.in) | Crude and product import quantity and value; LNG imports | Monthly, fiscal-year layout, national totals only. The public XLSX files carry no source-country column. A country-wise table may sit behind the free-registration "history" area or inside the monthly snapshot PDFs; not verified | Monthly | XLSX direct download for totals | "Content owned by PPAC", no open licence | Partial |
| Ministry of Petroleum and Natural Gas, "Indian Petroleum and Natural Gas Statistics" | Annual petroleum statistics | Editions 1970-71 to 2024-25, PDF only (5 to 98 MB); the data.gov.in CSV mirror of the 2022-23 edition is sector-wise, not country-wise | Annual, about a year's lag | PDF | Not stated | Partial |
| Ministry of Commerce databank, commodity × country module (tradestat.commerce.gov.in/eidb) | Trade value by HS 2/4/6/8-digit code for one partner at a time | Country × fiscal year 2017-18 to 2025-26; monthly module 2018 to 2026 with Excel download | Monthly | Livewire form with CSRF token; a second checker's plain POSTs returned empty bodies, while the country-wise total module did answer a POST. Treat programmatic access as fragile | Disclaimer only | Partial |
| UN Comtrade, commodity level | Crude (HS 2709), LNG (HS 2711), arms (HS 93), aircraft (HS 88) by partner | India × partner × HS code × year or month; the keyless preview returned India's 2023 crude imports from Russia | Annual and monthly | Keyless preview, 500 rows per call, rate-limited (a 429 was observed); free key for more | UN Comtrade attribution, free-app exception | Yes |
| data.gov.in, "Country-wise details of import of coal" (from Rajya Sabha answers) | Coal imports by source country | Country × fiscal year 2019-20 to 2023-24 only; the Coal Controller dashboard shows a non-exportable top-10 | Irregular, and stale after 2023-24 | CSV | GODL-India | Yes, but stale |
| IEA and US EIA | Bilateral crude flows | IEA trade data is paid and OECD-focused; EIA is free and public domain but its bilateral origin data covers the United States only | n/a | n/a | n/a | Yes, negative |

**What this means.** Defence procurement value by country cannot be sourced from any Indian
official series, so D2 is dead and D1 (SIPRI TIV) is the only defence indicator, usable only as
context under its own copyright terms and with the "not money" warning. For energy, the customs
route (Comtrade HS 2709/2711 by partner) is the one that can be automated; PPAC gives no country
split in its public files. Coal by source is available only through 2023-24.
### 2.4 People: mobility, diaspora, education and science

| Source | Indicator | Granularity available | Frequency | Format / programmatic access | Licence | Verified |
|---|---|---|---|---|---|---|
| MEA labour mobility agreements page (mea.gov.in/labour-mobility-agreements.htm) | Labour and migration agreements by partner | 23 partners with instrument name and year, from Qatar 1985 to Finland and the EU in 2026; a one-off event table, not a series | Irregular ("as of May 2026", updated 22 July 2026 at check) | HTML table, scrapeable | None stated | Yes |
| eMigrate portal and MEA dashboard | Emigration clearances (ECR) by destination | Not available: both are JavaScript apps with no public statistics page. The only open series is a data.gov.in resource of national annual totals with no country field | Annual | data.gov.in JSON API with a free key, totals only | GODL-India | Yes, and negative for country-wise |
| MEA "Population of Overseas Indians" (HTML page and PDF) | NRI and PIO stock by country | 207 territories, single snapshot "as of January 2026"; no dated archive of earlier snapshots on the page | Roughly annual | HTML and PDF | None stated | Yes |
| World Bank / KNOMAD bilateral remittance matrix | Remittances by corridor | Last estimates are for 2021; the KNOMAD site now redirects to a note that the programme ran 2013 to 2024 | Dead | No download found | n/a | No |
| RBI survey on remittances (RBI Bulletin, 19 March 2025) | Source-country shares of inward remittances | About 33 countries, three rounds (2016-17, 2020-21, 2023-24); shares, not levels | Roughly every three years | HTML and PDF | RBI terms | Yes |
| Ministry of Tourism, data.tourism.gov.in and India Tourism Data Compendium | Foreign tourist arrivals by nationality | The portal describes nationality × month 2015 to 2026 as freely downloadable, but no CSV button or API was found ("beta"). The annual Compendium PDFs (2024, 2025) carry nationality × year. data.gov.in has a GODL "nationality-wise FTAs 2017–2021" set, stale | Monthly (portal), annual (PDF) | PDF parsing; dashboard only | GODL for the stale data.gov.in set; otherwise unstated | Partial |
| DGCA quarterly international traffic (Table 3 country-pair) | Passengers and freight by country pair | Country pair × quarter, 2015 to 2025 | Quarterly | The DGCA portal is JavaScript-rendered with no fetchable file links. A community mirror on GitHub (Vonter/india-aviation-traffic) republishes the tables as CSV under ODbL with DGCA attribution | ODbL via mirror; DGCA original unstated | Partial |
| Lok Sabha and Rajya Sabha answers on Indian students abroad | Students abroad, national and country-wise | National totals verified (1.33 million as of 1 January 2024 per LS Q4166; Bureau of Immigration study departures 2019 to 2023 per RS Q2583). The country-wise annexure for 1 January 2025 (RS Q557) returned 404 | Ad hoc | PDF | None stated | Partial: country table not reachable |
| UNESCO Institute for Statistics API, indicator 26533 (api.uis.unesco.org) | Indian students hosted, by host country | Host country × year, 1998 to 2025 with gaps (e.g. Germany 2023 = 42,937; Japan 2023 = 1,314); about a two-year lag | Annual | JSON, no key, 100k records per request | Generally CC BY 3.0 IGO, not visible on the API, unverified | Yes |
| OpenAlex API (api.openalex.org) | Works with at least one India-affiliated and one partner-affiliated author | Country pair × publication year, continuous; a live query for India × Japan 2023 returned 4,248 works | Continuous | JSON, keyless with a daily credit budget (10× with a free key), 100 requests per second cap | CC0 | Yes |
| UK Home Office immigration statistics data tables (Vis_D01/D02) | UK visas granted to Indian nationals by type | Nationality × visa type × quarter | Quarterly | XLSX / ODS | Open Government Licence v3 | Yes |
| European Commission Schengen visa statistics | Schengen visas issued at consulates in India | Consulate (country) × year, 2012 to 2024, 2025 listed | Annual | XLSX | Unstated | Yes |
| US State Department nonimmigrant visa issuances by nationality | US visas to Indian nationals | Monthly PDFs exist per search index | Monthly | Site returns 403 to fetchers | US Government | No |

**What this means.** P1 (students) survives through the UNESCO API, with the caveat that the
Indian parliamentary country table is not reliably reachable. P2 (tourists) survives only at
annual granularity via PDF parsing. P3 (emigration clearances by country) is dead as an automated
series. P4 (remittances) is dead as a bilateral series. P6 (visas) is populable for the UK and
Schengen partners only. P7 (air traffic) is populable only through a community mirror, so it is
deferred. S1 (co-authorship via OpenAlex) is the cleanest source in the whole memo: keyless,
CC0, country pair by year in one call.
### 2.5 Multilateral alignment, reciprocity and event data

| Source | Indicator | Granularity available | Frequency | Format / programmatic access | Licence | Verified |
|---|---|---|---|---|---|---|
| Voeten, Bailey and Strezhnev, "United Nations General Assembly Voting Data", Harvard Dataverse doi:10.7910/DVN/LEJUQZ | Dyadic agreement share and ideal-point distance | Country pair × session. Version 39 (30 July 2026): ideal points through session 80 (2025); the 145 MB dyadic agreement file runs to session 79 (2024). Uses Correlates of War codes (India = 750) | Roughly annual, July | CSV via the Dataverse API, anonymous, no terms click | CC0 1.0 | Yes |
| UN Digital Library, bulk General Assembly voting CSV (record 4060887) and per-record MARCXML export | Every member state's vote on every adopted recorded-vote resolution | State × resolution with date and session, 947,434 rows through A/RES/80/246; India has 5,694 rows to 18 December 2025. A checker computed India–Japan agreement on 80th-session recorded votes at 123 of 166 | Several times a year | CSV (364 MB) and MARCXML, no login. The search API is blocked for anonymous clients | "Copyright, United Nations; non-commercial use with attribution" | Yes |
| UN Digital Library, Security Council voting CSV (record 4055387) | UNSC votes | State × resolution, through resolution 2815 (January 2026); covers India's 2021–22 term | Several times a year | CSV, no login | Same UN terms | Yes, but only 15 members vote, so alignment exists only with partners also on the Council |
| MEA incoming and outgoing visits pages (mea.gov.in/incoming-visits, /outgoing-visits, /prime-minister-visits) | Head-of-state, head-of-government and ministerial visits with dates and country | The listing is injected by JavaScript into an empty container; the XHR endpoint was not found in the site's scripts. Field structure (title, country, dates) therefore unverified | Continuous | Needs a headless browser or a network trace to find the endpoint | None stated | Partial |
| GDELT 2.0 raw events and DOC API | Bilateral event counts, Goldstein scale, media tone | Raw: dyad × 15-minute file, aggregable to month; DOC API: tone by day, rate-limited to one request per 5 seconds (429s observed) and tone only. BigQuery route needs a Google account, untested | 15 minutes | Zipped TSV without key; DOC API JSON without key | Free for any use; redistribution requires citation and link | Yes |
| Lowy Institute Global Diplomacy Index | India's diplomatic posts by host country | Country × edition (2016, 2017, 2019, 2021, 2023); the 2019 sheet appears truncated | Biennial | XLSX (TLS chain error for some clients) | CC BY-ND 4.0 | Yes, but too coarse for per-visit use |
| Joint military exercises | Exercises per partner per year | No official machine-readable list; only MoD annual report PDFs and unofficial lists | n/a | No | n/a | No |

**What this means.** M1 (UNGA agreement) is fully populable from two independent sources, one
CC0, one non-commercial; the site is non-commercial and attributes sources, so either is usable.
F3 and F4 (return and follow-up visits) are populable in principle from MEA's visits listing, but
the listing is script-rendered and the feed endpoint was not located; this is the one shortlist
indicator with a scraping risk, and PIB releases are the fallback. M2 (event tone) is confirmed
as a rejection for display.
### 2.6 Surviving indicators and their populating source

| Indicator | Primary source | Fallback source | Granularity | Automation risk |
|---|---|---|---|---|
| F1 Documents listed for the visit | MEA "List of Outcomes" backend (GET) | PIB mirror via RSS | Per bilateral visit | Low: undocumented endpoint could change |
| F2 Documents traceable in the Treaties Database | MEA Treaties Database backend (GET) | none | Per instrument, country, signature date | Medium: fuzzy join by country and date |
| F3/F4 Return and ministerial visits | MEA incoming visits listing | PIB RSS | Per visit | High: feed endpoint not located |
| T1/T2 Merchandise trade | UN Comtrade (free key) or IMF IMTS (SDMX) | Ministry of Commerce databank (scrape) | Partner × month | Low |
| T3 FDI equity inflows | DPIIT Table 11 PDF | RBI Bulletin Table 34 | Partner × fiscal year, top partners only | Medium: PDF parsing, 403 to fetchers |
| D1 Arms deliveries | SIPRI CSV export | none | Supplier × calendar year | Medium: UI-driven export; non-commercial terms |
| E1 Crude and LNG imports by source | UN Comtrade HS 2709/2711 | Ministry of Commerce commodity module | Partner × month | Low |
| L1 Lines of credit | EXIM Bank XLSX (signed, operative, pipeline) | MEA outcome lists | Per LoC and country | Low: dated filename must be scraped |
| P1 Students hosted by partner | UNESCO UIS API indicator 26533 | Parliamentary answers (PDF) | Host country × year | Low; licence unverified |
| P2 Tourist arrivals from partner | Ministry of Tourism Compendium PDF | data.gov.in stale set | Nationality × year | Medium: PDF parsing |
| P6 Visas issued to Indians | UK Home Office tables; EC Schengen tables | none | Quarter (UK), year (Schengen) | Low, but only for those partners |
| S1 Co-authored research works | OpenAlex API | none | Country pair × year | Low |
| M1 UNGA voting agreement | Harvard Dataverse agreement file (CC0) | UN Digital Library bulk CSV | Dyad × session | Low; 145 MB and 364 MB files need a build step |
## 3. Methodology: attributing movement without overclaiming

### 3.1 What the data can and cannot say

Every indicator in this memo is observational. A Prime Minister's visit is not randomly assigned:
it goes to countries where a relationship is already warming, where a deal is already near
signature, or where a crisis needs managing. Any before/after comparison therefore mixes three
things the data cannot separate: (1) the visit's own effect, (2) the pre-existing trajectory that
caused the visit to be scheduled, and (3) everything else that happened in the window (commodity
prices, sanctions, elections in the partner country, a pandemic).

The site can honestly support these claims:

- "Indicator X for country Y was A in the 12 months before the visit and B in the 12 months after."
- "Relative to India's trade with all countries, trade with Y grew faster / slower / about the same
  after the visit."
- "N agreements were listed as signed during the visit; as of <date>, M of them have a recorded
  entry-into-force or operational milestone in <source>."
- "Across all K visits to countries in group G, the median post-visit change was Z; the
  interquartile range was [a, b]."

The site cannot support these and must never phrase a number as if it did:

- "The visit caused / produced / delivered X."
- "The visit was worth ₹X" or "the visit paid for itself" (there is no cost-benefit basis, and the
  registry carries no cost figures anyway).
- Any ranking of visits or Prime Ministers by "outcome score".
- Any statement about a single-visit country that generalises beyond that one dyad.

The framing rule, applied everywhere: **numbers describe what changed around a visit; they do not
say why.** The word "outcome" is used only in the MEA sense (the list of documents the two
governments jointly issued), never as a synonym for "result of the visit".

### 3.2 Comparison baseline

Use three baselines simultaneously and show all three, because each one fails in a different way
and readers with different priors will trust different ones.

1. **Own history (pre/post).** Compare the indicator in the 12 months (or 4 quarters, or the
   fiscal year) before the visit with the same length window after. Simple and legible, but it
   credits the visit with any secular trend.
2. **India-wide benchmark (difference from the aggregate).** Compute the same pre/post change for
   India's total (all partners) and report the *difference*. This strips out India-wide shocks
   (a rupee move, a global demand slump, the 2022 energy price shock) that would otherwise appear
   as a visit effect in every dyad.
3. **Partner-peer benchmark (synthetic comparison).** Compare the visited country's change against
   the median change among a small pre-registered set of "peer" partners that were *not* visited in
   the same window, matched on region and pre-visit trade size (e.g. for a Gulf visit, the other
   GCC states not visited that year). Report the peer set by name so a reader can dispute it.

Where the three baselines agree, say so. Where they disagree, show the disagreement rather than
picking the flattering one. The rendering rule is that no single number is ever shown alone;
the panel shows the dyad's own change alongside the India-wide change at minimum.

### 3.3 Lag windows

Indicators respond on very different clocks, so each indicator carries its own fixed lag
window, declared once in configuration and shown in the caveat text. Do not let the window be
tuned per visit; a per-visit window is how a result gets cherry-picked.

| Indicator family | Pre window | Post window | Why |
|---|---|---|---|
| Joint statements, agreements listed, incoming return visits | n/a | 0–12 months | These are near-immediate, and the count is a fact of the visit itself |
| Treaty entry into force, MoU operational milestones | n/a | 12–36 months, checked yearly | Ratification typically takes 1–3 years; report "not yet" rather than "no" inside the window |
| Merchandise trade (monthly) | 12 months | 12 and 24 months | Monthly data lets the window be exact; seasonality handled by comparing same months year-on-year |
| Energy imports by source (monthly) | 12 months | 12 months | Same as trade; dominated by price and contract timing |
| FDI equity inflows (quarterly, fiscal year) | 2 fiscal years | 2 and 3 fiscal years | Announcement-to-realisation gap is routinely 2+ years; a 1-year window would mostly measure noise |
| Arms transfers (annual TIV) | 3 years | 3 years | Deliveries follow contracts by 3–7 years; treat as context, not an outcome |
| Student, tourist and emigration flows (annual) | 2 years | 2 years | Visa regime changes take an academic or travel season to show |
| UNGA voting agreement (per session) | 3 sessions | 2 sessions | One session is too noisy; alignment is structurally sticky |
| Research co-authorship (annual) | 3 years | 3 years | Publication lag alone is 1–2 years |

A consequence the site must state up front: with the registry covering March 2021 onward, only
trips through roughly the end of 2023 (16 of the 44) have a full 24-month post window today, and
FDI's 3-fiscal-year window is only closed for the 2021 and early-2022 trips. Most trips will show
"window still open" for most indicators for years. That is the honest state of the evidence, and
the panel should display it as such rather than filling the space with a shorter, noisier window.

### 3.4 Countries visited more than once

Thirteen of the 54 countries were visited two or more times in the current registry (France and
Japan four times each; Indonesia, Italy and the United States three times). When post windows of
successive visits overlap, a naive per-visit pre/post double-counts the same movement for each
visit.

Recommended treatment:

- **Unit of analysis is the country-year (dyad), not the visit.** The per-trip panel shows the
  dyad's indicator series with *every* visit marked on the timeline, so the reader sees the second
  visit sitting inside the first visit's post window.
- **Windows are truncated at the next visit.** The post window of visit 1 ends at visit 2's date
  if that comes first. The panel labels this: "Post-visit window shortened to 9 months because of
  the following visit."
- **Cross-trip comparison uses the first visit in a cluster as the anchor** and treats visits
  within 12 months of each other as one "engagement cluster" for the aggregate statistics, so
  France's four visits do not count four times in a median.
- **Multi-country trips (23 of 44)** are split into one dyad row per country, with the trip's
  share of days in each country shown; the per-trip panel shows one sub-panel per country rather
  than pooling them.
- **Multilateral-summit visits** (G7, G20, BRICS, SCO, COP, Quad, UNGA) are flagged as such and
  excluded from the bilateral cross-trip aggregates by default, because the host country is
  incidental. They still get a per-trip panel, restricted to the "documents issued" and
  "return visit" indicators.

### 3.5 Showing null and negative results with equal prominence

This is the credibility hinge of the whole feature. Rules:

- **Same visual weight in all directions.** Up, down and flat use the same typographic size and
  the same neutral colour family; a diverging palette is used only on the cross-trip chart, and it
  is symmetric. No green-for-good or red-for-bad, because whether higher imports are "good" depends
  on the reader's politics.
- **Flat is a result, not an absence.** If the post-visit change is inside the peer interquartile
  range, the panel says "No detectable change relative to peers" in the same place and font a
  positive number would occupy. Never leave the cell blank.
- **Declines are reported with the same sentence template as increases.** "Exports to Y fell 8%
  in the 12 months after the visit, against a 3% rise India-wide."
- **The "window still open" state is distinct from "no change."** Three states are rendered
  explicitly: measured (with value), window open (with the date it closes), and not measurable
  (with the reason, e.g. "partner not separately reported in DPIIT country table").
- **Every cross-trip view defaults to all visits, sorted by date,** never by size of effect. Sorting
  by effect is available but resets on reload, and the page title does not change with the sort.
- **Publish the counts.** A small footer line on the cross-trip view: "Of N measurable visit-
  indicator pairs, a rose, b fell, c were flat, d windows still open." That single line is what
  keeps the feature from reading as either cost-shaming or boosterism.

### 3.6 Attribution disclosure

Each indicator has a fixed one-paragraph methods note (source, vintage, window, baseline, known
confounders) reachable from an "How this is measured" link next to every number, mirroring the
existing Methodology section pattern. The same notes are exported in the JSON alongside the
values so downstream users inherit the caveats.
## 4. Presentation

### 4.1 Where it lives

Two surfaces, both additive to the current page and both gated behind the same three-tier data
loading pattern the site already uses (a `data/outcomes.json` produced by a separate scheduled job,
with the page degrading gracefully to "outcome data unavailable" rather than to a broken panel):

1. **Per-trip outcome panel** inside the existing trip drawer, below "Reported cost" (the drawer
   already has a slot for `trip.cost`; outcomes sit under a sibling `drawer-sec` heading).
2. **Cross-trip comparison view** as a new analysis section between the existing charts and the
   registry table, with its own anchor so it can be linked directly.

### 4.2 Per-trip outcome panel

Purpose: answer "what is on the record around this visit" for one trip, one country at a time,
with the caveat inseparable from the number.

Layout in prose. The panel opens with a one-line status strip: how many indicators are measured,
how many windows are still open, and the vintage date of the outcomes file. Below it, one card per
visited country (multi-country trips get tabs). Each country card has three bands:

- **Band A, documents on the record (0–12 months).** Count of documents listed by MEA for the
  visit, with a link to the MEA listing; count of treaties from that visit with a recorded entry
  into force; whether a return visit by the partner's head of state or government occurred within
  12 months, with the date. These are facts, not estimates, and they are shown first because they
  are the least contestable.
- **Band B, flows around the visit.** For each flow indicator (trade, energy, FDI, students,
  tourists, co-authorship, voting agreement): a small sparkline of 3 years before to 3 years after
  the visit, with the visit marked as a vertical rule and any other visits to the same country
  marked as lighter rules. To its right, three numbers in a fixed order: the dyad's pre-to-post
  change, the India-wide change over the same window, and the peer-median change. Below them, the
  templated sentence from 3.5. If the window is still open, the sparkline stops at the last data
  point and the number cells show "Window closes <month year>".
- **Band C, how to read this.** A collapsed disclosure, open by default on first view per browser,
  holding the fixed caveat paragraph for the panel (below) plus per-indicator "How this is
  measured" links.

Rough wireframe (all values illustrative, not real data):

```
┌─ Outcomes on the record ─────────────────────────────────────────────┐
│ 4 measured · 3 windows still open · data vintage 2026-08-30           │
│ [ France ]  [ Italy ]                                                  │
│                                                                        │
│ Documents on the record (0–12 months)                                  │
│   Documents listed by MEA for this visit ............ 12  ↗ MEA list  │
│   Of which treaties now in force .................... 2 (as of 2026)  │
│   Return visit by head of state/govt within 12 mo ... Yes, 2024-01-25 │
│                                                                        │
│ Flows around the visit                                                 │
│   Merchandise trade   ▁▂▃▅│▆▅▆▇   dyad +6%  · India-wide +9% · peers +5% │
│                        "Total trade with France rose 6% in the 12      │
│                         months after the visit, against 9% India-wide."│
│   FDI equity inflows  ▂▂▃▃│▃      Window closes Mar 2027               │
│   Students in France  ▃▃▄▄│▅▅     dyad +11% · India-wide +14% · peers +8%│
│   UNGA agreement      ▅▅▅▅│▅▅     No detectable change                 │
│                                                                        │
│ ▸ How to read this panel                                               │
└────────────────────────────────────────────────────────────────────────┘
```

Fixed caveat paragraph (Band C), reproduced verbatim next to every panel:

> These figures describe what changed in public statistics around the time of this visit. They
> do not show that the visit caused any of it. Visits are scheduled when relationships are already
> moving, and the same window contains prices, sanctions, elections and pandemics. Each number is
> shown beside India's overall change and a peer-country change so you can judge whether anything
> here is specific to this country. Flat and negative results are shown exactly the same way as
> positive ones. Sources, windows and known problems for each line are under "How this is
> measured".

Per-number caveat label (one short line under each indicator, from a fixed list):

- Trade: "Monthly customs data; dominated by prices and a few commodities."
- FDI: "By immediate investing country; Mauritius, Singapore and the Netherlands route third-
  country money; announcements are not inflows; 2–3 year lag."
- Energy: "Contract timing and world prices move this far more than diplomacy."
- Arms transfers: "Deliveries follow contracts signed years earlier; SIPRI values are volume
  indices, not prices."
- Students / tourists / emigration: "One season's lag; partner visa policy is the main driver."
- UNGA agreement: "Voting positions are sticky; small changes are noise."
- Co-authorship: "Publication lag of 1–2 years; counts favour large research systems."

### 4.3 Cross-trip comparison view

Purpose: let a reader see the whole distribution, so no single trip's number is read in isolation.

Layout in prose. A control row picks one indicator at a time (default: documents on the record,
because it is the least contestable) and one baseline (default: India-wide difference). The main
chart is a dot plot: one row per visit in date order (the default sort is always date), the dot's
horizontal position is the dyad change minus the chosen baseline, and a vertical zero line runs
through the middle. Dots for windows still open are hollow and sit in a right-hand "window open"
column rather than at zero. Dots for multilateral-summit visits are omitted from the bilateral
view by default with a toggle to include them. Hovering or focusing a dot shows the same three
numbers and templated sentence as the per-trip panel. Below the chart, the footer count line from
3.5 ("Of N pairs, a rose, b fell, c flat, d open") and a link to download the underlying table as
CSV, matching the existing registry export.

A second, smaller chart under it is a summary strip: the median and interquartile range of the
chosen indicator across all measurable visits, next to the same statistics for the peer set, so a
reader can see whether visited countries as a group differ from non-visited peers. This is the
only place the site says anything aggregate, and it says it as a range, not a point.

Rough wireframe (all values illustrative, not real data):

```
┌─ Across visits ────────────────────────────────────────────────────────┐
│ Indicator [Merchandise trade ▾]   Baseline [India-wide ▾]   ☐ include   │
│                                                            summits      │
│                     −20%      −10%       0       +10%      +20%   open  │
│ 2021-03 Bangladesh   ·          ·      ──●─      ·          ·           │
│ 2021-09 USA          ·          ·   ●────        ·          ·           │
│ 2022-05 Germany      ·          ·      ──────●   ·          ·           │
│ …                                                                       │
│ 2025-06 Cyprus       ·          ·        ·       ·          ·      ○    │
│                                                                         │
│ Of 38 measurable visit-indicator pairs: 17 rose, 14 fell, 7 flat,       │
│ 6 windows still open.                              ⭳ CSV  ⓘ Method     │
│                                                                         │
│ Visited countries, median +2% (IQR −5% to +8%)                          │
│ Peer countries not visited, median +3% (IQR −4% to +7%)                 │
└─────────────────────────────────────────────────────────────────────────┘
```

Caveat line that sits directly under the chart title, always visible, not collapsible:

> Positions show change relative to the chosen baseline, not the effect of a visit. Half the dots
> will sit left of zero in a world where visits change nothing. Sort by size is available but the
> default is by date, on purpose.

### 4.4 Accessibility and mobile

Every sparkline and dot has a text equivalent (the templated sentence), the dot plot is also
rendered as a sortable table behind a toggle, and colour is never the only carrier of direction.
On narrow screens the per-trip bands stack and the three-number row becomes a three-line list;
the dot plot collapses to the table by default under 480px, reusing the registry's existing
table styles.
## 5. Shortlist for the first build

Ordered by build sequence. Each earned its slot on the same four tests as section 1: public,
partner-specific, closable window for a meaningful share of trips, and direction-neutral.

1. **F1, documents listed for the visit (MEA "List of Outcomes", PIB fallback).** The one
   indicator that is a fact of the visit rather than a movement around it, available for every
   bilateral trip since 2021 with a zero-month lag, and populable from a plain GET. It anchors the
   per-trip panel and costs nothing in caveats. Its only design risk is being read as a score,
   which the "count with titles, never a ranking" rule handles.
2. **T1/T2, merchandise trade with the partner, monthly, relative to India-wide (Comtrade or IMF,
   ministry databank as citation).** The best-instrumented flow, monthly, with three independent
   routes and one clearly usable licence. Monthly data lets the pre/post window be exact and
   seasonally matched, and the India-wide difference is the single most credible defence against
   the 2022 price shock reading as a diplomatic result.
3. **S1, co-authored research works (OpenAlex).** Keyless, CC0, country pair by year in one
   call, and a genuinely different dimension from money. Both a critic and a supporter accept
   paper counts as a neutral measurement; the caveat is lag, not politics.
4. **M1, UNGA voting agreement (Harvard Dataverse, UN Digital Library as fallback).** Included as
   labelled context, not as an outcome, because both a critic and a supporter object to it as an
   outcome for opposite reasons. It earns its slot because it is the only indicator in the set that
   can show "no change" credibly, which the feature needs as much as it needs movement.
5. **L1, lines of credit (EXIM Bank XLSX).** The strongest follow-through chain available
   (announced, signed, operative) for the roughly one-third of trips, mostly African, South Asian
   and island partners, where money-flow indicators are otherwise empty. Drawdown is not
   published, and the panel says so.

FDI (T3) is deliberately not in the first build. It survives verification, but its country
attribution is dominated by routing hubs (Singapore 37%, Mauritius 10%, Cayman Islands 4% of
fiscal 2025-26 equity inflows), it is fiscal-year and provisional, and its three-year window is
closed for almost no trips yet. It belongs in the second build once the panel's caveat pattern is
established, so that the first thing readers see is not the weakest number.

## 6. Considered and rejected

- **Investment or trade "commitments announced" during the visit.** Not a measured flow,
  routinely restated, and the archetype of the boosterism the feature exists to avoid. May be
  quoted from an outcome document with an "announced, not measured" label, never charted.
- **Share of MoUs ratified or operationalised.** No public source links a document to its visit or
  records operational status; most MoUs enter force on signature. Replaced by counts of documents
  traceable in the Treaties Database with unmatched counts shown.
- **Defence procurement value by country.** The Ministry of Defence publishes national totals only
  and states country-wise values are withheld; the last country table is from 2013. SIPRI's volume
  index remains as context.
- **Emigration clearances by destination.** The eMigrate portal exposes no statistics; the only
  open series is national totals.
- **Bilateral remittances.** The World Bank corridor matrix stopped at 2021 estimates and the
  programme has closed; the RBI survey gives shares every three years, usable as context only.
- **Services trade by partner.** The RBI publishes services exports by broad region only.
- **Coal imports by source.** Country-wise data exist only through fiscal 2023-24 in parliamentary
  answers.
- **Air traffic by country pair.** The DGCA data exist but only a community mirror is
  machine-readable; deferred rather than rejected.
- **Media event tone (GDELT).** Verifiable and free, but it is English-language media sentiment,
  spikes on the visit itself, and would be read as a verdict on the Prime Minister. Rejected for
  display; possibly an internal sanity check.
- **Diplomatic footprint (Lowy Global Diplomacy Index).** Biennial and CC BY-ND, too coarse for a
  per-visit signal.
- **Joint military exercises.** No structured official list exists.
- **Bilateral investment treaties, DTAAs, social security agreements as flows.** The UNCTAD and
  Income Tax sources are blocked to fetchers and the EPFO list carries only a year; where these
  instruments appear they are documents and belong in F1/F2.
- **Any composite "outcome score" or ranking of visits.** Rejected on the non-partisan guardrail
  regardless of feasibility.

## 7. Not verified in this session

Stated so the reader does not mistake them for confirmed:

- IMF terms of use (site blocked); the SDMX endpoint itself was verified.
- UNESCO UIS licence (not visible on the API); the data endpoint was verified.
- Whether a country-wise crude import table exists behind PPAC's free registration.
- The field structure of MEA's incoming visits listing (script-rendered, feed not found).
- Country-wise LoC utilisation tables in parliamentary answers (sansad.in and eparlib
  unreachable).
- MEA Annual Report contents (PDF not opened).
- US State Department visa issuance PDFs (403).
