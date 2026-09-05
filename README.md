# India PM Foreign Visits Dashboard

A dashboard for tracking and visualizing the foreign visits made by the Prime Minister of India.

## Features

The dashboard provides an overview of foreign visits by country, date, and purpose. It includes interactive charts and filters for exploring visit history, along with summary statistics on travel frequency and destinations.

## Getting Started

Clone this repository and follow the setup instructions to run the dashboard locally.

## Data

- `data/visits.json` — every foreign visit parsed from the official PM India registry. Refreshed daily by `.github/workflows/refresh-data.yml` (`scripts/refresh.py`).
- `data/news.json` — third-party coverage of the current trip, produced by the same refresh.
- `data/outcomes.json` — public statistics around each visited country (MEA outcome lists, UN Comtrade trade, OpenAlex co-authorship, UN General Assembly voting agreement, EXIM Bank lines of credit). Refreshed daily by `.github/workflows/refresh-outcomes.yml` (`scripts/refresh_outcomes.py`). Descriptive only, never causal; see `docs/outcome-indicators.md`.

## License

This project is open source and available under the MIT License.
