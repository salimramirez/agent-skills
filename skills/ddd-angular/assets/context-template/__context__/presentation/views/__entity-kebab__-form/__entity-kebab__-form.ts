import {Component, inject} from '@angular/core';
import {FormBuilder, FormControl, ReactiveFormsModule, Validators} from '@angular/forms';
import {ActivatedRoute, Router} from '@angular/router';
import {BaseForm} from '../../../../shared/presentation/components/base-form/base-form';
import {__Entity__} from '../../../domain/model/__entity-kebab__.entity';
import {__Context__Store} from '../../../application/__context__.store';

/**
 * Routed view that creates or edits one __entity__.
 *
 * @remarks
 * One view serves both routes — the presence of an `id` parameter decides which.
 * The form collects and validates input as UX, then builds a {@link __Entity__}
 * and hands it to the store; the backend validates again and stays the authority.
 */
@Component({
  selector: 'app-__entity-kebab__-form',
  imports: [ReactiveFormsModule],
  templateUrl: './__entity-kebab__-form.html',
  styleUrl: './__entity-kebab__-form.css'
})
export class __Entity__Form extends BaseForm {
  private readonly formBuilder = inject(FormBuilder);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly store = inject(__Context__Store);

  protected readonly form = this.formBuilder.group({
    name: new FormControl<string>('', {nonNullable: true, validators: [Validators.required]})
  });

  protected readonly __entity__Id: number | null;
  protected readonly isEdit: boolean;

  constructor() {
    super();
    const id = this.route.snapshot.paramMap.get('id');
    this.__entity__Id = id ? Number(id) : null;
    this.isEdit = this.__entity__Id !== null;
    if (this.__entity__Id !== null) {
      const __entity__ = this.store.get__Entity__ById(this.__entity__Id)();
      if (__entity__) this.form.patchValue({name: __entity__.name});
    }
  }

  /**
   * Builds the __entity__ from the form and sends it through the store.
   */
  protected submit(): void {
    if (this.form.invalid) return;
    const __entity__ = new __Entity__({
      id: this.__entity__Id ?? 0,
      name: this.form.value.name!
    });
    if (this.isEdit) this.store.update__Entity__(__entity__);
    else this.store.add__Entity__(__entity__);
    this.router.navigate(['__context__/__entities-kebab__']).then();
  }
}
