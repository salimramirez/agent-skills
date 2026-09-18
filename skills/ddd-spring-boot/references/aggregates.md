# Aggregates and entities

The aggregate root, the entities inside it, and the rules that keep it consistent.

## The root

An aggregate root is a JPA `@Entity` that extends `AuditableAbstractAggregateRoot`, takes its creating command as a constructor argument, and exposes **behavior** — methods named after what the business does to it — instead of setters:

```java
@Entity
public class Order extends AuditableAbstractAggregateRoot<Order> {
    @Getter
    @Embedded
    private OrderCode code;

    @Getter
    @Embedded
    private CustomerId customerId;

    @Getter
    private Currency currency;

    @Getter
    @Enumerated(EnumType.STRING)
    private OrderStatus status;

    @Embedded
    private OrderLines lines;

    public Order() {
        // Required by JPA
    }

    public Order(CustomerId customerId, CreateOrderCommand command) {
        this.code = new OrderCode();
        this.customerId = customerId;
        this.currency = command.currency();
        this.status = OrderStatus.DRAFT;
        this.lines = new OrderLines();
    }

    public void addLine(MenuItemId menuItemId, int quantity, Money unitPrice) {
        if (!isDraft()) throw new IllegalStateException("Lines can only be added to a draft order");
        if (!unitPrice.currency().equals(currency))
            throw new IllegalArgumentException("Order is priced in %s, not %s".formatted(currency, unitPrice.currency()));
        this.lines.add(this, menuItemId, quantity, unitPrice);
    }

    public void place() {
        if (!isDraft()) throw new IllegalStateException("Only a draft order can be placed");
        if (lines.isEmpty()) throw new IllegalStateException("An order needs at least one line to be placed");
        this.status = OrderStatus.PLACED;
        this.addDomainEvent(new OrderPlacedEvent(this, this.getId(), this.customerId));
    }

    public void cancel() {
        if (this.status != OrderStatus.PLACED) throw new IllegalStateException("Only a placed order can be cancelled");
        this.status = OrderStatus.CANCELLED;
        this.addDomainEvent(new OrderCancelledEvent(this, this.getId()));
    }

    public boolean isDraft() {
        return this.status == OrderStatus.DRAFT;
    }

    public List<OrderLine> getLines() {
        return this.lines.asList();
    }

    public Money total() {
        return this.lines.total(currency);
    }
}
```

Read the two kinds of `throw`: an `IllegalArgumentException` means the *input* is wrong (a price in the wrong currency); an `IllegalStateException` means the input is fine but the aggregate's *current state* forbids the action (placing an order twice). The shared exception advice turns the first into a 400 and the second into a 409, so a controller never has to check either.

What the root guarantees, and how:

- **Every change goes through a method.** There is no `setStatus`. `place()` is the only way to reach `PLACED`, and it checks what must be true first. `@Getter` goes on the class when every field is read as it is (the generated template, `OrderLine`), and on the fields when one of them is exposed through a method instead (`lines`, read through `getLines()`); it never comes with `@Setter`.
- **Other aggregates are referenced by id.** `CustomerId`, never `Customer`. A `@ManyToOne` to another aggregate root would let Ordering load, and change, a Customer inside an Order's transaction.
- **A command in, an aggregate out.** `Order(CustomerId, CreateOrderCommand)` is the factory. The command service resolves what the command cannot carry (here, the customer's id from their email) and hands both over.
- **The no-arg constructor is public and empty**, with the comment that says why. JPA needs it; nothing else calls it.
- **A derived value is a method** (`total()`), not a field kept in sync. What a getter returns is computed from the lines every time, so it cannot be stale.

`updateInformation(...)` is the one "update" method an aggregate may have — for the attributes with no rule between them, such as a menu item's name and description. It returns `this` so the service can `save(entity.updateInformation(...))` in one line.

## Entities inside the aggregate

An entity that belongs to an aggregate — an `OrderLine` — extends `AuditableModel`, holds a `@ManyToOne` back to its root, and is created only by the root:

```java
@Getter
@Entity
public class OrderLine extends AuditableModel {
    @ManyToOne
    @JoinColumn(name = "order_id")
    private Order order;

    @Embedded
    private MenuItemId menuItemId;

    private int quantity;

    @Embedded
    @AttributeOverrides({
            @AttributeOverride(name = "amount", column = @Column(name = "unit_price_amount")),
            @AttributeOverride(name = "currency", column = @Column(name = "unit_price_currency"))})
    private Money unitPrice;

    public OrderLine() {
        // Required by JPA
    }

    public OrderLine(Order order, MenuItemId menuItemId, int quantity, Money unitPrice) {
        if (quantity < 1) throw new IllegalArgumentException("Quantity cannot be less than 1");
        this.order = order;
        this.menuItemId = menuItemId;
        this.quantity = quantity;
        this.unitPrice = unitPrice;
    }

    public Money subtotal() {
        return unitPrice.times(quantity);
    }
}
```

The `@ManyToOne` **inside** an aggregate is the one place that annotation belongs: it points from a part to its whole. The collection side lives in `OrderLines` (`value-objects.md`), an embeddable that owns the `@OneToMany(mappedBy = "order", cascade = CascadeType.ALL)` and the rules about the lines as a group. Cascade is what makes `orderRepository.save(order)` persist the new line; nothing ever saves an `OrderLine` on its own, and there is no `OrderLineRepository`.

A line records the price *at the time it was added*. That is not denormalization — it is the rule that a placed order does not change when the menu does.

## When the identity itself should be a value object

The base class gives every aggregate a generated `Long`. The alternative is a typed primary key:

```java
@Entity
public class Order {
    @EmbeddedId
    private OrderId id;      // record OrderId(UUID value), created with OrderId.newId()
```

It buys a signature that cannot confuse an order id with a customer id, and a `findById(OrderId)` that reads like the domain. It costs the base class (and with it the audit columns, unless you re-add them), `Long` everywhere at the edge (the path variable, the query, the ACL facade all turn into `UUID`/`String`), and — the part that decides it — **JPA does not generate values for an `@EmbeddedId`**: a `@GeneratedValue` on it is ignored, the insert goes out with a `NULL` key, and the database rejects it. So the domain must generate the identity itself, which means UUIDs.

The house style takes the `Long` from the base class, wraps *references* in typed records, and gives an aggregate a UUID-based code only when the outside needs to hold one. Choose the typed key when a context has no surrogate-id plumbing to protect and its identities are naturally UUIDs; then choose it for the whole context, not one aggregate.
