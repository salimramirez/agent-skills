const __entity__List = () => import('./views/__entity-kebab__-list.vue');
const __entity__Form = () => import('./views/__entity-kebab__-form.vue');

/**
 * Routes of the __context__ bounded context.
 *
 * @remarks
 * The context owns its routes and lazy-loads every view, so the boundary shows up
 * in the routing table and the bundles split along it. The root router mounts
 * this array as `children` of `/__context__`. Every route is named, because
 * navigation goes by name -- a path typed into `router.push` is a broken link
 * waiting for someone to rename a segment.
 *
 * @type {import('vue-router').RouteRecordRaw[]}
 */
const __context__Routes = [
    {path: '__entities-kebab__',            name: '__context__-__entities-kebab__',      component: __entity__List, meta: {title: '__Entities__'}},
    {path: '__entities-kebab__/new',        name: '__context__-__entity-kebab__-new',    component: __entity__Form, meta: {title: 'New __Entity__'}},
    {path: '__entities-kebab__/:id/edit',   name: '__context__-__entity-kebab__-edit',   component: __entity__Form, meta: {title: 'Edit __Entity__'}}
];

export default __context__Routes;
