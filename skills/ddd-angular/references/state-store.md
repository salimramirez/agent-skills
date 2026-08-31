# The application layer: the signal store

The store that holds a context's state and orchestrates its use cases.

One store per bounded context, named after the context: `OrderingStore`, not `OrderStore` and not `AppStore`. It fills the role command and query handlers play on the backend — it talks to the context API, publishes state through read-only signals, and keeps every bit of coordination out of the views.

```typescript
// ordering/application/ordering.store.ts
import {computed, DestroyRef, inject, Injectable, Signal, signal} from '@angular/core';
import {takeUntilDestroyed} from '@angular/core/rxjs-interop';
import {retry} from 'rxjs';

/**
 * State and use cases of the ordering bounded context.
 */
@Injectable({providedIn: 'root'})
export class OrderingStore {
  private readonly destroyRef = inject(DestroyRef);
  private readonly orderingApi = inject(OrderingApi);

  private readonly ordersSignal = signal<Order[]>([]);
  /** Every order currently loaded. */
  readonly orders = this.ordersSignal.asReadonly();

  private readonly couriersSignal = signal<Courier[]>([]);
  readonly couriers = this.couriersSignal.asReadonly();

  private readonly loadingSignal = signal<boolean>(false);
  readonly loading = this.loadingSignal.asReadonly();

  private readonly errorSignal = signal<string | null>(null);
  readonly error = this.errorSignal.asReadonly();

  /** Orders still in flight, for the dashboard. */
  readonly activeOrders = computed(() =>
    this.orders().filter(order => order.status !== 'DELIVERED' && order.status !== 'CANCELLED'));

  readonly orderCount = computed(() => this.orders().length);

  constructor() {
    this.loadCouriers();
    this.loadOrders();
  }

  /**
   * One order, as a signal that tracks the collection.
   *
   * @param id - Identity to look up.
   * @returns A signal holding the order, or `undefined` while it is absent.
   */
  getOrderById(id: number): Signal<Order | undefined> {
    return computed(() => id ? this.orders().find(order => order.id === id) : undefined);
  }

  /**
   * Loads every order and resolves each one's courier.
   */
  loadOrders(): void {
    this.loadingSignal.set(true);
    this.errorSignal.set(null);
    this.orderingApi.getOrders().pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: orders => {
        this.ordersSignal.set(orders);
        this.loadingSignal.set(false);
        this.assignCouriersToOrders();
      },
      error: error => {
        this.errorSignal.set(this.formatError(error, 'Failed to load orders'));
        this.loadingSignal.set(false);
      }
    });
  }

  /**
   * Creates an order and adds it to the collection.
   *
   * @param order - Order built by the form, with `id: 0`.
   */
  addOrder(order: Order): void {
    this.loadingSignal.set(true);
    this.errorSignal.set(null);
    this.orderingApi.createOrder(order).pipe(retry(2)).subscribe({
      next: created => {
        this.ordersSignal.update(orders => [...orders, this.assignCourierToOrder(created)]);
        this.loadingSignal.set(false);
      },
      error: error => {
        this.errorSignal.set(this.formatError(error, 'Failed to create the order'));
        this.loadingSignal.set(false);
      }
    });
  }

  // updateOrder, deleteOrder and cancelOrder have the same shape: set loading,
  // clear error, call the API, update the signal, clear loading.

  /**
   * Loads the couriers this context resolves orders against.
   */
  private loadCouriers(): void {
    this.orderingApi.getCouriers().pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: couriers => this.couriersSignal.set(couriers),
      error: error => this.errorSignal.set(this.formatError(error, 'Failed to load couriers'))
    });
  }

  private assignCouriersToOrders(): void {
    this.ordersSignal.update(orders => orders.map(order => this.assignCourierToOrder(order)));
  }

  private assignCourierToOrder(order: Order): Order {
    order.courier = this.couriers().find(courier => courier.id === order.courierId) ?? null;
    return order;
  }

  /**
   * Turns a failure into one sentence a view can show.
   */
  private formatError(error: unknown, fallback: string): string {
    if (error instanceof Error) {
      return error.message.includes('Resource not found') ? `${fallback}: Not found` : error.message;
    }
    return fallback;
  }
}
```

## What each convention is for

**Private signal, public read-only view, declared as a pair.** Nothing outside the store can write state. Views read `store.orders()` and get a value that only the store can change.

**`computed()` is the query side.** `activeOrders` and `orderCount` are derived, never stored — a second signal holding the same data in a different shape is the frontend's version of a denormalized field that drifts. `getOrderById(id)` returns a *signal*, not a value, so a form that opens before the load finishes still fills in when it lands.

**Eager loading in the constructor.** A root-provided store loads what its context needs as soon as something injects it, and load order matters: couriers before orders, so the stitching has something to match against.

**`takeUntilDestroyed(this.destroyRef)` on reads.** Passing the `DestroyRef` explicitly is what lets a load method be called from anywhere — a refresh button, a route change — instead of only from the constructor, which is the one place the parameterless form works.

**`retry(2)` on writes.** A write is worth retrying; a failed read is usually better reported than repeated. Retrying is not a substitute for an error path, which is why both are present.

**`loading` and `error` set on every call, in both branches.** Every operation sets `loading` true and clears `error` before starting, and clears `loading` in both `next` and `error`. A spinner that never stops is almost always a missing `set(false)` in the error branch.

**`formatError` in one place.** Endpoints throw a labelled `Error` (see `shared-kernel.md`); this turns it into a sentence for the UI. One helper, so the wording stays consistent and views never inspect an error object.

## Stitching related entities

`assignCourierToOrder` is where "reference other aggregates by id" gets reconciled with "the template needs a name". The store loads both collections, then attaches the resolved object; the id remains the source of truth, and no view ever performs a second lookup. Do it after the load and after each write, so a newly created order is stitched too.

Keep it here rather than in a view — that is the whole reason the application layer exists on the client.

## Caching what should not be refetched

Some data is read-only and expensive: a menu per restaurant, a provider's reference list, anything fetched per selection. Key it and only fetch on a miss:

```typescript
private readonly menuBySectionSignal = signal<Record<string, MenuItem[]>>({});
private readonly currentSectionSignal = signal<string>('');

loadMenuForSection(sectionId: string): void {
  if (this.menuBySectionSignal()[sectionId]) return;              // already have it
  this.orderingApi.getMenuItems(sectionId).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
    next: items => this.menuBySectionSignal.update(menu => ({...menu, [sectionId]: items}))
  });
}

readonly currentSectionMenu = computed(() =>
  this.menuBySectionSignal()[this.currentSectionSignal()] ?? []);
```

The store, not the view, decides what has already been fetched.

## Commands in the store

A command-shaped use case looks the same from the outside; the store passes the command to the context API and reacts to the resource that comes back:

```typescript
private readonly lastPlacedOrderIdSignal = signal<number | null>(null);

placeOrder(command: PlaceOrderCommand): void {
  this.loadingSignal.set(true);
  this.errorSignal.set(null);
  this.orderingApi.placeOrder(command).subscribe({
    next: placed => {
      this.lastPlacedOrderIdSignal.set(placed.id);
      this.loadOrders();
      this.loadingSignal.set(false);
    },
    error: error => {
      this.errorSignal.set(this.formatError(error, 'Failed to place the order'));
      this.loadingSignal.set(false);
    }
  });
}
```

Navigation after a successful command belongs to the view that dispatched it, not to the store — a store that injects `Router` starts deciding what the UI does next, and becomes hard to reuse from a second screen.
