# AGENTS.md

Rules for anyone (human or AI agent) contributing to this repo. Read before writing code.

## Read first

- [`README.md`](README.md): stack and folder structure.
- [`docs/API-CONTRACT.md`](docs/API-CONTRACT.md): endpoints and payloads. Source of truth for frontend and backend.
- [`docs/FLUJO-APP.md`](docs/FLUJO-APP.md): app screens and flows.
- [`data/crops/README.md`](data/crops/README.md): crop catalog and scoring rules.
- The GitHub issue you are working on, including its acceptance criteria and "Blocked by".

## Branches

- Every change starts from an issue. One issue, one branch, one PR.
- Base branch is `develop`. Never commit directly to `main` or `develop`. Never force-push them.
- Name: `<type>-<scope>-<issue>-<short-slug>`, in English, lowercase, only hyphens (no `/`, no `:`; git does not allow `:` in branch names).
  - Example: `feat-backend-13-db-schema`, `fix-frontend-21-hoy-offline-date`.
- Create it linked to the issue:
  `gh issue develop <issue> --base develop --name <branch> --checkout`

## Commits and pull requests

- Format, in English: `<type>:<scope>-<short-summary>`. No `/`, no parentheses.
  - Types: `feat`, `fix`, `chore`, `docs`, `refactor`, `test`, `perf`.
  - Scopes: `backend`, `data`, `frontend`.
  - Summary: lowercase words joined with hyphens, imperative, ≤ 72 characters in total.
  - Examples: `feat:backend-add-get-zones-endpoint`, `fix:frontend-hoy-offline-date`.
  - Optional body after a blank line, in English, to explain why.
- PRs target `develop`. Title follows the same format.
- PR body in English with these sections: **Summary**, **Changes**, **How to test**, **Screenshots** (frontend only), and `Closes #<issue>`.
- Open as draft until tests and linters pass. Request review from the reviewer (Gaambaa).
- Never merge automatically. A human merges after approval.
- No `Co-Authored-By` trailers, "Generated with" lines or any other credit to Claude or other AI tools in commits, PRs or code.
- Keep PRs small and focused (aim for < 400 changed lines, excluding data files).

## Code

- No emojis in code, comments, logs, commit messages or PRs.
- Comments explain *why*, never *what*. Do not write comments like "this is a get function".
- Follow the existing style. Run before pushing:
  - Python: `ruff check` and `ruff format`, `pytest`.
  - TypeScript: `eslint`, `prettier --check`, `jest`.
- New logic needs tests. Do not delete or skip failing tests to make CI pass.
- Ask before adding a new dependency. Prefer what the stack already has.
- Do not leave dead code, debug prints or commented-out blocks.

### Frontend (`app/`)

- Mobile-first: text ≥ 17 px, touch targets ≥ 56 px, one main action per screen.
- Offline-first: screens read from local SQLite, never block on the network. Show "actualizado + date", never "sin señal".
- User-facing text goes through i18n keys (Spanish and Quechua). No hardcoded strings.
- Short, plain language for farmers. No technical terms in the UI.
- Match the approved mockups. Attach screenshots to the PR.

### Backend (`api/`)

- Modular monolith (see README "Architecture"): `router → service → repository`, one module per domain.
- Routers hold no logic; repositories are private to their module; cross-module calls go through services.
- Follow `docs/API-CONTRACT.md` exactly: field names, units, dates in America/La_Paz.
- If a change needs a contract change, update `docs/API-CONTRACT.md` and `api/openapi.yaml` in the same PR and say so in the PR body.
- The API returns codes, not sentences; the app translates.

### Data (`src/`, `imerg/`, `data/`)

- Never invent data. Every value has a source (`fuente`) and units.
- Do not commit large raw files (NetCDF, HDF5, GeoTIFF). Commit scripts and small processed outputs.
- Scripts must be re-runnable without duplicating rows.
- Keep IMERG days in UTC and say so; do not mix Final and Late silently.

## Ask before doing

Stop and ask a human before you:

- Delete or rewrite sensitive code (auth, keys, tokens), database files, schemas or SQLModel models.
- Change environment or config files (`.env*`, CI, deployment, `.gitignore`).
- Delete or overwrite files in `data/`, or change crop ids in `data/crops/crops.json`.
- Run destructive commands: `rm -rf`, `git reset --hard`, `git push --force`, dropping tables.
- Close, reassign or edit issues that are not yours.

## Secrets

- Never commit secrets: `.env`, Earthdata credentials, API keys (including the GAMC key), tokens.
- Read secrets from environment variables. Keep `.env.example` with names only.
- If you find a secret in the repo, report it; do not copy it elsewhere.

## Definition of done

- All acceptance criteria in the issue are checked.
- Tests and linters pass.
- PR approved by a human and merged into `develop`.
