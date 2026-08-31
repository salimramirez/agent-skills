import {BaseEntity} from '../../../shared/domain/model/base-entity';

/**
 * __Entity__ in the __context__ bounded context.
 *
 * @remarks
 * Fields are private and reached through accessors, so the shape of the model
 * is a decision of this class rather than of whoever holds a reference to it.
 * A setter exists only where the UI genuinely changes the field.
 */
export class __Entity__ implements BaseEntity {
  private _id: number;
  private _name: string;

  /**
   * @param __entity__ - Initial state, in the ubiquitous language of the context.
   */
  constructor(__entity__: {id: number, name: string}) {
    this._id = __entity__.id;
    this._name = __entity__.name;
  }

  get id(): number {
    return this._id;
  }

  /**
   * @remarks
   * A new __Entity__ is built with a placeholder id; the backend assigns the
   * real one and the store writes it back here.
   */
  set id(value: number) {
    this._id = value;
  }

  get name(): string {
    return this._name;
  }

  set name(value: string) {
    this._name = value;
  }
}
