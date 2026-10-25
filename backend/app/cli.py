"""
Operational commands, run as `python -m app.cli <command>`.

In production run them through Railway, e.g. `railway run python -m app.cli migrate`.
"""
import argparse
import sys
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

from app.database import SessionLocal, engine
from app.models.enums import UserRole
from app.services.user import UserNotFoundError, UserService

BACKEND_DIR = Path(__file__).resolve().parents[1]
BASELINE_REVISION = "0001_baseline"


def _alembic_config() -> Config:
    return Config(str(BACKEND_DIR / "alembic.ini"))


def migrate(args: argparse.Namespace) -> int:
    """
    Bring the database schema to the latest migration.

    Databases created by the old Base.metadata.create_all have the baseline
    tables but no alembic_version table; they are stamped at the baseline
    first so that only later migrations run against them.
    """
    config = _alembic_config()
    tables = set(inspect(engine).get_table_names())
    if "alembic_version" not in tables and "users" in tables:
        print(f"Existing schema without alembic_version: stamping {BASELINE_REVISION}")
        command.stamp(config, BASELINE_REVISION)
    command.upgrade(config, "head")
    return 0


def grant_role(args: argparse.Namespace) -> int:
    """Set the role of an existing user (they must have logged in once)."""
    role = UserRole(args.role)
    with SessionLocal() as db:
        try:
            user = UserService(db).grant_role(args.email, role)
        except UserNotFoundError:
            print(f"No user with email {args.email}; they must log in once first", file=sys.stderr)
            return 1
        print(f"{user.email} now has role {user.role.value}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    commands = parser.add_subparsers(dest="command", required=True)

    migrate_parser = commands.add_parser("migrate", help="Run database migrations")
    migrate_parser.set_defaults(func=migrate)

    grant_parser = commands.add_parser("grant-role", help="Set a user's role")
    grant_parser.add_argument("email")
    grant_parser.add_argument("role", choices=[role.value for role in UserRole])
    grant_parser.set_defaults(func=grant_role)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
