# Changelog

All notable changes to the **ddd-playbook** skill are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this skill adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.1] - 2026-06-23

### Added

- Bundle the MIT `LICENSE` inside the skill directory so the license travels with `npx skills add` installs (the repo-root `LICENSE` isn't copied alongside the skill).

## [1.0.0] - 2026-06-23

First public release.

### Added

- Core `SKILL.md`: the prime directive (model the domain, and protect it), the four-layer architecture, tactical decision rules, strategic-design essentials, CQRS, and a "how to approach a DDD task" routine — with routing to the reference files via progressive disclosure.
- `references/strategic-design.md` — ubiquitous language, subdomains, bounded contexts, context mapping, and domain storytelling.
- `references/modeling-process.md` — EventStorming, Domain Message Flow Modelling, the Bounded Context Canvas, and the context-map pattern catalog.
- `references/tactical-patterns.md` — entities, value objects, aggregates (with aggregate-boundary design), domain events, domain services, repositories, factories, and CQRS.
- `references/spring-boot.md` — idiomatic DDD in Spring Boot / Java: the four layers, the shared kernel, value objects and typed ids, aggregates, command and query services, repositories, domain events, anti-corruption layers, the REST interface, and domain exceptions. Compatible with Spring Boot 3 and 4 on Java 17+ (including 21 and the 25 LTS).
- `references/angular.md` — DDD adapted for an Angular frontend: bounded-context feature folders, the shared kernel, the domain layer, infrastructure (DTOs, assemblers, endpoints, the context API), signal stores, the presentation layer, routing, and reactive forms. Idioms apply unchanged to Angular 20, 21, and 22.

[1.0.1]: https://github.com/salimramirez/agent-skills/releases/tag/ddd-playbook-v1.0.1
[1.0.0]: https://github.com/salimramirez/agent-skills/releases/tag/ddd-playbook-v1.0.0
