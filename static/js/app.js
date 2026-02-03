/* Agno Research - Frontend JavaScript */

// Theme toggle
function initTheme() {
  const toggle = document.getElementById('theme-toggle');
  const html = document.documentElement;

  // Check for saved preference or system preference
  const savedTheme = localStorage.getItem('theme');
  const systemDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

  if (savedTheme) {
    html.setAttribute('data-theme', savedTheme);
  } else if (systemDark) {
    html.setAttribute('data-theme', 'dark');
  }

  if (toggle) {
    toggle.addEventListener('click', () => {
      const current = html.getAttribute('data-theme');
      const next = current === 'dark' ? 'light' : 'dark';
      html.setAttribute('data-theme', next);
      localStorage.setItem('theme', next);
    });
  }

  // Listen for system theme changes
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
    if (!localStorage.getItem('theme')) {
      html.setAttribute('data-theme', e.matches ? 'dark' : 'light');
    }
  });
}

// Copy to clipboard utility
function copyToClipboard(text, button) {
  navigator.clipboard.writeText(text).then(() => {
    const originalText = button.innerHTML;
    button.innerHTML = `
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="20 6 9 17 4 12"></polyline>
      </svg>
      Copied!
    `;
    button.classList.add('btn-success');

    setTimeout(() => {
      button.innerHTML = originalText;
      button.classList.remove('btn-success');
    }, 2000);
  });
}

// Research form submission with loading state
function initResearchForm() {
  const form = document.getElementById('research-form');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const submitBtn = form.querySelector('button[type="submit"]');
    const resultsContainer = document.getElementById('results-container');
    const loadingContainer = document.getElementById('loading-container');

    // Show loading state
    submitBtn.disabled = true;
    submitBtn.innerHTML = `
      <div class="spinner"></div>
      Researching...
    `;

    if (loadingContainer) {
      loadingContainer.style.display = 'block';
      resultsContainer.style.display = 'none';
    }

    // Update loading stages
    const stages = [
      'Scraping website...',
      'Analyzing content...',
      'Identifying AI opportunities...',
      'Generating outreach drafts...'
    ];

    let stageIndex = 0;
    const stageText = document.getElementById('loading-stage');
    const stageInterval = setInterval(() => {
      if (stageIndex < stages.length && stageText) {
        stageText.textContent = stages[stageIndex];
        stageIndex++;
      }
    }, 3000);

    try {
      const formData = new FormData(form);
      const data = {
        website_url: formData.get('website_url'),
        instagram_url: formData.get('instagram_url') || null,
        facebook_url: formData.get('facebook_url') || null
      };

      const response = await fetch('/api/research', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
      });

      const result = await response.json();

      clearInterval(stageInterval);

      if (response.ok) {
        displayResults(result);
      } else {
        showError(result.error || 'Research failed');
      }
    } catch (error) {
      clearInterval(stageInterval);
      showError(error.message);
    } finally {
      submitBtn.disabled = false;
      submitBtn.innerHTML = `
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="11" cy="11" r="8"></circle>
          <path d="m21 21-4.3-4.3"></path>
        </svg>
        Start Research
      `;

      if (loadingContainer) {
        loadingContainer.style.display = 'none';
      }
    }
  });
}

