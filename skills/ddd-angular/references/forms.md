# Reactive forms and writes

Building an entity from a form for CRUD, and the command path for everything else.

A reactive form gathers and validates input as **UX** — fast feedback, while the server validates again. For CRUD, the form builds the **entity** and hands it to the store; a form view can `extend BaseForm` to reuse the kernel's validation-message helpers:

```typescript
// ordering/presentation/views/order-form/order-form.ts
export class OrderForm extends BaseForm {
  private fb = inject(FormBuilder);
  private store = inject(OrderStore);
  private router = inject(Router);

  protected form = this.fb.group({
    customerId: new FormControl<number | null>(null, { validators: [Validators.required] }),
    // ...one control group per order item
  });

  submit(): void {
    if (this.form.invalid) return;                       // a UX guard, not the authority
    const order = new Order({
      id: 0, customerId: this.form.value.customerId!, items: [],
      status: 'PLACED', total: 0,
    });
    this.store.addOrder(order);
    this.router.navigate(['ordering/orders']);
  }
}
```

For a **non-CRUD intent**, build a **command** instead and pass it to the store, which sends it through the command→request assembler from the infrastructure section:

```typescript
// identity/presentation/views/sign-in-form/sign-in-form.ts
export class SignInForm extends BaseForm {
  private store = inject(IdentityStore);

  protected form = new FormGroup({
    username: new FormControl('', { nonNullable: true, validators: [Validators.required] }),
    password: new FormControl('', { nonNullable: true, validators: [Validators.required] }),
  });

  signIn(): void {
    if (this.form.invalid) return;
    this.store.signIn(new SignInCommand({
      username: this.form.value.username!, password: this.form.value.password!,
    }));
  }
}
```

Either way: validation feedback stays in the form, the write's shape (entity or command) stays in the domain, and the coordination stays in the store — the view only collects input and dispatches.
