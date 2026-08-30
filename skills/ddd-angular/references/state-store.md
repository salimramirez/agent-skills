# The application layer: a signal store

The signal store that holds a context's state and talks to its API.

The application layer holds **state** and orchestrates **use cases**. A signal-based **store** fills the role command and query handlers play on the backend: it talks to the context API, exposes state through read-only signals, and keeps coordination out of the views.

```typescript
// ordering/application/order.store.ts
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { retry } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class OrderStore {
  private api = inject(OrderingApi);

  private readonly ordersSignal = signal<Order[]>([]);
  private readonly loadingSignal = signal(false);
  private readonly errorSignal = signal<string | null>(null);

  readonly orders = this.ordersSignal.asReadonly();
  readonly loading = this.loadingSignal.asReadonly();
  readonly error = this.errorSignal.asReadonly();
  readonly activeOrders = computed(() =>
    this.ordersSignal().filter(o => o.status !== 'DELIVERED' && o.status !== 'CANCELLED'));

  constructor() { this.loadOrders(); }          // a root store often loads eagerly

  orderById(id: number): Signal<Order | undefined> {
    return computed(() => this.ordersSignal().find(o => o.id === id));   // a reactive query
  }

  loadOrders(): void {
    this.loadingSignal.set(true);
    this.errorSignal.set(null);
    this.api.getOrders().pipe(takeUntilDestroyed()).subscribe({
      next: orders => { this.ordersSignal.set(orders); this.loadingSignal.set(false); },
      error: () => { this.errorSignal.set('Could not load orders'); this.loadingSignal.set(false); },
    });
  }

  addOrder(order: Order): void {
    this.loadingSignal.set(true);
    this.errorSignal.set(null);
    this.api.createOrder(order).pipe(retry(2)).subscribe({
      next: created => { this.ordersSignal.update(os => [...os, created]); this.loadingSignal.set(false); },
      error: () => { this.errorSignal.set('Could not create order'); this.loadingSignal.set(false); },
    });
  }
}
```

State is private; the outside reads it through `asReadonly()` signals and `computed()` derivations. `loadOrders`/`activeOrders`/`orderById` are the query side; `addOrder` (and `updateOrder`/`deleteOrder`, same shape) is the command side — each sets `loading`, clears `error`, retries writes, and updates the signal so the UI reflects the change. A new entity is created with `id: 0`; the backend assigns the real id and returns it. The store is also where **cross-entity coordination** lives — e.g. stitching each `Order`'s `Customer` in after a load — keeping that out of the views.
