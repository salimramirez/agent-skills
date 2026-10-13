# Routing eval — the three backend skills

With `ddd-spring-boot`, `ddd-fastapi` and `ddd-aspnet-core` installed side by side, does each query reach the right one — and does a backend question for a stack none of them covers reach none?

The backend skills share the core block, the vocabulary and most of the structure, and their descriptions differ mainly in the stack they name. The risk this set measures is the one a per-skill set cannot see: `ddd-aspnet-core` answering a Spring Boot question, or any of the three claiming a NestJS or Go one because "aggregates and layers" matched.

## Running it

```bash
python3 evals/run-trigger-eval.py \
  --eval-set evals/backend-routing/routing-eval.json \
  --project /path/to/a/scratch/neutral-project \
  --skill skills/ddd-aspnet-core --skill skills/ddd-spring-boot --skill skills/ddd-fastapi \
  --skill skills/ddd-playbook \
  --runs 2
```

Install all four: an EventStorming query reaching `ddd-playbook` is the correct outcome, and it cannot be observed if the skill is absent. Run it from a **stack-neutral project** — a .NET, Java or Python project would tell Claude the answer before the description does.

Exit codes as for the frontend set: `0` everything routed correctly, `1` something routed wrong, `2` some run never reached the model. **Code 2 means the numbers do not count.**

## The set

15 queries. Five that should reach `ddd-aspnet-core`, two each for `ddd-spring-boot` and `ddd-fastapi`, one for `ddd-playbook`, and five that should reach none:

- **the same DDD question for an uncovered stack** — NestJS, Go — where the right answer is that no backend skill claims it;
- **.NET questions with no domain modeling in them** — logging configuration, Blazor component state, a failing SQL Server migration — which `ddd-aspnet-core`'s `Not for …` clause says it does not take.

## Last result

**Not run yet.** The set was written with `ddd-aspnet-core` 1.0.0; running it costs about thirty model calls, and it is owed together with the `evals/ddd-angular/` set and a timeout-free run of `evals/frontend-routing/`.
