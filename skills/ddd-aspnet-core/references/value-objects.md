# Value objects

Records that validate, their limits, references to other aggregates, money, enums — and how each one is stored.

## A record with a constructor that refuses

A value object is a `sealed record` whose constructor checks the value and stores it normalized. Equality comes from the record: two `EmailAddress` with the same address are equal.

```csharp
public sealed record EmailAddress
{
    public const int MaxLength = 254;

    public EmailAddress(string address)
    {
        var normalized = address.Trim().ToLowerInvariant();
        if (normalized.Length > MaxLength || !MailAddress.TryCreate(normalized, out var parsed) ||
            parsed.Address != normalized)
            throw new InvalidValueException($"'{address}' is not an email address.");
        Address = normalized;
    }

    public string Address { get; }
}
```

- **The constructor is the only way in**, and it throws `InvalidValueException` — a 400 — for a value the domain cannot accept. Once an `EmailAddress` exists, it is a valid one; no service checks it again.
- **Properties are `{ get; }`, never `init`.** A positional record (`record Money(decimal Amount, …)`) validates nothing, and a property with `init` lets `money with { Amount = -5 }` copy the object and skip the constructor — measured: the copy came out negative. With a get-only property that line does not compile (CS0200).
- **It normalizes what it stores.** `Ana@Example.com ` and `ana@example.com` are one address, so they are one value, and a unique index sees them as one in every database — MySQL's default collation ignores case and PostgreSQL's does not (see `project-setup.md`).
- **Its operations return new values**: `Money.Add` returns a new `Money`; nothing changes an existing one.

## Limits are rules of the domain

Every column has a size, and every size is a rule: a dish name has at most 100 characters, an amount at most eight digits and the cents. The rule is a constant on the type that enforces it, and the mapping reads the same constant:

```csharp
public const int DishNameMaxLength = 100;                     // OrderLine
if (dishName.Trim().Length > DishNameMaxLength)
    throw new InvalidValueException($"A dish name has at most {DishNameMaxLength} characters.");

builder.Property(line => line.DishName).HasMaxLength(OrderLine.DishNameMaxLength);   // OrderLineConfiguration
```

A column narrower than what the domain accepts turns a client's mistake into a server error: with a `HasMaxLength(100)` and no rule behind it, a 101-character name reaches MySQL, which in its default strict mode answers "Data too long", and the client gets a 500 (measured). The same for an amount above what `decimal(10,2)` holds ("Out of range value"). With the constant, the domain refuses it first and the client gets a 400 that says why.

## Money

```csharp
public sealed record Money
{
    public const decimal MaxAmount = 99_999_999.99m;

    public Money(decimal amount, string currency)
    {
        if (amount < 0) throw new InvalidValueException("An amount of money cannot be negative.");
        if (amount > MaxAmount) throw new InvalidValueException($"An amount of money cannot exceed {MaxAmount}.");
        if (currency.Length != 3 || !currency.All(char.IsAsciiLetter))
            throw new InvalidValueException($"'{currency}' is not a currency code.");
        Amount = decimal.Round(amount, 2);
        Currency = currency.ToUpperInvariant();
    }

    public decimal Amount { get; }
    public string Currency { get; }

    public static Money Zero(string currency) { return new Money(0, currency); }

    public Money Add(Money other)
    {
        if (other.Currency != Currency) throw new InvalidValueException($"Cannot add {other.Currency} to {Currency}.");
        return new Money(Amount + other.Amount, Currency);
    }

    public Money Multiply(int factor) { return new Money(Amount * factor, Currency); }
}
```

Money is `decimal`, never `double`: binary floating point cannot hold 0.10 exactly, and a total off by a cent is a defect. The JSON stays exact on the way in — System.Text.Json reads `12345678901234567.89` into a `decimal` digit for digit (measured) — and `MaxAmount` is what `decimal(10,2)` holds, so the domain refuses what the column could not store.

## References to other aggregates

An `Order` refers to its customer by identity, and the identity has a type of its own:

```csharp
public sealed record CustomerId
{
    public CustomerId(int value)
    {
        if (value <= 0) throw new InvalidValueException($"{value} is not a customer identity.");
        Value = value;
    }

    public int Value { get; }
}
```

A `CustomerId` cannot be passed where an `OrderId` or a quantity is expected, and `0` or `-4` never become one. It lives in the context that *holds* the reference (`Ordering/Domain/Model/ValueObjects`), not in the context of the customer: it is Ordering's way of naming someone it does not own. Whether that customer exists is asked through the anti-corruption layer — see `anti-corruption-layer.md`.

The aggregate's *own* identity stays a database-generated `int` from `AuditableAggregateRoot`. A typed key for the root itself is possible too — see `aggregates.md`.

## Enums

An enum is a value object with a closed set of values: `OrderStatus { Draft, Placed, Cancelled }`. No prefix on the name, a `<summary>` on every member, and the shared convention stores it by name (`varchar` with `Placed` in it), so reordering or inserting a member never changes what a stored row means. A resource sends it with `ToString()`.

## How each one is mapped

| The value object | Mapped with | Columns | Why |
| --- | --- | --- | --- |
| one value — `EmailAddress`, `CustomerId` | `HasConversion` | one: `email`, `customer_id` | it can carry an index and be compared in a query |
| several values — `PersonName`, `Money` | `ComplexProperty` | one per property, prefixed: `name_first_name`, `unit_price_amount` | value semantics, no hidden key |
| an enum — `OrderStatus` | the shared convention | one, by name | — |

```csharp
// CustomerConfiguration
builder.ComplexProperty(customer => customer.Name, name =>
{
    name.Property(n => n.FirstName).HasMaxLength(PersonName.MaxLength).IsRequired();
    name.Property(n => n.LastName).HasMaxLength(PersonName.MaxLength).IsRequired();
});

builder.Property(customer => customer.Email)
    .HasConversion(email => email.Address, address => new EmailAddress(address))
    .HasMaxLength(EmailAddress.MaxLength)
    .IsRequired();
builder.HasIndex(customer => customer.Email).IsUnique();
```

A converted value object reads back through its constructor, so a stored value that no longer passes the rules fails loudly on load instead of spreading — measured: a row edited to hold `not-an-email` answered 500, because EF Core wraps the constructor's exception in its own ("An error occurred while reading a database value for property 'Customer.Email'"), and a bad row is the server's problem, not the client's. And a finder takes the value object, not a string: `customer.Email == email` translates to a plain comparison of the column.

**Owned types (`OwnsOne`, `OwnsMany`) are not the house style.** Many projects map value objects as owned entity types; they work, but an owned type cannot hold a complex property — `OwnedNavigationBuilder` has no `ComplexProperty` (measured) — so `Money` could not live inside an owned `OrderLine`. Complex properties and converters cover every value object here, and the entities inside an aggregate are mapped as entities (see `persistence.md`).

**A collection of values needs a converter too.** EF Core can map a `List<T>` of primitives on its own, but the MySQL provider has no support for it: left to the convention, it stored the list's `ToString()` — `System.Collections.Generic.List`1[…]` — and failed to read it back (measured). The IAM context stores a user's roles with an explicit converter for that reason — see `persistence.md`.
