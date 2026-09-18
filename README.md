# Agent Skills

A collection of [Agent Skills](https://agentskills.io) — portable, model-agnostic instructions that teach an AI agent how to perform a task. Works with skills-aware agents such as Claude Code, Cursor, and GitHub Copilot.

## Skills

Six skills for Domain-Driven Design: one for modeling a domain, and one per stack for writing the code. Each uses progressive disclosure — a lean `SKILL.md` with the decision rules, plus reference files loaded only when the task needs them.

They share a core block of DDD design rules, duplicated on purpose so that **every one of them works on its own**. Install only the stack skill you need, or the playbook alongside it when the work is modeling rather than coding.

### `ddd-playbook` — modeling a domain

The design rules and the modeling work, stack-agnostic.

- **Strategic design** — ubiquitous language, subdomains, bounded contexts, context mapping, domain storytelling.
- **Modeling process** — EventStorming, Domain Message Flow Modelling, the Bounded Context Canvas, the context-map pattern catalog.
- **Tactical patterns** — entities, value objects, aggregates (with aggregate-boundary design), domain events, domain services, repositories, factories, and CQRS.

### `ddd-spring-boot` — writing it in Spring Boot / Java

The four-layer package structure, the shared kernel, value objects and typed ids as JPA embeddables, aggregate roots as JPA entities with real behavior, commands and queries as records with their command and query services, repositories, domain events, anti-corruption layers, the REST interface with resources and assemblers, and domain exceptions.

Works on Spring Boot 3 and 4 with Java 17+.

### `ddd-fastapi` — writing it in FastAPI / Python

Bounded contexts as top-level packages with four layers and one module per kind in each, aggregates as plain classes with behavior, value objects as frozen dataclasses, application services that own the transaction through a unit-of-work port, repository ports with async SQLAlchemy adapters mapping to separate ORM models, Alembic migrations, domain events, anti-corruption layers, and the REST interface with Pydantic schemas and a clean OpenAPI description.

Like `ddd-spring-boot` it is an **opinionated** house style, lighter where Python leaves room for taste, and it ships code: `scripts/install.py` writes a new project with the shared kernel or an IAM context with sign-up, sign-in and JWT, and `scripts/new-context.py` scaffolds a whole bounded context. Every framework claim in it was checked by running the code — that a blocking call inside `async def` stalls every request, that an async session cannot refresh after a commit or lazy-load a relationship, that a commit in a dependency's teardown runs after the client already has its response.

FastAPI 0.122+ on Python 3.12+, SQLAlchemy 2 async over PostgreSQL, Alembic, Pydantic v2.

### `ddd-angular` — writing it in Angular

Bounded contexts as feature folders with four layers inside each, the shared kernel, entities and commands, DTOs and assemblers as an anti-corruption layer against the backend API, signal stores, views and components, per-context lazy routing, reactive forms, and cross-cutting concerns placed in the context that owns the rule.

It is deliberately **opinionated**: for every decision it names one convention — the file-to-class naming table, where URLs come from, how a store publishes state, what a JSDoc block is for — and says what that convention buys, rather than listing options. It also ships code: `assets/shared-kernel/` holds the seven base classes to copy as they are, and `scripts/new-context.py` scaffolds a whole bounded context from a context and an entity name.

It is honest about what DDD means on a client: the backend is the system of record and owns the invariants, so this is DDD-inspired organization rather than a second place to enforce business rules. The idioms are standalone components, signals, and `inject()`, and they hold across current Angular versions.

### `ddd-vue` — writing it in Vue

Bounded contexts as feature folders with four layers inside each, a two-class shared kernel over axios, entity and command classes that carry behaviour, assemblers as an anti-corruption layer, Pinia stores, views and components, named lazy routes per context, and cross-cutting concerns placed in the context that owns the rule.

Written in **JavaScript with JSDoc**, because that is what the convention uses — and with no compiler in the picture, the JSDoc block is where the shape of every class and store is written down. Like `ddd-angular` it ships code: `assets/shared-kernel/` holds the two base classes to copy as they are, and `scripts/new-context.py` scaffolds a whole bounded context from a context and an entity name.

It is honest about what DDD means on a client: the backend is the system of record and owns the invariants, so this is DDD-inspired organization rather than a second place to enforce business rules. Vue 3 with `<script setup>`, Pinia, Vue Router and axios.

### `ddd-react` — writing it in React

Bounded contexts as feature folders with four layers inside each, a two-class shared kernel over axios, immutable entity and command classes that carry behaviour, assemblers as an anti-corruption layer, Zustand stores, routed views and reusable components, path builders per context, and route protection placed in the context that owns the rule.

**React with TypeScript, React Router, Zustand and axios**, for a client-rendered SPA. Like its siblings it ships code: `assets/shared-kernel/` holds the two base classes to copy as they are, and `scripts/new-context.py` scaffolds a whole bounded context. A `javascript.md` reference covers what changes without a compiler — including the runtime schema check that has to replace the prop validation React 19 removed.

Unlike `ddd-angular` and `ddd-vue`, which mirror real codebases, this one **derives** the same four-layer model onto React and says so. Every framework-specific claim in it was checked by building and running a real app: that mutating an entity renders nothing while replacing it works, that a loader returning `redirect()` protects a route, and that a raw resource passed where an entity belongs fails to compile precisely because the entity has behaviour.

## Installation

Install a skill into your agent with the [`skills` CLI](https://github.com/vercel-labs/skills):

```bash
npx skills add salimramirez/agent-skills --skill ddd-playbook
```

```bash
npx skills add salimramirez/agent-skills --skill ddd-spring-boot
```

```bash
npx skills add salimramirez/agent-skills --skill ddd-fastapi
```

```bash
npx skills add salimramirez/agent-skills --skill ddd-angular
```

```bash
npx skills add salimramirez/agent-skills --skill ddd-vue
```

```bash
npx skills add salimramirez/agent-skills --skill ddd-react
```

## Versioning

Each skill is versioned and tagged independently, as `<skill>-vX.Y.Z`. The release notes for a tag are that skill's changelog.

> **Upgrading from `ddd-playbook` 1.x?** The Spring Boot and Angular implementation references no longer ship inside `ddd-playbook`. They are now the `ddd-spring-boot` and `ddd-angular` skills — install the one you need alongside it.

## License

[MIT](LICENSE)
