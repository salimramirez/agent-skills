# The presentation layer: views, components, and routing

Routed smart views, reusable dumb components, and how each context owns its routes.

The layer has exactly two kinds of component, and the split is the whole design:

- A **view** lives in `presentation/views/` — routed, "smart". It injects the store, reads its signals, dispatches user actions, and navigates.
- A **component** lives in `presentation/components/` — reusable, "dumb". It takes data through `input()`, reports intent through `output()`, and knows nothing about the store, the API, or the router.

```typescript
// ordering/presentation/views/order-list/order-list.ts
import {Component, inject} from '@angular/core';
import {Router} from '@angular/router';
import {OrderingStore} from '../../../application/ordering.store';
import {OrderCard} from '../../components/order-card/order-card';

/**
 * Routed view listing the active orders of the ordering context.
 */
@Component({
  selector: 'app-order-list',
  imports: [OrderCard],
  templateUrl: './order-list.html',
  styleUrl: './order-list.css'
})
export class OrderList {
  protected readonly store = inject(OrderingStore);
  private readonly router = inject(Router);

  protected readonly orders = this.store.activeOrders;

  protected cancelOrder(id: number): void {
    this.store.cancelOrder(id);
  }

  protected editOrder(id: number): void {
    this.router.navigate(['ordering/orders', id, 'edit']).then();
  }
}
```

```typescript
// ordering/presentation/components/order-card/order-card.ts
import {Component, input, output} from '@angular/core';

/**
 * Presents one order and reports the intent to cancel it.
 */
@Component({
  selector: 'app-order-card',
  templateUrl: './order-card.html',
  styleUrl: './order-card.css'
})
export class OrderCard {
  order = input.required<Order>();
  cancelRequested = output<number>();

  protected requestCancel(): void {
    this.cancelRequested.emit(this.order().id);
  }
}
```

A dumb component **emits, it does not decide**. `OrderCard` never calls the store; it says "the user asked to cancel this id" and the view decides what that means. That is what lets the same card appear in a dashboard, a search result, and a printout.

The view stays thin too: wire the store to the components, handle navigation, and stop. A view that filters, merges, or reformats domain data has taken work that belongs to a `computed()` in the store.

Signals are read straight in the template — `store.orders()`, `store.loading()`, `store.error()` — with no `async` pipe and no local copy of the data.

## File and class names

The class is `OrderList`, the file is `order-list.ts`, the selector is `app-order-list`, the template and styles are `order-list.html` and `order-list.css` beside it. No `.component` anywhere. A view and its template and styles form a folder named after the view.

## Routing

Each context owns a `*.routes.ts` **inside its `presentation/` folder**, exporting a `Routes` array that lazy-loads every view. Declaring the loaders as named constants above the array keeps the table readable:

```typescript
// ordering/presentation/ordering.routes.ts
import {Routes} from '@angular/router';

const orderList = () => import('./views/order-list/order-list').then(m => m.OrderList);
const orderForm = () => import('./views/order-form/order-form').then(m => m.OrderForm);

/**
 * Routes of the ordering bounded context.
 */
export const orderingRoutes: Routes = [
  {path: 'orders',           loadComponent: orderList},
  {path: 'orders/new',       loadComponent: orderForm},
  {path: 'orders/:id/edit',  loadComponent: orderForm}
];
```

The root `app.routes.ts` composes the contexts with `loadChildren`, mounts the shared app-wide views, and applies whatever guard the app needs:

```typescript
// app.routes.ts
import {Routes} from '@angular/router';
import {Home} from './shared/presentation/views/home/home';
import {identityGuard} from './identity/infrastructure/identity.guard';

const about = () => import('./shared/presentation/views/about/about').then(m => m.About);
const pageNotFound = () =>
  import('./shared/presentation/views/page-not-found/page-not-found').then(m => m.PageNotFound);
const orderingRoutes = () =>
  import('./ordering/presentation/ordering.routes').then(m => m.orderingRoutes);
const identityRoutes = () =>
  import('./identity/presentation/identity.routes').then(m => m.identityRoutes);

const baseTitle = 'QuickBite';

export const routes: Routes = [
  {path: 'home',      component: Home,      title: `${baseTitle} - Home`, canActivate: [identityGuard]},
  {path: 'about',     loadComponent: about, title: `${baseTitle} - About`},
  {path: 'ordering',  loadChildren: orderingRoutes, canActivate: [identityGuard]},
  {path: 'identity',  loadChildren: identityRoutes},
  {path: '',          redirectTo: '/home', pathMatch: 'full'},
  {path: '**',        loadComponent: pageNotFound, title: `${baseTitle} - Page Not Found`}
];
```

Three things this buys: the bounded-context boundary is visible in the routing table, the bundles split along it, and a `title` per route means the browser tab says where the user is. The catch-all comes last, and the sign-in routes stay outside the guard.

## The app shell

`app.ts` renders one thing — the layout — and the layout owns the chrome and the outlet:

```html
<!-- app.html -->
<app-layout/>
```

```html
<!-- shared/presentation/components/layout/layout.html -->
<header>
  <nav>
    @for (option of options; track option.link) {
      <a [routerLink]="option.link" routerLinkActive="active">{{ option.label }}</a>
    }
  </nav>
</header>
<router-outlet/>
<app-footer-content/>
```

Keeping the shell in `shared/presentation/components/layout/` rather than in `app.ts` is what lets the root component stay empty and the navigation list stay one array. The layout is the one place allowed to reach into several contexts at once — it links to all of them by route, which is the loosest coupling available.
