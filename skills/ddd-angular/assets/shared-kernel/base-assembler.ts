import {BaseResource, BaseResponse} from './base-response';
import {BaseEntity} from '../domain/model/base-entity';

/**
 * Contract for the anti-corruption layer between the API and the domain model.
 *
 * @remarks
 * An assembler is the only place that knows both shapes. Reads run
 * response to entities; writes run entity to resource.
 *
 * @typeParam TEntity - Domain entity this assembler produces.
 * @typeParam TResource - Wire shape of a single item.
 * @typeParam TResponse - Wire shape of the envelope holding many items.
 */
export interface BaseAssembler<
  TEntity extends BaseEntity,
  TResource extends BaseResource,
  TResponse extends BaseResponse
> {
  /**
   * Builds an entity from a single resource.
   *
   * @param resource - Resource as the API returned it.
   * @returns The entity the rest of the app works with.
   */
  toEntityFromResource(resource: TResource): TEntity;

  /**
   * Turns an entity back into the resource the API expects on a write.
   *
   * @param entity - Entity to send.
   * @returns The resource to put in the request body.
   */
  toResourceFromEntity(entity: TEntity): TResource;

  /**
   * Builds the whole collection from an envelope response.
   *
   * @param response - Envelope as the API returned it.
   * @returns The entities it carried.
   */
  toEntitiesFromResponse(response: TResponse): TEntity[];
}
