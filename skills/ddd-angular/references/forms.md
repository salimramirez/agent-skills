# Reactive forms and writes

Building an entity from a form for CRUD, and dispatching a command for everything else.

A reactive form gathers and validates input as **UX** — fast feedback while typing. The server validates again and stays the authority; `if (this.form.invalid) return;` is a courtesy to the user, not a rule of the domain.

## One view for create and edit

The presence of an `id` route parameter decides which. Both routes load the same view, so there is one form to maintain:

```typescript
// ordering/presentation/views/order-form/order-form.ts
import {Component, inject} from '@angular/core';
import {FormBuilder, FormControl, ReactiveFormsModule, Validators} from '@angular/forms';
import {ActivatedRoute, Router} from '@angular/router';
import {BaseForm} from '../../../../shared/presentation/components/base-form/base-form';

/**
 * Routed view that creates or edits one order.
 */
@Component({
  selector: 'app-order-form',
  imports: [ReactiveFormsModule],
  templateUrl: './order-form.html',
  styleUrl: './order-form.css'
})
export class OrderForm extends BaseForm {
  private readonly formBuilder = inject(FormBuilder);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly store = inject(OrderingStore);

  protected readonly form = this.formBuilder.group({
    customerId: new FormControl<number | null>(null, {validators: [Validators.required]}),
    deliveryAddress: new FormControl<string>('', {
      nonNullable: true, validators: [Validators.required, Validators.maxLength(160)]
    })
  });

  protected readonly orderId: number | null;
  protected readonly isEdit: boolean;

  constructor() {
    super();
    const id = this.route.snapshot.paramMap.get('id');
    this.orderId = id ? Number(id) : null;
    this.isEdit = this.orderId !== null;
    if (this.orderId !== null) {
      const order = this.store.getOrderById(this.orderId)();
      if (order) {
        this.form.patchValue({
          customerId: order.customerId,
          deliveryAddress: order.deliveryAddress
        });
      }
    }
  }

  /**
   * Builds the order from the form and sends it through the store.
   */
  protected submit(): void {
    if (this.form.invalid) return;
    const order = new Order({
      id: this.orderId ?? 0,
      customerId: this.form.value.customerId!,
      deliveryAddress: this.form.value.deliveryAddress!,
      lines: [], status: 'PLACED', total: 0, courierId: 0
    });
    if (this.isEdit) this.store.updateOrder(order);
    else this.store.addOrder(order);
    this.router.navigate(['ordering/orders']).then();
  }
}
```

The form does exactly three things: collect, validate for the user, and **build a domain object**. It does not talk to the API, and it does not shape a request body — `new Order({...})` is the boundary, and the assembler downstream decides what the wire sees.

`id: this.orderId ?? 0` is the placeholder convention: zero on create, the real id on edit, and the backend is what assigns identity.

When the form is opened by a deep link before the store has loaded, `getOrderById(id)()` returns `undefined` and the form simply stays empty. If that matters for the screen, read the signal in a `computed()` or an `effect()` and patch when it arrives, instead of blocking the route.

## Validation messages come from `BaseForm`

Extending `BaseForm` gives the template two helpers, so no view spells out its own `touched && hasError(...)` chain:

```html
<form [formGroup]="form" (ngSubmit)="submit()">
  <label for="deliveryAddress">Delivery address</label>
  <input id="deliveryAddress" type="text" formControlName="deliveryAddress"/>
  @if (isInvalidControl(form, 'deliveryAddress')) {
    <p role="alert">{{ errorMessagesForControl(form, 'deliveryAddress') }}</p>
  }

  <button type="submit" [disabled]="form.invalid">{{ isEdit ? 'Update' : 'Create' }}</button>
</form>
```

Add a case to `errorMessageForControl` in the kernel when you add a validator, and every form in the app gets the message. In a localized app that method returns a translation key instead of a sentence — one place to change, which is the reason the helper exists.

## The command path

For a **non-CRUD intent**, build a command instead and pass it to the store. Nothing else about the view changes:

```typescript
protected placeOrder(): void {
  if (this.form.invalid) return;
  this.store.placeOrder(new PlaceOrderCommand({
    customerId: this.form.value.customerId!,
    lines: this.cart().lines,
    deliveryAddress: this.form.value.deliveryAddress!
  }));
  this.router.navigate(['ordering/orders']).then();
}
```

The store sends it through the command-to-request assembler from `commands-and-actions.md`.

Either way the division holds: validation feedback stays in the form, the shape of the write (entity or command) stays in the domain, coordination stays in the store, and navigation stays with the view that dispatched.

> Reactive forms are the convention here and remain fully supported. Newer Angular versions add a signal-based forms API alongside them; adopting it changes how a form is declared, not where the write is built or who it is handed to.
