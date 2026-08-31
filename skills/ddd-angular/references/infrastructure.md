# Infrastructure: the CRUD path

DTOs, assemblers, endpoints, and the context API — the read/write path for a record.

Four files carry one aggregate from the wire to the domain and back. They rest on the kernel's base classes (`shared-kernel.md`), and each has exactly one job.

## 1. The DTOs — `orders-response.ts`

One file per collection, holding **both** wire shapes: the item and the envelope. They mirror the API exactly, quirks included, and never leave this layer.

```typescript
// ordering/infrastructure/orders-response.ts
import {BaseResource, BaseResponse} from '../../shared/infrastructure/base-response';

/**
 * Wire shape of a single order as the platform API returns it.
 */
export interface OrderResource extends BaseResource {
  id: number;
  customer_id: number;
  lines: {menu_item_id: number, quantity: number}[];
  delivery_address: string;
  status: string;
  total: number;
  courier_id: number | null;
}

/**
 * Wire shape of the envelope holding many orders.
 */
export interface OrdersResponse extends BaseResponse {
  orders: OrderResource[];
}
```

Snake case, a `status` typed as `string` rather than the union, a nullable field where the domain wants a default — leave all of it as the API actually sends it. Cleaning it up here would move the translation to the wrong place.

## 2. The assembler — `order-assembler.ts`

The anti-corruption layer. It is the only file that knows both shapes, and it maps both directions.

```typescript
// ordering/infrastructure/order-assembler.ts
import {BaseAssembler} from '../../shared/infrastructure/base-assembler';
import {Order, OrderStatus} from '../domain/model/order.entity';
import {OrderResource, OrdersResponse} from './orders-response';

/**
 * Anti-corruption layer between the orders API and the ordering model.
 */
export class OrderAssembler implements BaseAssembler<Order, OrderResource, OrdersResponse> {
  toEntitiesFromResponse(response: OrdersResponse): Order[] {
    return response.orders.map(resource => this.toEntityFromResource(resource));
  }

  toEntityFromResource(resource: OrderResource): Order {
    return new Order({
      id: resource.id,
      customerId: resource.customer_id,                       // the API's naming stops here
      lines: resource.lines.map(line => ({
        menuItemId: line.menu_item_id, quantity: line.quantity
      })),
      deliveryAddress: resource.delivery_address,
      status: resource.status as OrderStatus,
      total: resource.total,
      courierId: resource.courier_id ?? 0                     // the API's null becomes a domain default
    });
  }

  toResourceFromEntity(entity: Order): OrderResource {
    return {
      id: entity.id,
      customer_id: entity.customerId,
      lines: entity.lines.map(line => ({
        menu_item_id: line.menuItemId, quantity: line.quantity
      })),
      delivery_address: entity.deliveryAddress,
      status: entity.status,
      total: entity.total,
      courier_id: entity.courierId || null
    } as OrderResource;
  }
}
```

Everything the API does that your model should not inherit — naming, nulls, a flattened field, a date as a string — is absorbed in these three methods. This is the single most valuable file in the layer: when the backend changes a field name, exactly one file changes.

## 3. The endpoint — `orders-api-endpoint.ts`

The repository. It declares its URL and its assembler; the operations come from the base class.

```typescript
// ordering/infrastructure/orders-api-endpoint.ts
import {HttpClient} from '@angular/common/http';
import {BaseApiEndpoint} from '../../shared/infrastructure/base-api-endpoint';
import {environment} from '../../../environments/environment';
import {Order} from '../domain/model/order.entity';
import {OrderResource, OrdersResponse} from './orders-response';
import {OrderAssembler} from './order-assembler';

const ordersEndpointUrl =
  `${environment.platformProviderApiBaseUrl}${environment.platformProviderOrdersEndpointPath}`;

/**
 * CRUD endpoint for orders — the repository of this aggregate.
 */
export class OrdersApiEndpoint
  extends BaseApiEndpoint<Order, OrderResource, OrdersResponse, OrderAssembler> {
  constructor(http: HttpClient) {
    super(http, ordersEndpointUrl, new OrderAssembler());
  }
}
```

An endpoint is a plain class, not an `@Injectable`. It is constructed by the context API, which is the injectable one — that is what keeps a store from ever holding an endpoint.

## 4. The context API — `ordering-api.ts`

One per bounded context, extending `BaseApi`. It owns the context's endpoints and exposes them as operations named in the ubiquitous language.

```typescript
// ordering/infrastructure/ordering-api.ts
@Injectable({providedIn: 'root'})
export class OrderingApi extends BaseApi {
  private readonly ordersEndpoint: OrdersApiEndpoint;
  private readonly couriersEndpoint: CouriersApiEndpoint;
  private readonly menuItemsEndpoint: MenuItemsApiEndpoint;

  constructor(http: HttpClient) {
    super();
    this.ordersEndpoint = new OrdersApiEndpoint(http);
    this.couriersEndpoint = new CouriersApiEndpoint(http);
    this.menuItemsEndpoint = new MenuItemsApiEndpoint(http);
  }

  /**
   * @returns Every order in the context.
   */
  getOrders(): Observable<Order[]> { return this.ordersEndpoint.getAll(); }

  getOrder(id: number): Observable<Order> { return this.ordersEndpoint.getById(id); }

  createOrder(order: Order): Observable<Order> { return this.ordersEndpoint.create(order); }

  updateOrder(order: Order): Observable<Order> {
    return this.ordersEndpoint.update(order, order.id);
  }

  deleteOrder(id: number): Observable<void> { return this.ordersEndpoint.delete(id); }

  /**
   * @returns The couriers the store resolves each order against.
   */
  getCouriers(): Observable<Courier[]> { return this.couriersEndpoint.getAll(); }

  getMenuItems(sectionId: string): Observable<MenuItem[]> {
    return this.menuItemsEndpoint.getAll(sectionId);
  }
}
```

The store depends on `OrderingApi` and nothing else in this layer. A context with three aggregates has three endpoint fields here and one store talking to all of them — `Courier` and `MenuItem` each get the same four files `Order` did.

## The round trip

```
read    GET  → OrdersResponse → toEntitiesFromResponse → Order[]
write   Order → toResourceFromEntity → POST/PUT → OrderResource → toEntityFromResource → Order
delete  DELETE → void
```

For CRUD there is **no separate request DTO** — the resource is the write payload, which is why `BaseAssembler` has `toResourceFromEntity` and nothing else for writes. When the body is not a record, the path changes shape; see `commands-and-actions.md`.
