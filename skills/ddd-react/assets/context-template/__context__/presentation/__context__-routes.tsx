import type {RouteObject} from 'react-router';
import {__Entity__List} from './views/__Entity__List';
import {__Entity__Form} from './views/__Entity__Form';

/**
 * Routes of the __context__ bounded context, mounted by the root router under
 * `/__context__`. Paths stay relative here; `__context__-paths.ts` owns the
 * absolute ones so there is exactly one place a URL is written down.
 */
export const __context__Routes: RouteObject[] = [
    {path: '__entities-kebab__', Component: __Entity__List},
    {path: '__entities-kebab__/new', Component: __Entity__Form},
    {path: '__entities-kebab__/:id/edit', Component: __Entity__Form}
];
