# Database Migrations Guide

This project uses Alembic for database migrations.

## Production (Railway)

Migrations run **automatically** on container startup:
- The `start.sh` script runs `alembic upgrade head` before starting the server
- If migrations fail, the container will not start
- Check Railway logs to see migration output

## Development

### Running Migrations

#### With Docker (Recommended)

```bash
# Option 1: Run migration in the backend container
./dev.sh shell
alembic upgrade head

# Option 2: Execute directly
docker exec -it polito-log-backend alembic upgrade head
```

#### Without Docker (Local Python)

```bash
cd backend

# Make sure you have a .env file with DATABASE_URL
# Example: DATABASE_URL=postgresql://user:pass@localhost:5432/dbname

# Run migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# See migration history
alembic history

# See current version
alembic current
```

### Creating New Migrations

When you modify models in `app/models/`, create a migration:

```bash
# With Docker
./dev.sh shell
alembic revision -m "description of changes"

# Without Docker
cd backend
alembic revision -m "description of changes"
```

For auto-generating migrations based on model changes:

```bash
alembic revision --autogenerate -m "description of changes"
```

**Note:** Always review auto-generated migrations before committing!

### Migration Best Practices

1. **One logical change per migration** - Don't mix multiple unrelated schema changes
2. **Always review auto-generated migrations** - They may not catch all edge cases
3. **Test migrations both ways** - Test both upgrade and downgrade
4. **Handle existing data** - When adding non-nullable columns to tables with data:
   ```python
   # Add column as nullable first
   op.add_column('table', sa.Column('new_col', sa.String(), nullable=True))

   # Set default values for existing rows
   op.execute("UPDATE table SET new_col = 'default' WHERE new_col IS NULL")

   # Make column non-nullable
   op.alter_column('table', 'new_col', nullable=False)
   ```

5. **Commit migrations with code changes** - Always commit the migration file along with the model changes

## Migration Files

- `alembic/versions/` - Contains all migration files
- `alembic.ini` - Alembic configuration (database URL is overridden in env.py)
- `alembic/env.py` - Migration environment setup
- `start.sh` - Production startup script that runs migrations

## Troubleshooting

### Migration fails with "Target database is not up to date"

```bash
# Check current version
alembic current

# See history
alembic history

# Upgrade to latest
alembic upgrade head
```

### Need to rollback a migration

```bash
# Rollback one migration
alembic downgrade -1

# Rollback to specific version
alembic downgrade <revision_id>

# Rollback all migrations
alembic downgrade base
```

### Reset database completely (DANGEROUS)

```bash
# Drop all tables and rerun migrations
./dev.sh down -v  # Removes volumes
./dev.sh up
./dev.sh shell
alembic upgrade head
```
