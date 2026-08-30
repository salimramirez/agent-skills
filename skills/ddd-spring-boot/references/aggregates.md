# Aggregate root and entities

Writing the aggregate root and its entities as JPA entities with real behavior.

The aggregate root is a JPA `@Entity`. Give it real **behavior** (not just getters/setters), enforce invariants inside it, and **reference other aggregates by their typed id value object** — never map a `@ManyToOne` to another aggregate root. Extend Spring Data's `AbstractAggregateRoot` so the aggregate can register domain events (or a shared `AuditableAbstractAggregateRoot` that also adds a surrogate id and audit timestamps — see `shared-kernel.md`). A useful idiom is a constructor (or static factory) that builds the aggregate straight from a command.

```java
@Getter   // Lombok: generates getId(), getCustomerId(), getStatus(), getLines()
@Entity
public class Order extends AbstractAggregateRoot<Order> {

    @EmbeddedId
    private OrderId id;

    @Embedded
    private CustomerId customerId;        // another aggregate, referenced by typed id only

    @Enumerated(EnumType.STRING)
    private OrderStatus status;

    @ElementCollection
    private List<OrderLine> lines = new ArrayList<>();

    protected Order() { }                 // required by JPA

    public Order(PlaceOrderCommand command) {
        if (command.lines().isEmpty()) throw new IllegalArgumentException("an order needs at least one line");
        this.id = OrderId.newId();
        this.customerId = command.customerId();
        this.lines = new ArrayList<>(command.lines());
        this.status = OrderStatus.PLACED;
        registerEvent(new OrderPlaced(this, id, customerId));   // raise a domain event
    }

    public void cancel() {
        if (status == OrderStatus.SHIPPED) throw new IllegalStateException("a shipped order cannot be cancelled");
        status = OrderStatus.CANCELLED;
        registerEvent(new OrderCancelled(this, id));
    }

    public Money total() {
        return lines.stream().map(OrderLine::subtotal).reduce(Money.zero(), Money::add);
    }
}
```

Entities and value objects *inside* the aggregate (here `OrderLine`) are reached only through the root — that is what lets the root guarantee the aggregate's invariants. The Lombok `@Getter` exposes the fields for read access (the assemblers use them); all behavior stays in methods like `cancel()` and `total()`.
