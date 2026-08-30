# Repositories, identity, and persistence

Repositories for aggregate roots, and the identity and persistence trade-offs behind them.

Give each aggregate root a repository — collection-like access to whole aggregates by their root, one per aggregate root. The simplest and most common approach in Spring is to define a Spring Data repository **in `infrastructure`** and let command and query services depend on it directly:

```java
// infrastructure/persistence/jpa/repositories
@Repository
public interface OrderRepository extends JpaRepository<Order, OrderId> {
    Optional<Order> findByCustomerId(CustomerId customerId);   // finders named in the ubiquitous language
}
```

`JpaRepository` gives you `save`, `findById`, and the rest; add finders named in the domain's language, and keep them about whole aggregates (not arbitrary inner entities). The trade-off is that the application layer now depends on an infrastructure type.

> **Alternative — a domain port.** To keep the domain *and* the application free of any dependency on the persistence framework, declare a plain repository interface in the `domain` layer as a **port**, implemented in `infrastructure`:
>
> ```java
> // domain/repositories — no framework leakage
> public interface OrderRepository {
>     Optional<Order> findById(OrderId id);
>     Order save(Order order);
> }
>
> // infrastructure — Spring Data satisfies the port
> interface OrderJpaRepository extends JpaRepository<Order, OrderId>, OrderRepository { }
> ```
>
> This is the purer, hexagonal-style choice; the cost is a little more indirection. Prefer it when isolating the domain from infrastructure matters for the project.

## Identity and persistence: choices and trade-offs

Three honest choices, each with a primary recommendation and a common alternative:

- **Identity — typed id vs. surrogate base class.** *Primary:* a typed id value object (`OrderId` as `@EmbeddedId`) keeps identity a domain concept and type-safe. *Alternative (very common):* the shared `AuditableAbstractAggregateRoot` base class with a generated `Long` surrogate id and audit timestamps (see `shared-kernel.md`); even then, keep typed id value objects for *cross-aggregate references* (`CustomerId`, not bare `Long`).
- **Repository — infrastructure-only vs. domain port.** Covered above: the default here is a Spring Data repository in `infrastructure` that services use directly (simplest, and the common convention); declare a domain port instead when you want the persistence dependency kept out of the domain.
- **Domain purity — JPA in the domain.** Annotating domain entities with JPA (as shown) is idiomatic and fine for most projects; the cost is a soft dependency on the persistence framework. For maximum isolation, keep the domain as plain Java and map to a separate persistence model in `infrastructure`, at the cost of mapping boilerplate.

Whichever you pick, hold the non-negotiables: business rules and invariants stay in the domain model, and the domain never depends on `interfaces` or `application`.
