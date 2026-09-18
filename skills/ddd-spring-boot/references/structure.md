# Package structure

The package tree of a bounded context, the naming table, and where the shared kernel sits.

## One package per bounded context, four layers inside

Every bounded context is a package under the base package, and every one of them has the same four layers with the same sub-packages. Dependencies point inward: `interfaces` and `infrastructure` know `application` and `domain`; `application` knows `domain`; `domain` knows nothing outside itself.

```
com.quickbite.platform
├── QuickBitePlatformApplication.java        @SpringBootApplication + @EnableJpaAuditing
├── ordering/                                 a bounded context
│   ├── domain/
│   │   ├── model/
│   │   │   ├── aggregates/                   Order
│   │   │   ├── entities/                     OrderLine
│   │   │   ├── valueobjects/                 CustomerId, Money, OrderCode, OrderStatus, OrderLines
│   │   │   ├── commands/                     CreateOrderCommand, PlaceOrderCommand, …
│   │   │   ├── queries/                      GetOrderByIdQuery, GetAllOrdersQuery, …
│   │   │   └── events/                       OrderPlacedEvent, OrderCancelledEvent
│   │   ├── services/                         OrderCommandService, OrderQueryService  (interfaces)
│   │   └── exceptions/                       OrderNotFoundException, CustomerNotFoundException
│   ├── application/
│   │   ├── internal/
│   │   │   ├── commandservices/              OrderCommandServiceImpl
│   │   │   ├── queryservices/                OrderQueryServiceImpl
│   │   │   ├── eventhandlers/                OrderPlacedEventHandler
│   │   │   └── outboundservices/acl/         ExternalCustomerService
│   │   └── acl/                              <Context>ContextFacadeImpl, when this context is a provider
│   ├── infrastructure/
│   │   └── persistence/jpa/repositories/     OrderRepository
│   └── interfaces/
│       ├── rest/                             OrdersController, OrderLinesController, OrderingExceptionHandler
│       │   ├── resources/                    OrderResource, CreateOrderResource, …
│       │   └── transform/                    CreateOrderCommandFromResourceAssembler, OrderResourceFromEntityAssembler, …
│       └── acl/                              <Context>ContextFacade, when this context is a provider
├── customers/                                another bounded context, same shape
├── iam/                                      the identity context, same shape plus infrastructure/{authorization,hashing,tokens}
└── shared/                                   the shared kernel — see shared-kernel.md
    ├── domain/model/aggregates/              AuditableAbstractAggregateRoot
    ├── domain/model/entities/                AuditableModel
    ├── infrastructure/documentation/openapi/configuration/   OpenApiConfiguration
    ├── infrastructure/persistence/jpa/configuration/strategy/ SnakeCaseWithPluralizedTablePhysicalNamingStrategy
    └── interfaces/rest/                      GlobalExceptionHandler, resources/MessageResource
```

Two things about the tree that are decisions, not accidents:

- **Commands and queries live in the domain**, not in the application layer. They are part of the model: a `PlaceOrderCommand` is a sentence in the ubiquitous language, and the aggregate takes it as a constructor argument. The application layer only *executes* them.
- **The service interfaces live in `domain/services` and their implementations in `application/internal`.** The domain says what can be asked of it; the application layer says how it is done, with which repository and which other context. A controller depends on the interface and never sees the implementation.

What each layer is for:

| Layer | Holds | Never holds |
| --- | --- | --- |
| `domain` | aggregates, entities, value objects, commands, queries, events, the service interfaces, domain exceptions | anything from `org.springframework.web`, a repository, another context's types |
| `application` | command and query service implementations, event handlers, the outbound ACL services, the inbound facade implementation | business rules — if an `if` decides what the domain allows, it belongs in the aggregate |
| `infrastructure` | Spring Data repositories, and whatever talks to the outside: hashing, tokens, external APIs | logic that reads a domain object to decide something |
| `interfaces` | REST controllers, resources, assemblers, the context's exception advice, the facade interface other contexts call | domain types in a signature; a repository |

JPA annotations do live on the domain classes. That is a deliberate, pragmatic trade: the model stays readable and one class describes the concept and its persistence; the price is that the domain depends on `jakarta.persistence`. The domain still never depends on Spring Web, on a repository, or on another bounded context.

## Naming table

The same name, spelled the same way, everywhere. Given an aggregate `Order` in the context `ordering`:

| Thing | Name | Package |
| --- | --- | --- |
| Aggregate root | `Order` | `domain/model/aggregates` |
| Entity inside the aggregate | `OrderLine` | `domain/model/entities` |
| Value object | `Money`, `OrderCode`; enum `OrderStatus` | `domain/model/valueobjects` |
| Reference to another aggregate | `CustomerId`, `MenuItemId` | `domain/model/valueobjects` |
| Command | `<Verb><Aggregate>Command` — `CreateOrderCommand`, `PlaceOrderCommand`, `AddLineToOrderCommand` | `domain/model/commands` |
| Query | `Get<Aggregate>By<Field>Query`, `GetAll<Aggregates>Query`, `GetAll<Aggregates>By<Field>Query` | `domain/model/queries` |
| Domain event | `<Aggregate><PastParticiple>Event` — `OrderPlacedEvent` | `domain/model/events` |
| Service interfaces | `OrderCommandService`, `OrderQueryService` — every method is `handle` | `domain/services` |
| Domain exception | `OrderNotFoundException` | `domain/exceptions` |
| Service implementations | `OrderCommandServiceImpl`, `OrderQueryServiceImpl` | `application/internal/commandservices`, `…/queryservices` |
| Event handler | `OrderPlacedEventHandler`, method `on(OrderPlacedEvent)` | `application/internal/eventhandlers` |
| Outbound ACL service | `ExternalCustomerService` | `application/internal/outboundservices/acl` |
| Facade this context exposes | `CustomersContextFacade` / `CustomersContextFacadeImpl` | `interfaces/acl` / `application/acl` |
| Repository | `OrderRepository` | `infrastructure/persistence/jpa/repositories` |
| Controller | **plural** — `OrdersController` at `/api/v1/orders`; nested `OrderLinesController` at `/api/v1/orders/{orderId}/lines` | `interfaces/rest` |
| Context advice | `OrderingExceptionHandler` | `interfaces/rest` |
| Resources | `OrderResource` (response), `CreateOrderResource`, `AddLineToOrderResource` (requests) | `interfaces/rest/resources` |
| Assemblers | `CreateOrderCommandFromResourceAssembler.toCommandFromResource(resource)`, `OrderResourceFromEntityAssembler.toResourceFromEntity(entity)` | `interfaces/rest/transform` |
| Path variable | `{orderId}`, never `{id}` | |
| Database table | `orders`, `order_lines` — plural snake_case, produced by the naming strategy | |

A context package is one lowercase word (`ordering`, `customers`, `iam`); a REST path is plural kebab-case (`/api/v1/menu-items`). The generator derives every spelling from the two names you give it — see `adding-a-resource.md`.
