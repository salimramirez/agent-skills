#!/usr/bin/env python3
"""Scaffold a bounded context from assets/context-template/.

Writes the four layers of one context, wired for a single CRUD aggregate:

    <into>/<context>/
      domain/entities.py, exceptions.py, repositories.py
      application/services.py
      infrastructure/models.py, repositories.py
      interfaces/schemas.py, dependencies.py, routes.py

The template is the single source of truth: this script only substitutes the
naming placeholders, which is the part that is easy to get wrong by hand -- the
same concept appears as PascalCase and snake_case, singular and plural, in
class names, module paths, function names, table names and REST paths.

The context is written next to main.py, in the project root given by --into
(default: the current directory). The generated code builds on the shared
kernel, so install that first:
    python3 "$SKILL/scripts/install.py" shared-kernel

Examples (run from the root of the project, SKILL being this skill's directory):
    python3 "$SKILL/scripts/new-context.py" --context ordering --entity Order
    python3 "$SKILL/scripts/new-context.py" --context catalog --entity MenuItem --dry-run
    python3 "$SKILL/scripts/new-context.py" --context staffing --entity Person --plural People

Everything it writes is ordinary code -- read it, then change it. The generated
aggregate carries a single `name` field on purpose; model the real thing next.
"""
import argparse
import keyword
import re
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = SKILL_DIR / "assets" / "context-template"
KERNEL_MARKER = Path("shared/domain/entities.py")


def split_words(name):
    """Split an identifier written in any common case into lowercase words."""
    spaced = re.sub(r"[_\-\s]+", " ", name.strip())
    spaced = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", spaced)
    spaced = re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])", " ", spaced)
    words = [w for w in spaced.split(" ") if w]
    if not words:
        raise ValueError(f"{name!r} has no letters to work with")
    return [w.lower() for w in words]


def pascal(words):
    return "".join(w.capitalize() for w in words)


def snake(words):
    return "_".join(words)


def title(words):
    return " ".join(w.capitalize() for w in words)


def pluralize(words):
    """Naive English plural of the last word. Use --plural for anything else."""
    last = words[-1]
    if re.search(r"(s|x|z|ch|sh)$", last):
        plural = last + "es"
    elif re.search(r"[^aeiou]y$", last):
        plural = last[:-1] + "ies"
    else:
        plural = last + "s"
    return words[:-1] + [plural]


def replacements(context, entity, plural):
    context_words = split_words(context)
    entity_words = split_words(entity)
    plural_words = split_words(plural) if plural else pluralize(entity_words)
    return {
        "__context__": snake(context_words),
        "__Context_title__": title(context_words),
        "__Entity__": pascal(entity_words),
        "__entity__": snake(entity_words),
        "__entities__": snake(plural_words),
        "__entities-kebab__": "-".join(plural_words),
        "__entity_words__": " ".join(entity_words),
        "__Entity_sentence__": " ".join(entity_words).capitalize(),
        "__entities_words__": " ".join(plural_words),
        "__Entities_title__": title(plural_words),
    }


def substitute(text, mapping):
    for token, value in sorted(mapping.items(), key=lambda kv: -len(kv[0])):
        text = text.replace(token, value)
    return text


def sort_imports(text):
    """Sort one-line ``from x import a, b`` statements the way ruff's isort does.

    Where a generated module or class name lands among the others depends on
    the context's and the entity's names, so the template cannot fix the order
    in advance. Each run of consecutive ``from`` lines is one import section:
    the lines are sorted by module, and the names inside each line.
    """
    def sort_names(line):
        match = re.fullmatch(r"(from [\w.]+ import )([\w, ]+)", line)
        if not match:
            return line
        names = sorted(name.strip() for name in match.group(2).split(","))
        return f"{match.group(1)}{', '.join(names)}"

    lines, block, result = text.split("\n"), [], []
    for line in lines + [""]:
        if re.fullmatch(r"from [\w.]+ import [\w, ]+", line):
            block.append(sort_names(line))
            continue
        result.extend(sorted(block, key=lambda imported: imported.split()[1]))
        block = []
        result.append(line)
    return "\n".join(result[:-1])


