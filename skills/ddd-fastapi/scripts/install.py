#!/usr/bin/env python3
"""Install one of the copyable assets into a FastAPI project.

    install.py project         a new project: pyproject.toml, main.py, Alembic, .env.example,
                               and the shared kernel
    install.py shared-kernel   only the shared kernel, into an existing project
    install.py iam-context     a complete IAM bounded context: sign-up, sign-in, JWT

Everything is written under --into (default: the current directory), which is
the project root -- the directory that holds main.py and one package per
bounded context. The project's name, used in pyproject.toml and as the API
title, defaults to that directory's name; pass --name to choose it.

Examples (run from the root of the project, SKILL being this skill's directory):
    python3 "$SKILL/scripts/install.py" project --name "QuickBite Platform"
    python3 "$SKILL/scripts/install.py" shared-kernel --dry-run
    python3 "$SKILL/scripts/install.py" iam-context

Everything it writes is ordinary code -- read it, then change it. Each asset ends
with the edits the script cannot make for you: dependencies, main.py, migrations.
"""
import argparse
import re
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = SKILL_DIR / "assets"
ASSETS = ("project", "shared-kernel", "iam-context")
KERNEL_MARKER = Path("shared/domain/entities.py")

NOTES = {
    "project": """
Next steps:

  1. Create the environment and install the dependencies (uv makes .venv/ itself):
         uv sync
     or, with pip:
         python3 -m venv .venv && source .venv/bin/activate && pip install . --group dev
     (pip 25.1 or later reads --group; with an older one, install ruff and mypy by hand)

  2. Copy .env.example to .env and point DATABASE_URL at a PostgreSQL database.

  3. Add the first bounded context:
         python3 "{skill}/scripts/new-context.py" --context ordering --entity Order

  4. Optionally, the identity context (sign-up, sign-in, JWT):
         python3 "{skill}/scripts/install.py" iam-context
""",
    "shared-kernel": """
Three things the installer cannot do for you:

  1. Add the dependencies the kernel needs (uv add, or pyproject.toml):
         fastapi[standard]>=0.122  sqlalchemy[asyncio]>=2.0  asyncpg>=0.30
         alembic>=1.16  pydantic-settings>=2.6

  2. Wire it in main.py:
         from shared.interfaces.exception_handlers import register_exception_handlers
         register_exception_handlers(app)
     and point alembic/env.py at shared.infrastructure.models.Base.metadata.

  3. Set DATABASE_URL (postgresql+asyncpg://...) in the environment or in .env.

Nothing here holds business rules. If a module in shared/ starts to know what
an Order is, it belongs in a bounded context.
""",
    "iam-context": """
Five things the installer cannot do for you:

  1. Add the dependencies:
         uv add pyjwt "pwdlib[argon2]"

  2. Set the token secret, at least 32 characters, in .env (and from the
     environment in production):
         JWT_SECRET=<a long random string>
         JWT_EXPIRATION_DAYS=7

  3. Wire it in main.py: the handlers, the public router, and a bearer token on
     every other router:
         from fastapi import Depends
         from iam.interfaces.dependencies import get_current_user
         from iam.interfaces.exception_handlers import register_iam_exception_handlers
         from iam.interfaces.routes import authentication_router, roles_router, users_router
         from shared.interfaces.schemas import error_responses

         register_iam_exception_handlers(app)

         authenticated = [Depends(get_current_user)]
         unauthenticated = error_responses(401)

         app.include_router(authentication_router)
         app.include_router(users_router, dependencies=authenticated, responses=unauthenticated)
         app.include_router(roles_router, dependencies=authenticated, responses=unauthenticated)
     and add `dependencies=authenticated, responses=unauthenticated` to every
     other context's include_router.

  4. Import its models in alembic/env.py, then migrate:
         import iam.infrastructure.models  # noqa: F401
         alembic revision --autogenerate -m "create iam tables"
         alembic upgrade head

  5. Review the roles in iam/domain/value_objects.py: USER and ADMIN are
     placeholders. Name them in the ubiquitous language of the platform.
""",
}


def title_from(name):
    """Turn a directory or package name into words for a title."""
    words = re.sub(r"[_\-\s]+", " ", name).strip().split()
    return " ".join(w if w.isupper() else w.capitalize() for w in words) or "Platform"


def replacements(title):
    words = [w.lower() for w in re.findall(r"[A-Za-z0-9]+", title)] or ["platform"]
    return {
        "__project_title__": title,
        "__project_name__": "-".join(words),
        "__project_db__": "_".join(words),
    }


def planned_files(asset):
    """Return (source, path relative to the project root) for every file of an asset."""
    if asset == "project":
        sources = [(ASSETS_DIR / "project", p) for p in (ASSETS_DIR / "project").rglob("*")]
        sources += [(ASSETS_DIR / "shared-kernel", p) for p in (ASSETS_DIR / "shared-kernel").rglob("*")]
    else:
        sources = [(ASSETS_DIR / asset, p) for p in (ASSETS_DIR / asset).rglob("*")]
    return sorted(
        ((source, source.relative_to(base)) for base, source in sources
         if source.is_file() and "__pycache__" not in source.parts),
        key=lambda pair: str(pair[1]),
    )


def main():
    parser = argparse.ArgumentParser(
        description="Install a copyable asset of the ddd-fastapi skill.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("Examples", 1)[1].rstrip() if "Examples" in __doc__ else None,
    )
    parser.add_argument("asset", choices=ASSETS, help="which asset to install")
    parser.add_argument("--into", default=".", help="project root (default: the current directory)")
    parser.add_argument("--name", default=None,
                        help="project name, e.g. 'QuickBite Platform' (default: from the directory name)")
    parser.add_argument("--dry-run", action="store_true", help="list what would be written and stop")
    parser.add_argument("--force", action="store_true", help="overwrite files that already exist")
    args = parser.parse_args()

    root = Path(args.into)

    # Run this from the project, not from the skill. --into is resolved against
    # the current directory, so running it from the skill folder would quietly
    # install the asset inside the skill instead of inside the project.
    resolved = root.resolve()
    if resolved == SKILL_DIR or SKILL_DIR in resolved.parents:
        print(
            f"--into resolves to {resolved}, which is inside the skill itself.\n"
            f"Run this from the root of your FastAPI project, for example:\n"
            f'  cd path/to/project && python3 "{Path(__file__).resolve()}" {args.asset}',
            file=sys.stderr,
        )
        return 1

    if args.asset == "iam-context" and not (root / KERNEL_MARKER).exists():
        print(
            f"The shared kernel is not under {root / 'shared'}, and the IAM context builds on it.\n"
            f"Install it first:\n"
            f'  python3 "{Path(__file__).resolve()}" shared-kernel --into {args.into}',
            file=sys.stderr,
        )
        return 1

    mapping = replacements(args.name or title_from(resolved.name))
    planned = [(source, root / relative) for source, relative in planned_files(args.asset)]

    clashes = [target for _, target in planned if target.exists()]
    if clashes and not args.force:
        print("Refusing to overwrite existing files (pass --force to replace them):", file=sys.stderr)
        for target in clashes:
            print(f"  {target}", file=sys.stderr)
        return 1

    for source, target in planned:
        if args.dry_run:
            print(f"would write {target}")
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        text = source.read_text(encoding="utf-8")
        for token, value in mapping.items():
            text = text.replace(token, value)
        target.write_text(text, encoding="utf-8")
        print(f"wrote {target}")

    if args.dry_run:
        return 0

    print(NOTES[args.asset].format(skill=SKILL_DIR).rstrip())
    return 0


if __name__ == "__main__":
    sys.exit(main())
