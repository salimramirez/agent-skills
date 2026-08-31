import {BaseAssembler} from '../../shared/infrastructure/base-assembler';
import {__Entity__} from '../domain/model/__entity-kebab__.entity';
import {__Entities__Response, __Entity__Resource} from './__entities-kebab__-response';

/**
 * Anti-corruption layer between the __entities__ API and the domain model.
 *
 * @remarks
 * Naming differences, nullable fields and any other quirk of the wire format
 * are absorbed here and never reach the domain, the store or a template.
 */
export class __Entity__Assembler
  implements BaseAssembler<__Entity__, __Entity__Resource, __Entities__Response> {
  /**
   * @param response - Envelope as the API returned it.
   * @returns The __entities__ it carried.
   */
  toEntitiesFromResponse(response: __Entities__Response): __Entity__[] {
    return response.__entities__.map(resource => this.toEntityFromResource(resource));
  }

  /**
   * @param resource - Resource as the API returned it.
   * @returns The __entity__ the rest of the app works with.
   */
  toEntityFromResource(resource: __Entity__Resource): __Entity__ {
    return new __Entity__({
      id: resource.id,
      name: resource.name
    });
  }

  /**
   * @param entity - __Entity__ to send.
   * @returns The resource to put in the request body.
   */
  toResourceFromEntity(entity: __Entity__): __Entity__Resource {
    return {
      id: entity.id,
      name: entity.name
    } as __Entity__Resource;
  }
}
