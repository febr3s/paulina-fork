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

    this.input.addEventListener('blur', (e) => {
      setTimeout(() => {
        this.hideResults();
        // For multi-select, switch to display mode when focus leaves
        if (this.multiSelect && this.selectedItems.length > 0) {
          this.input.style.display = 'none';
          this.updateSelectedItemsDisplay();
        }
      }, 200);
    });

    this.input.addEventListener('focus', (e) => {
      // For multi-select, switch to editing mode when focused
      if (this.multiSelect) {
        this.input.style.display = 'block';
        this.updateSelectedItemsDisplay();
      }
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
      this.updateSelectedItemsDisplay();
      this.updateHiddenInput();
      this.updateVisibleInput();
      this.input.value = ''; // Clear input
      this.hideResults(); // Hide results
      this.input.focus(); // Keep focus on input for next selection
      
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
      this.input.style.display = 'block';
      return;
    }
    
    this.selectedContainer.classList.remove('d-none');
    this.input.style.display = 'none';
    
    // Style container to look like the input
    this.selectedContainer.style.cssText = `
      border: 1px solid #000;
      background-color: #ffe65b;
      padding: 0.375rem 0.75rem;
      min-height: 38px;
      display: flex;
      flex-wrap: wrap;
      gap: 4px;
      align-items: center;
    `;
    
    const badge = this.createPillElement(item, 0);
    this.selectedContainer.appendChild(badge);
  }
  
  updateSelectedItemsDisplay() {
    const container = this.multiSelect 
      ? document.getElementById(this.selectedItemsId)
      : this.selectedContainer;
      
    if (!container) return;
    
    container.innerHTML = '';
    
    if (this.selectedItems.length === 0) {
      container.classList.add('d-none');
      if (this.multiSelect) {
        this.input.style.display = 'block';
      }
      return;
    }
    
    container.classList.remove('d-none');
    
    // Check if input is currently visible (editing mode)
    const isInputVisible = this.input.style.display !== 'none';
    
    if (this.multiSelect) {
      if (isInputVisible) {
        // Editing mode: show badges above input in a simple flex container
        container.style.cssText = `
          display: flex;
          flex-wrap: wrap;
          gap: 4px;
          margin-bottom: 0.5rem;
        `;
      } else {
        // Display mode: hide input and style container to look like input
        container.style.cssText = `
          border: 1px solid #000;
          background-color: #ffe65b;
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
      
      // If no items left, show the input
      if (this.selectedItems.length === 0) {
        this.input.style.display = 'block';
      }
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
  
  this.hiddenInput.value = this.selectedItems.map(item => item.id).join(',');

  if (this.multiSelect) {
    const labelsInput = document.getElementById(this.inputId + '-labels');
    if (labelsInput) {
      labelsInput.value = this.selectedItems.map(item => item.label).join(',');
    }
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