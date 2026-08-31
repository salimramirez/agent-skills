# Commands and actions: the non-CRUD path

When the write is an intent rather than a record, and when the API is not yours.

`BaseEndpoint` covers "save this entity". Plenty of real operations are not that: placing an order from a cart, cancelling with a reason, signing in, asking a third party for a delivery estimate. Those get a different path — same anti-corruption idea, one more type.

## The shape

```
PlaceOrderCommand  →  gateway  →  POST
                                    ↓
Order  ←  toEntityFromResource  ←  PlaceOrderResource  ←  toResourceFromResponse
```

Three files beside the command itself (which lives in `domain/model/`, see `domain-model.md`): a resource, an assembler, and an operation on the context gateway.

## 1. The resource — `place-order.resource.ts`

What comes back, as an interface:

```typescript
// ordering/infrastructure/place-order.resource.ts

/** What the platform returns after placing an order. */
export interface PlaceOrderResource {
    id: number;
    status: string;
    total: number;
    estimated_delivery_at: string;
}
```

## 2. The assembler — `place-order.assembler.ts`

A different shape from the CRUD one: an action returns a confirmation, not a collection.

```typescript
// ordering/infrastructure/place-order.assembler.ts
import type {AxiosResponse} from 'axios';
import type {PlaceOrderResource} from './place-order.resource';
import type {PlaceOrderCommand} from '../domain/model/place-order.command';

/** Anti-corruption layer for the place-order call. */
export class PlaceOrderAssembler {
    /** The body to send. */
    static toRequestFromCommand(command: PlaceOrderCommand) {
        return {
            customer_id: command.customerId,
            lines: command.lines.map(line => ({
                menu_item_id: line.menuItemId, quantity: line.quantity
            })),
            delivery_address: command.deliveryAddress
        };
    }

    /** The confirmation, or null when the call did not succeed. */
    static toResourceFromResponse(
        response: AxiosResponse<PlaceOrderResource>
    ): PlaceOrderResource | null {
        if (response.status !== 200 && response.status !== 201) return null;
        return response.data;
    }
}
```

Returning `null` rather than throwing keeps the failure a value the store can branch on — and typing it `PlaceOrderResource | null` forces the caller to handle it, which is the whole point of doing this in TypeScript.

Note there is no runtime validation here: `response.data` is *asserted* to match, not checked. TypeScript describes the shape you expect, it does not verify what arrived. If the API is one you do not control, this is exactly where a runtime schema check belongs — see `javascript.md`, which needs it for a different reason and shows the same technique.

## 3. The operation on the gateway

```typescript
// ordering/infrastructure/ordering-api.ts
const placeOrderEndpointPath = import.meta.env.VITE_PLACE_ORDER_ENDPOINT_PATH;

// inside OrderingApi
placeOrder(command: PlaceOrderCommand): Promise<AxiosResponse<PlaceOrderResource>> {
    return this.http.post(placeOrderEndpointPath, PlaceOrderAssembler.toRequestFromCommand(command));
}
```

It reaches for `this.http` directly rather than constructing a `BaseEndpoint`, which is what the protected getter is for: not every operation is CRUD over a collection, and an endpoint object that only ever POSTs to one path earns nothing.

## In the store

```typescript
placeOrder: async (command: PlaceOrderCommand) => {
    try {
        const response = await orderingApi.placeOrder(command);
        const resource = PlaceOrderAssembler.toResourceFromResponse(response);
        if (!resource) {
            set({errors: [...get().errors, new Error('The order could not be placed')]});
            return;
        }
        set({lastPlacedOrderId: resource.id});
        await get().fetchOrders();
    } catch (error) {
        set({errors: [...get().errors, error as Error]});
    }
}
```

The action returns a `Promise<void>` and the **view decides where to go next**. Unlike `ddd-vue`, no router is passed in: React Router's `useNavigate` is a hook, so it belongs to the component, and the store stays free of React. Awaiting the action in the view and navigating afterwards keeps both rules intact:

```tsx
async function handlePlaceOrder() {
    await placeOrder(command);
    navigate(orderingPaths.orders());
}
```

## When the API is not yours

A third-party provider is where the anti-corruption layer earns its name — you do not get to ask them to rename a field. Same structure, two differences: its own env prefix, and its key and query parameters stay inside the gateway.

```typescript
// ordering/infrastructure/delivery-estimate-api.ts
import axios from 'axios';

const mapsApiUrl = import.meta.env.VITE_MAPS_API_URL;
const mapsApiKey = import.meta.env.VITE_MAPS_API_KEY;
const estimateEndpointPath = import.meta.env.VITE_ESTIMATE_ENDPOINT_PATH;

const http = axios.create({baseURL: mapsApiUrl, params: {key: mapsApiKey}});

/**
 * Delivery estimates from the maps provider.
 *
 * The provider's key and parameter names never leave this file. It does not extend
 * `BaseApi` because it is not the platform — a different host, a different auth
 * scheme, and none of the platform's interceptors should apply to it.
 */
export class DeliveryEstimateApi {
    getEstimate(origin: string, destination: string) {
        return http.get(estimateEndpointPath, {params: {origin, destination}});
    }
}
```

Default `params` on the instance apply the key to every call without repeating it. And **not everything extends `BaseApi`** — that base carries your platform's base URL and interceptors, and pointing it at a third party would send your bearer token to someone else's server.

A read-only integration often needs no write side at all: one gateway, one assembler with a single inbound method, and a store that caches what came back. That is a complete, honest context — a context is not obliged to have CRUD.
