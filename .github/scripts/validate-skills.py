#!/usr/bin/env python3
"""Validate every skill in the agent-skills collection.

For each skills/<name>/SKILL.md this checks:
  - a YAML frontmatter block delimited by '---'
  - required keys present and non-empty: name, description
  - frontmatter `name` matches the skill's directory name
  - SKILL.md and every Markdown file in the skill are <= 500 lines

Skills in the DDD family (directory name starting with "ddd-") additionally
carry a shared core block, delimited by the CORE_START/CORE_END markers below.
The block is duplicated on purpose: there is no cross-skill dependency
primitive, so a stack skill must be able to run on its own without losing the
DDD design rules. This check keeps every copy byte-identical.

Exits non-zero with a clear message listing every problem found.
Run locally with: python3 .github/scripts/validate-skills.py
"""
import sys
from pathlib import Path

MAX_LINES = 500
CORE_START = "<!-- ddd:core:start -->"
CORE_END = "<!-- ddd:core:end -->"
CORE_FAMILY_PREFIX = "ddd-"
ROOT = Path(__file__).resolve().parents[2]
SKILLS_DIR = ROOT / "skills"


def frontmatter(text):
    """Return the lines between the leading '---' fences, or None if absent."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return lines[1:i]
    return None


def get_key(fm_lines, key):
    prefix = key + ":"
    for line in fm_lines:
        if line.startswith(prefix):
            return line[len(prefix):].strip().strip('"').strip("'")
    return None


def core_block(text):
    """Return the text between the core markers.

    Returns None when no block is present, or the string "malformed" when the
    markers are missing a partner, out of order, or repeated.
    """
    if CORE_START not in text and CORE_END not in text:
        return None
    if text.count(CORE_START) != 1 or text.count(CORE_END) != 1:
        return "malformed"
    start = text.index(CORE_START) + len(CORE_START)
    end = text.index(CORE_END)
    if end < start:
        return "malformed"
    return text[start:end].strip()


def main():
    errors = []
    cores = {}

    # A skill is a directory under skills/. Skip dotfiles and local-only
    # eval artifacts (skills/<name>-workspace/, gitignored) which aren't skills.
    skill_dirs = (
        sorted(
            p
            for p in SKILLS_DIR.iterdir()
            if p.is_dir() and not p.name.startswith(".") and not p.name.endswith("-workspace")
        )
        if SKILLS_DIR.is_dir()
        else []
    )
    if not skill_dirs:
        print("No skills found under skills/", file=sys.stderr)
        return 1

    for skill in skill_dirs:
        skill_md = skill / "SKILL.md"
        if not skill_md.is_file():
            errors.append(f"{skill.name}: missing SKILL.md")
            continue

        skill_text = skill_md.read_text(encoding="utf-8")

        block = core_block(skill_text)
        if block == "malformed":
            errors.append(
                f"{skill.name}/SKILL.md: core block markers are unbalanced, "
                f"repeated, or out of order"
            )
        elif block is None:
            if skill.name.startswith(CORE_FAMILY_PREFIX):
                errors.append(
                    f"{skill.name}/SKILL.md: missing the shared core block "
                    f"({CORE_START} ... {CORE_END})"
                )
        else:
            cores[skill.name] = block

        fm = frontmatter(skill_text)
        if fm is None:
            errors.append(f"{skill.name}/SKILL.md: missing or unterminated '---' frontmatter")
        else:
            name = get_key(fm, "name")
            description = get_key(fm, "description")
            if not name:
                errors.append(f"{skill.name}/SKILL.md: frontmatter 'name' is missing or empty")
            elif name != skill.name:
                errors.append(
                    f"{skill.name}/SKILL.md: frontmatter name '{name}' "
                    f"does not match directory '{skill.name}'"
                )
            if not description:
                errors.append(f"{skill.name}/SKILL.md: frontmatter 'description' is missing or empty")

        for md in sorted(skill.rglob("*.md")):
            count = len(md.read_text(encoding="utf-8").splitlines())
            if count > MAX_LINES:
                errors.append(f"{md.relative_to(ROOT)}: {count} lines exceeds {MAX_LINES}")

    # Every core block in the collection must be byte-identical. ddd-playbook is
    # the canonical copy when it is present; otherwise the first skill wins.
    if len(set(cores.values())) > 1:
        canonical_name = "ddd-playbook" if "ddd-playbook" in cores else sorted(cores)[0]
        canonical = cores[canonical_name]
        for name in sorted(cores):
            if cores[name] != canonical:
                errors.append(
                    f"{name}/SKILL.md: core block differs from {canonical_name}/SKILL.md "
                    f"(copy it across verbatim)"
                )

    if errors:
        print("Skill validation failed:\n", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    print(f"All {len(skill_dirs)} skill(s) valid ({len(cores)} sharing the core block).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
