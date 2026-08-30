# The presentation layer: views, components, and routing

Routed views, reusable components, and how each context owns its lazy routes.

The presentation layer has two kinds of component. A **view** is a routed, "smart" component: it injects the store, reads its signals, and dispatches user actions. A **component** is a reusable, "dumb" piece: it takes data via `input()`, reports intent via `output()`, and knows nothing about the store or the API.

```typescript
// ordering/presentation/views/order-list/order-list.ts  (routed view — talks to the store)
@Component({
  selector: 'app-order-list',
  imports: [OrderItem],
  templateUrl: './order-list.html',
})
export class OrderList {
  private store = inject(OrderStore);
  private router = inject(Router);

  protected readonly orders = this.store.activeOrders;     // a signal, read straight in the template

  deleteOrder(id: number): void { this.store.deleteOrder(id); }
  editOrder(id: number): void { this.router.navigate(['ordering/orders', id, 'edit']); }
}
```

```typescript
// ordering/presentation/components/order-item/order-item.ts  (reusable — no store)
@Component({
  selector: 'app-order-item',
  templateUrl: './order-item.html',
})
export class OrderItem {
  order = input.required<Order>();
  cancel = output<number>();          // emits the id of the order to cancel
}
```

Business or coordination logic in a component is the frontend version of the fat-controller smell — push it into the store. The view stays thin too: it wires the store to the components and handles navigation, nothing more.

## Routing

Each context owns a `*.routes.ts` **inside its `presentation/` folder**, exporting a `Routes` array that lazy-loads its views with `loadComponent`:

```typescript
// ordering/presentation/ordering.routes.ts
import { Routes } from '@angular/router';

const orderList = () => import('./views/order-list/order-list').then(m => m.OrderList);
const orderForm = () => import('./views/order-form/order-form').then(m => m.OrderForm);

export const orderingRoutes: Routes = [
  { path: 'orders',          loadComponent: orderList },
  { path: 'orders/new',      loadComponent: orderForm },
  { path: 'orders/:id/edit', loadComponent: orderForm },
];
```

The root `app.routes.ts` composes the contexts with `loadChildren`, mounts the shared app-wide views, and applies cross-cutting guards:

```typescript
// app.routes.ts
const orderingRoutes = () => import('./ordering/presentation/ordering.routes').then(m => m.orderingRoutes);

export const routes: Routes = [
  { path: 'home',     component: Home, canActivate: [authGuard] },
  { path: 'ordering', loadChildren: orderingRoutes, canActivate: [authGuard] },
  { path: '',         redirectTo: '/home', pathMatch: 'full' },
  { path: '**',       loadComponent: () => import('./shared/presentation/views/page-not-found/page-not-found').then(m => m.PageNotFound) },
];
```

Lazy-loading each context (and each view) keeps the bounded-context boundary visible at the routing level, and the bundles split along it.
