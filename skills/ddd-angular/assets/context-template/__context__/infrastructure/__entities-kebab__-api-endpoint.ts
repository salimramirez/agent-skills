import {HttpClient} from '@angular/common/http';
import {BaseApiEndpoint} from '../../shared/infrastructure/base-api-endpoint';
import {environment} from '../../../environments/environment';
import {__Entity__} from '../domain/model/__entity-kebab__.entity';
import {__Entities__Response, __Entity__Resource} from './__entities-kebab__-response';
import {__Entity__Assembler} from './__entity-kebab__-assembler';

const __entities__EndpointUrl =
  `${environment.platformProviderApiBaseUrl}${environment.platformProvider__Entities__EndpointPath}`;

/**
 * CRUD endpoint for __entities__ — the repository of this aggregate.
 *
 * @remarks
 * It declares its URL and its assembler; every operation comes from
 * {@link BaseApiEndpoint}.
 */
export class __Entities__ApiEndpoint
  extends BaseApiEndpoint<__Entity__, __Entity__Resource, __Entities__Response, __Entity__Assembler> {
  /**
   * @param http - Angular HTTP client.
   */
  constructor(http: HttpClient) {
    super(http, __entities__EndpointUrl, new __Entity__Assembler());
  }
}
