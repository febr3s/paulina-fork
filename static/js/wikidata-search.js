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
    this.allowFreeText = config.allowFreeText !== false;
    this.apiEndpoint = config.apiEndpoint || '/api/search-wikidata-items';
    this.selectedItems = [];
    this.lastQuery = '';
    
    // All translatable messages with defaults
    this.messages = {
      searching: config.messages?.searching || 'Searching Wikidata...',
      noResults: config.messages?.noResults || 'No Wikidata results found',
      noDescription: config.messages?.noDescription || 'No description',
      error: config.messages?.error || 'Error searching Wikidata',
      addAsText: config.messages?.addAsText || 'Add as text',
      useAsText: config.messages?.useAsText || 'Use as entered',
      freeTextHint: config.messages?.freeTextHint || 'Not linked to Wikidata',
      alreadyAdded: config.messages?.alreadyAdded || 'This item is already added',
      alreadySelected: config.messages?.alreadySelected || 'This item is already selected',
      textLabel: config.messages?.textLabel || 'text',
      remove: config.messages?.remove || 'Remove'
    };
    
    this.input = document.getElementById(this.inputId);
    this.hiddenInput = document.getElementById(this.hiddenInputId);
    this.resultsContainer = document.getElementById(this.resultsId);
    
    if (!this.input || !this.hiddenInput || !this.resultsContainer) {
      console.error(`WikidataItemSearch: Elements not found for ${this.inputId}`);
      return;
    }
    
    // For single-select, get or create container for the selected pill
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
    
    // Handle Enter key for free text
    this.input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        const text = this.input.value.trim();
        if (text && this.allowFreeText) {
          if (this.multiSelect) {
            this.addFreeTextItem(text);
          } else {
            this.selectFreeText(text);
          }
        }
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
        this.displayNoResults(query);
        return;
      }
      
      this.displayResults(data, query);
      
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
  
  displayResults(results, query) {
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
        this.selectItem({ ...item, isText: false });
      });
      
      resultItem.addEventListener('mouseenter', () => {
        resultItem.style.backgroundColor = '#e7f1ff';
      });
      
      resultItem.addEventListener('mouseleave', () => {
        resultItem.style.backgroundColor = '';
      });
      
      this.resultsContainer.appendChild(resultItem);
    });
    
    if (this.allowFreeText && query) {
      this.addFreeTextOption(query);
    }
  }
  
  displayNoResults(query) {
    this.resultsContainer.innerHTML = `
      <div class="p-2 text-muted">
        <i class="bi bi-info-circle me-1"></i>
        ${this.messages.noResults}
      </div>
    `;
    
    if (this.allowFreeText && query) {
      this.addFreeTextOption(query, true);
    }
  }
  
  addFreeTextOption(query, prominent = false) {
    const freeTextItem = document.createElement('div');
    freeTextItem.className = `free-text-option p-2 ${prominent ? 'bg-light' : 'border-top'}`;
    freeTextItem.style.cursor = 'pointer';
    
    const actionText = this.multiSelect ? this.messages.addAsText : this.messages.useAsText;
    
    freeTextItem.innerHTML = `
      <div class="d-flex align-items-center ${prominent ? 'text-primary' : 'text-secondary'}">
        <i class="bi bi-plus-circle me-2"></i>
        <div class="flex-grow-1">
          <span>${actionText}:</span>
          <strong class="ms-1">"${this.escapeHtml(query)}"</strong>
        </div>
        <span class="badge bg-secondary ms-2">${this.messages.textLabel}</span>
      </div>
      <div class="small text-muted ms-4 mt-1">
        <i class="bi bi-lightbulb me-1"></i>
        ${this.messages.freeTextHint}
      </div>
    `;
    
    freeTextItem.addEventListener('mousedown', (e) => {
      e.preventDefault();
      if (this.multiSelect) {
        this.addFreeTextItem(query);
      } else {
        this.selectFreeText(query);
      }
    });
    
    freeTextItem.addEventListener('mouseenter', () => {
      freeTextItem.style.backgroundColor = '#fff3cd';
    });
    
    freeTextItem.addEventListener('mouseleave', () => {
      freeTextItem.style.backgroundColor = prominent ? '#f8f9fa' : '';
    });
    
    this.resultsContainer.appendChild(freeTextItem);
  }
  
  selectFreeText(text) {
    if (this.multiSelect) {
      this.addFreeTextItem(text);
    } else {
      // Single select: replace any existing selection
      this.selectedItems = [{ id: null, label: text, isText: true }];
      this.hiddenInput.value = '';
      this.input.value = '';
      this.updateSingleSelectDisplay();
      this.hideResults();
      
      this.input.dispatchEvent(new CustomEvent('wikidata:freetext', {
        detail: { label: text, isText: true }
      }));
    }
  }
  
  addFreeTextItem(text) {
    if (this.selectedItems.some(i => i.label.toLowerCase() === text.toLowerCase())) {
      alert(this.messages.alreadyAdded);
      return;
    }
    
    this.selectedItems.push({
      id: null,
      label: text,
      isText: true
    });
    
    this.updateSelectedItemsDisplay();
    this.updateHiddenInput();
    this.input.value = '';
    this.hideResults();
  }
  
  selectItem(item) {
    if (this.multiSelect) {
      if (this.selectedItems.some(i => i.id === item.id && i.id !== null)) {
        alert(this.messages.alreadySelected);
        return;
      }
      
      this.selectedItems.push(item);
      this.updateSelectedItemsDisplay();
      this.updateHiddenInput();
      this.input.value = '';
      this.hideResults();
      
    } else {
      // Single select: replace any existing selection
      this.selectedItems = [item];
      this.hiddenInput.value = item.id || '';
      this.input.value = '';
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
      return;
    }
    
    this.selectedContainer.classList.remove('d-none');
    
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
      return;
    }
    
    container.classList.remove('d-none');
    
    this.selectedItems.forEach((item, index) => {
      const badge = this.createPillElement(item, index);
      container.appendChild(badge);
    });
  }
  
  createPillElement(item, index) {
    const badge = document.createElement('span');
    badge.className = 'badge d-inline-flex align-items-center me-1 mb-1 py-2 px-3';
    
    // Blue for Wikidata items, gray for plain text
    const isWikidata = !item.isText && item.id;
    badge.style.backgroundColor = isWikidata ? '#0d6efd' : '#6c757d';
    
    const icon = isWikidata 
      ? '<i class="bi bi-link-45deg me-1"></i>' 
      : '<i class="bi bi-fonts me-1"></i>';
    
    badge.innerHTML = `
      ${icon}
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
    } else {
      this.hiddenInput.value = '';
      this.updateSingleSelectDisplay();
    }
    
    this.input.dispatchEvent(new CustomEvent('wikidata:remove', { detail: { index } }));
  }
  
  updateHiddenInput() {
    if (this.multiSelect) {
      const qids = this.selectedItems.filter(i => !i.isText).map(i => i.id).join(',');
      const texts = this.selectedItems.filter(i => i.isText).map(i => i.label).join('|');
      
      this.hiddenInput.value = qids;
      
      const textInput = document.getElementById(this.hiddenInputId.replace('-qids', '-texts'));
      if (textInput) {
        textInput.value = texts;
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
    
    const textInput = document.getElementById(this.hiddenInputId.replace('-qids', '-texts'));
    if (textInput) textInput.value = '';
    
    this.hideResults();
  }
  
  getSelectedItems() {
    return this.selectedItems;
  }
  
  getValue() {
    if (this.multiSelect) {
      return {
        qids: this.selectedItems.filter(i => !i.isText).map(i => i.id),
        texts: this.selectedItems.filter(i => i.isText).map(i => i.label)
      };
    } else {
      const item = this.selectedItems[0];
      return item ? { id: item.id, label: item.label, isText: item.isText } : null;
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