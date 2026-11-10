# AGENTS.md

Guidance for coding agents working in this repository.

## Project Overview

- Stack: Django (Python 3.14), Jinja templates, SCSS, vanilla JS, webpack.
- App purpose: hospital records search and detail pages.
- Main Django app: `app/hospitaldetails`.

## Repository Map

- `app/hospitaldetails/`: search/detail views, models, URLs, templates integration.
- `app/main/`: site-wide pages and routes.
- `config/settings/`: per-environment Django settings (`develop`, `test`, `production`, `staging`).
- `templates/`: Jinja/Django templates.
- `src/styles/` and `src/scripts/`: SCSS/JS sources compiled into `app/static/`.
- `test/`: pytest test suite.
- `docs/`: project docs (including data migration guidance).

## Local Development

Preferred path is Docker-based development.

- Start services:
  - `docker compose up -d`
- If static assets are missing on first run, copy frontend assets:
  - `docker compose exec app cp -r /app/node_modules/@nationalarchives/frontend/nationalarchives/assets /app/app/static`
- Run all Django commands through `docker compose exec app poetry run <command>`

## Test and Quality Commands

Python tests:

- Full test suite:
  - `docker compose exec app poetry run pytest --ds=config.settings.test`

Python formatting/linting:

- Project formatter/lint wrapper:
  - `docker compose exec app format`

Frontend build/lint:

- Build assets:
  - `npm run compile`
- Watch mode:
  - `npm run dev`
- Frontend lint:
  - `npm run test:lint`
- Auto-fix frontend formatting/lint issues:
  - `npm run lint:fix`

## Coding Conventions

- Keep changes minimal and scoped to the request.
- Preserve existing naming and structure in Django views/models/templates.
- Prefer small helper functions for search/filter logic.
- Avoid unrelated refactors in functional changes.
- Update tests when behavior changes.

## Search and Pagination Behavior

- Hospital search lives in `app/hospitaldetails/views.py` (`search` view).
- Invalid or out-of-range pagination pages should return HTTP 404.
- Keep query parameter behavior stable across pagination and back-links.

## Data and Migration Notes

- There is a custom management command for MSSQL to PostgreSQL migration:
  - `docker compose exec app poetry run python manage.py migrate_data`
- Review `docs/data-migration.md` before changing migration logic.

## Safety Rules for Agents

- Do not remove or alter unrelated user changes.
- Do not run destructive git commands.
- Prefer targeted edits and run relevant tests after changes.
- If requirements are ambiguous, ask for clarification before broad changes.
