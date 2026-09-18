# Value objects

Records as value objects, the three kinds of identifier, and the one case that needs a class.

A value object has no identity: two `Money(12.50, PEN)` are the same money. A Java `record` gives that for free — immutable, `equals` by value — and `@Embeddable` lets JPA store its components as columns of the owning table. Validate in the compact constructor, so an invalid value cannot exist:

```java
@Embeddable
public record Money(BigDecimal amount, Currency currency) {
    public Money {
        if (amount == null || currency == null) {
            throw new IllegalArgumentException("Money requires an amount and a currency");
        }
        if (amount.signum() < 0) {
            throw new IllegalArgumentException("Amount cannot be negative");
        }
    }

    public static Money zero(Currency currency) {
        return new Money(BigDecimal.ZERO, currency);
    }

    public Money add(Money other) {
        if (!currency.equals(other.currency)) {
            throw new IllegalArgumentException("Cannot add %s to %s".formatted(other.currency, currency));
        }
        return new Money(amount.add(other.amount), currency);
    }

    public Money times(int quantity) {
        return new Money(amount.multiply(BigDecimal.valueOf(quantity)), currency);
    }
}
```

Every operation returns a new instance. That is the whole discipline: a value object is never modified, it is replaced — `this.performance = this.performance.incrementCompletedOrders()`.

Hibernate 6 hydrates a record through its canonical constructor, so **no no-arg constructor is needed** — and none of the records above has one. Add a no-arg constructor only when it means something, as `OrderCode` does below.

## Three kinds of identifier

The persistence identity of an aggregate is the `Long id` inherited from the base class (see `shared-kernel.md`). Around it, three value objects appear, and they are not interchangeable:

**A reference to another aggregate** wraps that aggregate's `Long`. Ordering never holds a `Customer`; it holds a `CustomerId`, and the type says which aggregate the number points at:

```java
@Embeddable
public record CustomerId(Long customerId) {
    public CustomerId {
        if (customerId == null || customerId < 1) {
            throw new IllegalArgumentException("Customer id cannot be null or less than 1");
        }
    }
}
```

Name the component after the concept (`customerId`, not `value`): it becomes the column name, and `customer_id` reads better than `value` in a query. A `Long` inside a record like this is fine because the number already exists — the Customers context generated it.

**A natural identity the outside can hold** is generated in the domain, so the aggregate has it before it is ever saved. A UUID does that job:

```java
@Embeddable
public record OrderCode(String code) {
    public OrderCode() {
        this(UUID.randomUUID().toString());
    }

    public OrderCode {
        if (code == null || code.isBlank()) {
            throw new IllegalArgumentException("Order code cannot be null or blank");
        }
    }
}
```

The aggregate calls `new OrderCode()` in its constructor; a repository finder takes it directly (`Optional<Order> findByCode(OrderCode code)`), and the resource exposes it as a string. It sits *alongside* the surrogate `Long`, not instead of it.

**A typed primary key** — `@EmbeddedId` around a record — is the third option, and `aggregates.md` explains what it costs. The short version: JPA does not generate values for an embedded id, so it only works with an identity the domain generates itself.

## Enumerations

An enum is a value object with a closed set of values. Map it by name, always:

```java
public enum OrderStatus {
    DRAFT,
    PLACED,
    CANCELLED
}
```

```java
    @Enumerated(EnumType.STRING)
    private OrderStatus status;
```

Without `@Enumerated(EnumType.STRING)` JPA stores the ordinal — a `TINYINT` holding `0`, `1`, `2` — and the day someone inserts a new constant in the middle of the enum, every stored row changes meaning. Names cost a few bytes and survive that.

## Overriding column names

When a record is embedded twice in one entity, or its component name would collide, `@AttributeOverrides` on the field renames the columns without touching the value object:

```java
    @Embedded
    @AttributeOverrides({
            @AttributeOverride(name = "amount", column = @Column(name = "unit_price_amount")),
            @AttributeOverride(name = "currency", column = @Column(name = "unit_price_currency"))})
    private Money unitPrice;
```

The same on `Customer` maps `EmailAddress.address` to `email_address`, so the column says what it holds.

## When a value object must be a class

A record's components are final, and JPA cannot map an association onto a final field. So a value object that *owns a collection of entities* is a class — still `@Embeddable`, still without identity, still reached only through its aggregate:

```java
@Embeddable
public class OrderLines {
    @OneToMany(mappedBy = "order", cascade = CascadeType.ALL)
    private List<OrderLine> items;

    public OrderLines() {
        this.items = new ArrayList<>();
    }

    public void add(Order order, MenuItemId menuItemId, int quantity, Money unitPrice) {
        items.add(new OrderLine(order, menuItemId, quantity, unitPrice));
    }

    public boolean isEmpty() {
        return items.isEmpty();
    }

    public List<OrderLine> asList() {
        return List.copyOf(items);
    }

    public Money total(Currency currency) {
        return items.stream().map(OrderLine::subtotal).reduce(Money.zero(currency), Money::add);
    }
}
```

This is where the rules about the lines *as a whole* go — the total, whether there are any, later a maximum — instead of piling up on the aggregate root. Start the list as `new ArrayList<>()`: `List.of()` is immutable, and the first `add` on a fresh aggregate throws `UnsupportedOperationException`.

A record component may also carry a Bean Validation annotation (`@Email String address`), but whether anyone checks it depends on where the record happens to be validated. The compact constructor runs on every `new`, with no one to configure. Keep the rule there and treat the annotation as documentation.
