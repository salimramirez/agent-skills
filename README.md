# Agent Skills

A collection of [Agent Skills](https://agentskills.io) — portable, model-agnostic instructions that teach an AI agent how to perform a task. Works with skills-aware agents such as Claude Code, Cursor, and GitHub Copilot.

## Skills

Three skills for Domain-Driven Design: one for modeling a domain, and one per stack for writing the code. Each uses progressive disclosure — a lean `SKILL.md` with the decision rules, plus reference files loaded only when the task needs them.

They share a core block of DDD design rules, duplicated on purpose so that **every one of them works on its own**. Install only the stack skill you need, or the playbook alongside it when the work is modeling rather than coding.

### `ddd-playbook` — modeling a domain

The design rules and the modeling work, stack-agnostic.

- **Strategic design** — ubiquitous language, subdomains, bounded contexts, context mapping, domain storytelling.
- **Modeling process** — EventStorming, Domain Message Flow Modelling, the Bounded Context Canvas, the context-map pattern catalog.
- **Tactical patterns** — entities, value objects, aggregates (with aggregate-boundary design), domain events, domain services, repositories, factories, and CQRS.

### `ddd-spring-boot` — writing it in Spring Boot / Java

The four-layer package structure, the shared kernel, value objects and typed ids as JPA embeddables, aggregate roots as JPA entities with real behavior, commands and queries as records with their command and query services, repositories, domain events, anti-corruption layers, the REST interface with resources and assemblers, and domain exceptions.

Works on Spring Boot 3 and 4 with Java 17+.

### `ddd-angular` — writing it in Angular

Bounded contexts as feature folders with four layers inside each, the shared kernel, entities and commands, DTOs and assemblers as an anti-corruption layer against the backend API, signal stores, views and components, per-context lazy routing, reactive forms, and cross-cutting concerns placed in the context that owns the rule.

It is deliberately **opinionated**: for every decision it names one convention — the file-to-class naming table, where URLs come from, how a store publishes state, what a JSDoc block is for — and says what that convention buys, rather than listing options. It also ships code: `assets/shared-kernel/` holds the seven base classes to copy as they are, and `scripts/new-context.py` scaffolds a whole bounded context from a context and an entity name.

It is honest about what DDD means on a client: the backend is the system of record and owns the invariants, so this is DDD-inspired organization rather than a second place to enforce business rules. The idioms are standalone components, signals, and `inject()`, and they hold across current Angular versions.

## Installation

Install a skill into your agent with the [`skills` CLI](https://github.com/vercel-labs/skills):

```bash
npx skills add salimramirez/agent-skills --skill ddd-playbook
```

```bash
npx skills add salimramirez/agent-skills --skill ddd-spring-boot
```

```bash
npx skills add salimramirez/agent-skills --skill ddd-angular
```

## Versioning

Each skill is versioned and tagged independently, as `<skill>-vX.Y.Z`. The release notes for a tag are that skill's changelog.

> **Upgrading from `ddd-playbook` 1.x?** The Spring Boot and Angular implementation references no longer ship inside `ddd-playbook`. They are now the `ddd-spring-boot` and `ddd-angular` skills — install the one you need alongside it.

## License

[MIT](LICENSE)
