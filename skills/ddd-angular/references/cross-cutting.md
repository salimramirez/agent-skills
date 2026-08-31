# Cross-cutting concerns

Guards, interceptors, localization, and app bootstrap — where they go and why.

None of this is domain modeling, and that is exactly why it needs a rule: left alone, cross-cutting code drifts into `shared/` and then into stores and templates. What follows is the arrangement these conventions use. It is a recommendation, not a requirement — adapt it to what your app actually needs.

## A guard belongs to the context that owns the rule

An authentication guard is not generic plumbing: it enforces a rule that belongs to a specific context, and it reads that context's store. So it lives in **that context's `infrastructure/` folder**, not in `shared/`.

```typescript
// identity/infrastructure/identity.guard.ts
import {inject} from '@angular/core';
import {CanActivateFn, Router} from '@angular/router';
import {IdentityStore} from '../application/identity.store';

/**
 * Keeps unauthenticated visitors out of the routes that require an account.
 */
export const identityGuard: CanActivateFn = () => {
  const store = inject(IdentityStore);
  const router = inject(Router);
  if (store.isSignedIn()) return true;
  router.navigate(['/identity/sign-in']).then();
  return false;
};
```

The root router applies it (see `presentation.md`), which is the only place other contexts touch it — by name, not by reaching into `identity`. The same reasoning covers any guard whose decision comes from a domain rule: an `ordering.guard.ts` that blocks checkout without a cart belongs to `ordering`.

## An interceptor belongs to the context that owns the credential

Same argument. The token is `identity`'s state, so the interceptor that attaches it sits beside the guard:

```typescript
// identity/infrastructure/identity.interceptor.ts
import {HttpInterceptorFn} from '@angular/common/http';
import {inject} from '@angular/core';
import {IdentityStore} from '../application/identity.store';

/**
 * Attaches the bearer token to outgoing requests when there is one.
 */
export const identityInterceptor: HttpInterceptorFn = (request, next) => {
  const token = inject(IdentityStore).currentToken();
  return next(token
    ? request.clone({headers: request.headers.set('Authorization', `Bearer ${token}`)})
    : request);
};
```

Because it is registered globally, it reaches every context's endpoints — which is the point, and also the reason endpoints stay free of auth code. An endpoint that sets its own `Authorization` header is a sign the interceptor was forgotten.

If a token needs to survive a reload, the store is what reads and writes it (`localStorage` or a cookie), so persistence stays a decision of the application layer rather than of the interceptor.

## Localization and component libraries

A UI kit and a translation pipe are real dependencies of a real app, and they belong in the **presentation layer only**. The test is simple:

- A **view or component template** may use them freely.
- A **store, an entity, a command, an assembler, or an endpoint** may not import either. An error message a store publishes is a message key or a plain sentence; the template decides how it is rendered and in what language.

A language switcher is app-wide UI, so it lives in `shared/presentation/components/`, next to the layout that hosts it. Translation files sit outside `src/app/` entirely — they are assets, not code.

This is also why `BaseForm.errorMessageForControl` is a single method: it is the one seam where validation wording is produced, so returning a translation key there localizes every form at once.

## App bootstrap

`app.config.ts` is where the cross-cutting wiring is registered — the HTTP client with its interceptors, the router with the root routes, and whatever the app's own libraries need:

```typescript
// app.config.ts
import {ApplicationConfig} from '@angular/core';
import {provideHttpClient, withFetch, withInterceptors} from '@angular/common/http';
import {provideRouter} from '@angular/router';
import {routes} from './app.routes';
import {identityInterceptor} from './identity/infrastructure/identity.interceptor';

/**
 * Application-wide providers.
 */
export const appConfig: ApplicationConfig = {
  providers: [
    provideHttpClient(withFetch(), withInterceptors([identityInterceptor])),
    provideRouter(routes)
  ]
};
```

Keep it to wiring. Nothing domain-specific belongs here: stores and context APIs are `providedIn: 'root'` and register themselves, so a store appearing in this list usually means someone worked around a circular import instead of fixing it.

Angular's own defaults change between versions — change detection, error listeners, hydration. Add or drop those providers according to the version you are on; none of them affect the structure in this skill.