// Display research results
function displayResults(result) {
  const container = document.getElementById('results-container');
  if (!container) return;

  container.style.display = 'block';

  // Build HTML for results
  let html = `
    <div class="card">
      <div class="card-header">
        <h2 class="card-title">${result.company_name || 'Company'}</h2>
        <span class="badge badge-primary">${result.industry || 'Unknown Industry'}</span>
      </div>

      <div class="result-section">
        <h3 class="result-section-title">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
            <polyline points="14 2 14 8 20 8"></polyline>
            <line x1="16" y1="13" x2="8" y2="13"></line>
            <line x1="16" y1="17" x2="8" y2="17"></line>
            <polyline points="10 9 9 9 8 9"></polyline>
          </svg>
          Overview
        </h3>
        <p>${result.overview || 'No overview available'}</p>
      </div>
  `;

  // AI Opportunities
  if (result.ai_opportunities && result.ai_opportunities.length > 0) {
    html += `
      <div class="result-section">
        <h3 class="result-section-title">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 2v4m0 12v4M4.93 4.93l2.83 2.83m8.48 8.48l2.83 2.83M2 12h4m12 0h4M4.93 19.07l2.83-2.83m8.48-8.48l2.83-2.83"></path>
          </svg>
          AI Opportunities
        </h3>
    `;

    result.ai_opportunities.forEach(opp => {
      const complexityClass = opp.complexity?.toLowerCase() || 'medium';
      html += `
        <div class="opportunity-card">
          <div class="opportunity-header">
            <span class="opportunity-title">${opp.area}: ${opp.opportunity}</span>
            <span class="complexity-badge complexity-${complexityClass}">${opp.complexity || 'Medium'}</span>
          </div>
          <p style="color: var(--color-text-muted); margin: 0;">${opp.rationale}</p>
        </div>
      `;
    });

    html += '</div>';
  }

  // Outreach Drafts
  if (result.outreach_drafts) {
    const { whatsapp, email } = result.outreach_drafts;

    if ((whatsapp && whatsapp.length > 0) || (email && email.length > 0)) {
      html += `
        <div class="result-section">
          <h3 class="result-section-title">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
            </svg>
            Outreach Drafts
          </h3>
      `;

      // WhatsApp drafts
      if (whatsapp && whatsapp.length > 0) {
        whatsapp.forEach((draft, i) => {
          html += `
            <div class="draft-card">
              <div class="draft-type draft-type-whatsapp">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
                </svg>
                WhatsApp Draft ${i + 1}
              </div>
              <div class="draft-content">${draft.body}</div>
              <p style="font-size: 0.875rem; color: var(--color-text-muted); margin-top: var(--space-sm);">
                Personalized using: ${draft.personalization}
              </p>
              <div class="draft-actions">
                <button class="btn btn-sm btn-secondary" onclick="copyToClipboard(\`${draft.body.replace(/`/g, '\\`')}\`, this)">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                    <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                  </svg>
                  Copy
                </button>
              </div>
            </div>
          `;
        });
      }

      // Email drafts
      if (email && email.length > 0) {
        email.forEach((draft, i) => {
          html += `
            <div class="draft-card">
              <div class="draft-type draft-type-email">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path>
                  <polyline points="22,6 12,13 2,6"></polyline>
                </svg>
                Email Draft ${i + 1}
              </div>
              <p style="font-weight: 600; margin-bottom: var(--space-sm);">Subject: ${draft.subject || 'AI Solutions for Your Business'}</p>
              <div class="draft-content">${draft.body}</div>
              <p style="font-size: 0.875rem; color: var(--color-text-muted); margin-top: var(--space-sm);">
                Personalized using: ${draft.personalization}
              </p>
              <div class="draft-actions">
                <button class="btn btn-sm btn-secondary" onclick="copyToClipboard(\`${draft.body.replace(/`/g, '\\`')}\`, this)">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                    <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                  </svg>
                  Copy
                </button>
              </div>
            </div>
          `;
        });
      }

      html += '</div>';
    }
  }

  // Sources
  if (result.sources && result.sources.length > 0) {
    html += `
      <div class="result-section">
        <h3 class="result-section-title">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path>
            <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path>
          </svg>
          Sources
        </h3>
        <ul style="margin: 0; padding-left: var(--space-lg);">
    `;

    result.sources.forEach(source => {
      html += `<li><a href="${source}" target="_blank" style="color: var(--color-primary);">${source}</a></li>`;
    });

    html += '</ul></div>';
  }

  html += '</div>';

  container.innerHTML = html;

  // Scroll to results
  container.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// Show error message
function showError(message) {
  const container = document.getElementById('results-container');
  if (!container) return;

  container.style.display = 'block';
  container.innerHTML = `
    <div class="alert alert-error">
      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="10"></circle>
        <line x1="12" y1="8" x2="12" y2="12"></line>
        <line x1="12" y1="16" x2="12.01" y2="16"></line>
      </svg>
      <div>
        <strong>Research Failed</strong>
        <p style="margin: var(--space-xs) 0 0;">${message}</p>
      </div>
    </div>
  `;
}

// File upload handling
function initFileUpload() {
  const dropzone = document.getElementById('file-dropzone');
  const fileInput = document.getElementById('file-input');

  if (!dropzone || !fileInput) return;

  // Click to upload
  dropzone.addEventListener('click', () => fileInput.click());

  // Drag and drop
  dropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropzone.classList.add('dragover');
  });

  dropzone.addEventListener('dragleave', () => {
    dropzone.classList.remove('dragover');
  });

  dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropzone.classList.remove('dragover');

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      fileInput.files = files;
      fileInput.form.submit();
    }
  });

  // File input change
  fileInput.addEventListener('change', () => {
    if (fileInput.files.length > 0) {
      fileInput.form.submit();
    }
  });
}

// Mobile sidebar toggle
function initMobileSidebar() {
  const menuBtn = document.getElementById('mobile-menu-btn');
  const sidebar = document.querySelector('.sidebar');

  if (!menuBtn || !sidebar) return;

  menuBtn.addEventListener('click', () => {
    sidebar.classList.toggle('open');
  });

  // Close sidebar when clicking outside
  document.addEventListener('click', (e) => {
    if (!sidebar.contains(e.target) && !menuBtn.contains(e.target)) {
      sidebar.classList.remove('open');
    }
  });
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  initResearchForm();
  initFileUpload();
  initMobileSidebar();
});
