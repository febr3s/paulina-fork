/**
 * FormUtils - Utility functions for form validation
 */

const FormUtils = {
  
  /**
   * Validate a required field
   * @param {string} fieldId - The field ID
   * @param {string} errorMessage - Translated error message
   * @returns {object} - { valid: boolean, message: string }
   */
  validateRequired(fieldId, errorMessage) {
    const field = document.getElementById(fieldId);
    if (!field) {
      console.warn(`FormUtils: Field not found: ${fieldId}`);
      return { valid: false, message: errorMessage };
    }
    
    const value = field.value.trim();
    const isValid = value !== '';
    
    // Apply validation styling
    if (!isValid) {
      field.classList.add('is-invalid');
      field.classList.remove('is-valid');
    } else {
      field.classList.remove('is-invalid');
      field.classList.add('is-valid');
    }
    
    return { valid: isValid, message: isValid ? '' : errorMessage };
  },
  
  /**
   * Scroll to first invalid field
   * @param {HTMLFormElement} form - The form element
   */
  scrollToFirstError(form) {
    if (!form) return;
    
    const firstInvalid = form.querySelector('.is-invalid');
    if (firstInvalid) {
      firstInvalid.scrollIntoView({ behavior: 'smooth', block: 'center' });
      firstInvalid.focus();
    }
  }
};

window.FormUtils = FormUtils;