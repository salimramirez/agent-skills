# Trigger evals — `ddd-angular`

Does the skill get consulted when it should, and stay out of the way when it should not?

A skill's `description` is the whole trigger mechanism: Claude sees the name and description in its skill list and decides from that alone. These twenty queries measure whether that decision comes out right — especially against the two sibling skills, which share most of the vocabulary.

## Running it

```bash
python3 evals/ddd-angular/run-trigger-eval.py \
  --eval-set evals/ddd-angular/trigger-eval.json \
  --project /path/to/a/scratch/angular-app \
  --skill skills/ddd-angular \
  --skill skills/ddd-spring-boot \
  --skill skills/ddd-playbook \
  --expect ddd-angular --runs 2
```

Exit codes: `0` all cases passed, `1` some case failed, `2` some run never reached the model — a rate limit, a timeout, or a failed call. Code `2` matters: a call that never happened must not be read as "the skill chose not to trigger". That confusion is what makes a broken trigger eval look like a broken description.

Results are not committed — they go stale the moment a description or a model changes, and a saved number invites trusting a measurement nobody re-ran.

## Two setup rules that decide whether the result means anything

**Run it in a project that resembles what the queries describe.** These queries are about an Angular app. Measured in an empty directory, Claude's first move is to look around with `Bash`, and you learn nothing about the description.

**Install every skill that competes for the same vocabulary**, not just the one under test. The failure worth catching is a sibling winning: `ddd-spring-boot` answering a frontend question, or `ddd-angular` answering an aggregate-mapping one. Testing a skill alone cannot see that.

## Why not the skill-creator's `run_eval.py`

That script does not install a skill. It writes a slash command to `.claude/commands/` and counts a trigger only when the first tool call names *that command*. Three ways it reports a meaningless zero, all of them hit while writing this eval:

1. Without the target project in front of Claude, the first tool call is a `Bash` to look around — scored as no-trigger before the skill was considered at all.
2. Where the real skill is installed, Claude triggers the real skill while the script watches for its temporary command name. Every case fails.
3. Where the real skill is absent, the temporary command is not consulted the way a skill is — Claude answers in prose.

## The eval set

Ten queries that should trigger, ten that should not. The ones that earn their keep are the near-misses — they share vocabulary with the skill but need something else:

| Near-miss | What it shares |
| --- | --- |
| An `Order` aggregate with `@EmbeddedId` in Spring Boot | "aggregate", "value object" — belongs to `ddd-spring-boot` |
| Preparing an EventStorming session with the business | "bounded contexts" — belongs to `ddd-playbook` |
| Change detection errors after an Angular upgrade | Angular, explicitly out of scope |
| An Angular Material theme not applying | styling, explicitly out of scope |
| Reorganising a **React** app by domain | the same idea, the wrong framework |
| Lazy loading to cut a 2.2 MB bundle | touches routing, but for performance |
| Chaining two NgRx effects | state, but framework plumbing |
| Designing `/orders/{id}/cancel` REST endpoints | the DTO boundary is adjacent, but this is backend |
| Migrating Karma to Jest, and `HttpTestingController` specs | testing, not covered |

Queries are written the way someone actually types: lowercase, casual, with file names and a little backstory. Deliberately in Spanish while the description is in English — that mismatch is the real situation here, and worth measuring rather than assuming away.

## Last result

**20/20** against `ddd-angular` 1.1.4 on 2026-08-30 — ten positives triggering it, ten negatives not, at two runs per query. The Spring Boot near-miss went to `ddd-spring-boot` both times, so routing between the siblings holds. That measurement was taken with this script's predecessor, which used the same detection; the first re-run with this file hit a session limit, so a green run of this exact script is still owed.

One thing this run surfaced outside its own scope: the EventStorming query was answered in prose rather than reaching `ddd-playbook`. It passes here (it did not trigger `ddd-angular`), but it hints that `ddd-playbook` may under-trigger on purely strategic work. That needs its own eval set.
