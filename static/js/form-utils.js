/**
 * FormUtils - Utility functions for form validation and UI helpers
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
    
    let value = '';
    
    // Handle different field types
    if (field.tagName === 'SELECT') {
      value = field.value;
    } else if (field.tagName === 'INPUT' || field.tagName === 'TEXTAREA') {
      value = field.value.trim();
    } else {
      value = field.value || '';
    }
    
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
   * Validate email format
   * @param {string} fieldId - The field ID
   * @param {string} errorMessage - Translated error message
   * @returns {object} - { valid: boolean, message: string }
   */
  validateEmail(fieldId, errorMessage) {
    const field = document.getElementById(fieldId);
    if (!field) {
      return { valid: false, message: errorMessage };
    }
    
    const value = field.value.trim();
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    const isValid = value === '' || emailRegex.test(value);
    
    if (!isValid) {
      field.classList.add('is-invalid');
    } else {
      field.classList.remove('is-invalid');
    }
    
    return { valid: isValid, message: isValid ? '' : errorMessage };
  },
  
  /**
   * Validate URL format
   * @param {string} fieldId - The field ID
   * @param {string} errorMessage - Translated error message
   * @returns {object} - { valid: boolean, message: string }
   */
  validateUrl(fieldId, errorMessage) {
    const field = document.getElementById(fieldId);
    if (!field) {
      return { valid: false, message: errorMessage };
    }
    
    const value = field.value.trim();
    if (value === '') {
      return { valid: true, message: '' };
    }
    
    try {
      new URL(value);
      field.classList.remove('is-invalid');
      return { valid: true, message: '' };
    } catch {
      field.classList.add('is-invalid');
      return { valid: false, message: errorMessage };
    }
  },
  
  /**
   * Clear validation state from a form
   * @param {HTMLFormElement} form - The form element
   */
  clearValidation(form) {
    if (!form) return;
    
    const invalidFields = form.querySelectorAll('.is-invalid');
    invalidFields.forEach(field => field.classList.remove('is-invalid'));
    
    const validFields = form.querySelectorAll('.is-valid');
    validFields.forEach(field => field.classList.remove('is-valid'));
  },
  
  /**
   * Get form data as object
   * @param {HTMLFormElement} form - The form element
   * @returns {object} - Form data as key-value pairs
   */
  getFormData(form) {
    if (!form) return {};
    
    const formData = new FormData(form);
    const data = {};
    
    for (const [key, value] of formData.entries()) {
      if (data[key]) {
        if (Array.isArray(data[key])) {
          data[key].push(value);
        } else {
          data[key] = [data[key], value];
        }
      } else {
        data[key] = value;
      }
    }
    
    return data;
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
  },
  
  /**
   * Initialize collapse section icons (plus/minus toggle)
   */
  initCollapseIcons() {
    document.querySelectorAll('[data-bs-toggle="collapse"]').forEach(button => {
      const targetSelector = button.getAttribute('data-bs-target');
      if (!targetSelector) return;
      
      const target = document.querySelector(targetSelector);
      if (!target) return;
      
      // Toggle icon when section opens
      target.addEventListener('show.bs.collapse', () => {
        const icon = button.querySelector('.bi-plus-circle');
        if (icon) {
          icon.classList.remove('bi-plus-circle');
          icon.classList.add('bi-dash-circle');
        }
      });
      
      // Toggle icon when section closes
      target.addEventListener('hide.bs.collapse', () => {
        const icon = button.querySelector('.bi-dash-circle');
        if (icon) {
          icon.classList.remove('bi-dash-circle');
          icon.classList.add('bi-plus-circle');
        }
      });
    });
  }
};

document.addEventListener('DOMContentLoaded', function() {
  FormUtils.initCollapseIcons();
});

window.FormUtils = FormUtils;