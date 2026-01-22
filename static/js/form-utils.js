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
 * Validate date input parts (year, month, day)
 * Rejects invalid placeholders but allows less precise dates: year only, month & year only.
 * 
 * @param {string} year - Year value
 * @param {string} month - Month value
 * @param {string} day - Day value
 * @param {object} messages - Translated error messages
 * @returns {object} - { valid: boolean, message: string }
 */
validateDateInput(year, month, day, messages = {}) {
  const defaultMessages = {
    yearRequired: 'Year is required for dates',
    yearInvalid: 'Year must be a valid 4-digit number',
    monthInvalid: 'Month must be between 0-12 (0 for unknown)',
    dayInvalid: 'Day must be between 0-31 (0 for unknown)',
    monthRequiredForDay: 'Month cannot be 0 if day is specified',
    monthRequiredForYear: 'Month is required if you enter year and day'
  };
  
  const msg = { ...defaultMessages, ...messages };
  
  // If no year, date is completely empty - that's valid (optional field)
  if (!year || year === '') {
    // But if month or day is filled without year, that's invalid
    if (month || day) {
      return { valid: false, message: msg.yearRequired };
    }
    return { valid: true, message: '' };
  }
  
  // Year validation
  const yearNum = parseInt(year, 10);
  if (isNaN(yearNum) || yearNum < 1 || yearNum > 9999 || year.length !== 4) {
    return { valid: false, message: msg.yearInvalid };
  }
  
  // Month validation (0 = unknown, 1-12 = specific month)
  if (month !== '' && month !== null && month !== undefined) {
    const monthNum = parseInt(month, 10);
    if (isNaN(monthNum) || monthNum < 0 || monthNum > 12) {
      return { valid: false, message: msg.monthInvalid };
    }
    
    // If day is provided but month is 0, that's invalid
    if (monthNum === 0 && day && parseInt(day, 10) > 0) {
      return { valid: false, message: msg.monthRequiredForDay };
    }
  }
  
  // Day validation (0 = unknown, 1-31 = specific day)
  if (day !== '' && day !== null && day !== undefined) {
    const dayNum = parseInt(day, 10);
    if (isNaN(dayNum) || dayNum < 0 || dayNum > 31) {
      return { valid: false, message: msg.dayInvalid };
    }
    
    // If day is provided but month is empty/missing, that's invalid
    if (dayNum > 0 && (!month || month === '')) {
      return { valid: false, message: msg.monthRequiredForYear };
    }
  }
  
  return { valid: true, message: '' };
},
  
  /**
   * Combine date parts into YYYY-MM-DD format
   * Handles empty/unknown values by converting to '00'
   * 
   * @param {string} year - Year value
   * @param {string} month - Month value  
   * @param {string} day - Day value
   * @returns {string|null} - Combined date string or null if no year
   */
  combineDateParts(year, month, day) {
    if (!year || year === '') {
      return null;
    }
    
    const paddedYear = year.padStart(4, '0');
    const paddedMonth = (month && month !== '') ? month.padStart(2, '0') : '00';
    const paddedDay = (day && day !== '') ? day.padStart(2, '0') : '00';
    
    return `${paddedYear}-${paddedMonth}-${paddedDay}`;
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