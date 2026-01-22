/**
 * Combobox - Filterable dropdown select
 */

class Combobox {
  constructor(config) {
    this.input = document.getElementById(config.inputId);
    this.select = document.getElementById(config.selectId);
    this.dropdown = document.getElementById(config.dropdownId);
    
    // Translatable messages with English fallbacks
    this.msg = {
      noOption: config.noOptionText || 'No option'
    };
    
    this.options = [];
    this.selectedValue = '';
    
    this.init();
  }
  
  init() {
    if (!this.input || !this.select || !this.dropdown) {
      console.warn('Combobox: Required elements not found');
      return;
    }
    
    // Build options from select
    this.buildOptions();
    
    // Event listeners
    this.input.addEventListener('input', () => this.filter());
    this.input.addEventListener('focus', () => this.showDropdown());
    
    document.addEventListener('click', (e) => {
      if (!this.input.contains(e.target) && !this.dropdown.contains(e.target)) {
        this.hideDropdown();
      }
    });
  }
  
  buildOptions() {
    this.options = [];
    
    Array.from(this.select.options).forEach(option => {
      if (option.value) {
        this.options.push({
          value: option.value,
          label: option.textContent
        });
      }
    });
  }
  
  filter() {
    const query = this.input.value.toLowerCase().trim();
    this.dropdown.innerHTML = '';
    
    const filtered = query 
      ? this.options.filter(opt => opt.label.toLowerCase().includes(query))
      : this.options;
    
    if (filtered.length === 0) {
      const li = document.createElement('li');
      li.className = 'dropdown-item text-muted';
      li.textContent = this.msg.noOption;
      this.dropdown.appendChild(li);
    } else {
      filtered.forEach(opt => {
        const li = document.createElement('li');
        li.className = 'dropdown-item';
        li.style.cursor = 'pointer';
        li.textContent = opt.label;
        li.dataset.value = opt.value;
        
        li.addEventListener('click', () => this.selectOption(opt));
        li.addEventListener('mouseenter', () => li.classList.add('active'));
        li.addEventListener('mouseleave', () => li.classList.remove('active'));
        
        this.dropdown.appendChild(li);
      });
    }
    
    this.showDropdown();
  }
  
  selectOption(option) {
    this.input.value = option.label;
    this.select.value = option.value;
    this.selectedValue = option.value;
    this.hideDropdown();
    
    // Trigger change event
    this.select.dispatchEvent(new Event('change'));
  }
  
  showDropdown() {
    if (this.dropdown.children.length === 0) {
      this.filter();
    }
    this.dropdown.classList.add('show');
  }
  
  hideDropdown() {
    this.dropdown.classList.remove('show');
  }
  
  reset() {
    this.input.value = '';
    this.select.value = '';
    this.selectedValue = '';
    this.hideDropdown();
  }
  
  getValue() {
    return this.selectedValue;
  }
  
  setValue(value) {
    const option = this.options.find(opt => opt.value === value);
    if (option) {
      this.selectOption(option);
    }
  }
}

window.Combobox = Combobox;