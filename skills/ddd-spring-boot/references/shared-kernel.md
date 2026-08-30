# The shared kernel

Base classes and types that every bounded context in the application shares.

A `shared` package holds the small **shared kernel** every context reuses — base classes for the domain model, common REST resources, and cross-cutting technical configuration (a snake-case table-naming strategy, OpenAPI setup, database migrations). Keep it small and stable; it must never hold business rules — those belong to a bounded context.

When a project chooses the surrogate-id + auditing approach (a common alternative — see `persistence.md`), a base class carries that decision. `AuditableAbstractAggregateRoot` is the base for **aggregate roots**: it extends Spring Data's `AbstractAggregateRoot` (so it can register domain events) and adds a generated surrogate id plus created/updated timestamps.

```java
// shared/domain/model/aggregates
@Getter
@MappedSuperclass
@EntityListeners(AuditingEntityListener.class)
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
}
```

A sibling `AuditableModel` gives the same surrogate id and timestamps to **entities inside an aggregate** that aren't the root (without the event-registration base). For the timestamps to populate, enable auditing with `@EnableJpaAuditing` on a configuration class.

The shared kernel is also the home for a generic response resource reused across contexts — for example a message returned after a delete:

```java
// shared/interfaces/rest/resources
public record MessageResource(String message) { }
```
