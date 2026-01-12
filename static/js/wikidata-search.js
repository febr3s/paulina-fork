/**
 * WikidataItemSearch - Search and select Wikidata items
 */

class WikidataItemSearch {
  constructor(config) {
    this.inputId = config.inputId;
    this.hiddenInputId = config.hiddenInputId;
    this.resultsId = config.resultsId;
    this.multiSelect = config.multiSelect || false;
    this.selectedItemsId = config.selectedItemsId || null;
    this.apiEndpoint = config.apiEndpoint || '/api/search-wikidata-items';
    this.selectedItems = [];
    this.lastQuery = '';
    
    // All translatable messages with English fallbacks
    this.messages = {
      searching: config.messages?.searching || 'Searching Wikidata...',
      noResults: config.messages?.noResults || 'No Wikidata results found',
      noDescription: config.messages?.noDescription || 'No description',
      error: config.messages?.error || 'Error searching Wikidata',
      alreadyAdded: config.messages?.alreadyAdded || 'This item is already added',
      alreadySelected: config.messages?.alreadySelected || 'This item is already selected',
      remove: config.messages?.remove || 'Remove'
    };
    
    this.input = document.getElementById(this.inputId);
    this.hiddenInput = document.getElementById(this.hiddenInputId);
    this.resultsContainer = document.getElementById(this.resultsId);
    
    if (!this.input || !this.hiddenInput || !this.resultsContainer) {
      console.error(`WikidataItemSearch: Elements not found for ${this.inputId}`);
      return;
    }

    // For single-select, create container for the selected pill
    if (!this.multiSelect) {
      this.selectedContainer = document.getElementById(`${this.inputId}-selected`);
    } else {
      this.selectedContainer = document.getElementById(this.selectedItemsId);
    }
    
    this.searchTimeout = null;
    this.init();
  }
  
  init() {
    this.attachEventListeners();
  }
  
  attachEventListeners() {
    this.input.addEventListener('input', (e) => {
      const query = e.target.value.trim();
      this.lastQuery = query;
      
      clearTimeout(this.searchTimeout);
      
      if (query.length < 2) {
        this.hideResults();
        return;
      }
      
      this.searchTimeout = setTimeout(() => {
        this.search(query);
      }, 500);
    });
    
    document.addEventListener('click', (e) => {
      if (!this.resultsContainer.contains(e.target) && e.target !== this.input) {
        this.hideResults();
      }
    });
  }
  
  async search(query) {
    this.resultsContainer.innerHTML = `
      <div class="p-2 text-center text-muted">
        <div class="spinner-border spinner-border-sm me-2"></div>
        ${this.messages.searching}
      </div>
    `;
    this.showResults();
    
    try {
      const lang = document.documentElement.lang || 'en';
      const response = await fetch(`${this.apiEndpoint}?q=${encodeURIComponent(query)}&lang=${lang}`);
      const data = await response.json();
      
      if (!data || data.length === 0) {
        this.displayNoResults();
        return;
      }
      
      this.displayResults(data);
      
    } catch (error) {
      console.error('Wikidata search error:', error);
      this.resultsContainer.innerHTML = `
        <div class="p-2 text-danger">
          <i class="bi bi-exclamation-circle me-1"></i>
          ${this.messages.error}
        </div>
      `;
    }
  }
  
  displayResults(results) {
    this.resultsContainer.innerHTML = '';
    
    results.forEach(item => {
      const resultItem = document.createElement('div');
      resultItem.className = 'wikidata-result-item p-2 border-bottom';
      resultItem.style.cursor = 'pointer';
      
      resultItem.innerHTML = `
        <div class="d-flex align-items-start">
          <div class="flex-grow-1">
            <div class="fw-semibold">${this.escapeHtml(item.label)}</div>
            <div class="small text-muted">${this.escapeHtml(item.description) || this.messages.noDescription}</div>
          </div>
          <span class="badge bg-primary ms-2">${item.id}</span>
        </div>
      `;
      
      resultItem.addEventListener('mousedown', (e) => {
        e.preventDefault();
        this.selectItem(item);
      });
      
      resultItem.addEventListener('mouseenter', () => {
        resultItem.style.backgroundColor = '#e7f1ff';
      });
      
      resultItem.addEventListener('mouseleave', () => {
        resultItem.style.backgroundColor = '';
      });
      
      this.resultsContainer.appendChild(resultItem);
    });
  }
  
