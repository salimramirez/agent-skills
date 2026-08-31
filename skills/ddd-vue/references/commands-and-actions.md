# Commands and actions: the non-CRUD path

When the write is an intent rather than a record, and when the API is not yours.

`BaseEndpoint` covers "save this entity". Plenty of real operations are not that: placing an order from a cart, cancelling with a reason, signing in, asking a third party for a delivery estimate. Those get a different path — same anti-corruption idea, one more class.

## The shape

```
PlaceOrderCommand  →  gateway  →  POST
                                    ↓
Order  ←  toEntityFromResource  ←  PlaceOrderResource  ←  toResourceFromResponse
```

Three files beside the command itself (which lives in `domain/model/`, see `domain-model.md`): a resource class, an assembler, and an operation on the context gateway.

## 1. The resource — `place-order.resource.js`

What comes back. A **class**, not a bare object — not because it validates anything (a missing field lands as `undefined` here exactly as it would anywhere else), but because it gives the wire shape a name, one place to document it, and one place to add a check the day you want one.

```javascript
// ordering/infrastructure/place-order.resource.js

/**
 * What the platform returns after placing an order.
 *
 * @class PlaceOrderResource
 */
export class PlaceOrderResource {
    /**
     * @param {Object} params - Resource payload.
     * @param {number} params.id - Identity of the created order.
     * @param {string} params.status - Its initial status.
     * @param {number} params.total - The amount charged.
     * @param {string} params.estimatedDeliveryAt - ISO 8601 estimate.
     */
    constructor({id, status, total, estimatedDeliveryAt}) {
        this.id = id;
        this.status = status;
        this.total = total;
        this.estimatedDeliveryAt = estimatedDeliveryAt;
    }
}
```

## 2. The assembler — `place-order.assembler.js`

Maps the response into that resource. It is a different shape of assembler from the CRUD one — an action returns a confirmation, not a collection:

```javascript
// ordering/infrastructure/place-order.assembler.js
import {PlaceOrderResource} from './place-order.resource.js';

/**
 * Anti-corruption layer for the place-order call.
 *
 * @class PlaceOrderAssembler
 */
export class PlaceOrderAssembler {
    /**
     * @param {import('axios').AxiosResponse<Object>} response - The response.
     * @returns {?PlaceOrderResource} The resource, or null when the call did not succeed.
     */
    static toResourceFromResponse(response) {
        if (response.status !== 200 && response.status !== 201) return null;
        return new PlaceOrderResource(response.data);
    }
}
```

Returning `null` rather than throwing keeps the failure a value the store can branch on. The store decides what the user sees.

## 3. The operation on the gateway

The command is the body. No separate request class is needed when its fields already match what the API expects — the same reasoning as `toResourceFromEntity` in `infrastructure.md`, and it fails the same way when the shapes diverge.

```javascript
// ordering/infrastructure/ordering-api.js
const placeOrderEndpointPath = import.meta.env.VITE_PLACE_ORDER_ENDPOINT_PATH;

// inside OrderingApi
this.#placeOrderEndpoint = new BaseEndpoint(this, placeOrderEndpointPath);

/**
 * @param {PlaceOrderCommand} command - The customer's intent.
 * @returns {Promise<import('axios').AxiosResponse>} The response.
 */
placeOrder(command) {
    return this.#placeOrderEndpoint.create(command);
}
```

`create` is a POST, which is what an action almost always is. Reusing the CRUD endpoint for it is deliberate: an action is still just one HTTP call, and a second base class would earn nothing.

## In the store

```javascript
/**
 * Places the order currently in the cart.
 *
 * @param {PlaceOrderCommand} command - The customer's intent.
 * @param {import('vue-router').Router} router - Router used to redirect on success.
 * @returns {void}
 */
function placeOrder(command, router) {
    orderingApi.placeOrder(command)
        .then(response => {
            const resource = PlaceOrderAssembler.toResourceFromResponse(response);
            if (!resource) {
                errors.value.push(new Error('The order could not be placed'));
                return;
            }
            lastPlacedOrderId.value = resource.id;
            fetchOrders();
            router.push({name: 'ordering-orders'});
        })
        .catch(error => errors.value.push(error));
}
```

Passing the `router` in as a parameter is the convention for a command that ends in navigation. It keeps the store from importing the router module, so the same action can be dispatched from a different screen that wants to go somewhere else.

## When the API is not yours

A third-party provider is where the anti-corruption layer earns its name — you do not get to ask them to rename a field. Same structure, two differences: its own env prefix, and its query parameters and key stay inside the gateway.

```javascript
// ordering/infrastructure/delivery-estimate-api.js
import axios from 'axios';

const mapsApiUrl = import.meta.env.VITE_MAPS_API_URL;
const mapsApiKey = import.meta.env.VITE_MAPS_API_KEY;
const estimateEndpointPath = import.meta.env.VITE_ESTIMATE_ENDPOINT_PATH;

const http = axios.create({baseURL: mapsApiUrl, params: {key: mapsApiKey}});

/**
 * Delivery estimates from the maps provider.
 *
 * @remarks
 * The provider's key and parameter names never leave this file; callers ask for
 * an estimate between two addresses and get minutes back. It does not extend
 * {@link BaseApi} because it is not the platform — a different host, a different
 * auth scheme, and none of the platform's interceptors should apply to it.
 *
 * @class DeliveryEstimateApi
 */
export class DeliveryEstimateApi {
    /**
     * @param {string} origin - Where the courier starts.
     * @param {string} destination - Where the order goes.
     * @returns {Promise<import('axios').AxiosResponse>} The response.
     */
    getEstimate(origin, destination) {
        return http.get(estimateEndpointPath, {params: {origin, destination}});
    }
}
```

Two things this shows. Default `params` on the instance apply the key to every call without repeating it. And **not everything extends `BaseApi`** — that base carries your platform's base URL and interceptors, and pointing it at a third party would send your bearer token to someone else's server.

A read-only integration often needs no write side at all: one gateway, one assembler with a single inbound method, and a store that caches what came back. That is a complete, honest context — a context is not obliged to have CRUD.