def main():
    parser = argparse.ArgumentParser(
        description="Scaffold a DDD bounded context for a FastAPI project.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("Examples", 1)[1].rstrip() if "Examples" in __doc__ else None,
    )
    parser.add_argument("--context", required=True,
                        help="bounded context, in the ubiquitous language (e.g. ordering)")
    parser.add_argument("--entity", required=True,
                        help="aggregate this context starts with (e.g. Order, MenuItem)")
    parser.add_argument("--plural", default=None,
                        help="plural of the entity, when the naive one is wrong (e.g. People)")
    parser.add_argument("--into", default=".", help="project root (default: the current directory)")
    parser.add_argument("--dry-run", action="store_true", help="list what would be written and stop")
    parser.add_argument("--force", action="store_true", help="overwrite files that already exist")
    args = parser.parse_args()

    if not TEMPLATE_DIR.is_dir():
        print(f"Template directory not found: {TEMPLATE_DIR}", file=sys.stderr)
        return 1

    root = Path(args.into)

    # Run this from the project, not from the skill. --into is resolved against
    # the current directory, so running it from the skill folder would quietly
    # scaffold the context inside the skill instead of inside the project.
    resolved = root.resolve()
    if resolved == SKILL_DIR or SKILL_DIR in resolved.parents:
        print(
            f"--into resolves to {resolved}, which is inside the skill itself.\n"
            f"Run this from the root of your FastAPI project, for example:\n"
            f'  cd path/to/project && python3 "{Path(__file__).resolve()}" '
            f"--context {args.context} --entity {args.entity}",
            file=sys.stderr,
        )
        return 1

    try:
        mapping = replacements(args.context, args.entity, args.plural)
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 1

    package = mapping["__context__"]
    if not package.isidentifier() or keyword.iskeyword(package) or package in {"shared", "alembic"}:
        print(f"{package!r} cannot be the package of a bounded context", file=sys.stderr)
        return 1
    if not mapping["__Entity__"].isidentifier():
        print(f"{args.entity!r} does not give a valid Python class name", file=sys.stderr)
        return 1

    planned = []
    for source in sorted(p for p in TEMPLATE_DIR.rglob("*") if p.is_file() and "__pycache__" not in p.parts):
        relative = substitute(str(source.relative_to(TEMPLATE_DIR)), mapping)
        planned.append((source, root / relative))

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
        text = sort_imports(substitute(source.read_text(encoding="utf-8"), mapping))
        target.write_text(text, encoding="utf-8")
        print(f"wrote {target}")

    if args.dry_run:
        return 0

    protected = (root / "iam").is_dir()
    include = f"app.include_router({package}_router"
    include += ", dependencies=authenticated, responses=unauthenticated)" if protected else ")"
    print(f"""
Three things the generator cannot do for you:

  1. Register the router in main.py:
         from {package}.interfaces.routes import router as {package}_router
         {include}

  2. Import the models in alembic/env.py, then create and apply the migration:
         import {package}.infrastructure.models  # noqa: F401
         alembic revision --autogenerate -m "create {mapping['__entities__']} table"
         alembic upgrade head

  3. Model the aggregate. {mapping['__Entity__']} has one `name` field as a
     placeholder -- replace it with the real attributes, in the language the
     domain experts use, then walk outward: the model, the repository mapping,
     the schemas. Put the rules that protect those attributes in methods on
     the aggregate, and generate a new migration when the table changes.

The endpoints are at /api/v1/{mapping['__entities-kebab__']}, under "{mapping['__Entities_title__']}" in /docs.""")
    if not (root / KERNEL_MARKER).exists():
        print(f"""
The shared kernel is not under {root / 'shared'} yet, and the generated code
builds on it. Install it before running the application:
  python3 "{SKILL_DIR / 'scripts' / 'install.py'}" shared-kernel --into {args.into}""")
    return 0


if __name__ == "__main__":
    sys.exit(main())
