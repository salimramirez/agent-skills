# Value objects

Expressing value objects and typed identifiers as JPA embeddables.

Model value objects as **immutable** types. A Java `record` is the natural fit — immutable, with value equality for free. Validate in the compact constructor so invalid states cannot be built. Map them as JPA embeddables (`@Embeddable` on the type; `@Embedded` where used).

```java
public record Money(BigDecimal amount, Currency currency) {
    public Money {
        if (amount == null || currency == null) throw new IllegalArgumentException("money requires amount and currency");
        if (amount.signum() < 0) throw new IllegalArgumentException("amount cannot be negative");
    }
    public Money add(Money other) {
        if (!currency.equals(other.currency)) throw new IllegalArgumentException("cannot add different currencies");
        return new Money(amount.add(other.amount), currency);
    }
}
```

Use value objects for **typed identifiers** too, so a reference to another aggregate stays type-safe and meaningful:

```java
@Embeddable
public record CustomerId(Long value) {
    public CustomerId {
        if (value == null || value < 1) throw new IllegalArgumentException("invalid customer id");
    }
}
```

JPA needs a no-argument constructor to hydrate an embeddable, so give value objects a default constructor alongside the validating one — a record can declare its compact canonical constructor *and* a no-arg one that supplies a default:

```java
@Embeddable
public record EmailAddress(@Email String address) {
    public EmailAddress() { this(null); }   // required by JPA
}
```

A record fits most value objects, but use an `@Embeddable` **class** when the value object has to map a JPA association or collection — a record can't, because its components are final. A `LearningPath` that owns a `@OneToMany` list of items is such a case: a class with behavior, owned wholly by its aggregate and reached only through it.
