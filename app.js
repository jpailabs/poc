/* ============================================
   BANK OF SINGAPORE — SOURCE OF WEALTH PORTAL
   Application Logic
   ============================================ */

// ── DATA ─────────────────────────────────────────────────────────────────────

const USERS = {
  demo: { password: 'gdo2024', name: 'Demo', role: 'Private Client', initials: 'D' }
};

const SALARIED_DOCS = [
  {
    id: 'income_tax',
    title: 'Income Tax Returns / NOA',
    subtitle: 'Last 2 years',
    required: true,
    description: 'Provide your most recent Notice of Assessment (NOA) or income tax returns for the last two consecutive years to demonstrate your declared income.',
    examples: ['Notice of Assessment (NOA)', 'Income Tax Return (ITR)', 'e-Filing Acknowledgement']
  },
  {
    id: 'payslips',
    title: 'Recent Payslips',
    subtitle: 'Last 3 months',
    required: true,
    description: 'Provide your three most recent monthly payslips from your current employer, showing your name, employer name, salary details and CPF contributions.',
    examples: ['Monthly payslip (Jan–Mar)', 'CPF contribution statement', 'Electronic payslip PDF']
  },
  {
    id: 'employment_letter',
    title: 'Employment Letter',
    subtitle: 'Confirming salary & position',
    required: true,
    description: 'An official letter from your employer on company letterhead confirming your designation, employment start date, and gross monthly salary.',
    examples: ['Offer letter with salary', 'Employment confirmation letter', 'HR letter on letterhead']
  },
  {
    id: 'bank_statements',
    title: 'Bank Statements',
    subtitle: 'Last 6 months',
    required: true,
    description: 'Recent 6-month bank statements showing regular salary credits from your employer. All accounts receiving salary must be included.',
    examples: ['DBS/POSB statement', 'OCBC statement', 'UOB statement', 'Overseas bank statement']
  },
  {
    id: 'cpf_statement',
    title: 'CPF Contribution History',
    subtitle: 'Last 12 months',
    required: false,
    description: 'CPF contribution history for the last 12 months confirming employer and employee contributions consistent with declared salary.',
    examples: ['CPF statement via my.cpf.gov.sg', 'CPF annual history printout']
  },
  {
    id: 'bonus_letter',
    title: 'Bonus / Variable Pay Documentation',
    subtitle: 'If applicable',
    required: false,
    description: 'Where sources of wealth include bonuses or variable compensation, provide supporting documentation confirming the amount and source.',
    examples: ['Bonus confirmation letter', 'RSU/ESOP vesting statement', 'Commission statement']
  },
  {
    id: 'identification',
    title: 'Identity Document',
    subtitle: 'Passport or NRIC',
    required: true,
    description: 'A clear copy of your valid passport (biographical page) or NRIC (both sides). Document must be valid and not expired.',
    examples: ['Passport (bio page)', 'Singapore NRIC (front & back)', 'Employment Pass']
  }
];

