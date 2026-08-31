# The application layer: the Zustand store

The store that holds a context's state and orchestrates its use cases.

One store per bounded context, named after the context: `useOrderingStore`, not `useOrderStore` and not `useAppStore`. It fills the role command and query handlers play on the backend — it talks to the context gateway, calls the assembler, and keeps coordination out of the components.

Declare the shape as an exported interface, then build the store in one `create()` call.

```typescript
// ordering/application/ordering.store.ts
import {create} from 'zustand';
import {OrderingApi} from '../infrastructure/ordering-api';
import {OrderAssembler} from '../infrastructure/order.assembler';
import type {Order} from '../domain/model/order.entity';

const orderingApi = new OrderingApi();

/** State and use cases of the ordering bounded context. */
export interface OrderingState {
    orders: Order[];
    errors: Error[];
    ordersLoaded: boolean;
    fetchOrders: () => Promise<void>;
    addOrder: (order: Order) => Promise<void>;
    updateOrder: (order: Order) => Promise<void>;
    deleteOrder: (id: number) => Promise<void>;
}

/**
 * The application layer of the ordering context.
 *
 * The only thing that talks to `OrderingApi`, and the only place an assembler is
 * called: the endpoint hands back a raw response, and turning it into domain objects
 * is an application concern. It imports nothing from React, so it can be exercised
 * without rendering — and read outside a component with `useOrderingStore.getState()`.
 */
export const useOrderingStore = create<OrderingState>()((set, get) => ({
    orders: [],
    errors: [],
    ordersLoaded: false,

    fetchOrders: async () => {
        try {
            const response = await orderingApi.getOrders();
            set({orders: OrderAssembler.toEntitiesFromResponse(response), ordersLoaded: true});
        } catch (error) {
            set({errors: [...get().errors, error as Error]});
        }
    },

    addOrder: async (order: Order) => {
        try {
            const response = await orderingApi.createOrder(order);
            const created = OrderAssembler.toEntityFromResource(response.data);
            set({orders: [...get().orders, created]});
        } catch (error) {
            set({errors: [...get().errors, error as Error]});
        }
    },

    updateOrder: async (order: Order) => {
        try {
            const response = await orderingApi.updateOrder(order);
            const updated = OrderAssembler.toEntityFromResource(response.data);
            set({orders: get().orders.map(current => current.id === updated.id ? updated : current)});
        } catch (error) {
            set({errors: [...get().errors, error as Error]});
        }
    },

    deleteOrder: async (id: number) => {
        try {
            await orderingApi.deleteOrder(id);
            set({orders: get().orders.filter(current => current.id !== id)});
        } catch (error) {
            set({errors: [...get().errors, error as Error]});
        }
    }
}));
```

## What each convention is for

**`create<OrderingState>()(…)` — note the double call.** That is Zustand's curried form for TypeScript; without it the generic cannot be supplied and the state ends up inferred and loose.

**The gateway is instantiated once, at module scope.** One Axios instance for the app rather than one per store activation. It is safe there because building an Axios client touches nothing that needs React to be running.

**The store imports nothing from React.** This is the property everything else leans on: a route loader and an axios interceptor both read state with `useOrderingStore.getState()`, outside any component. Keep it that way — the moment a store imports a hook, half the app's plumbing stops working.

**Every update replaces; nothing mutates.** `[...get().orders, created]`, `.map`, `.filter`. React compares by reference, so a `push` renders nothing at all. See `house-style.md`.

**The store is the only caller of an assembler.** The endpoint returns a raw response (see `shared-kernel.md`); this is where it becomes domain objects. TypeScript enforces it here — `Order[]` and `OrderResource[]` are different types — so the mistake JavaScript would let through is a compile error.

**`errors` is an array, not a message.** Failures accumulate rather than overwrite, so a second failure never hides the first. Clear it when an operation succeeds if the screen should recover.

**`ordersLoaded` rather than a `loading` flag.** It answers "has this ever been fetched?", which is the question a component actually asks before deciding to fetch — and it is what stops a list refetching every time the user navigates back. For per-operation spinners, add a `saving` field; the two answer different questions.

## Reading a store from a component

Select one slice per call:

```typescript
const orders = useOrderingStore(state => state.orders);
const fetchOrders = useOrderingStore(state => state.fetchOrders);
```

Each selector subscribes the component to just that slice, so it re-renders only when that slice changes. Selecting the whole store — `useOrderingStore()` — re-renders on every unrelated change in the context, which on a busy store is the difference between a smooth list and a janky one.

Do not build a new object inside a selector (`state => ({a: state.a, b: state.b})`): it returns a fresh reference every time and defeats the comparison. Two selectors are cheaper than one clever one.

## Cross-entity coordination

When an order needs its menu items resolved for display, that stitching belongs here — after the load, and after each write so a newly created order is stitched too. Because entities are immutable, stitching means **rebuilding**, not assigning:

```typescript
const stitched = orders.map(order => order.withCourier(
    couriers.find(courier => courier.id === order.courierId) ?? null
));
set({orders: stitched});
```

Keep it out of the components — that is the whole reason the application layer exists on the client.

## About TanStack Query

It is excellent, it is very common in React, and it overlaps with this store's job: it owns fetching, caching, deduplication and staleness. Adopt it and the store stops being the owner of cached server state; what remains is orchestration on top of it, and the four-layer story gets harder to see because the fetching moves into hooks spread across components.

Neither `ddd-angular` nor `ddd-vue` adopted their equivalents either, for the same reason. If your project already uses it, keep the gateway and the assembler exactly as they are — they are what turn a query result into domain objects — and treat the store as the place where use cases that span more than one query still live.
