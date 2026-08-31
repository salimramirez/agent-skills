import {HttpErrorResponse} from '@angular/common/http';
import {Observable, throwError} from 'rxjs';

/**
 * Turns transport failures into domain-readable errors.
 *
 * @remarks
 * Extend this from any endpoint that talks to the network, so a failed call
 * surfaces one `Error` with a sentence a store can show, instead of an
 * `HttpErrorResponse` leaking upward into the application layer.
 */
export abstract class ErrorHandlingEnabledBaseType {
  /**
   * Builds a `catchError` handler that labels the failure with the operation.
   *
   * @param operation - What was being attempted, e.g. `'Failed to load orders'`.
   * @returns A handler that rethrows a labelled `Error`.
   */
  protected handleError(operation: string) {
    return (error: HttpErrorResponse): Observable<never> => {
      let errorMessage = operation;
      if (error.status === 404) {
        errorMessage = `${operation}: Resource not found`;
      } else if (error.error instanceof ErrorEvent) {
        errorMessage = `${operation}: ${error.error.message}`;
      } else {
        errorMessage = `${operation}: ${error.statusText || 'Unexpected error'}`;
      }
      return throwError(() => new Error(errorMessage));
    };
  }
}
