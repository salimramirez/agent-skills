#!/usr/bin/env python3
"""Install one of the copyable assets into an ASP.NET Core project.

    install.py project         a new project: the .csproj, Program.cs, settings, the
                               dotnet-ef tool manifest, and the shared kernel
    install.py shared-kernel   only the shared kernel, into an existing project
    install.py iam-context     a complete IAM bounded context: sign-up, sign-in, JWT

Everything is written under the project root -- the directory that holds the web
project's .csproj, Program.cs and one folder per bounded context. For
shared-kernel and iam-context that is the nearest directory, from the current one
upward, with an ASP.NET Core .csproj, so the script works from any directory of
the project. For project it is the current directory, which should be empty.
--into names the root explicitly in every case.

The root namespace of a new project comes from --name ("QuickBite Platform" gives
QuickBite.Platform) or, without it, from the directory's name; for the other two
assets it is read from <RootNamespace> in the .csproj, or is the .csproj's file
name. --namespace overrides it in every case.

Examples (SKILL being this skill's directory):
    mkdir QuickBite.Platform && cd QuickBite.Platform    # then install the skill into it
    python3 "$SKILL/scripts/install.py" project --name "QuickBite Platform"
    python3 "$SKILL/scripts/install.py" shared-kernel --dry-run    # from anywhere in a project
    python3 "$SKILL/scripts/install.py" iam-context

Everything it writes is ordinary code -- read it, then change it. Each asset ends
with the edits the script cannot make for you: packages, Program.cs, secrets,
migrations.
"""
import argparse
import random
import re
import sys
import uuid
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = SKILL_DIR / "assets"
ASSETS = ("project", "shared-kernel", "iam-context")
KERNEL_MARKER = Path("Shared/Infrastructure/Persistence/EntityFrameworkCore/Configuration/AppDbContext.cs")

NOTES = {
    "project": """
Next steps, from {root}:

  1. Point the connection string in appsettings.Development.json at a MySQL
     database (the database itself is created at start-up), then restore and
     build:
         dotnet tool restore
         dotnet build

  2. Add the first bounded context:
         python3 "{skill}/scripts/new-context.py" --context Ordering --entity Order

  3. Optionally, the identity context (sign-up, sign-in, JWT):
         python3 "{skill}/scripts/install.py" iam-context

  4. Create the first migration once there is a context, then run:
         dotnet ef migrations add InitialCreate
         dotnet run --launch-profile http

Swagger UI is at http://localhost:{http_port}/swagger.
""",
    "shared-kernel": """
Three things the installer cannot do for you:

  1. Add the packages the kernel needs:
         dotnet add package MySql.EntityFrameworkCore --version 10.0.9
         dotnet add package Microsoft.EntityFrameworkCore.Design --version 10.0.12
         dotnet add package Humanizer.Core --version 3.0.10
         dotnet add package Swashbuckle.AspNetCore --version 10.3.0
     and, to create migrations, the dotnet-ef tool:
         dotnet new tool-manifest && dotnet tool install dotnet-ef --version 10.0.12

  2. Wire it in Program.cs -- the file assets/project/Program.cs in this skill is
     the complete version to copy from: controllers with the kebab-case route
     convention, AddProblemDetails and the DomainExceptionHandler, the
     AppDbContext with the AuditableEntityInterceptor, the unit of work and the
     event dispatcher; then UseExceptionHandler and UseStatusCodePages first in
     the pipeline, and Database.Migrate() at start-up.

  3. Set the connection string "DefaultConnection" (appsettings.Development.json,
     or ConnectionStrings__DefaultConnection in the environment).

Nothing here holds business rules. If a class in Shared/ starts to know what
an Order is, it belongs in a bounded context.
""",
    "iam-context": """
Four things the installer cannot do for you:

  1. Add the packages:
         dotnet add package Microsoft.AspNetCore.Authentication.JwtBearer --version 10.0.12
         dotnet add package BCrypt.Net-Next --version 4.2.1

  2. Register it in Program.cs, under "// Bounded contexts":
         using {namespace}.Iam.Infrastructure.DependencyInjection;
         builder.Services.AddIamContext(builder.Configuration);
     From then on every endpoint needs a bearer token, except the ones marked
     [AllowAnonymous] (sign-up and sign-in).

  3. Set the signing key, at least 32 characters, outside any committed file --
     user secrets in development, the environment (TokenSettings__Secret) in
     production; the application refuses to start without it:
         dotnet user-secrets set "TokenSettings:Secret" "<a long random string>"

  4. Create the migration for the users table:
         dotnet ef migrations add AddIam

Review the roles in Iam/Domain/Model/ValueObjects/Role.cs: User and Admin are
placeholders. Name them in the ubiquitous language of the platform.
""",
}


