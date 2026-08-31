# Cross-cutting concerns

Route protection, request interception, and app bootstrap — where they go and why.

None of this is domain modeling, and that is exactly why it needs a rule: left alone, cross-cutting code drifts into `shared/` and then into stores and components. What follows is the arrangement this skill uses. It is a recommendation, not a requirement.

## Route protection belongs to the context that owns the rule

React Router has no guard primitive, but it has **loaders**, which run before a route's component renders and can return a `redirect()`. That is the equivalent, and the *placement* rule transfers unchanged: the check lives in the context whose state it reads.

```typescript
// identity/infrastructure/authentication.loader.ts
import {redirect} from 'react-router';
import {useIdentityStore} from '../application/identity.store';

/**
 * Keeps unauthenticated visitors out of the routes that require an account.
 *
 * It reads the store outside React with `.getState()` — which only works because the
 * application layer imports nothing from React. A loader is not a component and has
 * no hooks available to it.
 */
export function authenticationLoader() {
    if (!useIdentityStore.getState().isSignedIn) return redirect('/identity/sign-in');
    return null;
}
```

The root router applies it, which is the only place other contexts touch it:

```tsx
{path: 'ordering', children: orderingRoutes, loader: authenticationLoader}
```

Attaching it to the parent route protects every child at once. The sign-in routes stay outside it.

A wrapper component (`<RequireAuth>`) is the other common answer and works fine; the loader runs earlier — before the protected component renders at all — which is why it is the default here.

## An interceptor belongs to the context that owns the credential

The token is `identity`'s state, so the interceptor that attaches it sits beside the loader:

```typescript
// identity/infrastructure/identity.interceptor.ts
import type {InternalAxiosRequestConfig} from 'axios';
import {useIdentityStore} from '../application/identity.store';

/** Attaches the bearer token to outgoing requests when a user is signed in. */
export function identityInterceptor(config: InternalAxiosRequestConfig): InternalAxiosRequestConfig {
    const {isSignedIn, token} = useIdentityStore.getState();
    if (isSignedIn && token) config.headers.Authorization = `Bearer ${token}`;
    return config;
}
```

**Pass it in; do not import it from the kernel.** `BaseApi` takes interceptors as a constructor option precisely so `shared/` never imports from a bounded context:

```typescript
// ordering/infrastructure/ordering-api.ts
export class OrderingApi extends BaseApi {
    constructor() {
        super({requestInterceptors: [identityInterceptor]});
        // …
    }
}
```

It is tempting to import the interceptor inside `base-api.ts` so every gateway gets it for free. That inverts the dependency rule — the shared kernel would depend on `identity`, and a project without an identity context could no longer use the kernel. One line per gateway is the price of keeping the arrow pointing the right way.

Both of these read a store from outside React. That is the payoff for the rule in `state-store.md`: a store that imported a hook could not be used here at all.

If a token must survive a reload, the **store** reads and writes it — Zustand's `persist` middleware, or plain `localStorage` in the action — so persistence stays a decision of the application layer.

## Component libraries and localization

A UI kit and a translation hook are real dependencies of a real app, and they belong in the **presentation layer only**. The test is simple:

- A **view or component** may use them freely.
- A **store, an entity, a command, an assembler, or a gateway** may not import either. An error a store publishes is a message key or a plain sentence; the component decides how it is rendered and in what language.

## App bootstrap

`main.tsx` mounts the router and nothing else:

```tsx
// main.tsx
import {StrictMode} from 'react';
import {createRoot} from 'react-dom/client';
import {RouterProvider} from 'react-router';
import {router} from './router';

createRoot(document.getElementById('root')!).render(
    <StrictMode>
        <RouterProvider router={router}/>
    </StrictMode>
);
```

There is no store provider to install, and that is not an omission: a Zustand store is a module, created when it is first imported, so there is nothing to wire and no ordering constraint to get wrong.

`StrictMode` double-invokes effects in development, which is worth keeping: an effect that fetches twice is telling you it lacks the `ordersLoaded` guard from `state-store.md`, and you would rather learn that now.

Keep `main.tsx` to wiring. Nothing domain-specific belongs here.
