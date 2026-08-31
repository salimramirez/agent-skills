import {Component, inject} from '@angular/core';
import {Router} from '@angular/router';
import {__Context__Store} from '../../../application/__context__.store';

/**
 * Routed view listing the __entities__ of the __context__ context.
 *
 * @remarks
 * A view is the smart component — it injects the store, reads its signals and
 * dispatches user intent. It holds no business logic and no HTTP call.
 */
@Component({
  selector: 'app-__entity-kebab__-list',
  templateUrl: './__entity-kebab__-list.html',
  styleUrl: './__entity-kebab__-list.css'
})
export class __Entity__List {
  protected readonly store = inject(__Context__Store);
  private readonly router = inject(Router);

  /**
   * @param id - Identity of the __entity__ to edit.
   */
  protected edit__Entity__(id: number): void {
    this.router.navigate(['__context__/__entities-kebab__', id, 'edit']).then();
  }

  /**
   * @param id - Identity of the __entity__ to delete.
   */
  protected delete__Entity__(id: number): void {
    this.store.delete__Entity__(id);
  }

  protected navigateToNew(): void {
    this.router.navigate(['__context__/__entities-kebab__/new']).then();
  }
}
