/**
 * ImagePreview - Preview and validate Wikimedia Commons images
 */

class ImagePreview {
  constructor(config) {
    this.input = document.getElementById(config.inputId);
    this.preview = document.getElementById(config.previewId);
    this.errorEl = document.getElementById(config.errorId);
    this.clearBtn = document.getElementById(config.clearBtnId);
    this.requireCommons = config.requireCommons !== false;
    
    this.defaultImage = 'https://upload.wikimedia.org/wikipedia/commons/c/cd/Portrait_Placeholder_Square.png';
    this.isValidImage = true;
    this.hasImage = false;
    
    // Translatable messages with English fallbacks
    this.msg = Object.assign({
      invalidCommons: 'Please use an image from Wikimedia Commons.',
      loadError: 'Could not load image. Please check the URL.'
    }, config.messages || {});
    
    this.init();
  }
  
  init() {
    if (!this.input || !this.preview) {
      console.warn('ImagePreview: Required elements not found');
      return;
    }
    
    this.input.addEventListener('input', () => this.handleInput());
    this.input.addEventListener('paste', () => {
      setTimeout(() => this.handleInput(), 100);
    });
    
    if (this.clearBtn) {
      this.clearBtn.addEventListener('click', () => this.reset());
    }
  }
  
  handleInput() {
    const url = this.input.value.trim();
    
    if (!url) {
      this.reset();
      return;
    }
    
    // Validate Commons URL if required
    if (this.requireCommons && !this.isCommonsUrl(url)) {
      this.showError(this.msg.invalidCommons);
      this.isValidImage = false;
      return;
    }
    
    this.loadImage(url);
  }
  
  isCommonsUrl(url) {
    return url.includes('upload.wikimedia.org') || 
           url.includes('commons.wikimedia.org');
  }
  
  loadImage(url) {
    this.hideError();
    
    const img = new Image();
    
    img.onload = () => {
      this.preview.src = url;
      this.isValidImage = true;
      this.hasImage = true;
      
      if (this.clearBtn) {
        this.clearBtn.classList.remove('d-none');
      }
    };
    
    img.onerror = () => {
      this.showError(this.msg.loadError);
      this.isValidImage = false;
      this.preview.src = this.defaultImage;
    };
    
    img.src = url;
  }
  
  showError(message) {
    if (this.errorEl) {
      this.errorEl.textContent = message;
      this.errorEl.classList.remove('d-none');
    }
    this.input.classList.add('is-invalid');
  }
  
  hideError() {
    if (this.errorEl) {
      this.errorEl.classList.add('d-none');
    }
    this.input.classList.remove('is-invalid');
  }
  
  isValid() {
    // Valid if: no image entered, OR image is valid
    if (!this.input.value.trim()) {
      return true;
    }
    return this.isValidImage;
  }
  
  reset() {
    this.input.value = '';
    this.preview.src = this.defaultImage;
    this.isValidImage = true;
    this.hasImage = false;
    this.hideError();
    
    if (this.clearBtn) {
      this.clearBtn.classList.add('d-none');
    }
  }
  
  getImageUrl() {
    return this.hasImage ? this.input.value.trim() : null;
  }
}

window.ImagePreview = ImagePreview;