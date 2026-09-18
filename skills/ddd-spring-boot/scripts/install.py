#!/usr/bin/env python3
"""Install one of the copyable assets into a Spring Boot project.

    install.py shared-kernel   the base classes and configuration every context shares
    install.py iam-context     a complete IAM bounded context: sign-up, sign-in, JWT

The asset is copied as it is under <into>/<base package as a path>/, with the
package placeholder replaced by the project's base package -- the package of the
class annotated with @SpringBootApplication, found by scanning <into>. Pass
--package when there is no such class yet, or to override what was found.
A relative <into> is looked for under the current directory first and then under
the nearest parent that holds a pom.xml or build.gradle, so the script works from
any directory of the project.

Examples (run from anywhere inside the Spring Boot project, SKILL being this skill's directory):
    python3 "$SKILL/scripts/install.py" shared-kernel
    python3 "$SKILL/scripts/install.py" shared-kernel --into src/main/java --dry-run
    python3 "$SKILL/scripts/install.py" iam-context --package com.quickbite.platform

Everything it writes is ordinary code -- read it, then change it. Each asset ends
with the edits the script cannot make for you: dependencies, properties, annotations.
"""
import argparse
import re
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = SKILL_DIR / "assets"
PACKAGE_PLACEHOLDER = "__base_package__"
ASSETS = ("shared-kernel", "iam-context")
KERNEL_MARKER = "shared/domain/model/aggregates/AuditableAbstractAggregateRoot.java"

NOTES = {
    "shared-kernel": """
Four things the installer cannot do for you:

  1. Add the dependencies the kernel needs to pom.xml (versions as of writing):
         io.github.encryptorcode:pluralize:1.0.0                  (table pluralization)
         org.springdoc:springdoc-openapi-starter-webmvc-ui:2.8.13 (OpenAPI + Swagger UI)
         org.projectlombok:lombok                                  (optional, with the
             annotationProcessorPaths entry the Spring Initializr generates)
         org.springframework.boot:spring-boot-starter-validation

  2. Register the naming strategy and the documentation values in
     application.properties:
         spring.jpa.hibernate.naming.physical-strategy={package}.shared.infrastructure.persistence.jpa.configuration.strategy.SnakeCaseWithPluralizedTablePhysicalNamingStrategy
         documentation.application.description=@project.description@
         documentation.application.version=@project.version@

  3. Turn on auditing, or createdAt/updatedAt stay null and the insert fails:
         @EnableJpaAuditing on the @SpringBootApplication class

  4. Nothing here holds business rules. If a class in shared/ starts to know
     what an Order is, it belongs in a bounded context.
""",
    "iam-context": """
Four things the installer cannot do for you:

  1. Add the dependencies to pom.xml:
         org.springframework.boot:spring-boot-starter-security
         io.jsonwebtoken:jjwt-api:0.12.6
         io.jsonwebtoken:jjwt-impl:0.12.6      (scope runtime)
         io.jsonwebtoken:jjwt-jackson:0.12.6   (scope runtime)
         org.apache.commons:commons-lang3      (no version: Spring Boot manages it)

  2. Add the token settings to application.properties:
         authorization.jwt.secret=<at least 32 characters, from the environment in production>
         authorization.jwt.expiration.days=7

  3. Decide what stays public. WebSecurityConfiguration permits
     /api/v1/authentication/** and the Swagger endpoints; every other request
     needs a bearer token. Adjust the list and the CORS settings there.

  4. Review the roles. Roles.java carries ROLE_USER, ROLE_ADMIN and
     ROLE_INSTRUCTOR as placeholders; rename them in the ubiquitous language of
     your domain. They are seeded on startup by ApplicationReadyEventHandler.
""",
}


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
        description="Install a copyable asset of the ddd-spring-boot skill.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples" + __doc__.split("Examples", 1)[1].rstrip(),
    )
    parser.add_argument("asset", choices=ASSETS, help="which asset to install")
    parser.add_argument("--package", default=None,
                        help="base package of the project (default: that of the @SpringBootApplication class)")
    parser.add_argument("--into", default="src/main/java",
                        help="source root holding the packages (default: src/main/java)")
    parser.add_argument("--dry-run", action="store_true",
                        help="list what would be written and stop")
    parser.add_argument("--force", action="store_true",
                        help="overwrite files that already exist")
    args = parser.parse_args()

    asset_dir = ASSETS_DIR / args.asset
    if not asset_dir.is_dir():
        print(f"Asset directory not found: {asset_dir}", file=sys.stderr)
        return 1

    source_root, problem = locate_source_root(args.into)
    if problem:
        print(problem, file=sys.stderr)
        return 1

    # Run this from the project, not from the skill. --into is resolved against
    # the current directory, so running it from the skill folder would quietly
    # install the asset inside the skill instead of inside the project.
    resolved = source_root.resolve()
    if resolved == SKILL_DIR or SKILL_DIR in resolved.parents:
        print(
            f"--into resolves to {resolved}, which is inside the skill itself.\n"
            f"Run this from inside your Spring Boot project, for example:\n"
            f'  python3 "{Path(__file__).resolve()}" {args.asset} --into src/main/java',
            file=sys.stderr,
        )
        return 1

    package = args.package or (detect_package(source_root) if source_root.is_dir() else None)
    if not package:
        print(
            f"No class annotated with @SpringBootApplication under {source_root}, so the base\n"
            f"package cannot be detected. Pass it explicitly, for example:\n"
            f'  python3 "{Path(__file__).resolve()}" {args.asset} --package com.quickbite.platform',
            file=sys.stderr,
        )
        return 1
    if not re.fullmatch(r"[a-z_][\w]*(\.[a-z_][\w]*)*", package):
        print(f"{package!r} is not a valid Java package name", file=sys.stderr)
        return 1

    package_dir = source_root.joinpath(*package.split("."))
    planned = []
    for source in sorted(p for p in asset_dir.rglob("*") if p.is_file()):
        planned.append((source, package_dir / source.relative_to(asset_dir)))

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
        text = source.read_text(encoding="utf-8").replace(PACKAGE_PLACEHOLDER, package)
        target.write_text(text, encoding="utf-8")
        print(f"wrote {target}")

    if args.dry_run:
        return 0

    print(NOTES[args.asset].format(package=package).rstrip())
    if args.asset == "iam-context" and not (package_dir / KERNEL_MARKER).exists():
        print(f"""
The shared kernel is not under {package_dir / 'shared'} yet, and the IAM context
extends it. Install it before compiling:
  python3 "{Path(__file__).resolve()}" shared-kernel --into {args.into}""")
    return 0


if __name__ == "__main__":
    sys.exit(main())
