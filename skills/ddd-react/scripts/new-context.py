#!/usr/bin/env python3
"""Scaffold a bounded context from assets/context-template/.

Writes the four layers of one context, wired for a single CRUD aggregate:

    <into>/<context>/
      domain/model/<entity>.entity.ts
      application/<context>.store.ts
      infrastructure/<entity>.resource.ts, <entity>.assembler.ts, <context>-api.ts
      presentation/<context>-paths.ts, <context>-routes.tsx,
                   views/<Entity>List.tsx, views/<Entity>Form.tsx

The template is the single source of truth: this script only substitutes the
naming placeholders, which is the part that is easy to get wrong by hand -- the
same concept appears as PascalCase, camelCase and kebab-case, singular and
plural, plus SCREAMING_SNAKE for the environment key, across file names, class
names, store actions and route paths. Component files are PascalCase, matching
the component they export; everything else is kebab-case.

Examples (run from the root of the React app, SKILL being this skill's directory):
    python3 "$SKILL/scripts/new-context.py" --context ordering --entity Order --into src
    python3 "$SKILL/scripts/new-context.py" --context catalog --entity MenuItem --into src --dry-run
    python3 "$SKILL/scripts/new-context.py" --context delivery --entity Courier --plural Couriers --into src
    python3 "$SKILL/scripts/new-context.py" --context staffing --entity Person --plural People --into src

Everything it writes is ordinary code -- read it, then change it. The generated
entity carries a single `name` field on purpose; model the real thing next.
"""
import argparse
import re
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = SKILL_DIR / "assets" / "context-template"


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


def replacements(context, entity, plural):
    context_words = split_words(context)
    entity_words = split_words(entity)
    plural_words = split_words(plural) if plural else pluralize(entity_words)
    return {
        "__Context__": pascal(context_words),
        "__context__": kebab(context_words),
        "__Entity__": pascal(entity_words),
        "__entity__": camel(entity_words),
        "__entity-kebab__": kebab(entity_words),
        "__Entities__": pascal(plural_words),
        "__entities__": camel(plural_words),
        "__entities-kebab__": kebab(plural_words),
        "__ENTITIES_UPPER__": "_".join(w.upper() for w in plural_words),
    }


def substitute(text, mapping):
    for token, value in sorted(mapping.items(), key=lambda kv: -len(kv[0])):
        text = text.replace(token, value)
    return text


def main():
    parser = argparse.ArgumentParser(
        description="Scaffold a DDD bounded context for a React app.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("Examples:", 1)[1].rstrip() if "Examples:" in __doc__ else None,
    )
    parser.add_argument("--context", required=True,
                        help="bounded context, in the ubiquitous language (e.g. ordering)")
    parser.add_argument("--entity", required=True,
                        help="aggregate this context starts with (e.g. Order, MenuItem)")
    parser.add_argument("--plural", default=None,
                        help="plural of the entity, when the naive one is wrong (e.g. People)")
    parser.add_argument("--into", default="src",
                        help="directory holding the contexts (default: src)")
    parser.add_argument("--dry-run", action="store_true",
                        help="list what would be written and stop")
    parser.add_argument("--force", action="store_true",
                        help="overwrite files that already exist")
    args = parser.parse_args()

    if not TEMPLATE_DIR.is_dir():
        print(f"Template directory not found: {TEMPLATE_DIR}", file=sys.stderr)
        return 1

    try:
        mapping = replacements(args.context, args.entity, args.plural)
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 1

    destination_root = Path(args.into)

    # Run this from the app, not from the skill. --into is resolved against the
    # current directory, so running it from the skill folder would quietly
    # scaffold the context inside the skill instead of inside the app.
    resolved = destination_root.resolve()
    if resolved == SKILL_DIR or SKILL_DIR in resolved.parents:
        print(
            f"--into resolves to {resolved}, which is inside the skill itself.\n"
            f"Run this from the root of your React app, for example:\n"
            f'  python3 "{Path(__file__).resolve()}" '
            f"--context {args.context} --entity {args.entity} --into src",
            file=sys.stderr,
        )
        return 1

    planned = []
    for source in sorted(p for p in TEMPLATE_DIR.rglob("*") if p.is_file()):
        relative = substitute(str(source.relative_to(TEMPLATE_DIR)), mapping)
        planned.append((source, destination_root / relative))

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

    context_kebab = mapping["__context__"]
    context_camel = camel(split_words(context_kebab))
    print(f"""
Three things the generator cannot do for you:

  1. Add the endpoint path to every .env file -- .env.development and
     .env.production both declare the same keys -- and to the ImportMetaEnv
     interface in src/vite-env.d.ts:
         VITE_{mapping['__ENTITIES_UPPER__']}_ENDPOINT_PATH="/{mapping['__entities-kebab__']}"

  2. Mount the context in router.tsx:
         import {{{context_camel}Routes}} from './{context_kebab}/presentation/{context_kebab}-routes';
         {{path: '{context_kebab}', children: {context_camel}Routes}},

  3. Model the aggregate. The generated entity has one `name` field as a
     placeholder -- replace it with the real fields, in the language the domain
     experts use, update the assembler to match, and give the entity the
     behaviour that would otherwise be repeated across views.
""".rstrip())
    return 0


if __name__ == "__main__":
    sys.exit(main())
