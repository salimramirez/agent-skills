# Commands and actions: the non-CRUD path

When the write is an intent rather than a record, and when the API is not yours.

`BaseApiEndpoint` covers "save this entity". Plenty of real operations are not that: placing an order from a cart, cancelling with a reason, signing in, asking a third-party service for a delivery estimate. Those get a different path through infrastructure — same anti-corruption idea, one more DTO.

## The shape

```
PlaceOrderCommand  →  toRequestFromCommand  →  PlaceOrderRequest  →  POST
                                                        ↓
Order  ←  toEntityFromResource  ←  OrderResource  ←  toResourceFromResponse  ←  PlaceOrderResponse
```

Four files, mirroring the CRUD four: the command (in `domain/model/`, see `domain-model.md`), a request DTO, a response DTO, and an assembler that maps command to request and response to resource.

## 1. The request DTO — `place-order.request.ts`

What goes in the body. It exists because the body is **not** any resource — a cart and an address are not an order.

```typescript
// ordering/infrastructure/place-order.request.ts

/**
 * Body of a place-order call.
 */
export interface PlaceOrderRequest {
  customer_id: number;
  lines: {menu_item_id: number, quantity: number}[];
  delivery_address: string;
}
```

## 2. The response DTO — `place-order-response.ts`

What comes back. When the answer is a single object rather than a collection, the response and the resource are the same shape, and the convention states that rather than duplicating it:

```typescript
// ordering/infrastructure/place-order-response.ts
import {BaseResource, BaseResponse} from '../../shared/infrastructure/base-response';

/**
 * The order the backend created, as it reports it.
 */
export interface PlaceOrderResource extends BaseResource {
  id: number;
  status: string;
  total: number;
  estimated_delivery_at: string;
}

/**
 * Response of a place-order call.
 */
export interface PlaceOrderResponse extends BaseResponse, PlaceOrderResource {}
```

## 3. The assembler — `place-order-assembler.ts`

It does **not** implement `BaseAssembler`: that contract is about entities and collections, and this one maps an intent outward and a result inward.

```typescript
// ordering/infrastructure/place-order-assembler.ts

/**
 * Anti-corruption layer for the place-order call.
 */
export class PlaceOrderAssembler {
  /**
   * @param command - The customer's intent.
   * @returns The body to send.
   */
  toRequestFromCommand(command: PlaceOrderCommand): PlaceOrderRequest {
    return {
      customer_id: command.customerId,
      lines: command.lines.map(line => ({
        menu_item_id: line.menuItemId, quantity: line.quantity
      })),
      delivery_address: command.deliveryAddress
    } as PlaceOrderRequest;
  }

  /**
   * @param response - The answer as the API sent it.
   * @returns The resource the endpoint hands upward.
   */
  toResourceFromResponse(response: PlaceOrderResponse): PlaceOrderResource {
    return {
      id: response.id,
      status: response.status,
      total: response.total,
      estimated_delivery_at: response.estimated_delivery_at
    } as PlaceOrderResource;
  }
}
```

## 4. The endpoint — `place-order-endpoint.ts`

No `-api-` in the name, and it extends `ErrorHandlingEnabledBaseType` rather than `BaseApiEndpoint`: there is no CRUD to inherit, only the error handling.

```typescript
// ordering/infrastructure/place-order-endpoint.ts
import {HttpClient} from '@angular/common/http';
import {catchError, map, Observable} from 'rxjs';
import {environment} from '../../../environments/environment';
import {ErrorHandlingEnabledBaseType} from '../../shared/infrastructure/error-handling-enabled-base-type';

const placeOrderEndpointUrl =
  `${environment.platformProviderApiBaseUrl}${environment.platformProviderPlaceOrderEndpointPath}`;

/**
 * Endpoint for the place-order action.
 */
export class PlaceOrderApiEndpoint extends ErrorHandlingEnabledBaseType {
  constructor(private http: HttpClient, private assembler: PlaceOrderAssembler) {
    super();
  }

  /**
   * @param command - The customer's intent.
   * @returns The order the backend created.
   */
  placeOrder(command: PlaceOrderCommand): Observable<PlaceOrderResource> {
    const request = this.assembler.toRequestFromCommand(command);
    return this.http.post<PlaceOrderResponse>(placeOrderEndpointUrl, request).pipe(
      map(response => this.assembler.toResourceFromResponse(response)),
      catchError(this.handleError('Failed to place the order'))
    );
  }
}
```

The context API composes it beside the CRUD endpoints, passing the assembler in — an action endpoint takes its assembler as a parameter, where a CRUD endpoint constructs its own:

```typescript
// ordering/infrastructure/ordering-api.ts
constructor(http: HttpClient) {
  super();
  this.ordersEndpoint = new OrdersApiEndpoint(http);
  this.placeOrderEndpoint = new PlaceOrderApiEndpoint(http, new PlaceOrderAssembler());
}

placeOrder(command: PlaceOrderCommand): Observable<PlaceOrderResource> {
  return this.placeOrderEndpoint.placeOrder(command);
}
```

An action endpoint may return a **resource** rather than an entity, as here — the caller wanted a confirmation, not a record to hold. When the store is going to keep the result, map it to an entity instead and return that.

## When the API is not yours

A third-party provider is where the anti-corruption layer earns its name, because you do not get to ask them to change a field. Same structure, two differences: its base URL gets its own `environment` prefix, and its query parameters and keys stay inside the endpoint.

```typescript
// ordering/infrastructure/delivery-estimate-endpoint.ts
const estimateEndpointUrl =
  `${environment.mapsProviderApiBaseUrl}${environment.mapsProviderEstimateEndpointPath}`;

/**
 * Delivery estimates from the maps provider.
 *
 * @remarks
 * The provider's key and parameter names never leave this file; callers ask
 * for an estimate between two addresses and get minutes back.
 */
export class DeliveryEstimateApiEndpoint extends ErrorHandlingEnabledBaseType {
  constructor(private http: HttpClient, private assembler: DeliveryEstimateAssembler) {
    super();
  }

  getEstimate(from: string, to: string): Observable<DeliveryEstimate> {
    return this.http.get<DeliveryEstimateResponse>(estimateEndpointUrl, {
      params: {origin: from, destination: to, key: environment.mapsProviderApiKey}
    }).pipe(
      map(response => this.assembler.toEntityFromResponse(response)),
      catchError(this.handleError('Failed to estimate the delivery'))
    );
  }
}
```

Read-only integrations often need no write side at all: one endpoint, one assembler with a single inbound method, and a store that caches what came back. That is a complete, honest context — a context is not obliged to have CRUD.

> **Secrets.** A key in `environment.ts` ships to the browser and is readable by anyone. It is fine for a public, rate-limited provider; anything that must stay secret belongs behind your own backend, which then becomes just another platform endpoint.
