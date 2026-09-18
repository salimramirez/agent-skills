#!/usr/bin/env python3
"""Scaffold a bounded context from assets/context-template/.

Writes the four layers of one context, wired for a single CRUD aggregate:

    <into>/<base package>/<context>/
      domain/model/aggregates/<Entity>.java
      domain/model/commands/Create|Update|Delete<Entity>Command.java
      domain/model/queries/Get<Entity>ByIdQuery.java, GetAll<Entities>Query.java
      domain/services/<Entity>CommandService.java, <Entity>QueryService.java
      domain/exceptions/<Entity>NotFoundException.java
      application/internal/commandservices/<Entity>CommandServiceImpl.java
      application/internal/queryservices/<Entity>QueryServiceImpl.java
      infrastructure/persistence/jpa/repositories/<Entity>Repository.java
      interfaces/rest/<Entities>Controller.java, <Context>ExceptionHandler.java
      interfaces/rest/resources/<Entity>Resource.java, Create|Update<Entity>Resource.java
      interfaces/rest/transform/ the three assemblers

The template is the single source of truth: this script only substitutes the
naming placeholders, which is the part that is easy to get wrong by hand -- the
same concept appears as PascalCase and camelCase, singular and plural, in class
names, package names, path variables and REST paths.

The base package is the package of the class annotated with
@SpringBootApplication, found by scanning <into>; pass --package to override it.
A relative <into> is looked for under the current directory first and then under
the nearest parent that holds a pom.xml or build.gradle, so the script works from
any directory of the project.
The generated code extends the shared kernel, so install that first:
    python3 "$SKILL/scripts/install.py" shared-kernel

Examples (run from anywhere inside the Spring Boot project, SKILL being this skill's directory):
    python3 "$SKILL/scripts/new-context.py" --context ordering --entity Order
    python3 "$SKILL/scripts/new-context.py" --context catalog --entity MenuItem --into src/main/java --dry-run
    python3 "$SKILL/scripts/new-context.py" --context delivery --entity Courier --plural Couriers
    python3 "$SKILL/scripts/new-context.py" --context staffing --entity Person --plural People

Everything it writes is ordinary code -- read it, then change it. The generated
aggregate carries a single `name` field on purpose; model the real thing next.
"""
import argparse
import re
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = SKILL_DIR / "assets" / "context-template"
KERNEL_MARKER = "shared/domain/model/aggregates/AuditableAbstractAggregateRoot.java"


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


def camel(words):
    head, *tail = words
    return head + "".join(w.capitalize() for w in tail)


def kebab(words):
    return "-".join(words)


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


def replacements(package, context, entity, plural):
    context_words = split_words(context)
    entity_words = split_words(entity)
    plural_words = split_words(plural) if plural else pluralize(entity_words)
    return {
        "__base_package__": package,
        # A Java package segment: lowercase, no separators (ordering, menucatalog).
        "__context__": "".join(context_words),
        "__Context__": pascal(context_words),
        "__Entity__": pascal(entity_words),
        "__entity__": camel(entity_words),
        "__Entities__": pascal(plural_words),
        "__entities__": camel(plural_words),
        "__entities-kebab__": kebab(plural_words),
        # Prose: "menu item", "menu items", and "a menu item" / "an order".
        "__entity words__": " ".join(entity_words),
        "__entities words__": " ".join(plural_words),
        "__a_entity__": ("an " if entity_words[0][0] in "aeiou" else "a ") + " ".join(entity_words),
    }


def substitute(text, mapping):
    for token, value in sorted(mapping.items(), key=lambda kv: -len(kv[0])):
        text = text.replace(token, value)
    return text


PROJECT_MARKERS = ("pom.xml", "build.gradle", "build.gradle.kts")


def locate_source_root(into):
    """Resolve --into against the current directory, or against the project root above it.

    A relative --into that does not exist here is looked for under each parent
    directory that holds a Maven or Gradle build file, so the scripts work from
    anywhere inside the project. Returns (path, None) or (None, message).
    """
    given = Path(into)
    if given.is_absolute() or given.is_dir():
        return given, None
    for parent in Path.cwd().parents:
        if any((parent / marker).is_file() for marker in PROJECT_MARKERS):
            candidate = parent / given
            if candidate.is_dir():
                return candidate, None
            break
    return None, (
        f"{given} does not exist under the current directory, and no project root above it has it.\n"
        f"Run this from inside your Spring Boot project, or pass --into with the path to its sources."
    )


