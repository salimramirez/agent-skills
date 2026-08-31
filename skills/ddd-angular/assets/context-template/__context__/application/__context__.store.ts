import {computed, DestroyRef, inject, Injectable, Signal, signal} from '@angular/core';
import {takeUntilDestroyed} from '@angular/core/rxjs-interop';
import {retry} from 'rxjs';
import {__Entity__} from '../domain/model/__entity-kebab__.entity';
import {__Context__Api} from '../infrastructure/__context__-api';

/**
 * State and use cases of the __context__ bounded context.
 *
 * @remarks
 * The store is the only thing that talks to {@link __Context__Api}. It holds
 * writable signals privately, publishes them read-only, and keeps every bit of
 * coordination — retries, error text, cross-entity stitching — out of the views.
 */
@Injectable({providedIn: 'root'})
export class __Context__Store {
  private readonly destroyRef = inject(DestroyRef);
  private readonly __context__Api = inject(__Context__Api);

  private readonly __entities__Signal = signal<__Entity__[]>([]);
  /** Every __Entity__ currently loaded. */
  readonly __entities__ = this.__entities__Signal.asReadonly();

  private readonly loadingSignal = signal<boolean>(false);
  /** Whether a call is in flight. */
  readonly loading = this.loadingSignal.asReadonly();

  private readonly errorSignal = signal<string | null>(null);
  /** Message for the last failed call, or `null`. */
  readonly error = this.errorSignal.asReadonly();

  /** How many __Entities__ are loaded. */
  readonly __entity__Count = computed(() => this.__entities__().length);

  constructor() {
    this.load__Entities__();
  }

  /**
   * One __Entity__, as a signal that tracks the collection.
   *
   * @param id - Identity to look up.
   * @returns A signal holding the __Entity__, or `undefined` while it is absent.
   */
  get__Entity__ById(id: number): Signal<__Entity__ | undefined> {
    return computed(() => id ? this.__entities__().find(entity => entity.id === id) : undefined);
  }

  /**
   * Loads every __Entity__ from the API.
   */
  load__Entities__(): void {
    this.loadingSignal.set(true);
    this.errorSignal.set(null);
    this.__context__Api.get__Entities__().pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: __entities__ => {
        this.__entities__Signal.set(__entities__);
        this.loadingSignal.set(false);
      },
      error: error => {
        this.errorSignal.set(this.formatError(error, 'Failed to load __entities__'));
        this.loadingSignal.set(false);
      }
    });
  }

  /**
   * Creates a __Entity__ and adds it to the collection.
   *
   * @param __entity__ - __Entity__ built by the form, with a placeholder id.
   */
  add__Entity__(__entity__: __Entity__): void {
    this.loadingSignal.set(true);
    this.errorSignal.set(null);
    this.__context__Api.create__Entity__(__entity__).pipe(retry(2)).subscribe({
      next: created => {
        this.__entities__Signal.update(__entities__ => [...__entities__, created]);
        this.loadingSignal.set(false);
      },
      error: error => {
        this.errorSignal.set(this.formatError(error, 'Failed to create __entity__'));
        this.loadingSignal.set(false);
      }
    });
  }

  /**
   * Updates a __Entity__ in place.
   *
   * @param updated__Entity__ - __Entity__ carrying the new state.
   */
  update__Entity__(updated__Entity__: __Entity__): void {
    this.loadingSignal.set(true);
    this.errorSignal.set(null);
    this.__context__Api.update__Entity__(updated__Entity__).pipe(retry(2)).subscribe({
      next: __entity__ => {
        this.__entities__Signal.update(__entities__ =>
          __entities__.map(current => current.id === __entity__.id ? __entity__ : current));
        this.loadingSignal.set(false);
      },
      error: error => {
        this.errorSignal.set(this.formatError(error, 'Failed to update __entity__'));
        this.loadingSignal.set(false);
      }
    });
  }

  /**
   * Deletes a __Entity__ and drops it from the collection.
   *
   * @param id - Identity of the __entity__ to delete.
   */
  delete__Entity__(id: number): void {
    this.loadingSignal.set(true);
    this.errorSignal.set(null);
    this.__context__Api.delete__Entity__(id).pipe(retry(2)).subscribe({
      next: () => {
        this.__entities__Signal.update(__entities__ =>
          __entities__.filter(current => current.id !== id));
        this.loadingSignal.set(false);
      },
      error: error => {
        this.errorSignal.set(this.formatError(error, 'Failed to delete __entity__'));
        this.loadingSignal.set(false);
      }
    });
  }

  /**
   * Turns a failure into one sentence a view can show.
   *
   * @param error - Whatever the endpoint threw.
   * @param fallback - Message to use when the error carries nothing readable.
   * @returns The message to publish on `error`.
   */
  private formatError(error: unknown, fallback: string): string {
    if (error instanceof Error) {
      return error.message.includes('Resource not found') ? `${fallback}: Not found` : error.message;
    }
    return fallback;
  }
}
