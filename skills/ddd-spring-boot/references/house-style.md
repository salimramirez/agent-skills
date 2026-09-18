# House style

The conventions that make this code recognizable, beyond where the files sit.

## Javadoc on every type

Every class, record, interface and enum opens with a Javadoc block, and so does every public method that is not an override. The shape is always the same: a title line, then `@summary` with the prose when there is more to say than the title, then the tags.

```java
/**
 * Order aggregate root
 * @summary
 * This aggregate root represents an order a customer places with a restaurant. It starts as a
 * draft, collects lines, and is placed once. Every rule about what an order may do lives here.
 * @see OrderLine
 * @since 1.0
 */
```

On a record, document the components with `@param`, and say the rule, not the type:

```java
/**
 * Command to add a line to an order
 * @param orderId the order id.
 *                Cannot be null or less than 1
 * @param quantity how many.
 *                 Cannot be less than 1
 */
```

An implementation of an interface method carries `{@inheritDoc}` — the contract is documented once, on the interface in `domain/services` — and adds a paragraph only when the implementation does something the contract does not say, such as which failure it turns into which exception:

```java
    /**
     * {@inheritDoc}
     */
    @Override
    public Long handle(CreateOrderCommand command) {
```

`@summary` is not a standard Javadoc tag; the tooling ignores it and the reader does not. Write the comment for someone who does not know the domain: `@param orderId the order id` is noise, `@param orderId the order to place. Cannot be null or less than 1` is not.

## Locals mirror the type

A local variable is named after its class, in camelCase, and declared with `var`. Reading a controller method should read like the flow it performs:

```java
        var createOrderCommand = CreateOrderCommandFromResourceAssembler.toCommandFromResource(resource);
        var orderId = orderCommandService.handle(createOrderCommand);
        var getOrderByIdQuery = new GetOrderByIdQuery(orderId);
        var order = orderQueryService.handle(getOrderByIdQuery);
        if (order.isEmpty()) return ResponseEntity.notFound().build();
        var orderEntity = order.get();
        var orderResource = OrderResourceFromEntityAssembler.toResourceFromEntity(orderEntity);
```

An `Optional` is named after what it may hold (`order`), and the unwrapped value gets the `Entity` suffix (`orderEntity`) so the two never get confused.

## Constructor injection, and nothing else

Dependencies arrive through the constructor, as `private final` fields, with no `@Autowired` and no Lombok `@RequiredArgsConstructor`. The constructor is written out, in full, every time:

```java
@Service
public class OrderCommandServiceImpl implements OrderCommandService {
    private final OrderRepository orderRepository;
    private final ExternalCustomerService externalCustomerService;

    public OrderCommandServiceImpl(OrderRepository orderRepository, ExternalCustomerService externalCustomerService) {
        this.orderRepository = orderRepository;
        this.externalCustomerService = externalCustomerService;
    }
```

In the model, Lombok is for one thing: `@Getter`, on an aggregate, an entity or an event, so the assemblers can read them. Never `@Setter` — a setter is a rule that nobody wrote down — and never `@Data` on an entity, which drags in an `equals` over every field of a thing that has an identity.

## Strings, streams, and messages

- Format with `"…%s…".formatted(value)`, not `String.format` and not concatenation.
- Map a list with `.stream().map(OrderResourceFromEntityAssembler::toResourceFromEntity).toList()`.
- Validation messages name the field as it is spelled in code: `"orderId cannot be null or less than 1"`, `"name cannot be null or blank"`. Not-found messages name the concept and the key: `"Order with id %s not found"`.
- A one-line `if` that throws may go without braces; anything else gets them.

## What a controller looks like

The annotations, in this order, every time:

```java
@RestController
@RequestMapping(value = "/api/v1/orders", produces = APPLICATION_JSON_VALUE)
@Tag(name = "Orders", description = "Available Order Endpoints")
public class OrdersController {
```

`APPLICATION_JSON_VALUE` is a static import from `MediaType`. On each endpoint: the mapping first, then `@Operation(summary, description)`, then `@ApiResponses`. Path variables are named (`@GetMapping("/{orderId}")`, with the leading slash), and the method is named after what it does: `createOrder`, `getOrderById`, `getAllOrders`, `placeOrder`.

## Keep the layers honest

Each of these is a smell with a name:

- **A repository in a controller.** The controller talks to the two services and nothing else. If it needs data, there is a query for it.
- **A domain type in a resource.** Resources are records of primitives. `CustomerId` never crosses the HTTP boundary; `Long customerId` does, and the assembler wraps it.
- **A business rule in a service.** `if (order.getStatus() == DRAFT)` in a command service means the aggregate lost a method. The service asks `order.place()` and the aggregate decides whether it may.
- **`org.springframework.web` in the domain.** A domain exception with an `HttpStatus` in it, or a `ResponseEntity` anywhere below `interfaces`, has broken the direction of dependencies.
- **Another context's aggregate.** `ordering` never imports `customers.domain`. It holds a `CustomerId` and reaches the other context through its facade — see `anti-corruption-layer.md`.
- **A bare `RuntimeException`.** A failure has a name in the ubiquitous language (`OrderNotFoundException`) or it is invalid input (`IllegalArgumentException`) or an impossible transition (`IllegalStateException`). Nothing else reaches the edge.
- **A `try { save } catch (Exception e) { throw new IllegalArgumentException(…) }`.** It turns every database failure into a 400 and hides the cause. Let the exception through; the advice decides the status.
