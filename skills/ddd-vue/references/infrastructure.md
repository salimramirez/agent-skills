# Infrastructure: the CRUD path

Assemblers, endpoints, and the context gateway — the read/write path for a record.

Two files per aggregate, plus one gateway per context. They rest on the kernel's `BaseApi` and `BaseEndpoint` (see `shared-kernel.md`), and each has exactly one job.

## 1. The assembler — `order.assembler.js`

The anti-corruption layer, and the only file that knows both the wire shape and the domain shape. Methods are **static**: an assembler holds no state, it is a translation rather than a collaborator.

```javascript
// ordering/infrastructure/order.assembler.js
import {Order} from '../domain/model/order.entity.js';

/**
 * One order exactly as the API sends it, snake case and all.
 *
 * @typedef {Object} OrderApiResource
 * @property {number} id
 * @property {number} customer_id
 * @property {Array<{menu_item_id: number, quantity: number}>} lines
 * @property {string} delivery_address
 * @property {string} status
 * @property {number} total
 */

/**
 * Anti-corruption layer between the orders API and the ordering model.
 *
 * @class OrderAssembler
 */
export class OrderAssembler {
    /**
     * Builds one entity from a resource payload.
     *
     * @param {OrderApiResource} resource - Resource as the API returned it.
     * @returns {Order} The entity the rest of the app works with.
     */
    static toEntityFromResource(resource) {
        return new Order({
            id: resource.id,
            customerId: resource.customer_id,                       // the API's naming stops here
            lines: resource.lines.map(line => ({
                menuItemId: line.menu_item_id, quantity: line.quantity
            })),
            deliveryAddress: resource.delivery_address,
            status: resource.status,
            total: resource.total
        });
    }

    /**
     * Builds the collection from a response, tolerating both wire shapes.
     *
     * @param {import('axios').AxiosResponse<Array<Object>|Object>} response - The response.
     * @returns {Order[]} The entities it carried.
     */
    static toEntitiesFromResponse(response) {
        if (response.status !== 200) return [];
        const resources = response.data instanceof Array ? response.data : response.data['orders'];
        return resources.map(resource => this.toEntityFromResource(resource));
    }
}
```

Everything the API does that your model should not inherit — snake case, a flattened field, a date as a string, a null where the domain wants a default — is absorbed in these two methods. This is the most valuable file in the layer: when the backend renames a field, exactly one file changes.

**Write the wire shape as a `@typedef`.** It is the one thing in the codebase with no runtime declaration behind it: an entity has its constructor, a prop has `defineProps`, but the resource is whatever arrived over the network. Naming it is what makes a mistyped wire field — `resource.customerId` where the API sends `customer_id` — an error the editor reports, rather than an `undefined` that reaches a view and renders blank. This is the one place where spelling a shape out in JSDoc buys something that shorter code cannot.

Two more details worth copying deliberately:

- **`toEntitiesFromResponse` accepts a bare array or an envelope.** A mock server that returns `[…]` and a real backend that returns `{ orders: […] }` both work without touching the store.
- **A non-200 yields an empty collection, not a throw.** The store's `.catch` already records transport failures; a view rendering nothing beats a view that crashes. If a failed read must be visible, push to `errors` in the store rather than throwing from here.

## 2. The context gateway — `ordering-api.js`

One per bounded context, extending `BaseApi`. It owns the context's endpoints and exposes them as operations named in the ubiquitous language.

```javascript
// ordering/infrastructure/ordering-api.js
import {BaseApi} from '../../shared/infrastructure/base-api.js';
import {BaseEndpoint} from '../../shared/infrastructure/base-endpoint.js';

const ordersEndpointPath = import.meta.env.VITE_ORDERS_ENDPOINT_PATH;
const menuItemsEndpointPath = import.meta.env.VITE_MENU_ITEMS_ENDPOINT_PATH;

/**
 * The API of the ordering bounded context.
 *
 * @class OrderingApi
 * @extends BaseApi
 */
export class OrderingApi extends BaseApi {
    #ordersEndpoint;
    #menuItemsEndpoint;

    /**
     * @param {Object} [options] - Forwarded to {@link BaseApi}, including interceptors.
     */
    constructor(options = {}) {
        super(options);
        this.#ordersEndpoint = new BaseEndpoint(this, ordersEndpointPath);
        this.#menuItemsEndpoint = new BaseEndpoint(this, menuItemsEndpointPath);
    }

    /** @returns {Promise<import('axios').AxiosResponse>} Every order. */
    getOrders() {
        return this.#ordersEndpoint.getAll();
    }

    /**
     * @param {Order} order - Order built by the form, with `id: null`.
     * @returns {Promise<import('axios').AxiosResponse>} The response.
     */
    createOrder(order) {
        return this.#ordersEndpoint.create(order);
    }

    /**
     * @param {Order} order - Order carrying the new state.
     * @returns {Promise<import('axios').AxiosResponse>} The response.
     */
    updateOrder(order) {
        return this.#ordersEndpoint.update(order.id, order);
    }

    /**
     * @param {number} id - Identity of the order to delete.
     * @returns {Promise<import('axios').AxiosResponse<void>>} The response.
     */
    deleteOrder(id) {
        return this.#ordersEndpoint.delete(id);
    }

    /**
     * Cancels an order.
     *
     * @remarks
     * A sub-resource POST rather than a `update` — cancelling is a transition the
     * backend decides, not a field the client sets.
     *
     * @param {number} id - Identity of the order to cancel.
     * @returns {Promise<import('axios').AxiosResponse>} The response.
     */
    cancelOrder(id) {
        return this.http.post(`${ordersEndpointPath}/${id}/cancel`);
    }

    /** @returns {Promise<import('axios').AxiosResponse>} Every menu item. */
    getMenuItems() {
        return this.#menuItemsEndpoint.getAll();
    }
}
```

`cancelOrder` reaches for `this.http` directly, which is what `BaseApi`'s getter is for: not every operation is CRUD over a collection, and an endpoint that only ever POSTs to one sub-path earns nothing.

Endpoints are `#private`, so the store depends on `OrderingApi` and can never reach past it. A context with three aggregates has three endpoint fields here and one store talking to all of them.

## The round trip

```
read    getOrders() → AxiosResponse → OrderAssembler.toEntitiesFromResponse → Order[]
write   Order → create/update → AxiosResponse → toEntityFromResource → Order
delete  deleteOrder(id) → AxiosResponse<void>
```

Note where the assembler sits on a read: **in the store**, not in the endpoint. The gateway hands back a response and the store turns it into entities. See `state-store.md`.

## Why there is no `toResourceFromEntity`

On the write side the entity goes to the API **as it is** — `create(order)` serializes the instance. That works because these entities are public fields whose names already match the wire, and it saves a method that would otherwise be pure duplication.

It stops working the moment the two shapes diverge: the API expects `customer_id` while the entity says `customerId`, or the entity carries a hydrated `lines` array of `OrderLine` instances the API will not accept, or a field exists only on the client. At that point add the missing half to the assembler and call it from the gateway:

```javascript
static toResourceFromEntity(entity) {
    return {
        id: entity.id,
        customer_id: entity.customerId,
        lines: entity.lines.map(line => ({menu_item_id: line.menuItemId, quantity: line.quantity})),
        delivery_address: entity.deliveryAddress
    };
}
```

Sending the entity directly is a reasonable default, not a principle. The principle is that the translation lives in the assembler — including when the translation happens to be the identity function.
