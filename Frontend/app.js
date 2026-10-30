// State variables
let practicals = [];
let statuses = {};
let currentFilter = 'all';
let searchQuery = '';
let autoRefreshTimer = null;

// DOM Elements
const container = document.getElementById('practicalsContainer');
const searchInput = document.getElementById('searchInput');
const clearSearchBtn = document.getElementById('clearSearch');
const filterPills = document.querySelectorAll('.filter-pill');
const refreshBtn = document.getElementById('refreshBtn');
const guideBtn = document.getElementById('guideBtn');
const activeServicesCount = document.getElementById('activeServicesCount');

// Modal Elements
const viewerModal = document.getElementById('viewerModal');
const viewerFrame = document.getElementById('viewerFrame');
const modalBadge = document.getElementById('modalBadge');
const modalTitle = document.getElementById('modalTitle');
const modalUrlText = document.getElementById('modalUrlText');
const modalReloadBtn = document.getElementById('modalReloadBtn');
const modalExternalLink = document.getElementById('modalExternalLink');
const modalCloseBtn = document.getElementById('modalCloseBtn');

// Drawer Elements
const guideDrawer = document.getElementById('guideDrawer');
const closeDrawerBtn = document.getElementById('closeDrawerBtn');

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
  setupEventListeners();
  await loadPracticals();
  await refreshStatus();
  startAutoRefresh();
});

// Setup event listeners
function setupEventListeners() {
  // Search input
  searchInput.addEventListener('input', (e) => {
    searchQuery = e.target.value.toLowerCase().trim();
    clearSearchBtn.style.display = searchQuery ? 'block' : 'none';
    renderCards();
  });

  clearSearchBtn.addEventListener('click', () => {
    searchInput.value = '';
    searchQuery = '';
    clearSearchBtn.style.display = 'none';
    renderCards();
  });

  // Filter pills
  filterPills.forEach(pill => {
    pill.addEventListener('click', () => {
      filterPills.forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      currentFilter = pill.getAttribute('data-filter');
      renderCards();
    });
  });

  // Refresh button
  refreshBtn.addEventListener('click', async () => {
    refreshBtn.classList.add('is-refreshing');
    await refreshStatus();
    setTimeout(() => refreshBtn.classList.remove('is-refreshing'), 600);
    showToast('Status indicators updated');
  });

  // Guide button
  guideBtn.addEventListener('click', () => {
    guideDrawer.style.display = 'flex';
  });

  closeDrawerBtn.addEventListener('click', () => {
    guideDrawer.style.display = 'none';
  });

  guideDrawer.addEventListener('click', (e) => {
    if (e.target === guideDrawer) guideDrawer.style.display = 'none';
  });

  // Modal controls
  modalCloseBtn.addEventListener('click', closeModal);
  modalReloadBtn.addEventListener('click', () => {
    const src = viewerFrame.src;
    viewerFrame.src = '';
    viewerFrame.src = src;
  });

  viewerModal.addEventListener('click', (e) => {
    if (e.target === viewerModal) closeModal();
  });

  // Keyboard shortcut: Escape to close modals
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeModal();
      guideDrawer.style.display = 'none';
    }
  });
}

// Load practical definitions from the bundled JSON file (works on Netlify).
async function loadPracticals() {
  try {
    const res = await fetch('./practicals.json');
    if (!res.ok) throw new Error('Could not load practicals.json');
    practicals = await res.json();
    renderCards();
  } catch (error) {
    console.error('Error loading practicals:', error);
    container.innerHTML = '<div class="empty-state"><p>Could not load the practicals list. Please refresh the page.</p></div>';
  }
}

// Practicals deployment and live status indicators
async function refreshStatus() {
  statuses = {};
  for (const p of practicals) {
    statuses[p.id] = {
      status: p.id === 'pr4' ? 'Render Backend' : 'Deployed',
      badgeClass: 'badge-preview',
      details: p.id === 'pr4'
        ? 'Connected to Render Flask backend & MySQL database.'
        : 'Static files are included in this Netlify deployment.',
      isLive: true
    };
  }

  // Attempt live health ping to Render Flask backend
  const backendUrl = (window.API_BASE_URL || "https://auth-flask-api.onrender.com").replace(/\/+$/, "");
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 3500);
    const res = await fetch(`${backendUrl}/api/health`, { signal: controller.signal, mode: 'cors' });
    clearTimeout(timeoutId);
    if (res.ok) {
      statuses['pr4'] = {
        status: 'Online',
        badgeClass: 'badge-ready',
        details: 'Render Flask backend & MySQL are live and healthy.',
        isLive: true
      };
    }
  } catch (err) {
    // Render free tier may be cold-starting or offline; status stays 'Render Backend'
  }

  updateLiveMetrics();
  renderCards();
}


function startAutoRefresh() {
  // No server health-check API is available on a static Netlify deployment.
}

// Update top metric indicators
function updateLiveMetrics() {
  let readyCount = 0;
  for (const key in statuses) {
    if (statuses[key].status.startsWith('Ready')) {
      readyCount++;
    }
  }
  activeServicesCount.textContent = `${practicals.length || 6} Included`;
}

