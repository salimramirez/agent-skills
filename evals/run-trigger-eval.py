#!/usr/bin/env python3
"""Measure which skill a set of queries actually triggers.

For each query it runs `claude -p` in a scratch project, watches the streamed
events, and records the skill named by the first `Skill` tool call -- or the
tool it reached for instead, or that it answered in prose.

Why this exists rather than the skill-creator's `run_eval.py`: that script does
not install a skill. It writes a slash command to `.claude/commands/` and counts
a trigger only when the first tool call names *that command*. Three ways to get
a meaningless zero out of it, all of them hit while writing this:

  1. Run it from anywhere without the target project in front of Claude, and the
     first tool call is a `Bash` or `Glob` to look around -- scored as no-trigger
     before the skill was ever considered.
  2. Run it where the real skill is installed, and Claude triggers the real skill
     while the script watches for its temporary command name. Every case fails.
  3. Run it where the real skill is absent, and the temporary command is not
     consulted the way a skill is -- Claude just answers in prose.

So this installs the real skills and asks the question directly: with these
skills available, in this kind of project, which one wins?

Setup that makes the answer meaningful:

  - `--project` should look like what the queries describe. Queries about an
    Angular app measured in an empty directory tell you nothing.
  - Install every skill that competes for the same vocabulary, not just the one
    under test. The interesting failure is the sibling skill winning.

Usage:

    python3 evals/ddd-angular/run-trigger-eval.py \
        --eval-set evals/ddd-angular/trigger-eval.json \
        --project /path/to/a/scratch/angular-app \
        --skill skills/ddd-angular --skill skills/ddd-spring-boot \
        --skill skills/ddd-playbook \
        --expect ddd-angular --runs 2
"""
import argparse
import concurrent.futures as futures
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


