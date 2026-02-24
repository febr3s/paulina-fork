/**
 * ReferenceManager - Manage references for form fields
 */

class ReferenceManager {
  constructor(config = {}) {
    this.maxReferences = config.maxReferences || 3;
    this.referenceCounters = {}; // Track next index for each field

    // Translatable messages with English fallbacks
    this.msg = Object.assign(
      {
        reference: "Reference",
        url: "Reference URL",
        retrieved: "Date accessed",
        maxReached: "Maximum 3 references per field",
        remove: "Remove",
      },
      config.messages || {},
    );
  }

  toggleReference(fieldId) {
    const section = document.getElementById(`${fieldId}-references`);
    if (!section) return;

    // Show the section if hidden
    if (section.classList.contains("d-none")) {
      section.classList.remove("d-none");
    }

    // Add a reference
    this.addReference(fieldId);
  }

  addReference(fieldId) {
    const container = document.getElementById(`${fieldId}-reference-container`);
    if (!container) return;

    // Count existing references in the DOM
    const existingRefs = container.querySelectorAll(".reference-item");
    if (existingRefs.length >= this.maxReferences) {
      alert(this.msg.maxReached);
      return;
    }

    // Initialize counter for this field if it doesn't exist
    if (!this.referenceCounters[fieldId]) {
      this.referenceCounters[fieldId] = 0;
    }

    const refIndex = this.referenceCounters[fieldId];
    const refId = `${fieldId}-ref-${refIndex}`;

    // Increment counter for next reference
    this.referenceCounters[fieldId]++;

    const refDiv = document.createElement("div");
    refDiv.className = "reference-item mb-3 p-2 border rounded bg-light";
    refDiv.id = refId;
    refDiv.dataset.refIndex = refIndex;

    refDiv.innerHTML = `
  <div class="d-flex justify-content-between align-items-center mb-2">
    <strong>${this.msg.reference} ${existingRefs.length + 1}</strong>
    <button type="button" class="btn btn-sm btn-outline-danger remove-ref-btn" aria-label="${this.msg.remove}">
      <i class="bi bi-trash"></i>
    </button>
  </div>
  <div class="mb-2">
    <label class="form-label small" for="${fieldId}-ref-url-${refIndex}">${this.msg.url}</label>
    <input type="url" class="form-control form-control-sm ref-url"
      id="${fieldId}-ref-url-${refIndex}"
      name="${fieldId}_ref_url_${refIndex}"
      aria-label="${this.msg.url}"
      placeholder="https://">
  </div>
  <div>
    <label class="form-label small" for="${fieldId}-ref-retrieved-${refIndex}">${this.msg.retrieved}</label>
    <input type="date" class="form-control form-control-sm ref-retrieved"
      id="${fieldId}-ref-retrieved-${refIndex}"
      name="${fieldId}_ref_retrieved_${refIndex}"
      aria-label="${this.msg.retrieved}"
      value="${this.getTodayDate()}">
  </div>
`;

    // Remove button handler
    refDiv.querySelector(".remove-ref-btn").addEventListener("click", () => {
      this.removeReference(fieldId, refId);
    });

    container.appendChild(refDiv);

    // Update reference numbers for all references
    this.updateReferenceNumbers(fieldId);
  }

  removeReference(fieldId, refId) {
    const refDiv = document.getElementById(refId);
    if (refDiv) {
      refDiv.remove();
    }

    // Update reference numbers after removal
    this.updateReferenceNumbers(fieldId);
  }

  updateReferenceNumbers(fieldId) {
    const container = document.getElementById(`${fieldId}-reference-container`);
    if (!container) return;

    const references = container.querySelectorAll(".reference-item");
    references.forEach((ref, index) => {
      ref.dataset.refIndex = index;
      const label = ref.querySelector("strong");
      if (label) {
        label.textContent = `${this.msg.reference} ${index + 1}`;
      }
      const refUrl = ref.querySelector(".ref-url");
      if (refUrl) {
        refUrl.name = `${fieldId}_ref_url_${index}`;
      }
      const refRetrieved = ref.querySelector(".ref-retrieved");
      if (refRetrieved) {
        refRetrieved.name = `${fieldId}_ref_retrieved_${index}`;
      }
    });
  }

  getTodayDate() {
    return new Date().toISOString().split("T")[0];
  }

  reset() {
    // Clear all reference containers
    const containers = document.querySelectorAll(
      '[id$="-reference-container"]',
    );
    containers.forEach((container) => {
      container.innerHTML = "";
    });

    const sections = document.querySelectorAll('[id$="-references"]');
    sections.forEach((section) => {
      section.classList.add("d-none");
    });

    // Reset counters
    this.referenceCounters = {};
  }

  getReferences(fieldId) {
    const container = document.getElementById(`${fieldId}-reference-container`);
    if (!container) return [];

    return Array.from(container.querySelectorAll(".reference-item")).map(
      (ref) => ref.id,
    );
  }

  getAllReferences() {
    const allRefs = {};
    const containers = document.querySelectorAll(
      '[id$="-reference-container"]',
    );

    containers.forEach((container) => {
      const fieldId = container.id.replace("-reference-container", "");
      allRefs[fieldId] = this.getReferences(fieldId);
    });

    return allRefs;
  }
}

window.ReferenceManager = ReferenceManager;
