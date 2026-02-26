# Search functionality

## Overview

The search page lets users find hospitals by name or town. It uses a simple query string parameter and renders results in a paginated list.

- Route: `/hospital-records/hospitals`
- Method: `GET`
- Query parameter: `q` (string)
- Optional parameter: `page` (integer)

## Backend behavior

Search is implemented in the `search` view.

- `q` is trimmed before use.
- Results are filtered with case-insensitive partial matching on:
  - `Hospital.name`
  - `Hospital.previous_names`
  - `Hospital.town`
- Results are ordered by `Hospital.name`.
- When `q` is empty, the page renders with no results.
- When `q` is provided, results are paginated with 10 items per page.

Example request:

```
/hospital-records/hospitals?q=leeds
```

## Pagination behavior

Pagination uses Django's `Paginator` and a windowed page list.

- Page numbers include the first/last pages plus a small window around the current page.
- Missing ranges are represented as ellipses in the UI.
- The page selector uses `page` and preserves the original `q` value.

## Frontend rendering

The template renders:

- A search field pre-filled with the current `q` value.
- A results summary and count when matches are found.
- A list of result cards linking to the hospital detail page.
- An empty-state message when no matches are found.

Template: `app/templates/hospitaldetails/search.html`

## Tests

Search behavior is covered by Django tests in:

- `test/hospitaldetails/test_search.py`

These tests cover:

- Empty query behavior
- Matching by name, previous names, and town
- Ordering by name
- Form value persistence and links
- No-results messaging
