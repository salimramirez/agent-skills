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

**2026-08-31, 42 runs.** 38 reached the model; 4 timed out, which trips exit code `2`, so the headline `18/21` is not the number to quote. The routings themselves are unambiguous.

Of the 38 that reached the model, 29 named a skill and **exactly two were wrong — both of them the same query**:

| | |
| --- | --- |
| No sibling stole another's query | 26 frontend routings, every one correct |
| `ddd-spring-boot` and `ddd-playbook` | each won their own query |
| **`ddd-vue` claimed a Svelte query** | 2 of 2 here, and 3 of 3 in a follow-up probe |

The remaining nine non-routings were Claude reaching for `Bash` to look around first (7) or answering in prose (2). Both are harness characteristics rather than description failures: a bare scratch project gives the model nothing to read, so exploring first is reasonable behaviour.

### The one finding

**"tengo una app en svelte y quiero organizarla por dominio con capas"** goes to `ddd-vue`, consistently — five out of five successful runs across two sessions. Not variance.

Whether that is a defect is a judgment call. The four-layer structure genuinely transfers to Svelte, so the answer is not useless; but the skill is Vue-specific and will hand that reader Pinia, `<script setup>` and `defineProps`. The three descriptions are structurally identical — same opening, same `Not for …` clause — so nothing in the wording explains why Vue wins it rather than React or Angular.

Left as recorded rather than patched. Tightening a description is a change to the trigger mechanism, and it should not be made without the budget to measure the result.

### Still owed

A run with no timeouts, and the per-skill set at `evals/ddd-angular/`. Both attempts at the latter have now been cut short by the session limit; it is not a skill problem, and exit code `2` has correctly refused to publish numbers each time.
