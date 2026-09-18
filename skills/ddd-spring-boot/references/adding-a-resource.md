# Adding a resource, end to end

The order to write the files in, and what to check when you are done.

Use this when the task is "add X to the platform" — a new bounded context, or a new aggregate inside one. Work outward from the domain: each step depends only on the ones before it, so nothing is written twice.

## Before writing anything

1. **Name it in the ubiquitous language.** Ask what the domain experts call it. `Order`, not `Purchase` and not `Transaction`. Every class, package, path and column comes from this answer.
2. **Decide which bounded context it belongs to.** A new context if it has its own model and language; otherwise a new aggregate inside an existing one. When in doubt, ask whether it would share a command service with what is already there.
3. **Decide what is inside the aggregate and what is only referenced.** Lines are inside an order (`OrderLine`, reached through it); the customer is not (`CustomerId`, reached through the ACL). Getting this wrong is the expensive mistake — everything else is renaming.

## Scaffold, then model

For a new context, generate the tree instead of typing it:

```bash
SKILL=.claude/skills/ddd-spring-boot       # wherever this skill was installed
python3 "$SKILL/scripts/new-context.py" --context ordering --entity Order
```

Run it from the root of the project. It reads the base package from the `@SpringBootApplication` class, writes the twenty files of a CRUD aggregate under `src/main/java/<base package>/ordering/`, and tells you what it could not do. The naming — PascalCase and camelCase, singular and plural, class, package and path — is the error-prone part, and it is the part that is now done.

Install the shared kernel first if `<base package>/shared/` is not there yet: `python3 "$SKILL/scripts/install.py" shared-kernel`. See `shared-kernel.md`.

## The files, in the order to write them

| # | File | What to write |
| --- | --- | --- |
| 1 | `domain/model/valueobjects/*` | Every concept with a rule and no identity: `Money`, `OrderCode`, `OrderStatus`; the references to other aggregates: `CustomerId`. See `value-objects.md`. |
| 2 | `domain/model/entities/*` | The parts of the aggregate that have an identity of their own: `OrderLine`. |
| 3 | `domain/model/aggregates/Order.java` | The real attributes, the constructor from the command, the **behavior**: `place()`, `cancel()`, `addLine(...)`. Every rule about an order is a method here. See `aggregates.md`. |
| 4 | `domain/model/commands/*`, `queries/*` | One record per thing that can be asked, validating itself. |
| 5 | `domain/model/events/*` | One class per fact other code must react to. |
| 6 | `domain/exceptions/*` | `OrderNotFoundException` and whatever else has a name. |
| 7 | `domain/services/Order{Command,Query}Service.java` | The `handle` overloads, one per command and query, with the return types from the table in `application-services.md`. |
| 8 | `infrastructure/persistence/jpa/repositories/OrderRepository.java` | The finders the services need, taking value objects. See `persistence.md`. |
| 9 | `application/internal/outboundservices/acl/External*Service.java` | Only if this context needs another one. See `anti-corruption-layer.md`. |
| 10 | `application/internal/{commandservices,queryservices}/*Impl.java` | Check, load, act, save. No rules. |
| 11 | `application/internal/eventhandlers/*` | One handler per event, calling services. See `domain-events.md`. |
| 12 | `interfaces/rest/resources/*` | Records of primitives; requests validate presence. |
| 13 | `interfaces/rest/transform/*` | One assembler per direction. |
| 14 | `interfaces/rest/OrdersController.java`, nested controllers | Thin. Re-query after a write. See `rest.md`, `state-transitions.md`. |
| 15 | `interfaces/rest/OrderingExceptionHandler.java` | The context's exceptions to status codes. See `exceptions.md`. |

Then, outside the context, only if it is a provider for others: `interfaces/acl/<Context>ContextFacade` and `application/acl/<Context>ContextFacadeImpl`.

Start the application after step 8 already: with `ddl-auto=update` the tables appear, and a mistake in a mapping or a finder name fails the boot right there, before there is any controller to debug through.

## Checklist

Before calling it done:

- [ ] Every name reads in the ubiquitous language — no `Data`, `Info`, `Manager`, `Helper`, `Util`.
- [ ] The aggregate has **behavior**, and no `@Setter`. Any `if` on its state in a service belongs in one of its methods.
- [ ] Other aggregates are held as `XxxId` value objects, never as `@ManyToOne` entities.
- [ ] Every command and query validates in its compact constructor; every enum field carries `@Enumerated(EnumType.STRING)`.
- [ ] The service interfaces are in `domain/services`; the implementations in `application/internal`; the repository in `infrastructure`; nothing in `domain` imports Spring Web or a repository.
- [ ] Repository finders take value objects, and the uniqueness pair (`existsByX`, `existsByXAndIdIsNot`) exists for anything that must be unique.
- [ ] The controller is plural, at `/api/v1/<plural>`, names its two services and nothing else, re-queries after a write, returns `200 []` for an empty collection and a `MessageResource` for a transition.
- [ ] No domain type in a resource; no wire type in a command. The assemblers do all of the conversion.
- [ ] Domain exceptions carry no HTTP; the context's advice maps them; `IllegalArgumentException` and `IllegalStateException` are left to the shared one.
- [ ] The other context is reached only through `External<Context>Service`, and `grep External` lists every cross-context dependency.
- [ ] Every type has Javadoc with a title and a `@summary`; implementations carry `{@inheritDoc}`.
- [ ] The application starts, the tables in the log have the expected names, and Swagger UI shows the new tag.
