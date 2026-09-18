# Repositories and persistence

One Spring Data repository per aggregate root, in `infrastructure`, with finders in the ubiquitous language.

```java
@Repository
public interface OrderRepository extends JpaRepository<Order, Long> {
    Optional<Order> findByCode(OrderCode code);
    List<Order> findAllByCustomerId(CustomerId customerId);
}
```

That is the whole file. `JpaRepository` supplies `save`, `findById`, `findAll`, `existsById` and `deleteById`; the interface adds only what the domain asks for, named as the domain would say it.

## Finders take value objects

A finder's parameter is the value object, not what is inside it: `findByCode(OrderCode code)`, `findAllByCustomerId(CustomerId customerId)`, `existsByEmailAddress(EmailAddress emailAddress)`. Spring Data matches the embedded record's columns by itself. This keeps the query service from unwrapping anything, and it means a caller cannot pass the wrong `Long` — a `MenuItemId` does not fit where a `CustomerId` goes.

The uniqueness pair every create/update needs:

```java
    boolean existsByName(String name);
    boolean existsByNameAndIdIsNot(String name, Long id);
```

The second one is what an update uses, so that renaming an aggregate to its own current name is not a collision.

Derived query names are checked when the application starts: a method whose name does not match any property fails the boot, not the first request. That is the test.

## Where the repository sits, and why

The repository interface lives in `infrastructure/persistence/jpa/repositories`, and the command and query services in `application` depend on it directly. That is a deliberate shortcut: it saves an interface in the domain plus an adapter class per aggregate, at the price of the application layer naming a Spring Data type.

The purer arrangement declares the port in the domain and lets Spring Data satisfy it:

```java
// domain/repositories
public interface OrderRepository {
    Optional<Order> findById(Long id);
    Order save(Order order);
}

// infrastructure/persistence/jpa/repositories
public interface OrderJpaRepository extends JpaRepository<Order, Long>, OrderRepository {
}
```

Take it when the domain must compile with no Spring on the classpath, or when a second persistence mechanism is a real prospect. Otherwise the shortcut is the convention, and the non-negotiables hold either way: the repository is about whole aggregates, the domain classes never call it, and there is one per aggregate root — no `OrderLineRepository`, because a line is saved through its order.

## Tables

`spring.jpa.hibernate.ddl-auto=update` creates the tables from the entities on first run, using the naming strategy from the shared kernel:

```
Order          → orders          (id, created_at, updated_at, code, currency, customer_id, status)
OrderLine      → order_lines     (id, created_at, updated_at, order_id, menu_item_id, quantity, unit_price_amount, unit_price_currency)
Customer       → customers       (…, first_name, last_name, email_address)
```

Every embedded record becomes columns of the owner's table, named after the record's components — which is why a component is called `customerId` and not `value`. `@Column(unique = true)` on a field asks the database to guarantee a uniqueness as well; whatever `update` does not create for a table that already exists goes in a migration once the schema matters. Until then the `existsBy…` guards in the command services are the uniqueness rule.
