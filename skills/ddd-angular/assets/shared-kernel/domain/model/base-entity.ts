/**
 * Contract every entity in the application satisfies.
 *
 * @remarks
 * Entities are classes with private fields and accessors; this interface is the
 * one thing they all share, so the generic infrastructure base classes can work
 * with any of them.
 */
export interface BaseEntity {
  /**
   * Identity of the entity, assigned by the backend.
   */
  id: number;
}
