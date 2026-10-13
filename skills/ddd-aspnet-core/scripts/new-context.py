#!/usr/bin/env python3
"""Scaffold a bounded context from assets/context-template/.

Writes the four layers of one context, wired for a single CRUD aggregate:

    <root>/<Context>/
      Domain/Model/Aggregates, Commands, Queries;  Domain/Repositories
      Application/CommandServices, QueryServices;  Application/Internal/...
      Infrastructure/Persistence/EntityFrameworkCore/Configuration, Repositories
      Infrastructure/DependencyInjection
      Interfaces/Rest, Rest/Resources, Rest/Transform

The template is the single source of truth: this script only substitutes the
naming placeholders, which is the part that is easy to get wrong by hand -- the
same concept appears in PascalCase and camelCase, singular and plural, in type
names, namespaces, parameters, routes and the XML comments.

The context is written into the project root: the nearest directory, from the
current one upward, that holds the web project's .csproj, so the script works
from any directory of the project; --into names the root explicitly. The root
namespace is read from <RootNamespace> in the .csproj, or is the .csproj's file
name; --namespace overrides it. The generated code builds on the shared kernel,
so install that first:
    python3 "$SKILL/scripts/install.py" shared-kernel

Examples (run from anywhere inside the project, SKILL being this skill's directory):
    python3 "$SKILL/scripts/new-context.py" --context Ordering --entity Order
    python3 "$SKILL/scripts/new-context.py" --context menu-management --entity MenuItem --dry-run
    python3 "$SKILL/scripts/new-context.py" --context Staffing --entity Person --plural People

Everything it writes is ordinary code -- read it, then change it. The generated
aggregate carries a single Name property on purpose; model the real thing next.
"""
import argparse
import re
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = SKILL_DIR / "assets" / "context-template"
KERNEL_MARKER = Path("Shared/Infrastructure/Persistence/EntityFrameworkCore/Configuration/AppDbContext.cs")

# Folders of the project that are not bounded contexts, and namespaces a context must not shadow: a
# context named System makes every System.Text... written in the project resolve to it (measured, CS0234).
RESERVED_CONTEXTS = {"Shared", "Migrations", "Properties", "System", "Microsoft"}

# Types the generated code already sees -- through the implicit usings of a web project or from the
# shared kernel. An entity with one of these names makes every reference to it ambiguous (CS0104);
# measured for each of the first seventeen, the rest live in the same namespaces.
TAKEN_TYPE_NAMES = {
    "Task", "Path", "File", "Thread", "Timer", "Monitor", "Random", "Action", "Index", "Range", "Version",
    "Type", "Host", "Endpoint", "Exception", "Result", "Error",
    "Directory", "Stream", "Route", "Barrier", "Semaphore", "Mutex", "Environment", "Attribute", "Uri",
    "Guid", "Math", "Convert", "Delegate", "Enum", "Array", "Tuple", "Lazy", "Buffer", "Console",
    "Object", "String", "ErrorKind", "HttpContext", "Results", "WebApplication",
}

# The camelCase spelling of the entity names variables and parameters, so it cannot be a C# keyword:
# an entity named Event writes `var event = ...` (measured: the build fails with hundreds of errors).
CSHARP_KEYWORDS = {
    "abstract", "as", "base", "bool", "break", "byte", "case", "catch", "char", "checked", "class", "const",
    "continue", "decimal", "default", "delegate", "do", "double", "else", "enum", "event", "explicit",
    "extern", "false", "finally", "fixed", "float", "for", "foreach", "goto", "if", "implicit", "in", "int",
    "interface", "internal", "is", "lock", "long", "namespace", "new", "null", "object", "operator", "out",
    "override", "params", "private", "protected", "public", "readonly", "ref", "return", "sbyte", "sealed",
    "short", "sizeof", "stackalloc", "static", "string", "struct", "switch", "this", "throw", "true", "try",
    "typeof", "uint", "ulong", "unchecked", "unsafe", "ushort", "using", "virtual", "void", "volatile", "while",
}


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
    return words[0] + "".join(w.capitalize() for w in words[1:])


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


