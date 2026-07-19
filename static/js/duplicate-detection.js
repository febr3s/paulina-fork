/**
 * DuplicateDetector - Check for existing authors in Wikidata
 */

class DuplicateDetector {
  constructor(config) {
    this.nameInput = document.getElementById(config.inputId || 'name');
    this.sidebar = document.getElementById(config.sidebarId || 'duplicatesSidebar');
    this.resultsContainer = document.getElementById(config.containerId || 'duplicatesContainer');
    this.noMatchMessage = document.getElementById(config.noMatchId || 'noMatchesMessage');
    this.noneMatchBtn = document.getElementById(config.noneMatchBtnId || 'noneMatchBtn');
    
    this.apiEndpoint = config.apiEndpoint || '/api/search-wikidata-items';
    this.entityType = config.entityType || 'author';
    this.debounceTime = config.debounceTime || 500;
    this.minChars = config.minChars || 3;
    
    // Translatable messages with English fallbacks
    this.msg = Object.assign({
      searching: 'Searching...',
      noMatch: 'No exact match found.',
      error: 'Error searching Wikidata',
      noDescription: 'No description'
    }, config.messages || {});
    
    this.debounceTimer = null;
    this.userConfirmedNoMatch = false;
    
    this.init();
  }
  
  init() {
    if (!this.nameInput) {
      console.warn('DuplicateDetector: Name input not found');
      return;
    }
    
    this.nameInput.addEventListener('input', () => this.handleInput());
    
    if (this.noneMatchBtn) {
      this.noneMatchBtn.addEventListener('click', () => {
        this.userConfirmedNoMatch = true;
        this.hideSidebar();
        if (this.noMatchMessage) {
          this.noMatchMessage.classList.remove('d-none');
        }
      });
    }
  }
  
  handleInput() {
    clearTimeout(this.debounceTimer);
    
    this.userConfirmedNoMatch = false;
    if (this.noMatchMessage) {
      this.noMatchMessage.classList.add('d-none');
    }
    
    const query = this.nameInput.value.trim();
    
    if (query.length < this.minChars) {
      this.hideSidebar();
      return;
    }
    
    this.debounceTimer = setTimeout(() => this.searchDuplicates(query), this.debounceTime);
  }
  
  async searchDuplicates(query) {
    if (this.resultsContainer) {
      this.resultsContainer.innerHTML = `
        <div class="text-muted small">
          <div class="spinner-border spinner-border-sm me-1"></div>
          ${this.msg.searching}
        </div>
      `;
    }
    this.showSidebar();
    
    try {
      const lang = document.documentElement.lang || 'en';
      const response = await fetch(`${this.apiEndpoint}?q=${encodeURIComponent(query)}&type=${this.entityType}&lang=${lang}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error: ${response.status}`);
      }
      
      const results = await response.json();
      this.displayResults(results);
      
    } catch (error) {
      console.error('Duplicate search error:', error);
      if (this.resultsContainer) {
        this.resultsContainer.innerHTML = `
          <div class="text-danger small">
            <i class="bi bi-exclamation-circle me-1"></i>
            ${this.msg.error}
          </div>
        `;
      }
    }
  }
  
  displayResults(results) {
    if (!results || results.length === 0) {
      // No matches found
      // Check if noMatchMessage is inside or outside the sidebar
      const isMessageInsideSidebar = this.noMatchMessage && this.sidebar && this.sidebar.contains(this.noMatchMessage);
      
      if (isMessageInsideSidebar) {
        // Case 1: Message is inside sidebar 
        // Clear results, show sidebar with no-matches message, hide button
        if (this.resultsContainer) {
          this.resultsContainer.innerHTML = '';
        }
        if (this.noneMatchBtn) {
          this.noneMatchBtn.classList.add('d-none');
        }
        if (this.noMatchMessage) {
          this.noMatchMessage.classList.remove('d-none');
        }
        this.showSidebar();
      } else {
        // Case 2: Message is outside sidebar
        // Hide sidebar completely, show external no-matches message
        this.hideSidebar();
        if (this.noMatchMessage) {
          this.noMatchMessage.classList.remove('d-none');
        }
      }
      return;
    }
    
    if (this.noMatchMessage) {
      this.noMatchMessage.classList.add('d-none');
    }
    if (this.noneMatchBtn) {
      this.noneMatchBtn.classList.remove('d-none');
    }
    
    let resultsHTML = '';

    let itemPath;
    if (this.entityType === "author") {
      itemPath = "author";
    } else if (this.entityType === "item") {
      itemPath = "work";
    }
    
    results.forEach(item => {
      const description = item.description || this.msg.noDescription;
      
      resultsHTML += `
        <div class="d-flex align-items-start mb-2 p-2 border rounded bg-white">
          <a href="/${itemPath}/${item.id}" target="_blank" class="text-decoration-none flex-grow-1 me-2">
            <div class="fw-semibold text-primary">${this.escapeHtml(item.label)}</div>
            <small class="text-muted">${this.escapeHtml(description)}</small>
            <small class="text-secondary d-block">${item.id}</small>
          </a>
          <a href="https://www.wikidata.org/wiki/${item.id}" 
            target="_blank" 
            rel="noopener noreferrer"
            class="btn btn-sm btn-outline-secondary flex-shrink-0" 
            title="Wikidata">
            <i class="bi bi-box-arrow-up-right"></i>
          </a>
        </div>
      `;
    });
    
    if (this.resultsContainer) {
      this.resultsContainer.innerHTML = resultsHTML;
    }
    this.showSidebar();
  }
  
  showSidebar() {
    if (this.sidebar) {
      this.sidebar.classList.remove('d-none');
    }
  }
  
  hideSidebar() {
    if (this.sidebar) {
      this.sidebar.classList.add('d-none');
    }
    if (this.resultsContainer) {
      this.resultsContainer.innerHTML = '';
    }
  }
  
  reset() {
    this.userConfirmedNoMatch = false;
    this.hideSidebar();
    if (this.noMatchMessage) {
      this.noMatchMessage.classList.add('d-none');
    }
  }
  
  escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
}

window.DuplicateDetector = DuplicateDetector;