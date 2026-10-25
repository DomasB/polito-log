# Database Migrations

The schema is managed by Alembic. The app never creates tables itself: every
schema change is a migration in `alembic/versions/`.

Run migrations with:

```bash
python -m app.cli migrate
```

It runs `alembic upgrade head`. On a database that the old
`Base.metadata.create_all` built (tables exist, no `alembic_version` table) it
first stamps the baseline revision `0001_baseline`, so only the migrations after
the baseline run. That is how existing databases, production included, are
adopted. Running it again is a no-op.

## Where migrations run

- **Production (Railway):** the backend's pre-deploy command,
  `python -m app.cli migrate` (`backend/railway.json`, `deploy.preDeployCommand`).
  It runs once per deploy in a separate container, before the new version takes
  traffic. A failed migration stops the deploy and the old version keeps
  serving. Output is in the deployment's logs. Migrations do not run at
  container start.
- **Development (Docker):** `./dev.sh` starts the backend with
  `python -m app.cli migrate && uvicorn ...`, so the dev database is migrated on
  every start.
- **CI:** the backend workflow migrates a fresh database before `pytest`, and
  `tests/test_migrations.py` fails if the models and the migrations disagree.

## Creating a migration

After changing a model in `app/models/`:

```bash
./dev.sh shell
alembic revision --autogenerate -m "describe the change" --rev-id 0003_short_name
```

Then review the generated file. Autogenerate misses things such as CHECK
constraints, data migrations and enum changes, and it can turn a rename into a
drop plus an add. Number revision IDs sequentially (`0003_...`, `0004_...`).

Apply it with `python -m app.cli migrate` (or restart `./dev.sh`) and run the
tests. Commit the migration with the model change.

### Guidelines

1. One logical change per migration.
2. Write `downgrade()` too, and try it: `alembic downgrade -1`, then upgrade again.
3. When adding a NOT NULL column to a table with rows, give it a
   `server_default`, or add it nullable, backfill, then set NOT NULL.
4. Keep migrations compatible with the running version where possible: the new
   schema is live briefly before the new code is.

## Useful commands

```bash
alembic current            # revision the database is at
alembic history            # all revisions
alembic downgrade -1       # roll back one revision
alembic upgrade head       # upgrade without the baseline stamping step
```

## Files

- `alembic/versions/`: migrations. `0001_baseline` is the schema that
  `create_all` produced before Alembic was introduced.
- `alembic/env.py`: takes the database URL from `app.config.settings`.
- `alembic.ini`: Alembic configuration.
- `app/cli.py`: the `migrate` command.
