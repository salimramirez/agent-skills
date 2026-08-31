import {FormGroup} from '@angular/forms';

/**
 * Validation-message helpers shared by every form view.
 *
 * @remarks
 * Form views extend this so their templates ask the same two questions —
 * "should I show an error?" and "which one?" — instead of each template
 * spelling out its own `touched && hasError(...)` chains.
 *
 * Client-side validation here is UX. The backend validates again and stays the
 * authority.
 */
export class BaseForm {
  /**
   * Whether a control should currently show its error.
   *
   * @param form - Form group holding the control.
   * @param controlName - Name of the control.
   * @returns True once the control is both invalid and touched.
   */
  protected isInvalidControl(form: FormGroup, controlName: string): boolean {
    return form.controls[controlName].invalid && form.controls[controlName].touched;
  }

  /**
   * Every error message currently applying to a control.
   *
   * @param form - Form group holding the control.
   * @param controlName - Name of the control.
   * @returns The messages, concatenated; empty when the control is valid.
   */
  protected errorMessagesForControl(form: FormGroup, controlName: string): string {
    const errors = form.controls[controlName].errors;
    if (!errors) return '';
    return Object.keys(errors)
      .map(errorKey => this.errorMessageForControl(controlName, errorKey))
      .join(' ');
  }

  /**
   * Message for one error key on one control.
   *
   * @remarks
   * Extend the switch as validators are added, or return a translation key
   * here when the app is localised.
   *
   * @param controlName - Name of the control.
   * @param errorKey - Error key reported by the validator, e.g. `'required'`.
   * @returns The message to display.
   */
  private errorMessageForControl(controlName: string, errorKey: string): string {
    switch (errorKey) {
      case 'required':  return `The field ${controlName} is required.`;
      case 'email':     return `The field ${controlName} must be a valid email address.`;
      case 'min':       return `The field ${controlName} is below the allowed minimum.`;
      case 'minlength': return `The field ${controlName} is too short.`;
      case 'maxlength': return `The field ${controlName} is too long.`;
      default:          return `The field ${controlName} is invalid.`;
    }
  }
}
