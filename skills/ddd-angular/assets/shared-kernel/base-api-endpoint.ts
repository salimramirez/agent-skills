import {HttpClient} from '@angular/common/http';
import {Observable} from 'rxjs';
import {catchError, map} from 'rxjs/operators';
import {BaseEntity} from '../domain/model/base-entity';
import {BaseResource, BaseResponse} from './base-response';
import {BaseAssembler} from './base-assembler';
import {ErrorHandlingEnabledBaseType} from './error-handling-enabled-base-type';

/**
 * Generic CRUD endpoint for one aggregate of a bounded context.
 *
 * @remarks
 * This is the repository of the frontend. A concrete endpoint only declares its
 * URL and its assembler; every operation below comes from here, and every
 * result crosses the assembler, so a resource never escapes infrastructure.
 *
 * @typeParam TEntity - Domain entity this endpoint reads and writes.
 * @typeParam TResource - Wire shape of a single item.
 * @typeParam TResponse - Wire shape of the envelope holding many items.
 * @typeParam TAssembler - Assembler mapping between the three.
 */
export abstract class BaseApiEndpoint<
  TEntity extends BaseEntity,
  TResource extends BaseResource,
  TResponse extends BaseResponse,
  TAssembler extends BaseAssembler<TEntity, TResource, TResponse>
> extends ErrorHandlingEnabledBaseType {
  /**
   * @param http - Angular HTTP client.
   * @param endpointUrl - Absolute URL of the collection, composed from `environment`.
   * @param assembler - Assembler for this aggregate.
   */
  protected constructor(
    protected http: HttpClient,
    protected endpointUrl: string,
    protected assembler: TAssembler
  ) {
    super();
  }

  /**
   * Reads the whole collection.
   *
   * @remarks
   * Accepts both wire shapes an API may use — a bare array or an envelope —
   * so a mock server and the real backend can be swapped without touching the
   * store.
   *
   * @returns The entities in the collection.
   */
  getAll(): Observable<TEntity[]> {
    return this.http.get<TResponse | TResource[]>(this.endpointUrl).pipe(
      map(response => Array.isArray(response)
        ? response.map(resource => this.assembler.toEntityFromResource(resource))
        : this.assembler.toEntitiesFromResponse(response as TResponse)),
      catchError(this.handleError('Failed to fetch entities'))
    );
  }

  /**
   * Reads one item by its identity.
   *
   * @param id - Identity of the item.
   * @returns The entity.
   */
  getById(id: number): Observable<TEntity> {
    return this.http.get<TResource>(`${this.endpointUrl}/${id}`).pipe(
      map(resource => this.assembler.toEntityFromResource(resource)),
      catchError(this.handleError('Failed to fetch entity'))
    );
  }

  /**
   * Creates an item.
   *
   * @param entity - Entity to create; its `id` is whatever placeholder the
   * caller used, and the backend assigns the real one.
   * @returns The created entity as the backend returned it.
   */
  create(entity: TEntity): Observable<TEntity> {
    const resource = this.assembler.toResourceFromEntity(entity);
    return this.http.post<TResource>(this.endpointUrl, resource).pipe(
      map(created => this.assembler.toEntityFromResource(created)),
      catchError(this.handleError('Failed to create entity'))
    );
  }

  /**
   * Updates an item.
   *
   * @param entity - Entity carrying the new state.
   * @param id - Identity of the item to update.
   * @returns The updated entity as the backend returned it.
   */
  update(entity: TEntity, id: number): Observable<TEntity> {
    const resource = this.assembler.toResourceFromEntity(entity);
    return this.http.put<TResource>(`${this.endpointUrl}/${id}`, resource).pipe(
      map(updated => this.assembler.toEntityFromResource(updated)),
      catchError(this.handleError('Failed to update entity'))
    );
  }

  /**
   * Deletes an item.
   *
   * @param id - Identity of the item to delete.
   */
  delete(id: number): Observable<void> {
    return this.http.delete<void>(`${this.endpointUrl}/${id}`).pipe(
      catchError(this.handleError('Failed to delete entity'))
    );
  }
}
