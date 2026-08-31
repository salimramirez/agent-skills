import {BaseResource, BaseResponse} from '../../shared/infrastructure/base-response';

/**
 * Wire shape of a single __entity__ as the API returns it.
 */
export interface __Entity__Resource extends BaseResource {
  id: number;
  name: string;
}

/**
 * Wire shape of the envelope holding many __entities__.
 */
export interface __Entities__Response extends BaseResponse {
  __entities__: __Entity__Resource[];
}
