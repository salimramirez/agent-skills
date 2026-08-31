import {Routes} from '@angular/router';

const __entity__List = () =>
  import('./views/__entity-kebab__-list/__entity-kebab__-list').then(m => m.__Entity__List);
const __entity__Form = () =>
  import('./views/__entity-kebab__-form/__entity-kebab__-form').then(m => m.__Entity__Form);

/**
 * Routes of the __context__ bounded context.
 *
 * @remarks
 * The context owns its routes and lazy-loads every view, so the boundary is
 * visible in the routing table and the bundles split along it. The root router
 * mounts this array with `loadChildren`.
 */
export const __context__Routes: Routes = [
  {path: '__entities-kebab__',           loadComponent: __entity__List},
  {path: '__entities-kebab__/new',       loadComponent: __entity__Form},
  {path: '__entities-kebab__/:id/edit',  loadComponent: __entity__Form}
];
