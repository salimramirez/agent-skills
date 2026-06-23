#!/usr/bin/env python3
"""Validate every skill in the agent-skills collection.

For each skills/<name>/SKILL.md this checks:
  - a YAML frontmatter block delimited by '---'
  - required keys present and non-empty: name, description
  - frontmatter `name` matches the skill's directory name
  - SKILL.md and every Markdown file in the skill are <= 500 lines

Exits non-zero with a clear message listing every problem found.
Run locally with: python3 .github/scripts/validate-skills.py
"""
import sys
from pathlib import Path

MAX_LINES = 500
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


def main():
    errors = []

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

        fm = frontmatter(skill_md.read_text(encoding="utf-8"))
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

    if errors:
        print("Skill validation failed:\n", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    print(f"All {len(skill_dirs)} skill(s) valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
