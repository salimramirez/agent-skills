# House style

The conventions that make this code recognizable, beyond where the files sit.

## Document with JSDoc

Every class, interface, and public method carries a JSDoc block. This is not decoration: the domain layer is where the ubiquitous language lives, and a doc comment is where the language gets written down in prose next to the code that implements it.

The rule: **document classes, interfaces, and public methods; use `@param` and `@returns` when the name alone does not say it; use `@remarks` for the reason behind a decision and `@see {@link Other}` to point at the related piece.** Accessors that only read or write a field can be left bare — a `get total()` above `private _total` says everything already.

```typescript
/**
 * An order placed by a customer in the ordering context.
 *
 * @remarks
 * The backend owns the invariants — a total is recomputed server-side on every
 * write, so nothing here should be trusted as authoritative.
 *
 * @see {@link PlaceOrderCommand} for the non-CRUD path that creates one.
 */
export class Order implements BaseEntity {
  /**
   * Adds a line to the order.
   *
   * @param line - Line to add, already priced by the catalog.
   * @returns The order, so calls can be chained while building one.
   */
  addLine(line: OrderLine): Order { /* … */ }
}
```

Write the comment for someone who does not know the domain. `@param id - The id` is noise; `@param id - Identity of the order to cancel` is not.

## Order members predictably

Within a class: injected dependencies, then private writable signals paired with their public read-only counterparts, then computed signals, then the constructor, then public methods, then private helpers. Reading a store top to bottom should read as "what it depends on, what it holds, what it derives, what it does".

```typescript
private readonly ordersSignal = signal<Order[]>([]);
/** Every order currently loaded. */
readonly orders = this.ordersSignal.asReadonly();
```

Pair each writable signal with its read-only view immediately, not in a separate block. It keeps the two from drifting and makes an unexposed signal obvious.

## Prefer `inject()`

Use `inject()` for dependencies rather than constructor parameters — in components, views, stores, guards, and interceptors alike. A constructor is then free to do actual work, such as an eager load or reading a route parameter. The exception is a dependency you need **in order to build something else** in the constructor: a context API declares `constructor(http: HttpClient)` because it forwards `http` into the endpoints it constructs, and those endpoints are plain classes outside the injector entirely. Everywhere else, `inject()`.

That exception is also the one thing tying a class to `@Injectable`. Angular's `@Service()` decorator is a shorthand for `@Injectable({ providedIn: 'root' })` — root-provided by default, `autoProvided: false` to opt out — but it accepts **only** `inject()`, never constructor injection. So a store, which injects everything, can move to `@Service()` untouched; a context API cannot, unless you first rewrite it as a field:

```typescript
@Service()
export class OrderingApi extends BaseApi {
  private readonly http = inject(HttpClient);
  private readonly ordersEndpoint = new OrdersApiEndpoint(this.http);
}
```

Both forms are correct. Pick one per project and stay with it — a codebase where half the services take a constructor and half do not is harder to read than either convention alone.

## Keep the layers honest

These are the rules the structure exists to enforce. Each is a smell with a name:

- **No `HttpClient` in a component or a store.** Only an endpoint touches it. A store calls its context API; a view calls its store.
- **No resource in a template.** `OrderResource` never leaves `infrastructure`. If a view reads `order.customer_id`, the assembler was skipped.
- **No business or coordination logic in a view.** Stitching two collections together, deciding what to load next, formatting an error — that is the store's job. Logic in a component is the frontend's fat controller.
- **No `any`.** The wire shape is described by an interface; if the API is genuinely dynamic, the assembler is where that gets narrowed, once.
- **No leftover `console.log`.** Debug output that ships tells readers the file was never finished.
- **One store per bounded context**, not one per entity and not one for the app. `OrderingStore` may hold orders and order items; it does not hold users.

## Comparisons and identity

Entities are compared by `id`, never by object identity — an entity that has been through a write is a different instance carrying the same identity. `orders.find(order => order.id === id)` is the idiom, and it is why `BaseEntity` exists.

A new entity is built with `id: 0` as a placeholder; the backend assigns the real one and the store writes back what comes back from the call.