def replacements(root_namespace, context, entity, plural):
    context_words = split_words(context)
    entity_words = split_words(entity)
    plural_words = split_words(plural) if plural else pluralize(entity_words)
    entity_phrase = " ".join(entity_words)
    a_entity = ("an " if entity_phrase[0] in "aeiou" else "a ") + entity_phrase
    return {
        "__RootNamespace__": root_namespace,
        "__Context__": pascal(context_words),
        "__Entity__": pascal(entity_words),
        "__Entities__": pascal(plural_words),
        "__entity__": camel(entity_words),
        "__entities__": camel(plural_words),
        "__entity words__": entity_phrase,
        "__Entity words__": entity_phrase.capitalize(),
        "__entities words__": " ".join(plural_words),
        "__a_entity__": a_entity,
        "__A_entity__": a_entity.capitalize(),
        "__entities-kebab__": "-".join(plural_words),
    }


def substitute(text, mapping):
    for token, value in sorted(mapping.items(), key=lambda kv: -len(kv[0])):
        text = text.replace(token, value)
    return text


def find_web_project(directory):
    """Return the .csproj of an ASP.NET Core project in a directory, or None."""
    for csproj in sorted(directory.glob("*.csproj")):
        if 'Sdk="Microsoft.NET.Sdk.Web"' in csproj.read_text(encoding="utf-8", errors="replace"):
            return csproj
    return None


def locate_project(into):
    """Return (root, csproj, None) or (None, None, message).

    The root is --into if given, else the nearest directory, from the current one
    upward, holding an ASP.NET Core .csproj -- so the script works from anywhere
    inside the project.
    """
    candidates = [Path(into)] if into is not None else [Path.cwd(), *Path.cwd().parents]
    for directory in candidates:
        csproj = find_web_project(directory)
        if csproj is not None:
            return directory, csproj, None
    where = f"in {into}" if into is not None else "in the current directory or above it"
    return None, None, (
        f"No ASP.NET Core project (a .csproj with Sdk=\"Microsoft.NET.Sdk.Web\") {where}.\n"
        f"Run this from inside your project, or pass --into with the path to the directory of its .csproj."
    )


def root_namespace_of(csproj):
    """The <RootNamespace> of a project, or its file name, which is what MSBuild uses by default."""
    match = re.search(r"<RootNamespace>\s*([^<\s]+)\s*</RootNamespace>", csproj.read_text(encoding="utf-8"))
    return match.group(1) if match else csproj.stem


def name_problem(mapping):
    """Say why the context or entity name would not compile, or return None."""
    context, entity = mapping["__Context__"], mapping["__Entity__"]
    if context in RESERVED_CONTEXTS:
        return (f"{context!r} cannot be a bounded context: it is a folder of the project or a namespace the "
                f"code relies on. Name the context after what it owns, in the ubiquitous language.")
    if context == entity:
        return (f"The context and the entity are both {entity!r}: inside the context, {entity} would be the "
                f"namespace, not the class (CS0118). Name the context after the capability -- "
                f"'{entity}ing', '{entity}Management' -- or after the plural, '{mapping['__Entities__']}'.")
    if entity in TAKEN_TYPE_NAMES:
        return (f"{entity!r} is already a type the generated code uses, so every reference to it would be "
                f"ambiguous (CS0104). Give the entity a more specific name in the ubiquitous language, e.g. "
                f"'Kitchen{entity}' or 'Delivery{entity}'.")
    if entity == "Name":
        return ("An entity named Name would hold the template's Name property, a member with the name of its "
                "own class (CS0542). Give the entity a more specific name, e.g. 'BrandName' or 'DisplayName'.")
    for token in ("__entity__", "__entities__"):
        if mapping[token] in CSHARP_KEYWORDS:
            return (f"{mapping[token]!r}, the camelCase form of the entity, is a C# keyword, and the generated "
                    f"code uses it as a variable name. Give the entity a more specific name, e.g. "
                    f"'Domain{entity}' or '{entity}Record'.")
    return None


