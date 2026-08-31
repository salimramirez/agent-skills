# Cross-cutting concerns

Guards, interceptors, localization, and app bootstrap — where they go and why.

None of this is domain modeling, and that is exactly why it needs a rule: left alone, cross-cutting code drifts into `shared/` and then into stores and templates. What follows is the arrangement these conventions use. It is a recommendation, not a requirement.

## A guard belongs to the context that owns the rule

An authentication guard is not generic plumbing: it enforces a rule belonging to a specific context, and it reads that context's store. So it lives in **that context's `infrastructure/` folder**, not in `shared/`.

```javascript
// identity/infrastructure/authentication.guard.js
import useIdentityStore from '../application/identity.store.js';

/**
 * Keeps unauthenticated visitors out of the routes that require an account.
 *
 * @param {import('vue-router').RouteLocationNormalized} to - Target route.
 * @returns {boolean | {name: string}} True to allow, or a route to redirect to.
 */
export const authenticationGuard = (to) => {
    const store = useIdentityStore();
    const publicRouteNames = ['identity-sign-in', 'identity-sign-up', 'about', 'not-found'];
    if (store.isSignedIn || publicRouteNames.includes(to.name)) return true;
    return {name: 'identity-sign-in'};
};
```

Match on **route names, not paths**. A path list breaks the moment someone renames a segment, and it breaks silently — by locking users out or, worse, by letting them in.

The root router applies it, which is the only place other contexts touch it — by name, not by reaching into `identity`:

```javascript
// router.js
router.beforeEach((to) => {
    document.title = `QuickBite - ${to.meta.title ?? ''}`;
    return authenticationGuard(to);
});
```

The same reasoning covers any guard whose decision comes from a domain rule: an `ordering.guard.js` that blocks checkout on an empty cart belongs to `ordering`.

## An interceptor belongs to the context that owns the credential

The token is `identity`'s state, so the interceptor that attaches it sits beside the guard:

```javascript
// identity/infrastructure/identity.interceptor.js
import useIdentityStore from '../application/identity.store.js';

/**
 * Attaches the bearer token to outgoing requests when a user is signed in.
 *
 * @param {import('axios').InternalAxiosRequestConfig} config - Request configuration.
 * @returns {import('axios').InternalAxiosRequestConfig} The configuration to send.
 */
export const identityInterceptor = (config) => {
    const store = useIdentityStore();
    if (store.isSignedIn) config.headers.Authorization = `Bearer ${store.currentToken}`;
    return config;
};
```

**Pass it in; do not import it from the kernel.** `BaseApi` takes interceptors as a constructor option precisely so `shared/` never imports from a bounded context:

```javascript
// ordering/infrastructure/ordering-api.js
import {identityInterceptor} from '../../identity/infrastructure/identity.interceptor.js';

export class OrderingApi extends BaseApi {
    constructor() {
        super({requestInterceptors: [identityInterceptor]});
        // …
    }
}
```

It is tempting to import the interceptor inside `base-api.js` so every gateway gets it for free. That inverts the dependency rule — the shared kernel would depend on `identity`, and a project without an identity context could no longer use the kernel. One line per gateway is the price of keeping the arrow pointing the right way.

Because a store is read inside the interceptor, Pinia must be installed before the first request goes out. Constructing gateways at module scope in a store file (see `state-store.md`) is fine: the module only evaluates when the store is first used, which is after `app.use(pinia)`.

If a token must survive a reload, the **store** reads and writes it (`localStorage`, or a cookie), so persistence stays a decision of the application layer rather than of the interceptor.

## Localization and component libraries

A UI kit and a translation composable are real dependencies of a real app, and they belong in the **presentation layer only**. The test is simple:

- A **view or component** may use `useI18n()` and the library's components freely.
- A **store, an entity, a command, an assembler, or a gateway** may not import either. An error a store publishes is a message key or a plain sentence; the template decides how it is rendered and in what language.

A language switcher is app-wide UI, so it lives in `shared/presentation/components/` next to the layout. Translation files sit outside the context folders entirely — they are assets, not code.

## App bootstrap

Three small modules, each with one job, and `main.js` composing them:

```javascript
// pinia.js
import {createPinia} from 'pinia';

/** @type {import('pinia').Pinia} Shared Pinia instance for every context store. */
const pinia = createPinia();
export default pinia;
```

```javascript
// main.js
import {createApp} from 'vue';
import App from './app.vue';
import router from './router.js';
import pinia from './pinia.js';
import i18n from './i18n.js';
import './style.css';

createApp(App)
    .use(pinia)      // before the router: guards read stores
    .use(router)
    .use(i18n)
    .mount('#app');
```

Order matters in exactly one place: **Pinia before the router**, because the navigation guard resolves a store on the first navigation. Get it backwards and the app throws on load with an error that does not mention either.

Keep `main.js` to wiring. Nothing domain-specific belongs here: stores and gateways are reached through their own modules, so a context appearing in this file usually means someone worked around a circular import instead of fixing it.
