# Routing eval — the three frontend skills

With `ddd-angular`, `ddd-vue` and `ddd-react` installed side by side, does each query reach the right one?

This is the risk the per-skill eval sets cannot see. The three share a domain, a vocabulary and most of a structure; a query about organising a frontend by bounded context could plausibly reach any of them. A set that only asks "does `ddd-angular` trigger, yes or no" scores a perfect result while `ddd-vue` quietly answers half the Angular questions.

## Running it

```bash
python3 evals/run-trigger-eval.py \
  --eval-set evals/frontend-routing/routing-eval.json \
  --project /path/to/a/scratch/frontend-project \
  --skill skills/ddd-angular --skill skills/ddd-vue --skill skills/ddd-react \
  --skill skills/ddd-spring-boot --skill skills/ddd-playbook \
  --runs 2
```

Install **all five**, not just the three under test. A Spring Boot query reaching `ddd-spring-boot` is the correct outcome, and you cannot observe it if the skill is absent.

Run it from a **framework-neutral project**. Hosting it in an Angular workspace would tell Claude the answer before the description does.

Exit codes: `0` everything routed correctly, `1` something routed wrong, `2` some run never reached the model — a rate limit, a timeout, or a failed call. **Code 2 means the numbers do not count.** A call that never happened is not evidence that a skill chose not to trigger; conflating the two is what makes a broken eval look like a broken description.

## The set

21 queries. Five each that should reach Angular, Vue and React, and six that should reach none of the three.

The negatives are the interesting half, and they are a kind this family had not tested before: **the same DDD question asked for a different stack.** "How do I organise my app by bounded contexts, with layers" is the query that could go anywhere — so the set includes it for Svelte, where the right answer is that none of the three should claim it.

The other negatives cover a Spring Boot aggregate (should reach `ddd-spring-boot`), an EventStorming session (should reach `ddd-playbook`), bundle size, a test-runner migration, and REST endpoint design.

## Last result

**Partial, 2026-08-31.** The run hit the session limit part-way through: 13 of 42 calls never reached the model, so it exited `2` and the headline score does not count.

What the 29 calls that *did* reach the model show, and it is the answer to the question this set exists to ask:

- **Not one query routed to the wrong sibling.** 26 frontend routings — 10 to `ddd-angular`, 8 to `ddd-vue`, 8 to `ddd-react` — every one of them correct.
- The Spring Boot query reached `ddd-spring-boot`, and the EventStorming query reached `ddd-playbook`. The two non-frontend siblings won their own queries rather than losing them to a frontend skill.

A clean run is still owed. Every failure was a non-answer — a `<call-failed>`, a `<timeout>`, or Claude reaching for `Bash` to look around first — and none was a wrong routing, so the expectation is that a full run confirms this. Until it does, treat the result as a strong signal rather than a measurement.
