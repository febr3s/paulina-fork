/**
 * ImagePreview - Preview and validate Wikimedia Commons images
 */

class ImagePreview {
  constructor(config) {
    this.input = document.getElementById(config.inputId);
    this.preview = document.getElementById(config.previewId);
    this.placeholder = config.placeholderId ? document.getElementById(config.placeholderId) : null;
    this.errorEl = document.getElementById(config.errorId);
    this.clearBtn = document.getElementById(config.clearBtnId);
    this.requireCommons = config.requireCommons !== false;
    
    // Preview dimensions 
    this.previewWidth = config.previewWidth || 400;
    this.previewHeight = config.previewHeight || 400;
    
    this.isValidImage = true;
    this.hasImage = false;
    this.isLoading = false;
    
    // Translatable messages with English fallbacks
    this.msg = Object.assign({
      invalidCommons: 'Please use an image from Wikimedia Commons.',
      loadError: 'Could not load image. Please check the URL.',
      tiffNotSupported: 'TIFF images cannot be previewed in the browser, but will work on Wikidata.',
      loading: 'Loading preview...'
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
    
    // Check for TIFF files (can't preview but valid for Wikidata)
    if (this.isTiffFile(url)) {
      this.showWarning(this.msg.tiffNotSupported);
      this.isValidImage = true;
      this.hasImage = true;
      
      if (this.clearBtn) {
        this.clearBtn.classList.remove('d-none');
      }
      return;
    }
    
    this.loadImage(url);
  }
  
  isCommonsUrl(url) {
    return url.includes('upload.wikimedia.org') || 
           url.includes('commons.wikimedia.org');
  }
  
  isTiffFile(url) {
    return url.toLowerCase().match(/\.(tiff?|tif)(\?|$)/);
  }
  
  /**
   * Extract filename from various Commons URL formats and return optimized image URL
   */
  getOptimizedCommonsUrl(url) {
    let filename = null;

    // Format 1: Direct upload URL
    if (url.includes('upload.wikimedia.org') && !url.includes('/thumb/')) {
      const parts = url.split('/');
      filename = decodeURIComponent(parts[parts.length - 1].split('?')[0]);
    }

    // Format 2: Commons file page
    else if (url.includes('commons.wikimedia.org/wiki/File:')) {
      filename = url.split('File:')[1].split('?')[0].split('#')[0];
      filename = decodeURIComponent(filename);
    }

    // Format 3: Using Special:Redirect
    else if (url.includes('Special:Redirect/file/')) {
      return url;
    }
    
    // Format 4: Thumb URL
    else if (url.includes('/thumb/')) {
      const parts = url.split('/');
      const lastPart = parts[parts.length - 1];
      filename = decodeURIComponent(lastPart.replace(/^\d+px-/, ''));
    }

    if (!filename) {
      return url; // Fallback to original URL if parsing fails
    }

    // Return optimized Commons URL with specified dimensions
    const encodedFilename = encodeURIComponent(filename);
    return `https://commons.wikimedia.org/w/index.php?title=Special:Redirect/file/${encodedFilename}&width=${this.previewWidth}&height=${this.previewHeight}`;
  }
  
  showLoading() {
    this.isLoading = true;
    this.hideError();
    
    // Hide both placeholder and preview
    if (this.placeholder) {
      this.placeholder.classList.add('d-none');
    }
    this.preview.classList.add('d-none');
    
    // Show loading spinner
    let loadingEl = this.placeholder ? this.placeholder.parentElement.querySelector('.image-loading') : null;
    
    if (!loadingEl && this.placeholder && this.placeholder.parentElement) {
      loadingEl = document.createElement('div');
      loadingEl.className = 'image-loading d-flex flex-column align-items-center justify-content-center';
      loadingEl.style.width = '100%';
      loadingEl.style.height = '100%';
      loadingEl.innerHTML = `
        <div class="spinner-border text-secondary mb-2" role="status">
          <span class="visually-hidden">${this.msg.loading}</span>
        </div>
        <small class="text-secondary">${this.msg.loading}</small>
      `;
      this.placeholder.parentElement.appendChild(loadingEl);
    } else if (loadingEl) {
      loadingEl.classList.remove('d-none');
    }
  }
  
  hideLoading() {
    this.isLoading = false;
    
    // Hide loading spinner
    if (this.placeholder && this.placeholder.parentElement) {
      const loadingEl = this.placeholder.parentElement.querySelector('.image-loading');
      if (loadingEl) {
        loadingEl.classList.add('d-none');
      }
    }
  }
  
  loadImage(url) {
    this.showLoading();
    
    // Convert to optimized Commons URL if it's a Commons image
    const optimizedUrl = this.isCommonsUrl(url) ? 
      this.getOptimizedCommonsUrl(url) : url;
    
    const img = new Image();
    
    img.onload = () => {
      this.hideLoading();
      this.preview.src = optimizedUrl;
      this.isValidImage = true;
      this.hasImage = true;
      
      // Hide placeholder, show image
      if (this.placeholder) {
        this.placeholder.classList.add('d-none');
      }
      this.preview.classList.remove('d-none');
      
      if (this.clearBtn) {
        this.clearBtn.classList.remove('d-none');
      }
    };
    
    img.onerror = () => {
      this.hideLoading();
      this.showError(this.msg.loadError);
      this.isValidImage = false;
      
      // Show placeholder again on error
      if (this.placeholder) {
        this.placeholder.classList.remove('d-none');
      }
    };
    
    img.src = optimizedUrl;
  }
  
  showError(message) {
    if (this.errorEl) {
      this.errorEl.textContent = message;
      this.errorEl.classList.remove('d-none');
      this.errorEl.classList.remove('alert-warning');
      this.errorEl.classList.add('alert-danger');
    }
    this.input.classList.add('is-invalid');
  }
  
  showWarning(message) {
    if (this.errorEl) {
      this.errorEl.textContent = message;
      this.errorEl.classList.remove('d-none');
      this.errorEl.classList.remove('alert-danger');
      this.errorEl.classList.add('alert-warning');
    }
    this.input.classList.remove('is-invalid');
  }
  
  hideError() {
    if (this.errorEl) {
      this.errorEl.classList.add('d-none');
      this.errorEl.classList.remove('alert-danger', 'alert-warning');
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
    this.preview.src = '';
    this.preview.classList.add('d-none');
    this.hideLoading();
    
    if (this.placeholder) {
      this.placeholder.classList.remove('d-none');
    }
    
    this.isValidImage = true;
    this.hasImage = false;
    this.hideError();
    
    if (this.clearBtn) {
      this.clearBtn.classList.add('d-none');
    }
  }
  
  getImageUrl() {
    // Return original URL entered by user
    return this.hasImage ? this.input.value.trim() : null;
  }
}

window.ImagePreview = ImagePreview;