# Infrastructure: DTOs, assemblers, endpoints, and the context API

The API boundary: wire-shaped DTOs, assemblers as the anti-corruption layer, endpoints, and the context API facade.

The infrastructure layer rests on the shared base classes from the kernel: `BaseResource`/`BaseResponse` (DTO markers), `BaseAssembler<Entity, Resource, Response>` (the mapping contract), the generic `BaseApiEndpoint<Entity, Resource, Response, Assembler>` that implements CRUD — `getAll`, `getById`, `create`, `update`, `delete` — with error handling, and `BaseApi` for a context's API facade.

**The DTOs** live in `*-response.ts`: a `Resource` (one item, extends `BaseResource`) and a `Response` (the envelope, extends `BaseResponse`). They mirror the API's wire shape and never leave this layer:

```typescript
// ordering/infrastructure/orders-response.ts
import { BaseResource, BaseResponse } from '../../shared/infrastructure/base-response';

export interface OrderResource extends BaseResource {
  id: number;
  customer_id: number;
  items: { item_id: number; quantity: number }[];
  status: OrderStatus;
  total: number;
}

export interface OrdersResponse extends BaseResponse {
  orders: OrderResource[];
}
```

**The assembler** `implements BaseAssembler` and maps both ways — building entities with `new`, and turning an entity back into a resource for writes:

```typescript
// ordering/infrastructure/order-assembler.ts
import { BaseAssembler } from '../../shared/infrastructure/base-assembler';

export class OrderAssembler implements BaseAssembler<Order, OrderResource, OrdersResponse> {
  toEntityFromResource(resource: OrderResource): Order {
    return new Order({
      id: resource.id,
      customerId: resource.customer_id,                                  // translate the API's naming
      items: resource.items.map(i => ({ itemId: i.item_id, quantity: i.quantity })),
      status: resource.status,
      total: resource.total,
    });
  }

  toEntitiesFromResponse(response: OrdersResponse): Order[] {
    return response.orders.map(resource => this.toEntityFromResource(resource));
  }

  toResourceFromEntity(entity: Order): OrderResource {
    return {
      id: entity.id,
      customer_id: entity.customerId,
      items: entity.items.map(i => ({ item_id: i.itemId, quantity: i.quantity })),
      status: entity.status,
      total: entity.total,
    } as OrderResource;
  }
}
```

**The endpoint** is the repository — it declares only its URL and assembler; the CRUD comes from the base class:

```typescript
// ordering/infrastructure/orders-api-endpoint.ts
export class OrdersApiEndpoint extends BaseApiEndpoint<Order, OrderResource, OrdersResponse, OrderAssembler> {
  constructor(http: HttpClient) {
    super(http, `${environment.apiBaseUrl}/orders`, new OrderAssembler());
  }
}
```

**The context API** (`*-api.ts`, extends `BaseApi`) is the single service the application layer talks to. It owns the context's endpoints (often more than one) and exposes its operations — so the store never touches an endpoint directly:

```typescript
// ordering/infrastructure/ordering-api.ts
@Injectable({ providedIn: 'root' })
export class OrderingApi extends BaseApi {
  private readonly orders: OrdersApiEndpoint;

  constructor(http: HttpClient) {
    super();
    this.orders = new OrdersApiEndpoint(http);
  }

  getOrders(): Observable<Order[]> { return this.orders.getAll(); }
  createOrder(order: Order): Observable<Order> { return this.orders.create(order); }
  updateOrder(order: Order): Observable<Order> { return this.orders.update(order, order.id); }
  deleteOrder(id: number): Observable<void> { return this.orders.delete(id); }
}
```

So a read runs `response → toEntitiesFromResponse → entities`, and a create/update runs `entity → toResourceFromEntity → POST/PUT → entity`. For CRUD there's **no separate request DTO** — the resource is the write payload. The assembler is the **anti-corruption layer**: the API's naming and quirks stop here and never reach the domain or the views.

> **Command-style writes.** When a write carries a command rather than an entity (the non-CRUD case), the request body often differs from any resource, so add a dedicated **`*.request.ts`** DTO and an assembler that maps **command → request** (and **response → resource**) — e.g. a `SignInAssembler` with `toRequestFromCommand(command): SignInRequest` and `toResourceFromResponse(response): SignInResource`. Same ACL idea, just for an action instead of a record.
