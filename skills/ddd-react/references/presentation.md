# The presentation layer: views, components, and routing

Routed smart views, reusable dumb components, and how each context owns its routes and its URLs.

The layer has exactly two kinds of component, and the split is the whole design — React named it *container and presentational* long before this skill did:

- A **view** lives in `presentation/views/` — routed, "smart". It selects from the store, dispatches actions, and navigates.
- A **component** lives in `presentation/components/` — reusable, "dumb". It takes data through props, reports intent through callback props, and knows nothing about the store, the gateway, or the router.

```tsx
// ordering/presentation/views/OrderList.tsx
import {useEffect} from 'react';
import {useNavigate} from 'react-router';
import {useOrderingStore} from '../../application/ordering.store';
import {orderingPaths} from '../ordering-paths';
import {OrderCard} from '../components/OrderCard';

/** Routed view listing the orders of the ordering context. */
export function OrderList() {
    const navigate = useNavigate();
    const orders = useOrderingStore(state => state.orders);
    const errors = useOrderingStore(state => state.errors);
    const ordersLoaded = useOrderingStore(state => state.ordersLoaded);
    const fetchOrders = useOrderingStore(state => state.fetchOrders);
    const deleteOrder = useOrderingStore(state => state.deleteOrder);

    useEffect(() => {
        if (!ordersLoaded) void fetchOrders();
    }, [ordersLoaded, fetchOrders]);

    return (
        <section>
            <h1>Orders</h1>
            {!ordersLoaded && <p>Loading…</p>}
            {errors.length > 0 && <p role="alert">{errors.map(error => error.message).join(', ')}</p>}

            {orders.map(order => (
                <OrderCard
                    key={order.id}
                    order={order}
                    onEditRequested={id => navigate(orderingPaths.editOrder(id))}
                    onCancelRequested={id => void deleteOrder(id)}
                />
            ))}

            <button type="button" onClick={() => navigate(orderingPaths.newOrder())}>New Order</button>
        </section>
    );
}
```

```tsx
// ordering/presentation/components/OrderCard.tsx
import type {Order} from '../../domain/model/order.entity';

interface OrderCardProps {
    order: Order;
    onEditRequested: (id: number) => void;
    onCancelRequested: (id: number) => void;
}

/** Presents one order and reports what the user wants done with it. */
export function OrderCard({order, onEditRequested, onCancelRequested}: OrderCardProps) {
    return (
        <article>
            <h2>Order #{order.id}</h2>
            <p>{order.itemCount()} items · {order.status}</p>
            <button type="button" onClick={() => onEditRequested(order.id!)}>Edit</button>
            {order.isCancellable() && (
                <button type="button" onClick={() => onCancelRequested(order.id!)}>Cancel</button>
            )}
        </article>
    );
}
```

A dumb component **reports, it does not decide**. `OrderCard` never calls the store; it says "the user asked to cancel this id" and the view decides what that means. That is what lets the same card appear in a dashboard, a search result, and a printout.

Two details keep the split honest:

- **Type the prop as the entity, not as a shape.** `order: Order` is what makes a skipped assembler a compile error — and it works precisely because `Order` has methods, so a lookalike payload cannot satisfy it structurally. See `domain-model.md`.
- **`order.isCancellable()` in the markup, not the rule itself.** The component asks the entity rather than re-deriving, so the same question from three components gets the same answer.

The view stays thin too: wire the store to the components, handle navigation, stop. A view that filters, merges, or reformats domain data has taken work that belongs to the store or to a method on the entity.

## URLs live in one file per context

React Router has **no named routes** — navigation is by path. A path typed into `navigate()` is a broken link waiting for someone to rename a segment, so each context owns a `*-paths.ts` and nothing else writes a URL:

```typescript
// ordering/presentation/ordering-paths.ts

/**
 * Every URL the ordering context owns, built in one place.
 *
 * These builders give the guarantee a route name would in another router: change a
 * segment here and every caller follows.
 */
export const orderingPaths = {
    orders: () => '/ordering/orders',
    newOrder: () => '/ordering/orders/new',
    editOrder: (id: number | string) => `/ordering/orders/${id}/edit`
} as const;
```

Functions rather than string constants, so a parameterised route reads the same as a static one and the parameter is typed. `as const` keeps the object from widening.

## Routing

Each context owns a `*-routes.tsx` **inside its `presentation/` folder**, exporting a `RouteObject[]`:

```tsx
// ordering/presentation/ordering-routes.tsx
import type {RouteObject} from 'react-router';
import {OrderList} from './views/OrderList';
import {OrderForm} from './views/OrderForm';

/**
 * Routes of the ordering bounded context, mounted by the root router under
 * `/ordering`. Paths stay relative here; `ordering-paths.ts` owns the absolute ones.
 */
export const orderingRoutes: RouteObject[] = [
    {path: 'orders', Component: OrderList},
    {path: 'orders/new', Component: OrderForm},
    {path: 'orders/:id/edit', Component: OrderForm}
];
```

Relative paths inside the context, absolute ones only in `ordering-paths.ts`. That is what keeps `/ordering` written down twice rather than twenty times.

The root `router.tsx` composes the contexts as children of the shell:

```tsx
// router.tsx
import {createBrowserRouter} from 'react-router';
import {Layout} from './shared/presentation/components/Layout';
import {orderingRoutes} from './ordering/presentation/ordering-routes';
import {identityRoutes} from './identity/presentation/identity-routes';
import {authenticationLoader} from './identity/infrastructure/authentication.loader';

export const router = createBrowserRouter([
    {
        path: '/',
        Component: Layout,
        children: [
            {path: 'ordering', children: orderingRoutes, loader: authenticationLoader},
            {path: 'identity', children: identityRoutes}
        ]
    }
]);
```

Lazy-loading is opt-in per route with `lazy`, and worth adding once a context is large enough to matter; the boundary is already visible without it.

## The app shell

`Layout` owns the chrome and renders the `<Outlet/>`; `main.tsx` mounts the router and nothing else:

```tsx
// shared/presentation/components/Layout.tsx
import {Link, Outlet} from 'react-router';
import {orderingPaths} from '../../../ordering/presentation/ordering-paths';

const options = [
    {label: 'Orders', to: orderingPaths.orders()}
];

/** The app shell — chrome around whatever the router puts in the outlet. */
export function Layout() {
    return (
        <>
            <header>
                <nav>
                    {options.map(option => <Link key={option.label} to={option.to}>{option.label}</Link>)}
                </nav>
            </header>
            <Outlet/>
        </>
    );
}
```

The layout is the one place allowed to reach into several contexts at once — and it does so through their `*-paths.ts`, which is the loosest coupling available.

A real app also puts a component library here and a translation hook in the components. Keep both in the presentation layer: a store, an entity, an assembler, or a gateway must not import either.