def detect_package(root):
    """Return the package of the @SpringBootApplication class under root, or None."""
    for source in sorted(root.rglob("*.java")):
        text = source.read_text(encoding="utf-8", errors="replace")
        if "@SpringBootApplication" not in text:
            continue
        match = re.search(r"^\s*package\s+([\w.]+)\s*;", text, re.MULTILINE)
        if match:
            return match.group(1)
    return None


def main():
    parser = argparse.ArgumentParser(
        description="Scaffold a DDD bounded context for a Spring Boot project.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples" + __doc__.split("Examples", 1)[1].rstrip(),
    )
    parser.add_argument("--context", required=True,
                        help="bounded context, in the ubiquitous language (e.g. ordering)")
    parser.add_argument("--entity", required=True,
                        help="aggregate this context starts with (e.g. Order, MenuItem)")
    parser.add_argument("--plural", default=None,
                        help="plural of the entity, when the naive one is wrong (e.g. People)")
    parser.add_argument("--package", default=None,
                        help="base package of the project (default: that of the @SpringBootApplication class)")
    parser.add_argument("--into", default="src/main/java",
                        help="source root holding the packages (default: src/main/java)")
    parser.add_argument("--dry-run", action="store_true",
                        help="list what would be written and stop")
    parser.add_argument("--force", action="store_true",
                        help="overwrite files that already exist")
    args = parser.parse_args()

    if not TEMPLATE_DIR.is_dir():
        print(f"Template directory not found: {TEMPLATE_DIR}", file=sys.stderr)
        return 1

    source_root, problem = locate_source_root(args.into)
    if problem:
        print(problem, file=sys.stderr)
        return 1

    # Run this from the project, not from the skill. --into is resolved against
    # the current directory, so running it from the skill folder would quietly
    # scaffold the context inside the skill instead of inside the project.
    resolved = source_root.resolve()
    if resolved == SKILL_DIR or SKILL_DIR in resolved.parents:
        print(
            f"--into resolves to {resolved}, which is inside the skill itself.\n"
            f"Run this from inside your Spring Boot project, for example:\n"
            f'  python3 "{Path(__file__).resolve()}" '
            f"--context {args.context} --entity {args.entity} --into src/main/java",
            file=sys.stderr,
        )
        return 1

    package = args.package or (detect_package(source_root) if source_root.is_dir() else None)
    if not package:
        print(
            f"No class annotated with @SpringBootApplication under {source_root}, so the base\n"
            f"package cannot be detected. Pass it explicitly, for example:\n"
            f'  python3 "{Path(__file__).resolve()}" '
            f"--context {args.context} --entity {args.entity} --package com.quickbite.platform",
            file=sys.stderr,
        )
        return 1
    if not re.fullmatch(r"[a-z_][\w]*(\.[a-z_][\w]*)*", package):
        print(f"{package!r} is not a valid Java package name", file=sys.stderr)
        return 1

    try:
        mapping = replacements(package, args.context, args.entity, args.plural)
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 1

    package_dir = source_root.joinpath(*package.split("."))
    planned = []
    for source in sorted(p for p in TEMPLATE_DIR.rglob("*") if p.is_file()):
        relative = substitute(str(source.relative_to(TEMPLATE_DIR)), mapping)
        planned.append((source, package_dir / relative))

    clashes = [target for _, target in planned if target.exists()]
    if clashes and not args.force:
        print("Refusing to overwrite existing files (pass --force to replace them):",
              file=sys.stderr)
        for target in clashes:
            print(f"  {target}", file=sys.stderr)
        return 1

    for source, target in planned:
        if args.dry_run:
            print(f"would write {target}")
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(substitute(source.read_text(encoding="utf-8"), mapping),
                          encoding="utf-8")
        print(f"wrote {target}")

    if args.dry_run:
        return 0

    kernel_missing = not (package_dir / KERNEL_MARKER).exists()
    print(f"""
Two things the generator cannot do for you:

  1. Model the aggregate. {mapping['__Entity__']} has one `name` field as a
     placeholder -- replace it with the real attributes, in the language the
     domain experts use, then walk outward: commands, resources, assemblers.
     Put the rules that protect those attributes in methods on the aggregate.

  2. Start the application: Hibernate creates the table on startup
     (ddl-auto=update) and names it after the naming strategy; the endpoints are
     at /api/v1/{mapping['__entities-kebab__']} and in Swagger UI under "{mapping['__Entities__']}".
""".rstrip())
    if kernel_missing:
        print(f"""
The shared kernel is not under {package_dir / 'shared'} yet, and the generated
aggregate extends it. Install it before compiling:
  python3 "{SKILL_DIR / 'scripts' / 'install.py'}" shared-kernel --into {args.into}""")
    return 0


if __name__ == "__main__":
    sys.exit(main())
