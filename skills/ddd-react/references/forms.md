# Forms and writes

Building an entity from a form for CRUD, and dispatching a command for everything else.

A form gathers and validates input as **UX** — fast feedback while typing. The server validates again and stays the authority; a `required` attribute is a courtesy to the user, not a rule of the domain.

## One view for create and edit

The presence of an `id` route parameter decides which. Both routes load the same view, so there is one form to maintain:

```tsx
// ordering/presentation/views/OrderForm.tsx
import {useEffect, useState, type FormEvent} from 'react';
import {useNavigate, useParams} from 'react-router';
import {useOrderingStore} from '../../application/ordering.store';
import {Order} from '../../domain/model/order.entity';
import {orderingPaths} from '../ordering-paths';

/** Routed view that creates or edits one order. */
export function OrderForm() {
    const navigate = useNavigate();
    const {id} = useParams();
    const isEdit = id !== undefined;

    const orders = useOrderingStore(state => state.orders);
    const addOrder = useOrderingStore(state => state.addOrder);
    const updateOrder = useOrderingStore(state => state.updateOrder);

    const [deliveryAddress, setDeliveryAddress] = useState('');

    useEffect(() => {
        if (!isEdit) return;
        // A route param is a string; compare against a number or nothing ever matches.
        const order = orders.find(candidate => candidate.id === Number(id));
        if (order) setDeliveryAddress(order.deliveryAddress);
    }, [isEdit, id, orders]);

    function handleSubmit(event: FormEvent) {
        event.preventDefault();
        const order = new Order({id: isEdit ? Number(id) : null, deliveryAddress});
        void (isEdit ? updateOrder(order) : addOrder(order));
        navigate(orderingPaths.orders());
    }

    return (
        <section>
            <h1>{isEdit ? 'Edit Order' : 'New Order'}</h1>
            <form onSubmit={handleSubmit}>
                <label htmlFor="deliveryAddress">Delivery address</label>
                <input
                    id="deliveryAddress"
                    required
                    maxLength={160}
                    value={deliveryAddress}
                    onChange={event => setDeliveryAddress(event.target.value)}
                />
                <button type="submit">{isEdit ? 'Update' : 'Create'}</button>
                <button type="button" onClick={() => navigate(orderingPaths.orders())}>Cancel</button>
            </form>
        </section>
    );
}
```

The form does exactly three things: collect, validate for the user, and **build a domain object**. It does not talk to the gateway, and it does not shape a request body — `new Order({...})` is the boundary, and the assembler downstream decides what the wire sees.

Five details that matter more than they look:

**Local `useState` per field, not the entity in state.** Holding an `Order` in component state and rebuilding it on every keystroke means a new instance per character; worse, entities are immutable, so you would be calling `with…` in an `onChange`. Plain values in, entity built once at submit.

**`id: null` on create, `Number(id)` on edit.** The route param is a string; passing it through unconverted gives an entity whose id never matches anything in the store, and the next update silently creates a duplicate.

**The effect depends on `orders`.** A deep link can arrive before the store has loaded, in which case `find` returns `undefined` and the form stays empty. Listing `orders` in the dependency array means it fills in when the data lands, with no extra machinery.

**`void` on the action.** The store's actions return promises; `void` says "deliberately not awaited" and keeps the linter quiet. Await instead when what happens next depends on the result — see the command path below.

**Uncontrolled inputs are fine too.** A large form with `useRef` or a form library reads better than twenty `useState` calls. What must not change is where the entity is built: at submit, from whatever the form gathered.

## Validation

Native constraints (`required`, `maxLength`, `type="email"`) cover most of it and cost nothing. When a rule is a **domain** rule, put it on the entity and ask it, so the form and the rest of the app agree:

```typescript
const canSubmit = deliveryAddress.trim().length > 0;
```

A rule that only the form knows will drift from the one the backend enforces. A rule that lives on the entity is asked the same way everywhere.

## The command path

For a **non-CRUD intent**, build a command instead. The difference from CRUD is that the outcome usually decides where the user goes, so the view awaits and then navigates:

```tsx
async function handlePlaceOrder(event: FormEvent) {
    event.preventDefault();
    await placeOrder(new PlaceOrderCommand({
        customerId,
        lines: cart.lines,
        deliveryAddress
    }));
    navigate(orderingPaths.orders());
}
```

The store sends it through the gateway and the assembler from `commands-and-actions.md`. Navigation stays in the component because `useNavigate` is a hook and the store imports nothing from React — a constraint that pays for itself in `cross-cutting.md`.

Either way the division holds: validation feedback stays in the form, the shape of the write (entity or command) stays in the domain, coordination stays in the store, and navigation stays with the view that dispatched.
