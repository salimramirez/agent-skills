# Adding a resource, end to end

The order to write the files in, the scaffold that writes them for a new context, and the checklist before calling it done.

## Start from the scaffold when the context is new

```bash
python3 "$SKILL/scripts/new-context.py" --context MenuManagement --entity MenuItem
```

It writes the whole context — 21 files over the four layers — for one CRUD aggregate with a single `Name` property, and prints the two edits it cannot make:

```csharp
using QuickBite.Platform.MenuManagement.Infrastructure.DependencyInjection;
builder.Services.AddMenuManagementContext();      // in Program.cs, under "// Bounded contexts"
```

```bash
dotnet ef migrations add AddMenuManagement
```

After those, the context runs: `/api/v1/menu-items` creates, reads, updates and deletes, answers 404, 409 and 400 with problem details, and is protected if the IAM context is in. The generator derives every spelling from the two names — `MenuItem`, `MenuItems`, `menuItem`, `menu-items`, "a menu item" — and refuses names that would not compile: a context named like its entity, an entity named like a type every file already sees (`Task`, `Path`, `Result`…), or one whose camelCase is a C# keyword (`Event`). `--plural People` fixes an irregular plural.

Then **model the real aggregate**: the `Name` is a placeholder. Replace it with the attributes the domain experts talk about, and walk outward in the order below.

## The order to write the files in

From the inside out — each layer only uses what the previous one wrote:

| # | File | What goes in it |
| --- | --- | --- |
| 1 | `Domain/Model/ValueObjects/` | every concept with a rule and no identity — `Money`, `OrderStatus` — and the references to other aggregates — `CustomerId`. See `value-objects.md`. |
| 2 | `Domain/Model/Entities/` | the entities inside the aggregate, if any — `OrderLine`. |
| 3 | `Domain/Model/Commands/`, `Queries/` | one record per use case. See `application-services.md`. |
| 4 | `Domain/Model/Aggregates/` | the root: constructors from its values and from the create command, the private EF Core constructor, a method per rule. See `aggregates.md`. |
| 5 | `Domain/Model/Events/` | an event per transition something must react to. See `domain-events.md`. |
| 6 | `Domain/Repositories/` | the port: the finders the use cases need, taking value objects. |
| 7 | `Application/CommandServices/`, `QueryServices/` | the interfaces, one `Handle` per command or query. |
| 8 | `Application/Internal/…` | the implementations; the event handlers; an `External<Context>Service` per other context asked. |
| 9 | `Infrastructure/Persistence/EntityFrameworkCore/` | an `IEntityTypeConfiguration` per type, using the domain's constants; the repository. See `persistence.md`. |
| 10 | `Infrastructure/DependencyInjection/` | every repository, service, handler, outbound service and facade, registered in `Add<Context>Context`. |
| 11 | `Interfaces/Rest/Resources/`, `Transform/` | the request and response records, one assembler per direction. See `rest.md`. |
| 12 | `Interfaces/Rest/` | the controller: CRUD actions, transitions as `POST`s to plural nouns, filters as query parameters. See `state-transitions.md`. |
| 13 | `Program.cs`, `Migrations/` | the context's line in `Program.cs`; `dotnet ef migrations add`. |

Adding a second aggregate to an existing context is the same list without the scaffold, and without step 13's line in `Program.cs` — the context is registered already; its `Add<Context>Context` grows instead.

## Checklist

**Domain**
- [ ] Every property has a private setter; every change is a method that checks what must be true and throws `InvalidValueException` (a value) or `BusinessRuleViolationException` (a state).
- [ ] Every length and amount the mapping limits has a constant in the domain, checked in the constructor.
- [ ] Value objects are `sealed record`s with get-only properties and a constructor that validates and normalizes.
- [ ] Another aggregate is referenced by a typed id, never a navigation property.
- [ ] Transitions record their events after the state changed.

**Application**
- [ ] Commands return `Result<T>` or `Result`; queries return `T?` or a collection.
- [ ] Each handler loads, answers `NotFound`, acts, calls `CompleteAsync`, returns `Success` — and checks no business rule itself.
- [ ] A unique rule is checked by the service *and* backed by a unique index.

**Infrastructure**
- [ ] The entities inside the aggregate are `HasMany(...).WithOne()...IsRequired()` with cascade and `AutoInclude()`.
- [ ] Value objects: one value → `HasConversion`; several → `ComplexProperty`; a collection → an explicit converter with a value comparer.
- [ ] Everything new is registered in `Add<Context>Context` — in development a missing registration stops the start-up, which is the moment to catch it.
- [ ] `dotnet ef migrations add …` was run, and the migration was read.

**Interfaces**
- [ ] Plural controller at `api/v1/[controller]`, route parameters named `{xxxId:int}`, no `[Produces]`.
- [ ] Commands answered through `ToActionResult`; a query's `null` answered with `Problem(…, 404)`.
- [ ] Every action has a `<summary>`, a `<response>` per status, and the matching `[ProducesResponseType]`.
- [ ] No domain type in a resource or an action's signature.

**Running it**
- [ ] `dotnet build` gives no warnings — a public member without an XML comment is one.
- [ ] The start-up log has no `fail:` line about pending model changes.
- [ ] Each endpoint answered the codes its comments promise: the success, 400 for a blank value, 404 for a missing id, 409 for a broken rule — and 401 without a token, if the IAM context is in.