def first_tool(query, cwd, model, timeout):
    """Return the skill named by the first Skill call, or a marker for what happened."""
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
    command = ["claude", "-p", query, "--output-format", "stream-json",
               "--verbose", "--include-partial-messages"]
    if model:
        command += ["--model", model]
    try:
        done = subprocess.run(command, cwd=cwd, env=env, capture_output=True,
                              text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return "<timeout>"

    name, payload = None, ""
    for line in done.stdout.split("\n"):
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        # A call that never reached the API must not be scored as "chose not to
        # trigger" -- that is the false zero this whole script exists to avoid.
        if event.get("type") == "result" and event.get("is_error"):
            return "<call-failed>"
        if event.get("type") != "stream_event":
            continue
        inner = event["event"]
        kind = inner.get("type", "")
        if kind == "content_block_start":
            block = inner.get("content_block", {})
            if block.get("type") == "tool_use":
                name, payload = block.get("name"), ""
        elif kind == "content_block_delta" and name:
            payload += inner.get("delta", {}).get("partial_json", "")
        elif kind == "content_block_stop" and name:
            if name != "Skill":
                return f"<{name}>"
            try:
                return json.loads(payload).get("skill", "<unparsed>")
            except json.JSONDecodeError:
                return "<unparsed>"
        elif kind == "message_stop":
            return "<prose>"
    return "<prose>"


def install_skills(project, skill_paths):
    """Put the real skills where Claude will find them for this project."""
    target = Path(project) / ".claude" / "skills"
    target.mkdir(parents=True, exist_ok=True)
    for path in skill_paths:
        source = Path(path).resolve()
        if not (source / "SKILL.md").is_file():
            raise SystemExit(f"Not a skill directory: {source}")
        destination = target / source.name
        shutil.rmtree(destination, ignore_errors=True)
        shutil.copytree(source, destination)
    return sorted(p.name for p in target.iterdir() if p.is_dir())


def main():
    parser = argparse.ArgumentParser(
        description="Measure which skill a set of queries triggers.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("Usage:", 1)[1] if "Usage:" in __doc__ else None)
    parser.add_argument("--eval-set", required=True,
                        help="JSON array of either {query, should_trigger} or {query, expect}")
    parser.add_argument("--project", required=True,
                        help="scratch project to run in; should resemble what the queries describe")
    parser.add_argument("--skill", action="append", required=True, dest="skills",
                        help="skill directory to install; repeat for every competing skill")
    parser.add_argument("--expect", default=None,
                        help="skill a should_trigger query should reach; omit when the eval set "
                             "names an expected skill per case")
    parser.add_argument("--runs", type=int, default=2, help="runs per query (default 2)")
    parser.add_argument("--workers", type=int, default=8, help="parallel workers (default 8)")
    parser.add_argument("--timeout", type=int, default=180, help="seconds per run (default 180)")
    parser.add_argument("--model", default=None, help="model id passed to claude -p")
    parser.add_argument("--json-out", default=None, help="write raw observations here")
    args = parser.parse_args()

    cases = json.loads(Path(args.eval_set).read_text(encoding="utf-8"))
    # Two eval-set shapes. The original asks one yes/no question about one skill;
    # the routing shape asks which of several skills should win, which is the only
    # way to see a sibling stealing a query.
    per_case = any("expect" in case for case in cases)
    if not per_case and not args.expect:
        raise SystemExit("--expect is required unless every case names its own expected skill")
    installed = install_skills(args.project, args.skills)
    print(f"skills installed in {args.project}: {', '.join(installed)}\n")

    observed = {index: [] for index in range(len(cases))}
    work = [(index, run) for index in range(len(cases)) for run in range(args.runs)]
    with futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        pending = {pool.submit(first_tool, cases[index]["query"], args.project,
                               args.model, args.timeout): index
                   for index, _ in work}
        for future in futures.as_completed(pending):
            index = pending[future]
            try:
                observed[index].append(future.result())
            except Exception as error:                      # noqa: BLE001
                observed[index].append(f"<error:{type(error).__name__}>")

    broken = {i: [r for r in v if r.startswith("<call-failed") or r.startswith("<timeout") or r.startswith("<error")]
              for i, v in observed.items()}
    broken_count = sum(len(v) for v in broken.values())
    if broken_count:
        print(f"WARNING: {broken_count} of {len(work)} runs never reached the model "
              f"(rate limit, timeout, or a failed call). Scores below are not "
              f"trustworthy -- re-run when calls succeed.\n")

    def expected(case):
        return case.get("expect") if per_case else (args.expect if case["should_trigger"] else None)

    passed_positive = passed_negative = 0
    groups = sorted({expected(c) for c in cases if expected(c)}) if per_case else [args.expect]
    for wanted in groups + [None]:
        print(f"=== {'should reach ' + wanted if wanted else 'should reach none of them'} ===")
        for index, case in enumerate(cases):
            if expected(case) != wanted:
                continue
            results = observed[index]
            if wanted:
                hits = sum(1 for r in results if r == wanted)
                good = hits >= len(results) / 2
                passed_positive += good
            else:
                watched = groups if per_case else [args.expect]
                hits = sum(1 for r in results if r in watched)
                good = hits < len(results) / 2
                passed_negative += good
            print(f"  {'ok  ' if good else 'FAIL'} {hits}/{len(results)} "
                  f"{','.join(sorted(set(results))):34.34} {case['query'][:52]}")
        print()

    total = len(cases)
    positives = sum(1 for c in cases if expected(c))
    print(f"routed correctly {passed_positive}/{positives}   "
          f"correctly not routed {passed_negative}/{total - positives}   "
          f"total {passed_positive + passed_negative}/{total}")

    if args.json_out:
        Path(args.json_out).write_text(
            json.dumps({"cases": cases, "observed": {str(k): v for k, v in observed.items()}},
                       ensure_ascii=False, indent=1), encoding="utf-8")

    if broken_count:
        return 2
    return 0 if passed_positive + passed_negative == total else 1


if __name__ == "__main__":
    sys.exit(main())