const BUSINESS_OWNER_DOCS = [
  {
    id: 'biz_reg',
    title: 'Business Registration / Incorporation Certificate',
    subtitle: 'Company registration documents',
    required: true,
    description: 'Official certificate of incorporation or business registration showing company name, registration number, date of incorporation, and registered address.',
    examples: ['ACRA BizFile printout', 'Certificate of Incorporation', 'Business Registration Certificate']
  },
  {
    id: 'ownership_structure',
    title: 'Ownership / Shareholding Structure',
    subtitle: 'Shareholding chart or register',
    required: true,
    description: 'Document showing the complete ownership structure of the business, including all shareholders with name and percentage held. For complex structures, provide group-level chart.',
    examples: ['Shareholder register', 'ACRA shareholders listing', 'Group structure chart']
  },
  {
    id: 'biz_financials',
    title: 'Audited Financial Statements',
    subtitle: 'Last 2 years',
    required: true,
    description: 'Signed audited or unaudited financial statements (balance sheet, P&L) for the last two financial years showing business revenue, profit and net assets.',
    examples: ['Audited accounts FY2022–2023', 'Unaudited management accounts', 'Financial summary letter from auditor']
  },
  {
    id: 'bank_statements_biz',
    title: 'Business Bank Statements',
    subtitle: 'Last 6 months — company account',
    required: true,
    description: 'Six months of the company\'s primary operating bank account statements showing business transactions and cashflow.',
    examples: ['DBS business account statement', 'Corporate current account statement']
  },
  {
    id: 'personal_bank_statements',
    title: 'Personal Bank Statements',
    subtitle: 'Last 6 months',
    required: true,
    description: 'Personal bank statements for the last six months showing directors\' fees, dividends, or salary received from the business entity.',
    examples: ['Personal DBS/OCBC statement', 'Foreign personal account statement']
  },
  {
    id: 'dividend_record',
    title: 'Dividend Records',
    subtitle: 'If income via dividends',
    required: false,
    description: 'Board resolutions or dividend vouchers confirming dividend declared and paid to you from the company, with amounts and dates.',
    examples: ['Board resolution on dividends', 'Dividend vouchers', 'CDP dividend statement']
  },
  {
    id: 'director_fee',
    title: 'Director Fee Evidence',
    subtitle: 'Director\'s remuneration proof',
    required: false,
    description: 'Documents confirming director\'s fees paid, such as board resolutions, service agreements, or IR8A forms.',
    examples: ['Director fee resolution', 'Service contract', 'IR8A from company']
  },
  {
    id: 'tax_returns_biz',
    title: 'Corporate Tax Returns / NOA',
    subtitle: 'Last 2 years',
    required: true,
    description: 'Company income tax filings or Notice of Assessment (NOA) for the last two years, confirming taxable income declared by the business.',
    examples: ['Form C / C-S filing', 'Corporate NOA from IRAS', 'Tax clearance certificate']
  },
  {
    id: 'biz_contracts',
    title: 'Material Business Contracts',
    subtitle: 'Key revenue contracts',
    required: false,
    description: 'Where business income derives from specific contracts or clients, provide redacted copies of key contracts demonstrating recurring revenue.',
    examples: ['Service agreements', 'Supply contracts', 'Retainer contracts']
  },
  {
    id: 'asset_documents',
    title: 'Asset Ownership Documents',
    subtitle: 'Property, investments, etc.',
    required: false,
    description: 'Documents evidencing significant personal or business assets that form part of your wealth, such as property title deeds, investment portfolio statements, or vehicle valuations.',
    examples: ['Property title deed', 'Investment portfolio statement', 'Asset valuation report']
  },
  {
    id: 'ubo_declaration',
    title: 'UBO Declaration Form',
    subtitle: 'Ultimate Beneficial Owner declaration',
    required: true,
    description: 'Completed and signed UBO declaration form identifying all ultimate beneficial owners holding 25% or more of the company, as required under MAS guidelines.',
    examples: ['Signed BOS UBO form', 'ACRA register of registrable controllers']
  },
  {
    id: 'identification_biz',
    title: 'Identity Document',
    subtitle: 'Passport or NRIC',
    required: true,
    description: 'Valid passport (biographical page) or NRIC (both sides) of the business owner / director. Document must be current and unexpired.',
    examples: ['Passport (bio page)', 'Singapore NRIC (front & back)', 'Employment Pass']
  }
];

// ── STATE ─────────────────────────────────────────────────────────────────────

const state = {
  currentUser: null,
  currentStep: 1,
  selectedProfile: null, // 'salaried' | 'business'
  uploadedFiles: {},     // docId -> File
  submissionRef: null
};

// ── ROUTER ────────────────────────────────────────────────────────────────────

function showPage(pageId) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  const page = document.getElementById(pageId);
  if (page) page.classList.add('active');
}

// ── AUTH ──────────────────────────────────────────────────────────────────────

function handleLogin(e) {
  e.preventDefault();
  const username = document.getElementById('username').value.trim();
  const password = document.getElementById('password').value;
  const errEl = document.getElementById('login-error');

  const user = USERS[username.toLowerCase()];
  if (!user || user.password !== password) {
    errEl.classList.add('visible');
    errEl.querySelector('span').textContent = 'Invalid credentials. Please check your Client ID and password.';
    document.getElementById('password').value = '';
    return;
  }
  errEl.classList.remove('visible');
  state.currentUser = { username, ...user };
  state.currentStep = 1;
  state.selectedProfile = null;
  state.uploadedFiles = {};
  showPortal();
}

function handleSignOut() {
  state.currentUser = null;
  state.selectedProfile = null;
  state.uploadedFiles = {};
  state.currentStep = 1;
  showPage('page-login');
  document.getElementById('login-form').reset();
}

// ── PORTAL LAYOUT ─────────────────────────────────────────────────────────────

function showPortal() {
  showPage('page-portal');
  // Set user info in header
  document.getElementById('header-user-name').textContent = state.currentUser.name;
  document.getElementById('header-user-role').textContent = state.currentUser.role;
  document.getElementById('header-user-initials').textContent = state.currentUser.initials;
  navigateToStep(1);
}

