# polito-log

Open-source tracker of political accountability: politicians' statements, a query engine over them, and an open data API. Principles: open data, verifiability (every statement traceable to its source), minimal UI.

## Layout
- `backend/`: FastAPI + SQLAlchemy + PostgreSQL, Python 3.13+. Magic-link passwordless auth.
- `frontend/`: Vue 3 + Pinia + Naive UI + TypeScript (Vite).
- Deploy: Railway deploys from GitHub after GitHub Actions CI (tests only) passes. See `DEPLOYMENT.md`.

## Running
- Backend: `cd backend && ./dev.sh` (Docker; `./dev.sh help` lists subcommands). `dev.sh` starts the Docker daemon before any subcommand, including `help`, and can fall back to sudo. Swagger: `localhost:8000/api/v1/docs`.
- Frontend: `cd frontend && npm run dev` (:5173). Scripts are in `package.json`.

## Backend layering
A request flows router → service → repository → model:
- `routers/` handle HTTP only.
- `services/` hold business logic.
- `repositories/` are the only layer that touches the SQLAlchemy session.
- `schemas/` (Pydantic) define every request/response shape.
- Sessions and services come in through FastAPI dependency injection.

New endpoints follow this chain.

## API contract
The frontend client in `frontend/src/api` is generated from the backend's OpenAPI spec. After changing a schema or route, run the backend, then `npm run generate-api`, and commit the regenerated client with the backend change. Usage: `frontend/API_CLIENT.md`.

## Verifying changes
- Frontend: `npm run type-check`, `npm run test:unit`. `npm run lint` (oxlint) rewrites files (`--fix`); `npm run format` runs oxfmt.
- Backend: `cd backend && DATABASE_URL=postgresql://polito_user:polito_password@localhost:5432/polito_log pytest` (needs the `./dev.sh` stack's Postgres). For endpoint behavior not covered by tests, use Swagger or `curl` against the running stack.

## Issue tracking
Work is tracked in beads (`bd`); run `bd prime` for the workflow. `bd ready` finds work, `bd update <id> --claim` claims it, `bd close <id>` finishes it. File follow-up work as beads issues.

## Finishing a session
Close or update the beads issues you touched, run the checks above, then commit and push. Work on a feature branch (`git switch -c <topic>` if on `main`), push it with `git push -u origin HEAD`, and merge to `main` through a PR.
