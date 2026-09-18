# Anti-corruption layer

Reaching another bounded context through its facade, and translating what comes back into this context's own model.

Ordering needs to know which customer an order is for. It must not import `customers.domain`: the day Customers renames a field, Ordering would break, and the day Ordering reads a `Customer`'s email to make a decision, the two models have merged. The ACL is three classes — two on the provider's side, one on the consumer's — and only primitives cross between them.

## The provider exposes a facade

An interface in `customers/interfaces/acl`. Its methods take and return primitives, and `0` means "no such thing":

```java
public interface CustomersContextFacade {
    Long createCustomer(String firstName, String lastName, String email);
    Long fetchCustomerIdByEmail(String email);
}
```

Its implementation in `customers/application/acl` is written with the context's own command and query services — it is one more caller of them, with no privileged access:

```java
@Service
public class CustomersContextFacadeImpl implements CustomersContextFacade {
    private final CustomerCommandService customerCommandService;
    private final CustomerQueryService customerQueryService;

    public CustomersContextFacadeImpl(CustomerCommandService customerCommandService, CustomerQueryService customerQueryService) {
        this.customerCommandService = customerCommandService;
        this.customerQueryService = customerQueryService;
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public Long createCustomer(String firstName, String lastName, String email) {
        var createCustomerCommand = new CreateCustomerCommand(firstName, lastName, email);
        var customerId = customerCommandService.handle(createCustomerCommand);
        return customerId == null ? 0L : customerId;
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public Long fetchCustomerIdByEmail(String email) {
        var getCustomerByEmailQuery = new GetCustomerByEmailQuery(new EmailAddress(email));
        var customer = customerQueryService.handle(getCustomerByEmailQuery);
        return customer.isEmpty() ? 0L : customer.get().getId();
    }
}
```

The interface sits in `interfaces` because it is an inbound port — another context drives Customers through it, the way a controller does over HTTP. The implementation sits in `application` because it orchestrates, the way a command service does.

## The consumer wraps it

One class in `ordering/application/internal/outboundservices/acl`, and it is the **only** class in Ordering that knows Customers exists:

```java
@Service
public class ExternalCustomerService {
    private final CustomersContextFacade customersContextFacade;

    public ExternalCustomerService(CustomersContextFacade customersContextFacade) {
        this.customersContextFacade = customersContextFacade;
    }

    public Optional<CustomerId> fetchCustomerByEmail(String email) {
        var customerId = customersContextFacade.fetchCustomerIdByEmail(email);
        return customerId == 0L ? Optional.empty() : Optional.of(new CustomerId(customerId));
    }
}
```

This is where the translation happens: the facade's `0L` becomes `Optional.empty()`, and its `Long` becomes Ordering's own `CustomerId`. The command service then speaks only Ordering's language:

```java
    @Override
    public Long handle(CreateOrderCommand command) {
        var customerId = externalCustomerService.fetchCustomerByEmail(command.customerEmail())
                .orElseThrow(() -> new CustomerNotFoundException(command.customerEmail()));
        var order = new Order(customerId, command);
        orderRepository.save(order);
        return order.getId();
    }
```

`CustomerNotFoundException` is an Ordering exception, in `ordering/domain/exceptions`, even though the customer lives elsewhere: from where Ordering stands, "there is no such customer" is a failure of *placing an order*.

## The rules, and what they protect

- **Primitives across the boundary.** `Long`, `String`, `boolean`. Never a `Customer`, never an `EmailAddress` from the other side — each context keeps the freedom to change its own types.
- **`0L` for "not found"**, translated to `Optional` on the consumer's side. The facade stays simple to implement from any language or transport; the consumer gets a type that forces the caller to handle absence.
- **Consumer names the service after the other context, with `External` in front**: `ExternalCustomerService`, `ExternalCatalogService`. Grep for `External` and you have the map of every cross-context dependency.
- **One facade per provider context**, not one per aggregate. It describes what the context offers, not its internals.

When the other context becomes a separate service, only `ExternalCustomerService` changes — it calls HTTP instead of a bean — and the facade interface becomes that service's API contract. Nothing in `ordering/domain` notices.