def namespace_from(name):
    """Turn a project name into a root namespace: 'QuickBite Platform' -> 'QuickBite.Platform'."""
    parts = [part for part in re.split(r"[^A-Za-z0-9]+", name) if part]
    parts = [part[0].upper() + part[1:] for part in parts]
    return ".".join(parts) or "Platform"


def title_from(namespace):
    """The API title: 'QuickBite.Platform' -> 'QuickBite Platform'."""
    return namespace.replace(".", " ")


def database_from(namespace):
    """The database name: 'QuickBite.Platform' -> 'quickbite_platform'."""
    return "_".join(part.lower() for part in namespace.split("."))


def find_web_project(directory):
    """Return the .csproj of an ASP.NET Core project in a directory, or None."""
    for csproj in sorted(directory.glob("*.csproj")):
        if 'Sdk="Microsoft.NET.Sdk.Web"' in csproj.read_text(encoding="utf-8", errors="replace"):
            return csproj
    return None


def locate_project(into):
    """Return (root, csproj, None) or (None, None, message), as new-context.py does."""
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


def planned_files(asset):
    """Return (source, path relative to the project root) for every file of an asset."""
    bases = [ASSETS_DIR / "project", ASSETS_DIR / "shared-kernel"] if asset == "project" else [ASSETS_DIR / asset]
    pairs = [(source, source.relative_to(base)) for base in bases for source in base.rglob("*") if source.is_file()]
    return sorted(pairs, key=lambda pair: str(pair[1]))


def main():
    parser = argparse.ArgumentParser(
        description="Install a copyable asset of the ddd-aspnet-core skill.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples" + __doc__.split("Examples", 1)[1].rstrip(),
    )
    parser.add_argument("asset", choices=ASSETS, help="which asset to install")
    parser.add_argument("--into", default=None,
                        help="project root (default: the current directory for project, the nearest "
                             "directory with the web project's .csproj otherwise)")
    parser.add_argument("--name", default=None,
                        help="project name for a new project, e.g. 'QuickBite Platform' "
                             "(default: the directory's name)")
    parser.add_argument("--namespace", default=None, help="root namespace, overriding the one worked out")
    parser.add_argument("--dry-run", action="store_true", help="list what would be written and stop")
    parser.add_argument("--force", action="store_true", help="overwrite files that already exist")
    args = parser.parse_args()

    if args.asset == "project":
        root = Path(args.into or ".")
        enclosing = next((d for d in [Path.cwd().resolve(), *Path.cwd().resolve().parents]
                          if find_web_project(d) is not None), None)
        if args.into is None and enclosing is not None:
            print(
                f"{enclosing} already holds an ASP.NET Core project, so this directory is inside one.\n"
                f"Run this in a new, empty directory, or pass --into to create the project there anyway.",
                file=sys.stderr,
            )
            return 1
        namespace = args.namespace or namespace_from(args.name or root.resolve().name)
    else:
        root, csproj, problem = locate_project(args.into)
        if root is None:
            print(problem, file=sys.stderr)
            return 1
        namespace = args.namespace or root_namespace_of(csproj)

    # Never write inside the skill: its assets hold a .csproj of their own, and
    # running from there would install the asset into the skill.
    resolved = root.resolve()
    if resolved == SKILL_DIR or SKILL_DIR in resolved.parents:
        print(
            f"The project root resolves to {resolved}, which is inside the skill itself.\n"
            f"Run this from inside your ASP.NET Core project, for example:\n"
            f'  cd path/to/project && python3 "{Path(__file__).resolve()}" {args.asset}',
            file=sys.stderr,
        )
        return 1

    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)*", namespace):
        print(f"{namespace!r} is not a valid C# namespace; pass --namespace to choose one.", file=sys.stderr)
        return 1

    if args.asset == "iam-context" and not (root / KERNEL_MARKER).exists():
        print(
            f"The shared kernel is not under {root / 'Shared'}, and the IAM context builds on it.\n"
            f"Install it first:\n"
            f'  python3 "{Path(__file__).resolve()}" shared-kernel --into {root}',
            file=sys.stderr,
        )
        return 1

    # Not 5000: macOS keeps it (and 7000) for the AirPlay Receiver.
    http_port = str(random.randint(5001, 5299))
    mapping = {
        "__RootNamespace__": namespace,
        "__Title__": title_from(namespace),
        "__database__": database_from(namespace),
        "__UserSecretsId__": str(uuid.uuid4()),
        "__HttpPort__": http_port,
    }
    planned = []
    for source, relative in planned_files(args.asset):
        target_relative = str(relative).replace("__RootNamespace__", namespace)
        planned.append((source, root / target_relative))

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

    print(NOTES[args.asset].format(skill=SKILL_DIR, root=resolved, namespace=namespace, http_port=http_port).rstrip())
    return 0


if __name__ == "__main__":
    sys.exit(main())
