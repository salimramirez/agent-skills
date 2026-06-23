# Agent Skills

A collection of [Agent Skills](https://agentskills.io) — portable, model-agnostic instructions that teach an AI agent how to perform a task. Works with skills-aware agents such as Claude Code, Cursor, and GitHub Copilot.

## Skills

### `ddd` — Domain-Driven Design

Teaches an agent to follow Domain-Driven Design correctly when modeling a domain or writing backend code — so you don't have to re-explain DDD each time. It uses progressive disclosure: a lean core with the decision rules, plus reference files loaded on demand.

- **Strategic design** — ubiquitous language, subdomains, bounded contexts, context mapping, domain storytelling.
- **Modeling process** — EventStorming, Domain Message Flow Modelling, the Bounded Context Canvas, the context-map pattern catalog.
- **Tactical patterns** — entities, value objects, aggregates (with aggregate-boundary design), domain events, domain services, repositories, factories, and CQRS.
- **Implementation** — idiomatic DDD in Spring Boot: the four-layer architecture, command/query services, repositories, domain events, anti-corruption layers, domain exceptions, and more.

The concepts are stack-agnostic; **Spring Boot / Java** is the first implementation reference, with more stacks to come.

## Installation

Install a skill into your agent with the [`skills` CLI](https://github.com/vercel-labs/skills):

```bash
npx skills add salimramirez/agent-skills --skill ddd
```

## License

[MIT](LICENSE)
