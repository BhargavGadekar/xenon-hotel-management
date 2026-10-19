/**
 * XENON PALACE & RESIDENCES
 * Luxury Hotel & Lodge POS — Controller Script
 * Aesthetic: The Leela Palace & Lemon and Olive Quiet Luxury
 */

// Global State
let state = {
  attendant: null,
  rooms: [],
  catalog: [],
  history: [],
  overview: null,
  currentView: 'suites',
  suiteFilter: 'all',
  catalogCategory: 'all',
  selectedSuiteId: null,
  ticketItems: [], // Cart for the Hotel Guest Check: [{ item, qty }]
};

// Currency & Date Formatting
function formatCurrency(amount) {
  const num = Number(amount) || 0;
  return '₹' + num.toLocaleString('en-IN');
}

function formatDateTime(timestamp) {
  if (!timestamp) return '—';
  const d = new Date(Number(timestamp));
  return d.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function formatDateOnly(timestamp) {
  if (!timestamp) return '—';
  const d = new Date(Number(timestamp));
  return d.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

// Toast Notifications
function showToast(message, type = 'normal') {
  const container = document.getElementById('toast-container');
  if (!container) return;
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <span>${message}</span>
    <button style="background:none; border:none; color:inherit; margin-left:14px; cursor:pointer;" onclick="this.parentElement.remove()">✕</button>
  `;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// API Helper
async function api(endpoint, options = {}) {
  try {
    const res = await fetch(endpoint, {
      headers: {
        'Content-Type': 'application/json',
        ...(options.headers || {}),
      },
      ...options,
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || data.message || 'API request failed');
    }
    return data;
  } catch (err) {
    console.error(`API Error on ${endpoint}:`, err);
    throw err;
  }
}

// ==========================================================================
// 1. AUTHENTICATION & DEMO LOGIN
// ==========================================================================

function initAuth() {
  const savedUser = sessionStorage.getItem('xenon_attendant');
  if (savedUser) {
    enterPosApp(savedUser);
  } else {
    showLoginScreen();
  }

  const loginForm = document.getElementById('login-form');
  if (loginForm) {
    loginForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const name = document.getElementById('login-name').value.trim() || 'Concierge Attendant';
      enterPosApp(name);
    });
  }

  const quickDemoBtn = document.getElementById('btn-quick-demo');
  if (quickDemoBtn) {
    quickDemoBtn.addEventListener('click', () => {
      enterPosApp('Vikramaditya Rao');
    });
  }

  const logoutBtn = document.getElementById('btn-logout');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', () => {
      sessionStorage.removeItem('xenon_attendant');
      showLoginScreen();
    });
  }
}

function showLoginScreen() {
  document.getElementById('login-screen').style.display = 'flex';
  document.getElementById('pos-app').style.display = 'none';
}

function enterPosApp(name) {
  state.attendant = name;
  sessionStorage.setItem('xenon_attendant', name);
  document.getElementById('display-attendant-name').textContent = name;
  document.getElementById('login-screen').style.display = 'none';
  document.getElementById('pos-app').style.display = 'flex';
  loadAllData();
}

// ==========================================================================
// 2. DATA LOADING & LIVE REFRESH
// ==========================================================================

async function loadAllData() {
  try {
    await Promise.all([
      fetchOverview(),
      fetchRooms(),
      fetchCatalog(),
    ]);
  } catch (err) {
    showToast(`Notice: ${err.message}`, 'error');
  }
}

async function fetchOverview() {
  const data = await api('/api/overview');
  state.overview = data;
  renderOverviewStrip();
}

async function fetchRooms() {
  const data = await api('/api/rooms');
  state.rooms = data.rooms;
  renderSuitesGrid();
  populateSuiteDropdowns();
  updateSelectedSuiteInfo();
}

async function fetchCatalog() {
  const data = await api('/api/catalog');
  state.catalog = data.catalog;
  renderCatalogGrid();
}

async function fetchHistory(query = '') {
  const url = query ? `/api/history?search=${encodeURIComponent(query)}` : '/api/history';
  const data = await api(url);
  state.history = data.history;
  renderHistoryTable();
}

// ==========================================================================
// 3. QUICK STATUS STRIP
// ==========================================================================

function renderOverviewStrip() {
  if (!state.overview) return;
  const o = state.overview;

  document.getElementById('qs-total-rooms').textContent = `${o.total_rooms} Residences`;
  document.getElementById('qs-occupied').textContent = `${o.occupied} In-House (${o.active_guests_count} Guests)`;
  document.getElementById('qs-vacant').textContent = `${o.vacant} Available`;
  document.getElementById('qs-cleaning').textContent = `${o.cleaning} in Turnover`;
  document.getElementById('qs-revenue').textContent = formatCurrency(o.live_folio_revenue);
}

// ==========================================================================
// 4. SUITES GRID (UNCLUTTERED, PALACE AESTHETIC)
// ==========================================================================

function renderSuitesGrid() {
  const container = document.getElementById('suites-card-grid');
  if (!container) return;

  let list = state.rooms;

  // Filter pills
  if (state.suiteFilter !== 'all') {
    list = list.filter((r) => r.status === state.suiteFilter);
  }

  // Search filter
  const searchInput = document.getElementById('suite-search');
  if (searchInput && searchInput.value.trim()) {
    const q = searchInput.value.trim().toLowerCase();
    list = list.filter((r) => {
      const matchNum = r.room_number.toLowerCase().includes(q);
      const matchWing = r.wing.toLowerCase().includes(q);
      const matchType = r.room_type.toLowerCase().includes(q);
      const matchGuest = r.active_stay && r.active_stay.guest_name.toLowerCase().includes(q);
      return matchNum || matchWing || matchType || matchGuest;
    });
  }

  if (list.length === 0) {
    container.innerHTML = `
      <div style="grid-column: 1 / -1; text-align: center; padding: 48px 20px; color: var(--ink-muted);">
        <p style="font-family: var(--font-serif-display); font-size: 1.1rem;">No suites match the selected filter.</p>
      </div>
    `;
    return;
  }

  container.innerHTML = list.map((room) => {
    const stay = room.active_stay;
    const isOccupied = room.status === 'occupied' && stay;
    const isCleaning = room.status === 'cleaning';
    const isVacant = room.status === 'vacant';

    return `
      <div class="suite-box">
        <div>
          <!-- Suite Head -->
          <div class="suite-box-header">
            <div>
              <span class="sb-wing">${room.wing}</span>
              <h3 class="sb-number">${room.room_number}</h3>
              <div class="sb-type">${room.room_type}</div>
            </div>
            <span class="palace-pill ${room.status}">
              ${room.status === 'occupied' ? 'Occupied' : room.status === 'vacant' ? 'Available' : 'Turnover'}
            </span>
          </div>

          <!-- Specs Line -->
          <div class="suite-box-meta">
            <span>Tariff: <b>${formatCurrency(room.base_rate)}</b>/nt</span>
            <span>Capacity: ${room.capacity} Guests</span>
          </div>

          <!-- Body Content based on status -->
          ${isOccupied ? `
            <div class="sb-resident-details">
              <div class="sb-resident-head">
                <span class="sb-guest-name">👤 ${stay.guest_name}</span>
                <span class="sb-vip-tag">${stay.vip_tier}</span>
              </div>
              <div class="sb-timing">
                Checked in ${formatDateTime(stay.check_in_at)} · <b>${stay.nights_elapsed} Night(s)</b>
              </div>
              <div class="sb-folio-row">
                <span>Current Folio Balance:</span>
                <span class="sb-folio-due tabular">${formatCurrency(stay.calculated_due)}</span>
              </div>
            </div>
          ` : isCleaning ? `
            <div class="sb-cleaning-prompt">
              <span>🧹 Housekeeping turnover active. Sanitizing & linen renewal in progress.</span>
            </div>
          ` : `
            <div class="sb-ready-prompt">
              <span>✨ Inspected and ready to welcome distinguished residents.</span>
            </div>
          `}
        </div>

        <!-- Action Controls -->
        <div class="suite-card-actions">
          ${isOccupied ? `
            <button class="btn-palace-secondary sm" onclick="openCheckoutModalForRoom(${room.id})">
              <span>📋 Folio & Settle</span>
            </button>
            <button class="btn-palace-primary sm" onclick="selectSuiteForTicket(${room.id}, true)">
              <span>🍷 + Order / Bill</span>
            </button>
          ` : isCleaning ? `
            <button class="btn-palace-primary sm" onclick="markRoomReady(${room.id})">
              <span>✓ Mark Ready for Guest</span>
            </button>
          ` : `
            <button class="btn-palace-primary sm" onclick="openCheckInModalForRoom(${room.id})">
              <span>⚡ Quick Check-In</span>
            </button>
          `}
        </div>
      </div>
    `;
  }).join('');
}

// ==========================================================================
// 5. IN-SUITE DINING & BAR POS VIEW
// ==========================================================================

function renderCatalogGrid() {
  const container = document.getElementById('menu-items-grid');
  if (!container) return;

  let list = state.catalog;

  // Category filter
  if (state.catalogCategory !== 'all') {
    list = list.filter((i) => i.category.toLowerCase().includes(state.catalogCategory.toLowerCase()));
  }

  // Search filter
  const searchInput = document.getElementById('menu-search');
  if (searchInput && searchInput.value.trim()) {
    const q = searchInput.value.trim().toLowerCase();
    list = list.filter((i) => i.name.toLowerCase().includes(q) || i.description.toLowerCase().includes(q));
  }

  container.innerHTML = list.map((item) => `
    <div class="menu-card">
      <div>
        <div class="mc-top">
          <span class="mc-icon">${item.icon}</span>
          <span class="mc-cat">${item.category}</span>
        </div>
        <h4 class="mc-title">${item.name}</h4>
        <p class="mc-desc">${item.description}</p>
      </div>
      <div class="mc-bottom">
        <span class="mc-price tabular">${formatCurrency(item.price)}</span>
        <button class="btn-add-item" onclick="addItemToTicket(${item.id})">
          <span>+ Add to Check</span>
        </button>
      </div>
    </div>
  `).join('');
}

// ==========================================================================
// 6. RIGHT-HAND HOTEL GUEST CHECK / TICKET CONTROLLER
// ==========================================================================

function selectSuiteForTicket(roomId, switchToDining = false) {
  state.selectedSuiteId = roomId;
  const select = document.getElementById('ticket-suite-select');
  if (select) select.value = roomId;
  updateSelectedSuiteInfo();

  if (switchToDining) {
    switchPosView('dining');
    showToast(`Active Ticket assigned to Suite. Select items to charge!`, 'success');
  }
}

function updateSelectedSuiteInfo() {
  const infoBox = document.getElementById('ticket-room-info');
  const chargeBtn = document.getElementById('btn-charge-to-room');
  const checkoutBtn = document.getElementById('btn-sidebar-checkout');
  const directSettleBtn = document.getElementById('btn-direct-settle');

  const select = document.getElementById('ticket-suite-select');
  const roomId = select ? Number(select.value) : null;
  state.selectedSuiteId = roomId;

  const room = state.rooms.find((r) => r.id === roomId);
  const stay = room && room.active_stay ? room.active_stay : null;

  if (room && stay) {
    infoBox.style.display = 'block';
    document.getElementById('tri-guest-name').textContent = stay.guest_name;
    document.getElementById('tri-vip-badge').textContent = stay.vip_tier;
    document.getElementById('tri-folio-due').textContent = formatCurrency(stay.calculated_due);

    checkoutBtn.style.display = 'block';
    checkoutBtn.onclick = () => openCheckoutModalForRoom(room.id);
  } else {
    infoBox.style.display = 'none';
    checkoutBtn.style.display = 'none';
  }

  // Update button enabled states
  const hasItems = state.ticketItems.length > 0;
  if (chargeBtn) chargeBtn.disabled = !hasItems || !stay;
  if (directSettleBtn) directSettleBtn.disabled = !hasItems;
}

function addItemToTicket(catalogId) {
  const item = state.catalog.find((c) => c.id === catalogId);
  if (!item) return;

  const existing = state.ticketItems.find((ti) => ti.item.id === catalogId);
  if (existing) {
    existing.qty += 1;
  } else {
    state.ticketItems.push({ item, qty: 1 });
  }

  renderTicket();
  showToast(`Added ${item.name} to Guest Check`, 'normal');
}

function changeTicketItemQty(catalogId, delta) {
  const existing = state.ticketItems.find((ti) => ti.item.id === catalogId);
  if (!existing) return;

  existing.qty += delta;
  if (existing.qty <= 0) {
    state.ticketItems = state.ticketItems.filter((ti) => ti.item.id !== catalogId);
  }

  renderTicket();
}

function clearTicket() {
  state.ticketItems = [];
  renderTicket();
}

function renderTicket() {
  const listContainer = document.getElementById('ticket-lines-list');
  const chargeBtn = document.getElementById('btn-charge-to-room');
  const directSettleBtn = document.getElementById('btn-direct-settle');

  if (state.ticketItems.length === 0) {
    listContainer.innerHTML = `
      <div class="ticket-empty-state">
        <p>No dining or service items on this check yet.</p>
        <small>Select items from "In-Suite Dining & Bar" or click "+ Order" on any occupied suite.</small>
      </div>
    `;
    document.getElementById('ticket-subtotal').textContent = '₹0';
    document.getElementById('ticket-tax').textContent = '₹0';
    document.getElementById('ticket-total').textContent = '₹0';
    if (chargeBtn) chargeBtn.disabled = true;
    if (directSettleBtn) directSettleBtn.disabled = true;
    return;
  }

  let subtotal = 0;

  listContainer.innerHTML = state.ticketItems.map((line) => {
    const lineTotal = line.item.price * line.qty;
    subtotal += lineTotal;

    return `
      <div class="ticket-line-row">
        <span class="tl-name">${line.item.name}</span>
        <div class="tl-stepper">
          <button class="tl-btn" onclick="changeTicketItemQty(${line.item.id}, -1)">−</button>
          <span>${line.qty}</span>
          <button class="tl-btn" onclick="changeTicketItemQty(${line.item.id}, 1)">+</button>
        </div>
        <span class="tl-amt tabular">${formatCurrency(lineTotal)}</span>
      </div>
    `;
  }).join('');

  const tax = Math.round(subtotal * 0.12);
  const grandTotal = subtotal + tax;

  document.getElementById('ticket-subtotal').textContent = formatCurrency(subtotal);
  document.getElementById('ticket-tax').textContent = formatCurrency(tax);
  document.getElementById('ticket-total').textContent = formatCurrency(grandTotal);

  updateSelectedSuiteInfo();
}

async function chargeTicketToRoomFolio() {
  const select = document.getElementById('ticket-suite-select');
  const roomId = select ? Number(select.value) : null;
  const room = state.rooms.find((r) => r.id === roomId);
  const stay = room && room.active_stay ? room.active_stay : null;

  if (!stay) {
    showToast('Please select an occupied suite to bill this check to.', 'error');
    if (select) select.focus();
    return;
  }

  if (state.ticketItems.length === 0) return;

  try {
    for (const line of state.ticketItems) {
      const lineTotal = line.item.price * line.qty;
      await api('/api/folio/charge', {
        method: 'POST',
        body: JSON.stringify({
          stay_id: stay.id,
          charge_type: 'room_service',
          description: `${line.item.name} (x${line.qty})`,
          amount: lineTotal,
        }),
      });
    }

    showToast(`Successfully billed ${formatCurrency(document.getElementById('ticket-total').textContent)} to ${room.room_number} folio!`, 'success');
    clearTicket();
    await loadAllData();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

function directSettleTicket() {
  if (state.ticketItems.length === 0) return;
  const total = document.getElementById('ticket-total').textContent;
  showToast(`Tender settled for ${total} via Cash / Terminal Card. Thank you!`, 'success');
  clearTicket();
}

// ==========================================================================
// 7. STAY LEDGER TABLE (VIEW 3)
// ==========================================================================

function renderHistoryTable() {
  const tbody = document.getElementById('ledger-table-body');
  if (!tbody) return;

  if (state.history.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="10" style="text-align: center; padding: 32px; color: var(--ink-muted);">
          No past residencies recorded yet.
        </td>
      </tr>
    `;
    return;
  }

  tbody.innerHTML = state.history.map((h) => {
    const isOut = h.status === 'checked_out';
    const totalDisplay = formatCurrency(h.total_billed || (h.stay_nights * h.nightly_rate + h.folio_charges));

    return `
      <tr>
        <td><code>${h.id}</code></td>
        <td>
          <strong>${h.room_number}</strong>
          <div style="font-size: 0.72rem; color: var(--ink-muted);">${h.room_type}</div>
        </td>
        <td>
          <strong>${h.guest_name}</strong>
          ${h.guest_phone ? `<div style="font-size:0.72rem; color: var(--ink-muted);">${h.guest_phone}</div>` : ''}
        </td>
        <td>
          <span style="font-size:0.75rem; color:var(--gold-bronze); font-weight:600;">${h.vip_tier}</span>
        </td>
        <td class="tabular">${formatDateTime(h.check_in_at)}</td>
        <td class="tabular">${h.actual_check_out_at ? formatDateTime(h.actual_check_out_at) : '<span style="color:var(--gold-bronze);">In-House Active</span>'}</td>
        <td class="tabular" style="text-align:right;">${formatCurrency(h.nightly_rate)}</td>
        <td class="tabular" style="text-align:right;"><strong>${totalDisplay}</strong></td>
        <td>
          <span class="palace-pill ${isOut ? 'vacant' : 'occupied'}">
            ${isOut ? 'Settled' : 'In-House'}
          </span>
        </td>
        <td style="text-align:center;">
          <button class="btn-palace-secondary sm" onclick="viewHistoricalInvoice('${h.id}')">
            <span>📄 View Bill</span>
          </button>
        </td>
      </tr>
    `;
  }).join('');
}

// ==========================================================================
// 8. SUITE STATUS & MODAL CONTROLLERS
// ==========================================================================

function populateSuiteDropdowns() {
  const checkinSelect = document.getElementById('ci-suite');
  const ticketSelect = document.getElementById('ticket-suite-select');

  const vacantRooms = state.rooms.filter((r) => r.status === 'vacant');
  if (checkinSelect) {
    checkinSelect.innerHTML = vacantRooms.map((r) => `
      <option value="${r.id}">${r.room_number} — ${r.room_type} (${formatCurrency(r.base_rate)}/nt)</option>
    `).join('') || '<option value="">No vacant suites</option>';
  }

  if (ticketSelect) {
    const curVal = ticketSelect.value;
    let opts = '<option value="">Select Suite or Walk-In Bar...</option>';
    state.rooms.forEach((r) => {
      const stay = r.active_stay;
      opts += `<option value="${r.id}">${r.room_number} ${stay ? '· ' + stay.guest_name + ' (In-House)' : '· Available'}</option>`;
    });
    ticketSelect.innerHTML = opts;
    if (curVal) ticketSelect.value = curVal;
  }
}

async function markRoomReady(roomId) {
  try {
    await api(`/api/rooms/${roomId}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status: 'vacant' }),
    });
    showToast('Suite inspected & marked available for arrival.', 'success');
    await loadAllData();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

function openCheckInModalForRoom(roomId) {
  const room = state.rooms.find((r) => r.id === roomId);
  const select = document.getElementById('ci-suite');
  const rateInput = document.getElementById('ci-rate');

  if (room) {
    document.getElementById('checkin-modal-title').textContent = `Check-In: ${room.room_number} (${room.room_type})`;
    if (select) select.value = room.id;
    if (rateInput) rateInput.value = room.base_rate;
  } else {
    document.getElementById('checkin-modal-title').textContent = 'Register Distinguished Guest';
    if (rateInput) rateInput.value = '';
  }

  openModal('modal-checkin');
}

// Check-Out Folio Modal
async function openCheckoutModalForRoom(roomId) {
  const room = state.rooms.find((r) => r.id === roomId);
  if (!room || !room.active_stay) return;

  const stayId = room.active_stay.id;
  try {
    const folio = await api(`/api/folio/${stayId}`);
    renderCheckoutModal(folio, room);
    openModal('modal-checkout');
  } catch (err) {
    showToast(err.message, 'error');
  }
}

function renderCheckoutModal(folio, room) {
  const stay = folio.stay;
  document.getElementById('co-modal-title').textContent = `Folio & Settlement: ${room.room_number}`;
  document.getElementById('co-guest-name').textContent = stay.guest_name;
  document.getElementById('co-guest-meta').textContent = `${stay.vip_tier} · Check-In ${formatDateTime(stay.check_in_at)} (${folio.nights} Night/s)`;
  document.getElementById('co-net-due-display').textContent = formatCurrency(folio.net_due);

  const tbody = document.getElementById('co-items-body');
  let rows = `
    <tr>
      <td>
        <strong>Accommodation (${folio.nights} Night(s))</strong>
        <div style="font-size:0.72rem; color:var(--ink-muted);">@ ${formatCurrency(stay.nightly_rate)} / night</div>
      </td>
      <td>Sanctuary Lodging</td>
      <td class="tabular">${formatDateTime(stay.check_in_at)}</td>
      <td class="tabular" style="text-align:right;">${formatCurrency(folio.room_charges)}</td>
    </tr>
  `;

  if (folio.folio_items && folio.folio_items.length > 0) {
    rows += folio.folio_items.map((i) => `
      <tr>
        <td>${i.description}</td>
        <td>${i.charge_type.replace('_', ' ').toUpperCase()}</td>
        <td class="tabular">${formatDateTime(i.created_at)}</td>
        <td class="tabular" style="text-align:right;">+${formatCurrency(i.amount)}</td>
      </tr>
    `).join('');
  }

  tbody.innerHTML = rows;

  document.getElementById('co-stay-id').value = stay.id;
  document.getElementById('co-damage').value = '0';
  document.getElementById('co-discount').value = '0';

  updateCheckoutCalculations(folio);

  document.getElementById('co-damage').oninput = () => updateCheckoutCalculations(folio);
  document.getElementById('co-discount').oninput = () => updateCheckoutCalculations(folio);
}

function updateCheckoutCalculations(folio) {
  const stay = folio.stay;
  const damage = Number(document.getElementById('co-damage').value) || 0;
  const discount = Number(document.getElementById('co-discount').value) || 0;

  const roomCharge = folio.room_charges;
  const folioSum = folio.folio_sum;
  const advance = stay.advance_paid || 0;

  const finalDue = Math.max(0, roomCharge + folioSum + damage - discount - advance);

  document.getElementById('co-sum-room').textContent = formatCurrency(roomCharge);
  document.getElementById('co-sum-folio').textContent = `+${formatCurrency(folioSum + damage)}`;
  document.getElementById('co-sum-advance').textContent = `−${formatCurrency(advance + discount)}`;
  document.getElementById('co-sum-final').textContent = formatCurrency(finalDue);
  document.getElementById('co-net-due-display').textContent = formatCurrency(finalDue);
}

// Invoice Generator
async function viewHistoricalInvoice(stayId) {
  try {
    const data = await api(`/api/folio/${stayId}`);
    populateStationeryInvoice(data);
    openModal('modal-invoice');
  } catch (err) {
    showToast(err.message, 'error');
  }
}

function populateStationeryInvoice(data) {
  const s = data.stay;
  document.getElementById('inv-folio-ref').textContent = s.id;
  document.getElementById('inv-date').textContent = formatDateOnly(Date.now());
  document.getElementById('inv-room').textContent = `${s.room_number} (${s.room_type})`;

  document.getElementById('inv-guest').textContent = s.guest_name;
  document.getElementById('inv-contact').textContent = `${s.guest_phone || 'Direct'} ${s.guest_email ? '· ' + s.guest_email : ''}`;
  document.getElementById('inv-vip').textContent = `Membership: ${s.vip_tier} · ID: ${s.id_proof_type} ${s.id_proof_number}`;

  document.getElementById('inv-in').textContent = formatDateTime(s.check_in_at);
  document.getElementById('inv-out').textContent = s.actual_check_out_at ? formatDateTime(s.actual_check_out_at) : formatDateTime(Date.now());
  document.getElementById('inv-nights').textContent = `${data.nights} Night(s)`;

  const tbody = document.getElementById('inv-tbody');
  let rows = `
    <tr>
      <td>Accommodation (${data.nights} Night(s) @ ${formatCurrency(s.nightly_rate)})</td>
      <td>Sanctuary Lodging</td>
      <td class="tabular" style="text-align:right;">${formatCurrency(data.room_charges)}</td>
    </tr>
  `;

  if (data.folio_items && data.folio_items.length > 0) {
    rows += data.folio_items.map((i) => `
      <tr>
        <td>${i.description}</td>
        <td>${i.charge_type.replace('_', ' ').toUpperCase()}</td>
        <td class="tabular" style="text-align:right;">${formatCurrency(i.amount)}</td>
      </tr>
    `).join('');
  }

  tbody.innerHTML = rows;

  document.getElementById('inv-gross').textContent = formatCurrency(data.gross_total);
  document.getElementById('inv-advance').textContent = `−${formatCurrency(s.advance_paid)}`;
  document.getElementById('inv-net').textContent = formatCurrency(data.net_due);
}

// Modal View toggles
function openModal(id) {
  const m = document.getElementById(id);
  if (m) m.classList.add('open');
}

function closeModal(id) {
  const m = document.getElementById(id);
  if (m) m.classList.remove('open');
}

function switchPosView(viewName) {
  state.currentView = viewName;
  document.querySelectorAll('.mode-tab').forEach((t) => {
    t.classList.toggle('active', t.dataset.view === viewName);
  });

  document.querySelectorAll('.pos-view').forEach((v) => {
    v.style.display = 'none';
  });

  const activeView = document.getElementById(`view-${viewName}`);
  if (activeView) activeView.style.display = 'block';

  if (viewName === 'ledger') {
    fetchHistory();
  }
}

// ==========================================================================
// 9. EVENT LISTENERS SETUP
// ==========================================================================

function setupEventListeners() {
  // Mode Switch Tabs
  document.querySelectorAll('.mode-tab').forEach((tab) => {
    tab.addEventListener('click', () => {
      switchPosView(tab.dataset.view);
    });
  });

  // Suite Filter Pills
  document.querySelectorAll('.filter-pill[data-filter]').forEach((pill) => {
    pill.addEventListener('click', () => {
      document.querySelectorAll('.filter-pill[data-filter]').forEach((p) => p.classList.remove('active'));
      pill.classList.add('active');
      state.suiteFilter = pill.dataset.filter;
      renderSuitesGrid();
    });
  });

  // Suite Search Input
  const suiteSearch = document.getElementById('suite-search');
  if (suiteSearch) {
    suiteSearch.addEventListener('input', () => renderSuitesGrid());
  }

  // Menu Category Filter Pills
  document.querySelectorAll('#menu-category-pills .filter-pill').forEach((pill) => {
    pill.addEventListener('click', () => {
      document.querySelectorAll('#menu-category-pills .filter-pill').forEach((p) => p.classList.remove('active'));
      pill.classList.add('active');
      state.catalogCategory = pill.dataset.category;
      renderCatalogGrid();
    });
  });

  // Menu Search Input
  const menuSearch = document.getElementById('menu-search');
  if (menuSearch) {
    menuSearch.addEventListener('input', () => renderCatalogGrid());
  }

  // Ledger Search Input
  const ledgerSearch = document.getElementById('ledger-search');
  if (ledgerSearch) {
    ledgerSearch.addEventListener('input', (e) => fetchHistory(e.target.value));
  }

  // Top Register Guest Button
  const headerCheckin = document.getElementById('btn-header-checkin');
  if (headerCheckin) {
    headerCheckin.addEventListener('click', () => openCheckInModalForRoom(null));
  }

  // Suite Selector in Ticket
  const ticketSuiteSelect = document.getElementById('ticket-suite-select');
  if (ticketSuiteSelect) {
    ticketSuiteSelect.addEventListener('change', () => updateSelectedSuiteInfo());
  }

  // Charge to Room Button
  const chargeBtn = document.getElementById('btn-charge-to-room');
  if (chargeBtn) {
    chargeBtn.addEventListener('click', () => chargeTicketToRoomFolio());
  }

  // Direct Settle Button
  const directSettleBtn = document.getElementById('btn-direct-settle');
  if (directSettleBtn) {
    directSettleBtn.addEventListener('click', () => directSettleTicket());
  }

  // Clear Ticket Button
  const clearBtn = document.getElementById('btn-clear-ticket');
  if (clearBtn) {
    clearBtn.addEventListener('click', () => clearTicket());
  }

  // Close Modals
  document.querySelectorAll('[data-close]').forEach((el) => {
    el.addEventListener('click', () => closeModal(el.dataset.close));
  });

  document.querySelectorAll('.palace-modal-backdrop').forEach((backdrop) => {
    backdrop.addEventListener('click', (e) => {
      if (e.target === backdrop) backdrop.classList.remove('open');
    });
  });

  // Check-In Form Submit
  const checkinForm = document.getElementById('form-checkin');
  if (checkinForm) {
    checkinForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const suiteSelect = document.getElementById('ci-suite');
      const roomId = Number(suiteSelect.value);
      if (!roomId) {
        showToast('Please select a suite to check in.', 'error');
        return;
      }

      const payload = {
        room_id: roomId,
        guest_name: document.getElementById('ci-name').value.trim(),
        guest_phone: document.getElementById('ci-phone').value.trim(),
        guest_email: '',
        vip_tier: document.getElementById('ci-vip').value,
        id_proof_type: document.getElementById('ci-id-type').value,
        id_proof_number: document.getElementById('ci-id-num').value.trim(),
        stay_nights: Number(document.getElementById('ci-nights').value) || 1,
        nightly_rate: document.getElementById('ci-rate').value ? Number(document.getElementById('ci-rate').value) : null,
        advance_paid: Number(document.getElementById('ci-advance').value) || 0,
        notes: document.getElementById('ci-notes').value.trim(),
      };

      try {
        const res = await api('/api/checkin', {
          method: 'POST',
          body: JSON.stringify(payload),
        });

        showToast(res.message, 'success');
        closeModal('modal-checkin');
        checkinForm.reset();
        await loadAllData();
      } catch (err) {
        showToast(err.message, 'error');
      }
    });
  }

  // Check-Out Form Submit
  const checkoutForm = document.getElementById('form-checkout');
  if (checkoutForm) {
    checkoutForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const stayId = document.getElementById('co-stay-id').value;
      if (!stayId) return;

      const payload = {
        stay_id: stayId,
        damage_charges: Number(document.getElementById('co-damage').value) || 0,
        discount: Number(document.getElementById('co-discount').value) || 0,
        notes: `Tendered via ${document.getElementById('co-method').value}`,
      };

      try {
        const res = await api('/api/checkout', {
          method: 'POST',
          body: JSON.stringify(payload),
        });

        showToast(`Settled & Checked Out ${res.summary.guest_name}. Room moved to Turnover.`, 'success');
        closeModal('modal-checkout');
        await loadAllData();
      } catch (err) {
        showToast(err.message, 'error');
      }
    });
  }

  // Print Bill Button inside Checkout Modal
  const printBillBtn = document.getElementById('btn-print-bill');
  if (printBillBtn) {
    printBillBtn.addEventListener('click', async () => {
      const stayId = document.getElementById('co-stay-id').value;
      if (!stayId) return;
      await viewHistoricalInvoice(stayId);
    });
  }

  // Live Palace Clock
  setInterval(() => {
    const clock = document.getElementById('estate-clock');
    if (clock) {
      clock.textContent = new Date().toLocaleTimeString('en-US', { hour12: false });
    }
  }, 1000);
}

// Global bootstrap
document.addEventListener('DOMContentLoaded', () => {
  setupEventListeners();
  initAuth();
});
