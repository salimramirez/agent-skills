# Infrastructure: the CRUD path

Resources, assemblers, endpoints, and the context gateway — the read/write path for a record.

Three files per aggregate, plus one gateway per context. They rest on the kernel's `BaseApi` and `BaseEndpoint` (see `shared-kernel.md`), and each has exactly one job.

## 1. The resource — `order.resource.ts`

The wire shape, as an **interface**. It mirrors the API exactly, quirks included, and never leaves this layer.

```typescript
// ordering/infrastructure/order.resource.ts

/** Wire shape of a single order as the platform API returns it. */
export interface OrderResource {
    id: number;
    customer_id: number;
    lines: Array<{menu_item_id: number; quantity: number}>;
    delivery_address: string;
    status: string;
    total: number;
}
```

Snake case, a `status` typed as `string` rather than the union, a nullable field where the domain wants a default — leave all of it as the API actually sends it. Cleaning it up here would move the translation to the wrong place.

An interface rather than a class: nothing is ever constructed from it, it exists to be checked against. That is also why it costs nothing.

## 2. The assembler — `order.assembler.ts`

The anti-corruption layer, and the only file that knows both shapes. Methods are **static**: an assembler holds no state, it is a translation rather than a collaborator.

```typescript
// ordering/infrastructure/order.assembler.ts
import type {AxiosResponse} from 'axios';
import {Order, type OrderStatus} from '../domain/model/order.entity';
import type {OrderResource} from './order.resource';

/** Anti-corruption layer between the orders API and the ordering model. */
export class OrderAssembler {
    /** Builds one entity from a resource payload. */
    static toEntityFromResource(resource: OrderResource): Order {
        return new Order({
            id: resource.id,
            customerId: resource.customer_id,                       // the API's naming stops here
            lines: resource.lines.map(line => ({
                menuItemId: line.menu_item_id, quantity: line.quantity
            })),
            deliveryAddress: resource.delivery_address,
            status: resource.status as OrderStatus,
            total: resource.total
        });
    }

    /** Builds the collection from a response, tolerating both wire shapes. */
    static toEntitiesFromResponse(
        response: AxiosResponse<OrderResource[] | Record<string, OrderResource[]>>
    ): Order[] {
        if (response.status !== 200) return [];
        const resources = Array.isArray(response.data)
            ? response.data
            : response.data['orders'] ?? [];
        return resources.map(resource => this.toEntityFromResource(resource));
    }

    /** Turns an entity back into the payload the API expects on a write. */
    static toResourceFromEntity(entity: Order): Omit<OrderResource, 'id'> & {id?: number} {
        return {
            ...(entity.id !== null ? {id: entity.id} : {}),
            customer_id: entity.customerId ?? 0,
            lines: entity.lines.map(line => ({
                menu_item_id: line.menuItemId, quantity: line.quantity
            })),
            delivery_address: entity.deliveryAddress,
            status: entity.status,
            total: entity.total
        };
    }
}
```

Everything the API does that your model should not inherit is absorbed in these three methods. This is the most valuable file in the layer: when the backend renames a field, exactly one file changes — and the compiler tells you it is the only one that needs to.

Three details worth copying deliberately:

- **`toEntitiesFromResponse` accepts a bare array or an envelope.** A mock server returning `[…]` and a real backend returning `{ orders: […] }` both work without touching the store.
- **A non-200 yields an empty collection, not a throw.** The store's `catch` already records transport failures.
- **`status as OrderStatus` is the one honest cast.** The wire says `string`; the domain says union. The assembler is exactly where that narrowing belongs, and the fact that it needs a cast is a reminder the value came from outside.

## 3. The context gateway — `ordering-api.ts`

One per bounded context, extending `BaseApi`. It owns the context's endpoints and exposes them as operations named in the ubiquitous language.

```typescript
// ordering/infrastructure/ordering-api.ts
import type {AxiosResponse} from 'axios';
import {BaseApi, type BaseApiOptions} from '../../shared/infrastructure/base-api';
import {BaseEndpoint} from '../../shared/infrastructure/base-endpoint';
import {OrderAssembler} from './order.assembler';
import type {Order} from '../domain/model/order.entity';
import type {OrderResource} from './order.resource';

const ordersEndpointPath = import.meta.env.VITE_ORDERS_ENDPOINT_PATH;

/** The API of the ordering bounded context. */
export class OrderingApi extends BaseApi {
    readonly #orders: BaseEndpoint<OrderResource>;

    constructor(options: BaseApiOptions = {}) {
        super(options);
        this.#orders = new BaseEndpoint<OrderResource>(this.http, ordersEndpointPath);
    }

    getOrders() {
        return this.#orders.getAll();
    }

    createOrder(order: Order): Promise<AxiosResponse<OrderResource>> {
        return this.#orders.create(OrderAssembler.toResourceFromEntity(order));
    }

    updateOrder(order: Order): Promise<AxiosResponse<OrderResource>> {
        return this.#orders.update(order.id!, OrderAssembler.toResourceFromEntity(order));
    }

    deleteOrder(id: number): Promise<AxiosResponse<void>> {
        return this.#orders.delete(id);
    }
}
```

Endpoints are `#private`, so the store depends on `OrderingApi` and can never reach past it. A context with three aggregates has three endpoint fields here and one store talking to all of them.

Note that the gateway calls `toResourceFromEntity` on the way **out**, while the store calls `toEntityFromResource` on the way **in**. Both directions cross the assembler; they just happen at the two ends of the call.

## The round trip

```
read    getOrders() → AxiosResponse → OrderAssembler.toEntitiesFromResponse → Order[]
write   Order → toResourceFromEntity → POST/PUT → AxiosResponse → toEntityFromResource → Order
delete  deleteOrder(id) → AxiosResponse<void>
```

Note where the assembler sits on a read: **in the store**, not in the endpoint. The gateway hands back a response and the store turns it into entities. See `state-store.md`.

## Why the write side has its own method

`toResourceFromEntity` exists because the two shapes genuinely differ — `customerId` against `customer_id`, `OrderLine` instances against plain objects. Sending the entity directly would put `readonly` class instances on the wire and hope the backend ignores the mismatch.

When the shapes happen to coincide the method is nearly the identity function, and it still earns its place: it is the one file that changes when they stop coinciding, and the compiler points at it.