function updateStepNav(step) {
  document.querySelectorAll('.step-item').forEach((el, i) => {
    el.classList.remove('active', 'completed');
    const n = i + 1;
    if (n < step) el.classList.add('completed');
    else if (n === step) el.classList.add('active');
    // Update check icon for completed
    const numEl = el.querySelector('.step-num');
    if (n < step) {
      numEl.innerHTML = `<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" width="10" height="10"><polyline points="2,8 6,12 14,4"/></svg>`;
    } else {
      numEl.textContent = n;
    }
  });
}

function navigateToStep(step) {
  state.currentStep = step;
  updateStepNav(step);
  document.querySelectorAll('.portal-page').forEach(p => p.classList.remove('active'));
  if (step === 1) {
    document.getElementById('portal-step1').classList.add('active');
    renderStep1();
  } else if (step === 2) {
    document.getElementById('portal-step2').classList.add('active');
    renderStep2();
  } else if (step === 3) {
    document.getElementById('portal-step3').classList.add('active');
    renderStep3();
  }
  // Footer bar
  const backBtn = document.getElementById('footer-back-btn');
  const continueBtn = document.getElementById('footer-continue-btn');
  const footerInfo = document.getElementById('footer-step-info');
  if (step === 1) {
    backBtn.style.visibility = 'hidden';
  } else {
    backBtn.style.visibility = 'visible';
  }
  if (step === 3) {
    continueBtn.textContent = 'Submit Documents';
    continueBtn.innerHTML = 'Submit Documents <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>';
  } else {
    continueBtn.innerHTML = 'Continue to ' + (step === 1 ? 'Document Upload' : 'Generate Report') + ' <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"/></svg>';
  }
  footerInfo.textContent = `Step ${step} of 3`;
}

// ── STEP 1 ────────────────────────────────────────────────────────────────────

function renderStep1() {
  const cards = document.querySelectorAll('.profile-card');
  cards.forEach(c => {
    c.classList.toggle('selected', c.dataset.profile === state.selectedProfile);
  });
}

function handleProfileSelect(profile) {
  state.selectedProfile = profile;
  renderStep1();
}

// ── STEP 2 ────────────────────────────────────────────────────────────────────

function renderStep2() {
  const docs = state.selectedProfile === 'salaried' ? SALARIED_DOCS : BUSINESS_OWNER_DOCS;
  const container = document.getElementById('doc-list-container');
  container.innerHTML = '';

  docs.forEach((doc, idx) => {
    const isUploaded = !!state.uploadedFiles[doc.id];
    const item = document.createElement('div');
    item.className = `doc-item${isUploaded ? ' uploaded' : ''}`;
    item.id = `doc-item-${doc.id}`;

    item.innerHTML = `
      <button class="doc-item-header" onclick="toggleDocItem('${doc.id}')" aria-expanded="false" aria-controls="doc-body-${doc.id}">
        <div class="doc-item-header-top">
          <div class="doc-status-icon ${isUploaded ? 'uploaded' : 'empty'}">
            ${isUploaded ? `<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="2,8 6,12 14,4"/></svg>` : ''}
          </div>
          <div class="doc-item-required">
            <span class="${doc.required ? 'required-badge' : 'optional-badge'}">${doc.required ? 'Required' : 'Optional'}</span>
            <svg class="doc-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg>
          </div>
        </div>
        <div class="doc-item-info">
          <div class="doc-item-title">${doc.title}</div>
          <div class="doc-item-subtitle">${doc.subtitle}</div>
        </div>
      </button>
      <div class="doc-item-body" id="doc-body-${doc.id}">
        <p class="doc-description">${doc.description}</p>
        <div class="doc-examples">
          <div class="doc-examples-title">Accepted Documents</div>
          <div class="doc-examples-list">
            ${doc.examples.map(ex => `<span class="doc-example-tag">${ex}</span>`).join('')}
          </div>
        </div>
        <div class="doc-upload-area" onclick="triggerFileInput('${doc.id}')">
          <input type="file" id="file-input-${doc.id}" accept=".pdf,.jpg,.jpeg,.png" onchange="handleFileUpload('${doc.id}', this)" onclick="event.stopPropagation()"/>
          <div class="doc-upload-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" width="36" height="36"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
          </div>
          <div class="doc-upload-text">Drag & drop or <span class="doc-upload-link">browse file</span></div>
          <div class="doc-upload-subtext">PDF, JPG or PNG — max 10MB</div>
        </div>
        <div class="doc-file-preview ${isUploaded ? 'visible' : ''}" id="preview-${doc.id}">
          <div class="doc-file-name" id="filename-${doc.id}">${isUploaded ? state.uploadedFiles[doc.id].name : ''}</div>
          <button class="doc-file-remove" onclick="removeFile('${doc.id}')" title="Remove file">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="16" height="16"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          </button>
        </div>
      </div>
    `;
    container.appendChild(item);
  });

  updateSidebar();
}

