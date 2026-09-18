# The shared kernel

The six classes every bounded context shares, and how they get into a project.

The `shared` package is the one place code lives that belongs to no bounded context. It holds base classes for the model, the technical configuration every context relies on, and the one resource every controller may return. It never holds a business rule: the moment a class under `shared/` knows what an `Order` is, it belongs in `ordering`.

## Install it, do not retype it

```bash
SKILL=.claude/skills/ddd-spring-boot       # wherever this skill was installed
python3 "$SKILL/scripts/install.py" shared-kernel
```

Run it from the root of the project. It finds the base package by reading the class annotated with `@SpringBootApplication` under `src/main/java`, writes the six files under `<base package>/shared/`, and then prints the four edits it cannot make: the dependencies, the properties, `@EnableJpaAuditing`, and the reminder above. `project-setup.md` shows every one of them in place.

## What each file is

```
shared/
├── domain/model/aggregates/AuditableAbstractAggregateRoot.java
├── domain/model/entities/AuditableModel.java
├── infrastructure/documentation/openapi/configuration/OpenApiConfiguration.java
├── infrastructure/persistence/jpa/configuration/strategy/SnakeCaseWithPluralizedTablePhysicalNamingStrategy.java
└── interfaces/rest/
    ├── GlobalExceptionHandler.java
    └── resources/MessageResource.java
```

**`AuditableAbstractAggregateRoot<T>`** — the base of every aggregate root. It extends Spring Data's `AbstractAggregateRoot`, which is what lets an aggregate register domain events that get published when it is saved, and it adds the three columns every aggregate table has:

```java
@Getter
@EntityListeners(AuditingEntityListener.class)
@MappedSuperclass
public class AuditableAbstractAggregateRoot<T extends AbstractAggregateRoot<T>> extends AbstractAggregateRoot<T> {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @CreatedDate
    @Column(nullable = false, updatable = false)
    private Date createdAt;

    @LastModifiedDate
    @Column(nullable = false)
    private Date updatedAt;

    public void addDomainEvent(Object event) {
        super.registerEvent(event);
    }
}
```

The `Long id` is the persistence identity, and it is deliberately a plain `Long`: the database generates it, the REST path carries it (`/api/v1/orders/{orderId}`), and a query names it (`GetOrderByIdQuery(Long orderId)`). A *reference* to an aggregate from another one is a value object around that `Long` — `CustomerId` — never the bare number; and an aggregate that needs an identity the outside can hold, before it is ever saved, adds one of its own (`OrderCode`). Both are in `value-objects.md`; the alternative of making the identity itself a value object is in `aggregates.md`.

**`AuditableModel`** — the same id and timestamps for an entity that lives *inside* an aggregate (`OrderLine`), without the event registration: only the root raises events.

**`SnakeCaseWithPluralizedTablePhysicalNamingStrategy`** — a Hibernate `PhysicalNamingStrategy` that maps `OrderLine` to `order_lines` and `menuItemId` to `menu_item_id`, so entities stay in Java conventions and tables in SQL ones without a single `@Table` or `@Column(name = …)`. Registered through the `spring.jpa.hibernate.naming.physical-strategy` property; needs the `pluralize` dependency.

**`OpenApiConfiguration`** — one `OpenAPI` bean with the title, description and version read from the properties, and the `bearerAuth` security scheme, so Swagger UI shows an "Authorize" button that sends `Authorization: Bearer …`. Without the IAM context the scheme is inert; with it, it is how you try a protected endpoint from the browser.

**`GlobalExceptionHandler`** — the `@RestControllerAdvice` for failures that are not specific to any context: an `IllegalArgumentException` becomes a 400, an `IllegalStateException` a 409, a Bean Validation failure a 400. Each context maps its *own* exceptions in its own advice — see `exceptions.md`.

**`MessageResource`** — `record MessageResource(String message)`, returned by endpoints that have nothing else to say: a state transition, a delete.

## What is not here

No `BaseEntity` with `equals`/`hashCode`, no generic repository, no `BaseController`, no `BaseAssembler`. Every one of those was considered and left out because it would make the contexts share behavior rather than plumbing, and shared behavior is where contexts start leaking into each other.
