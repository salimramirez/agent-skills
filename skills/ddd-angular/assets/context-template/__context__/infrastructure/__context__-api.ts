import {Injectable} from '@angular/core';
import {HttpClient} from '@angular/common/http';
import {Observable} from 'rxjs';
import {BaseApi} from '../../shared/infrastructure/base-api';
import {__Entity__} from '../domain/model/__entity-kebab__.entity';
import {__Entities__ApiEndpoint} from './__entities-kebab__-api-endpoint';

/**
 * The API of the __context__ bounded context.
 *
 * @remarks
 * It owns the endpoints of the context and exposes them as operations named in
 * the ubiquitous language, so the store never holds an endpoint itself. Add one
 * private endpoint field per aggregate this context reads or writes.
 */
@Injectable({providedIn: 'root'})
export class __Context__Api extends BaseApi {
  private readonly __entities__Endpoint: __Entities__ApiEndpoint;

  constructor(http: HttpClient) {
    super();
    this.__entities__Endpoint = new __Entities__ApiEndpoint(http);
  }

  /**
   * @returns Every __Entity__ in the context.
   */
  get__Entities__(): Observable<__Entity__[]> {
    return this.__entities__Endpoint.getAll();
  }

  /**
   * @param id - Identity of the __Entity__.
   */
  get__Entity__(id: number): Observable<__Entity__> {
    return this.__entities__Endpoint.getById(id);
  }

  /**
   * @param __entity__ - __Entity__ to create.
   */
  create__Entity__(__entity__: __Entity__): Observable<__Entity__> {
    return this.__entities__Endpoint.create(__entity__);
  }

  /**
   * @param __entity__ - __Entity__ carrying the new state.
   */
  update__Entity__(__entity__: __Entity__): Observable<__Entity__> {
    return this.__entities__Endpoint.update(__entity__, __entity__.id);
  }

  /**
   * @param id - Identity of the __Entity__ to delete.
   */
  delete__Entity__(id: number): Observable<void> {
    return this.__entities__Endpoint.delete(id);
  }
}