function toggleDocItem(docId) {
  const item = document.getElementById(`doc-item-${docId}`);
  const header = item.querySelector('.doc-item-header');
  const isExpanded = item.classList.toggle('expanded');
  header.setAttribute('aria-expanded', isExpanded);
}

function triggerFileInput(docId) {
  document.getElementById(`file-input-${docId}`).click();
}

function handleFileUpload(docId, input) {
  if (!input.files || !input.files[0]) return;
  const file = input.files[0];
  state.uploadedFiles[docId] = file;

  const item = document.getElementById(`doc-item-${docId}`);
  item.classList.add('uploaded');
  const statusIcon = item.querySelector('.doc-status-icon');
  statusIcon.className = 'doc-status-icon uploaded';
  statusIcon.innerHTML = `<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="2,8 6,12 14,4"/></svg>`;

  document.getElementById(`filename-${docId}`).textContent = file.name;
  document.getElementById(`preview-${docId}`).classList.add('visible');

  showToast(`✓ ${file.name} uploaded`);
  updateSidebar();
}

function removeFile(docId) {
  delete state.uploadedFiles[docId];
  const item = document.getElementById(`doc-item-${docId}`);
  item.classList.remove('uploaded');
  const statusIcon = item.querySelector('.doc-status-icon');
  statusIcon.className = 'doc-status-icon empty';
  statusIcon.innerHTML = '';
  document.getElementById(`preview-${docId}`).classList.remove('visible');
  document.getElementById(`file-input-${docId}`).value = '';
  updateSidebar();
}

function updateSidebar() {
  const docs = state.selectedProfile === 'salaried' ? SALARIED_DOCS : BUSINESS_OWNER_DOCS;
  const total = docs.length;
  const done = Object.keys(state.uploadedFiles).filter(id => docs.find(d => d.id === id)).length;

  document.getElementById('progress-done').textContent = done;
  document.getElementById('progress-total').textContent = total;
  const pct = total > 0 ? Math.round((done / total) * 100) : 0;
  document.getElementById('progress-fill').style.width = pct + '%';

  const listEl = document.getElementById('sidebar-doc-list');
  listEl.innerHTML = docs.map(doc => {
    const isDone = !!state.uploadedFiles[doc.id];
    return `<li class="sidebar-doc-item">
      <div class="sidebar-doc-status ${isDone ? 'done' : 'pending'}">
        ${isDone ? `<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="2,8 6,12 14,4"/></svg>` : ''}
      </div>
      <span style="${isDone ? 'text-decoration:line-through;color:var(--color-text-muted)' : ''}">${doc.title}</span>
    </li>`;
  }).join('');
}

// ── STEP 3 ────────────────────────────────────────────────────────────────────

function renderStep3() {
  const docs = state.selectedProfile === 'salaried' ? SALARIED_DOCS : BUSINESS_OWNER_DOCS;
  const uploadedDocs = docs.filter(d => state.uploadedFiles[d.id]);
  const total = docs.length;
  const done = uploadedDocs.length;
  const profileLabel = state.selectedProfile === 'salaried' ? 'Salaried Professional' : 'Business Owner';

  document.getElementById('review-profile-type').textContent = profileLabel;
  document.getElementById('review-doc-count').textContent = `${done} of ${total}`;
  document.getElementById('review-client-name').textContent = state.currentUser.name;
  document.getElementById('review-submission-date').textContent = new Date().toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' });

  document.getElementById('summary-total').textContent = done;
  document.getElementById('summary-required').textContent = docs.filter(d => d.required && state.uploadedFiles[d.id]).length;
  document.getElementById('summary-optional').textContent = docs.filter(d => !d.required && state.uploadedFiles[d.id]).length;

  const docListEl = document.getElementById('review-doc-items');
  if (uploadedDocs.length === 0) {
    docListEl.innerHTML = `<p style="color:var(--color-text-muted);font-size:13px;padding:12px 0;">No documents uploaded yet.</p>`;
  } else {
    docListEl.innerHTML = uploadedDocs.map(doc => {
      const file = state.uploadedFiles[doc.id];
      return `<div class="review-doc-item">
        <div class="review-doc-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="16" height="16" color="var(--color-green)"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
        </div>
        <div class="review-doc-name">${doc.title}</div>
        <div class="review-doc-file">${file.name}</div>
        <div class="review-status-badge">
          <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" width="10" height="10"><polyline points="2,8 6,12 14,4"/></svg>
          Uploaded
        </div>
      </div>`;
    }).join('');
  }
}