  displayNoResults() {
    this.resultsContainer.innerHTML = `
      <div class="p-2 text-muted">
        <i class="bi bi-info-circle me-1"></i>
        ${this.messages.noResults}
      </div>
    `;
  }
  
  selectItem(item) {
    if (this.multiSelect) {
      if (this.selectedItems.some(i => i.id === item.id)) {
        alert(this.messages.alreadySelected);
        return;
      }
      
    this.selectedItems.push(item);
    this.input.value = ''; // Clear input
    this.input.style.display = 'none'; // Hide input after selection
    this.updateSelectedItemsDisplay(); // Re-render in display mode
    this.updateHiddenInput();
    this.updateVisibleInput();
    this.hideResults();
      
    } else {
      // Single select: replace any existing selection
      this.selectedItems = [item];
      this.hiddenInput.value = item.id;
      this.input.value = item.label;  
      this.updateSingleSelectDisplay();
      this.hideResults();
    }
    
    this.input.dispatchEvent(new CustomEvent('wikidata:select', {
      detail: item
    }));
  }
  
  updateSingleSelectDisplay() {
  if (!this.selectedContainer) return;
  
  this.selectedContainer.innerHTML = '';
  
  const item = this.selectedItems[0];
  if (!item) {
    this.selectedContainer.classList.add('d-none');
    // Show input when no selection
    this.input.style.display = 'block';
    return;
  }
  
  this.selectedContainer.classList.remove('d-none');
  
  // Hide the text input when we have a selection
  this.input.style.display = 'none';
  
  // Style container to look like the input
  this.selectedContainer.style.cssText = `
    border: 1px solid #000;
    background-color: #ffe65b;
    border-radius: 0.375rem;
    padding: 0.375rem 0.75rem;
    min-height: 38px;
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
    align-items: center;
    cursor: pointer;
  `;
  
  // Make container clickable to change selection
  this.selectedContainer.onclick = () => {
    this.input.style.display = 'block';
    this.input.focus();
    this.selectedContainer.style.display = 'none';
  };
  
  const badge = this.createPillElement(item, 0);
  this.selectedContainer.appendChild(badge);
  
  // Add a change button
  const changeBtn = document.createElement('button');
  changeBtn.type = 'button';
  changeBtn.className = 'btn btn-sm btn-outline-secondary';
  changeBtn.innerHTML = '<i class="bi bi-pencil"></i>';
  changeBtn.style.cssText = 'padding: 0.25rem 0.5rem; margin-left: auto;';
  changeBtn.onclick = (e) => {
    e.stopPropagation();
    this.input.style.display = 'block';
    this.input.focus();
    this.selectedContainer.style.display = 'none';
  };
  this.selectedContainer.appendChild(changeBtn);
}
  