// Render cards based on filters and search query
function renderCards() {
  if (!practicals || practicals.length === 0) return;

  const filtered = practicals.filter(p => {
    // Category filter
    if (currentFilter !== 'all' && p.type !== currentFilter) {
      return false;
    }

    // Search query filter
    if (searchQuery) {
      const matchTitle = p.title.toLowerCase().includes(searchQuery);
      const matchSubtitle = p.subtitle.toLowerCase().includes(searchQuery);
      const matchDesc = p.description.toLowerCase().includes(searchQuery);
      const matchTech = p.tech.some(t => t.toLowerCase().includes(searchQuery));
      const matchFolder = p.folder.toLowerCase().includes(searchQuery);
      return matchTitle || matchSubtitle || matchDesc || matchTech || matchFolder;
    }

    return true;
  });

  if (filtered.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <p>No practicals match your search "${escapeHtml(searchQuery)}".</p>
        <button class="btn btn-secondary btn-sm" onclick="clearFilters()" style="margin-top:12px;">Reset Filters</button>
      </div>
    `;
    return;
  }

  container.innerHTML = filtered.map(p => createCardHtml(p)).join('');

  // Attach card event listeners
  attachCardEvents();
}

function clearFilters() {
  searchInput.value = '';
  searchQuery = '';
  currentFilter = 'all';
  filterPills.forEach(p => p.classList.remove('active'));
  filterPills[0].classList.add('active');
  renderCards();
}

// Create Card HTML
function createCardHtml(p) {
  const currentStatus = statuses[p.id] || {
    status: 'Deployed',
    badgeClass: 'badge-preview',
    details: 'Static files included in deployment'
  };

  const statusBadge = `
    <span class="status-badge ${currentStatus.badgeClass}">
      <span class="status-dot"></span>
      <span>${currentStatus.status}</span>
    </span>
  `;

  const techBadges = p.tech.map(t => `<span class="tech-tag">${escapeHtml(t)}</span>`).join('');

  // Target URL logic
  let openUrl = p.externalUrl;
  let isExternalService = p.type === 'fullstack' || p.type === 'vite';

  return `
    <article class="practical-card" data-id="${p.id}">
      <div class="card-top">
        <div class="badge-group">
          <span class="pr-number-badge">${p.number}</span>
          <span class="type-pill ${p.type}">${p.type === 'static' ? 'Static Web' : p.type === 'fullstack' ? 'Flask + DB' : 'React Vite'}</span>
        </div>
        ${statusBadge}
      </div>

      <div class="card-title-group">
        <h2 class="card-title">${escapeHtml(p.title)}</h2>
        <div class="card-subtitle">${escapeHtml(p.subtitle)}</div>
      </div>

      <p class="card-description">${escapeHtml(p.description)}</p>

      <div class="card-tech-list">
        ${techBadges}
      </div>

      <div class="card-meta-box">
        <div class="meta-row">
          <span class="meta-label">Location</span>
          <span class="meta-value">${escapeHtml(p.folder)}</span>
        </div>
        <div class="meta-row">
          <span class="meta-label">Port / Target</span>
          <span class="meta-value">${escapeHtml(p.port)}</span>
        </div>
        <div class="meta-status-text">
          ${escapeHtml(currentStatus.details)}
        </div>
      </div>

      <div class="card-actions">
        <div class="primary-actions">
          <a href="${openUrl}" target="_blank" rel="noopener noreferrer" class="btn btn-primary open-practical-btn" data-id="${p.id}" id="openBtn-${p.id}">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
              <polyline points="15 3 21 3 21 9"></polyline>
              <line x1="10" y1="14" x2="21" y2="3"></line>
            </svg>
            <span>Open Practical</span>
          </a>

          <button class="btn btn-secondary preview-btn" data-id="${p.id}" id="previewBtn-${p.id}">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect>
              <line x1="8" y1="21" x2="16" y2="21"></line>
              <line x1="12" y1="17" x2="12" y2="21"></line>
            </svg>
            <span>Preview</span>
          </button>
        </div>
      </div>
    </article>
  `;
}

// Attach event handlers to card buttons
function attachCardEvents() {
  // Preview in modal buttons
  document.querySelectorAll('.preview-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const id = btn.getAttribute('data-id');
      const practical = practicals.find(p => p.id === id);
      if (practical) openModal(practical);
    });
  });


  // Copy command buttons
  document.querySelectorAll('.copy-cmd-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const cmd = btn.getAttribute('data-cmd');
      navigator.clipboard.writeText(cmd).then(() => {
        showToast(`Copied: ${cmd}`);
      }).catch(() => {
        showToast(`Command: ${cmd}`);
      });
    });
  });
}

// Open embedded modal viewer
function openModal(p) {
  let url = p.entryPath;
  const currentStatus = statuses[p.id];

  // If Pr6 dev server is offline but preview build exists, use preview
  if (p.id === 'pr6' && (!currentStatus || !currentStatus.isLive) && p.previewUrl) {
    url = p.previewUrl;
  }

  modalBadge.textContent = p.number;
  modalTitle.textContent = p.title;
  modalUrlText.textContent = url;
  modalExternalLink.href = url;
  viewerFrame.src = url;
  viewerModal.style.display = 'flex';
}

// Close modal viewer
function closeModal() {
  viewerModal.style.display = 'none';
  viewerFrame.src = '';
}

// Toast notification helper
function showToast(message) {
  const existing = document.querySelector('.toast');
  if (existing) existing.remove();

  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.textContent = message;
  document.body.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transition = 'opacity 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 2800);
}

// HTML escape helper
function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