// ── SUBMISSION ────────────────────────────────────────────────────────────────

async function handleSubmit() {
  const declared = document.getElementById('declaration-checkbox').checked;
  if (!declared) {
    showToast('⚠ Please confirm the declaration before submitting.');
    return;
  }
  const overlay = document.getElementById('loading-overlay');
  overlay.classList.add('visible');

  try {
    const docs = state.selectedProfile === 'salaried' ? SALARIED_DOCS : BUSINESS_OWNER_DOCS;
    const uploadedDocs = docs.filter(d => state.uploadedFiles[d.id]);
    
    let sessionId = null;
    
    for (const doc of uploadedDocs) {
      const file = state.uploadedFiles[doc.id];
      const formData = new FormData();
      formData.append('doc_types', doc.id);
      if (sessionId) formData.append('session_id', sessionId);
      formData.append('file', file);
      
      const response = await fetch('http://localhost:8000/sessions/extract', {
        method: 'POST',
        body: formData
      });
      
      if (!response.ok) {
        throw new Error(`Failed to upload ${doc.title}`);
      }
      
      const data = await response.json();
      if (!sessionId && data && data.length > 0) {
        sessionId = data[0].session_id;
      }
    }
    
    overlay.classList.remove('visible');
    
    if (sessionId) {
      state.submissionRef = 'BOS-' + sessionId.substring(0, 8).toUpperCase();
    } else {
      state.submissionRef = 'BOS-' + Date.now().toString().slice(-8).toUpperCase();
    }
    
    document.getElementById('success-ref-num').textContent = state.submissionRef;
    document.querySelectorAll('.portal-page').forEach(p => p.classList.remove('active'));
    document.getElementById('portal-success').classList.add('active');
    document.getElementById('portal-footer-bar').style.display = 'none';
    updateStepNav(4); // all done
    
  } catch (error) {
    console.error('Submission error:', error);
    overlay.classList.remove('visible');
    showToast('⚠ An error occurred during submission. Please try again.');
  }
}

// ── NAVIGATION HANDLERS ───────────────────────────────────────────────────────

function handleContinue() {
  if (state.currentStep === 1) {
    if (!state.selectedProfile) {
      showToast('⚠ Please select a client profile to continue.');
      return;
    }
    navigateToStep(2);
  } else if (state.currentStep === 2) {
    const docs = state.selectedProfile === 'salaried' ? SALARIED_DOCS : BUSINESS_OWNER_DOCS;
    const missingRequired = docs.filter(d => d.required && !state.uploadedFiles[d.id]);
    if (missingRequired.length > 0) {
      showToast(`⚠ ${missingRequired.length} required document(s) missing.`);
      return;
    }
    navigateToStep(3);
  } else if (state.currentStep === 3) {
    handleSubmit();
  }
}

function handleBack() {
  if (state.currentStep > 1) navigateToStep(state.currentStep - 1);
}

// ── TOAST ─────────────────────────────────────────────────────────────────────

function showToast(msg) {
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.textContent = msg;
  container.appendChild(toast);
  setTimeout(() => { toast.remove(); }, 3500);
}

// ── INIT ──────────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
  // Pages
  showPage('page-login');

  // Login form
  document.getElementById('login-form').addEventListener('submit', handleLogin);
  document.getElementById('signout-btn').addEventListener('click', handleSignOut);
  document.getElementById('success-signout-btn').addEventListener('click', handleSignOut);

  // Profile cards
  document.querySelectorAll('.profile-card').forEach(card => {
    card.addEventListener('click', () => handleProfileSelect(card.dataset.profile));
  });

  // Nav buttons
  document.getElementById('footer-continue-btn').addEventListener('click', handleContinue);
  document.getElementById('footer-back-btn').addEventListener('click', handleBack);
  document.getElementById('review-edit-btn').addEventListener('click', () => navigateToStep(2));
});