  updateSelectedItemsDisplay() {
  const container = this.multiSelect 
    ? document.getElementById(this.selectedItemsId)
    : this.selectedContainer;
    
  if (!container) return;
  
  container.innerHTML = '';
  
  if (this.selectedItems.length === 0) {
    container.classList.add('d-none');
    // Show input when no selections
    if (this.multiSelect) {
      this.input.style.display = 'block';
    }
    return;
  }
  
  container.classList.remove('d-none');
  
  // Check if input is currently visible (editing mode)
  const isEditing = this.input.style.display !== 'none';
  
  if (this.multiSelect) {
    if (isEditing) {
      // Editing mode: show badges above input in a simple flex container
      container.style.cssText = `
        display: flex;
        flex-wrap: wrap;
        gap: 4px;
        margin-bottom: 0.5rem;
      `;
    } else {
      // Display mode: hide input and style container to look like input
      this.input.style.display = 'none';
      
      container.style.cssText = `
        border: 1px solid #000;
        background-color: #ffe65b;
        border-radius: 0.375rem;
        padding: 0.375rem 0.75rem;
        min-height: 38px;
        display: flex;
        flex-wrap: wrap;
        gap: 4px;
        align-items: center;
        cursor: pointer;
      `;
      
      // Make container clickable to add more items
      container.onclick = () => {
        this.input.value = ''; // Clear input before showing
        this.input.style.display = 'block';
        this.input.focus();
        this.updateSelectedItemsDisplay(); // Re-render in editing mode
      };
    }
  }
  
  this.selectedItems.forEach((item, index) => {
    const badge = this.createPillElement(item, index);
    container.appendChild(badge);
  });
  
  // Add a "+" button only in display mode (not editing)
  if (this.multiSelect && !isEditing) {
    const addMoreBtn = document.createElement('button');
    addMoreBtn.type = 'button';
    addMoreBtn.className = 'btn btn-sm btn-outline-primary';
    addMoreBtn.innerHTML = '<i class="bi bi-plus"></i>';
    addMoreBtn.style.cssText = 'padding: 0.25rem 0.5rem; margin-left: auto;';
    addMoreBtn.onclick = (e) => {
      e.stopPropagation();
      this.input.value = ''; // Clear input before showing
      this.input.style.display = 'block';
      this.input.focus();
      this.updateSelectedItemsDisplay(); // Re-render in editing mode
    };
    container.appendChild(addMoreBtn);
  }
}

  createPillElement(item, index) {
    const badge = document.createElement('span');
    badge.className = 'badge d-inline-flex align-items-center me-1 mb-1 py-2 px-3';
    badge.style.backgroundColor = '#29a4e2';
    badge.innerHTML = `
      <span>${this.escapeHtml(item.label)}</span>
      <button type="button" class="btn-close btn-close-white ms-2" style="font-size: 0.55em;" aria-label="${this.messages.remove}"></button>
    `;
    
    badge.querySelector('.btn-close').addEventListener('click', (e) => {
      e.stopPropagation();
      this.removeSelectedItem(index);
    });
    
    return badge;
  }
  
  removeSelectedItem(index) {
    this.selectedItems.splice(index, 1);
    
    if (this.multiSelect) {
      this.updateSelectedItemsDisplay();
      this.updateHiddenInput();
      this.updateVisibleInput();
    } else {
      this.hiddenInput.value = '';
      this.input.value = '';
      this.updateSingleSelectDisplay();
    }
    
    this.input.dispatchEvent(new CustomEvent('wikidata:remove', { detail: { index } }));
  }
  
  updateHiddenInput() {
    if (this.multiSelect) {
      const qids = this.selectedItems.map(i => i.id).join(',');
      this.hiddenInput.value = qids;
    }
  }

  updateVisibleInput() {
  if (this.multiSelect) {
    const labels = this.selectedItems.map(i => i.label).join(',');
    this.input.value = labels;
  }
}
  
  showResults() {
    this.resultsContainer.style.display = 'block';
  }
  
  hideResults() {
    this.resultsContainer.style.display = 'none';
  }
  
  reset() {
    this.selectedItems = [];
    this.lastQuery = '';
    this.hiddenInput.value = '';
    this.input.value = '';
    
    if (this.selectedContainer) {
      this.selectedContainer.classList.add('d-none');
      this.selectedContainer.innerHTML = '';
    }
    
    if (this.multiSelect && this.selectedItemsId) {
      const container = document.getElementById(this.selectedItemsId);
      if (container) {
        container.classList.add('d-none');
        container.innerHTML = '';
      }
    }
    
    this.hideResults();
  }
  
  getSelectedItems() {
    return this.selectedItems;
  }
  
  getValue() {
    if (this.multiSelect) {
      return {
        qids: this.selectedItems.map(i => i.id)
      };
    } else {
      const item = this.selectedItems[0];
      return item ? { id: item.id, label: item.label } : null;
    }
  }
  
  hasValue() {
    return this.selectedItems.length > 0;
  }
  
  escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
}

window.WikidataItemSearch = WikidataItemSearch;