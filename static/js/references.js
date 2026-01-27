/**
 * ReferenceManager - Manage references for form fields
 */

class ReferenceManager {
  constructor(config = {}) {
    this.maxReferences = config.maxReferences || 3;
    this.references = {};
    
    // Translatable messages with English fallbacks
    this.msg = Object.assign({
      reference: 'Reference',
      url: 'Reference URL',
      title: 'Title',
      retrieved: 'Date accessed',
      maxReached: 'Maximum 3 references per field',
      remove: 'Remove'
    }, config.messages || {});
  }
  
  toggleReference(fieldId) {
    const section = document.getElementById(`${fieldId}-references`);
    if (!section) return;
    
    // Show the section if hidden
    if (section.classList.contains('d-none')) {
      section.classList.remove('d-none');
    }
    
    // Add a reference 
    this.addReference(fieldId);
  }
  
  addReference(fieldId) {
    const container = document.getElementById(`${fieldId}-reference-container`);
    if (!container) return;
    
    if (!this.references[fieldId]) {
      this.references[fieldId] = [];
    }
    
    if (this.references[fieldId].length >= this.maxReferences) {
      alert(this.msg.maxReached);
      return;
    }
    
    const refIndex = this.references[fieldId].length;
    const refId = `${fieldId}-ref-${refIndex}`;
    
    this.references[fieldId].push(refId);
    
    const refDiv = document.createElement('div');
    refDiv.className = 'reference-item mb-3 p-2 border rounded bg-light';
    refDiv.id = refId;
    
    refDiv.innerHTML = `
      <div class="d-flex justify-content-between align-items-center mb-2">
        <strong>${this.msg.reference} ${refIndex + 1}</strong>
        <button type="button" class="btn btn-sm btn-outline-danger remove-ref-btn" aria-label="${this.msg.remove}">
          <i class="bi bi-trash"></i>
        </button>
      </div>
      <div class="mb-2">
        <label class="form-label small">${this.msg.url}</label>
        <input type="url" class="form-control form-control-sm" name="${fieldId}_ref_url_${refIndex}" placeholder="Enter the full URL including https://">
      </div>
      <div class="mb-2">
        <label class="form-label small">${this.msg.title}</label>
        <input type="text" class="form-control form-control-sm" name="${fieldId}_ref_title_${refIndex}">
      </div>
      <div>
        <label class="form-label small">${this.msg.retrieved}</label>
        <input type="date" class="form-control form-control-sm" name="${fieldId}_ref_retrieved_${refIndex}" value="${this.getTodayDate()}">
      </div>
    `;
    
    // Remove button handler
    refDiv.querySelector('.remove-ref-btn').addEventListener('click', () => {
      this.removeReference(fieldId, refId);
    });
    
    container.appendChild(refDiv);
  }
  
  removeReference(fieldId, refId) {
    const refDiv = document.getElementById(refId);
    if (refDiv) {
      refDiv.remove();
    }
    
    if (this.references[fieldId]) {
      this.references[fieldId] = this.references[fieldId].filter(id => id !== refId);
    }
  }
  
  fillTemplate(fieldId, template) {
    const container = document.getElementById(`${fieldId}-reference-container`);
    if (!container) return;
    
    // Get the last reference or add one
    let lastRef = container.querySelector('.reference-item:last-child');
    if (!lastRef) {
      this.addReference(fieldId);
      lastRef = container.querySelector('.reference-item:last-child');
    }
    
    if (!lastRef) return;
    
    const urlInput = lastRef.querySelector('input[type="url"]');
    
    // Set template-specific placeholder
    const templates = {
      wikipedia: 'https://en.wikipedia.org/wiki/...',
      library: 'https://viaf.org/... or https://id.loc.gov/...',
      website: 'https://...'
    };
    
    if (urlInput && templates[template]) {
      urlInput.placeholder = templates[template];
      urlInput.focus();
    }
  }
  
  getTodayDate() {
    return new Date().toISOString().split('T')[0];
  }
  
  reset() {
    // Clear all reference containers
    Object.keys(this.references).forEach(fieldId => {
      const container = document.getElementById(`${fieldId}-reference-container`);
      if (container) {
        container.innerHTML = '';
      }
      
      const section = document.getElementById(`${fieldId}-references`);
      if (section) {
        section.style.display = 'none';
      }
    });
    
    this.references = {};
  }
  
  getReferences(fieldId) {
    return this.references[fieldId] || [];
  }
  
  getAllReferences() {
    return this.references;
  }
}

window.ReferenceManager = ReferenceManager;