def main():
    parser = argparse.ArgumentParser(
        description="Scaffold a DDD bounded context for an ASP.NET Core project.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples" + __doc__.split("Examples", 1)[1].rstrip(),
    )
    parser.add_argument("--context", required=True,
                        help="bounded context, in the ubiquitous language (e.g. Ordering, menu-management)")
    parser.add_argument("--entity", required=True,
                        help="aggregate this context starts with (e.g. Order, MenuItem)")
    parser.add_argument("--plural", default=None,
                        help="plural of the entity, when the naive one is wrong (e.g. People)")
    parser.add_argument("--into", default=None,
                        help="project root (default: the nearest directory with the web project's .csproj)")
    parser.add_argument("--namespace", default=None,
                        help="root namespace (default: <RootNamespace> in the .csproj, or its file name)")
    parser.add_argument("--dry-run", action="store_true", help="list what would be written and stop")
    parser.add_argument("--force", action="store_true", help="overwrite files that already exist")
    args = parser.parse_args()

    if not TEMPLATE_DIR.is_dir():
        print(f"Template directory not found: {TEMPLATE_DIR}", file=sys.stderr)
        return 1

    root, csproj, problem = locate_project(args.into)
    if root is None:
        print(problem, file=sys.stderr)
        return 1

    resolved = root.resolve()
    if resolved == SKILL_DIR or SKILL_DIR in resolved.parents:
        print(
            f"The project root resolves to {resolved}, which is inside the skill itself.\n"
            f"Run this from inside your ASP.NET Core project, for example:\n"
            f'  cd path/to/project && python3 "{Path(__file__).resolve()}" '
            f"--context {args.context} --entity {args.entity}",
            file=sys.stderr,
        )
        return 1

    try:
        mapping = replacements(args.namespace or root_namespace_of(csproj), args.context, args.entity, args.plural)
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 1

    for token in ("__Context__", "__Entity__", "__Entities__"):
        if not re.fullmatch(r"[A-Z][A-Za-z0-9]*", mapping[token]):
            print(f"{mapping[token]!r} is not a valid C# type name", file=sys.stderr)
            return 1
    problem = name_problem(mapping)
    if problem:
        print(problem, file=sys.stderr)
        return 1

    planned = []
    for source in sorted(p for p in TEMPLATE_DIR.rglob("*") if p.is_file()):
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
        target.write_text(substitute(source.read_text(encoding="utf-8"), mapping), encoding="utf-8")
        print(f"wrote {target}")

    if args.dry_run:
        return 0

    context, namespace = mapping["__Context__"], mapping["__RootNamespace__"]
    print(f"""
Three things the generator cannot do for you:

  1. Register the context in Program.cs, under "// Bounded contexts":
         using {namespace}.{context}.Infrastructure.DependencyInjection;
         builder.Services.Add{context}Context();

  2. Create the migration; the application applies it at start-up:
         dotnet ef migrations add Add{context}

  3. Model the aggregate. {mapping['__Entity__']} has one Name property as a
     placeholder -- replace it with the real attributes, in the language the
     domain experts use, then walk outward: the configuration, the resources,
     the assemblers. Put the rules that protect those attributes in methods on
     the aggregate, and add a migration whenever the model changes.

The endpoints are at /api/v1/{mapping['__entities-kebab__']}, under "{mapping['__Entities__']}" in Swagger UI.""")
    if not (root / KERNEL_MARKER).exists():
        print(f"""
The shared kernel is not under {root / 'Shared'} yet, and the generated code
builds on it. Install it before building:
  python3 "{SKILL_DIR / 'scripts' / 'install.py'}" shared-kernel --into {root}""")
    return 0


if __name__ == "__main__":
    sys.exit(main())
