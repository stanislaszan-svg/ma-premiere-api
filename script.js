const API = 'http://localhost:8000';

// ─── State ───────────────────────────────────────────────────────────────────

const state = {
    tasks: [],
    stats: {},
    filter: 'all',
    query: '',
    editingId: null,
    tags: [],
};

// ─── HTTP helper ─────────────────────────────────────────────────────────────

async function http(method, path, body = null) {
    const opts = { method, headers: { 'Content-Type': 'application/json' } };
    if (body) opts.body = JSON.stringify(body);
    const res = await fetch(API + path, opts);
    if (!res.ok) throw new Error(`${res.status} ${await res.text()}`);
    if (res.status === 204) return null;
    return res.json();
}

// ─── Load data ───────────────────────────────────────────────────────────────

async function loadAll() {
    await Promise.all([loadStats(), loadTasks()]);
}

async function loadStats() {
    try {
        state.stats = await http('GET', '/tasks/stats');
        renderStats();
        updateCounts();
    } catch {
        showToast('Impossible de joindre l\'API', 'error');
    }
}

async function loadTasks() {
    try {
        const map = {
            all:      '/tasks',
            today:    '/tasks/today',
            overdue:  '/tasks/overdue',
            upcoming: '/tasks/upcoming',
            done:     '/tasks?done=true',
        };
        const url = state.query
            ? `/tasks/search?q=${encodeURIComponent(state.query)}`
            : map[state.filter];
        state.tasks = await http('GET', url);
        renderTasks();
    } catch {
        showToast('Erreur lors du chargement des tâches', 'error');
    }
}

// ─── Render stats ─────────────────────────────────────────────────────────────

function renderStats() {
    const s = state.stats;
    const overdue = s.due_date_summary?.overdue ?? 0;

    document.getElementById('statsGrid').innerHTML = [
        { icon: '📋', bg: '#eef2ff', color: '#6366f1', value: s.total ?? 0,   label: 'Total' },
        { icon: '✅', bg: '#ecfdf5', color: '#10b981', value: s.done ?? 0,    label: 'Terminées' },
        { icon: '⏳', bg: '#fffbeb', color: '#f59e0b', value: s.pending ?? 0, label: 'En cours' },
        { icon: '🚨', bg: '#fef2f2', color: '#ef4444', value: overdue,        label: 'En retard' },
    ].map(c => `
        <div class="stat-card">
            <div class="stat-icon" style="background:${c.bg}">${c.icon}</div>
            <div>
                <div class="stat-value" style="color:${c.color}">${c.value}</div>
                <div class="stat-label">${c.label}</div>
            </div>
        </div>
    `).join('');

    const bp = s.by_priority ?? {};
    const maxTotal = Math.max(...['high','medium','low'].map(k => bp[k]?.total ?? 0), 1);
    const priorityCfg = [
        { key: 'high',   label: 'Haute',   color: '#ef4444' },
        { key: 'medium', label: 'Moyenne', color: '#f59e0b' },
        { key: 'low',    label: 'Basse',   color: '#10b981' },
    ];

    const priorityHtml = priorityCfg.map(({ key, label, color }) => {
        const d = bp[key] ?? { total: 0, done: 0, pending: 0 };
        const pct = Math.round((d.total / maxTotal) * 100);
        return `
            <div class="priority-row">
                <span class="priority-label" style="color:${color}">${label}</span>
                <div class="bar-track"><div class="bar-fill" style="width:${pct}%;background:${color}"></div></div>
                <span class="bar-count">${d.total}</span>
            </div>`;
    }).join('');

    const bt = s.by_tag ?? {};
    const tagHtml = Object.keys(bt).length
        ? Object.entries(bt).map(([tag, d]) => `
            <span class="tag-stat" onclick="searchByTag('${esc(tag)}')" title="${d.done}/${d.total} terminées">
                ${esc(tag)} <strong>${d.total}</strong>
            </span>`).join('')
        : '<span style="color:var(--text-muted);font-size:13px">Aucun tag</span>';

    document.getElementById('statsDetail').innerHTML = `
        <div class="detail-card">
            <div class="detail-title">Par priorité</div>
            <div class="priority-bars">${priorityHtml}</div>
        </div>
        <div class="detail-card">
            <div class="detail-title">Par tag <span style="font-weight:400;text-transform:none;letter-spacing:0"> — cliquez pour filtrer</span></div>
            <div class="tag-cloud">${tagHtml}</div>
        </div>`;
}

function updateCounts() {
    const s = state.stats;
    const ds = s.due_date_summary ?? {};
    document.getElementById('cnt-all').textContent      = s.total   ?? 0;
    document.getElementById('cnt-done').textContent     = s.done    ?? 0;
    document.getElementById('cnt-overdue').textContent  = ds.overdue  ?? 0;
    document.getElementById('cnt-today').textContent    = ds.today    ?? 0;
    document.getElementById('cnt-upcoming').textContent = ds.upcoming ?? 0;
}

// ─── Render tasks ─────────────────────────────────────────────────────────────

function renderTasks() {
    const grid = document.getElementById('tasksGrid');
    if (!state.tasks.length) {
        grid.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">${state.query ? '🔍' : '📭'}</div>
                <p>${state.query ? `Aucun résultat pour « ${esc(state.query)} »` : 'Aucune tâche ici'}</p>
            </div>`;
        return;
    }
    grid.innerHTML = state.tasks.map(taskCard).join('');
}

function taskCard(t) {
    const today = new Date().toISOString().slice(0, 10);
    let dueHtml = '';
    if (t.due_date) {
        const cls = t.due_date < today ? 'overdue' : t.due_date === today ? 'today' : '';
        const label = t.due_date === today ? "Aujourd'hui" : fmtDate(t.due_date);
        dueHtml = `<span class="due-badge ${cls}">📅 ${label}</span>`;
    }
    const tags = (t.tags ?? []).map(g => `<span class="tag-badge">${esc(g)}</span>`).join('');
    const actionBtn = t.done
        ? `<button class="btn-icon reopen" onclick="doReopen(${t.id})" title="Rouvrir">↩</button>`
        : `<button class="btn-icon ok"     onclick="doComplete(${t.id})" title="Terminer">✓</button>`;

    return `
        <div class="task-card priority-${t.priority} ${t.done ? 'done' : ''}" id="card-${t.id}">
            <div class="card-body">
                <div class="card-header">
                    <div class="card-title">${esc(t.title)}</div>
                    <span class="priority-badge ${t.priority}">${priorityLabel(t.priority)}</span>
                </div>
                ${t.description ? `<div class="card-desc">${esc(t.description)}</div>` : ''}
                <div class="card-meta">${dueHtml}${tags}</div>
            </div>
            <div class="card-footer">
                <div class="card-status">
                    <div class="dot ${t.done ? '' : 'active'}"></div>
                    ${t.done ? 'Terminée' : 'En cours'}
                </div>
                <div class="card-actions">
                    ${actionBtn}
                    <button class="btn-icon" onclick="openModal(${t.id})" title="Modifier">✎</button>
                    <button class="btn-icon del" onclick="doDelete(${t.id})" title="Supprimer">🗑</button>
                </div>
            </div>
        </div>`;
}

// ─── Task actions ─────────────────────────────────────────────────────────────

async function doComplete(id) {
    await http('POST', `/tasks/${id}/complete`);
    showToast('Tâche terminée ✓', 'success');
    loadAll();
}

async function doReopen(id) {
    await http('POST', `/tasks/${id}/reopen`);
    showToast('Tâche réouverte', 'info');
    loadAll();
}

async function doDelete(id) {
    if (!confirm('Supprimer cette tâche ?')) return;
    await http('DELETE', `/tasks/${id}`);
    showToast('Tâche supprimée', 'error');
    loadAll();
}

// ─── Modal ────────────────────────────────────────────────────────────────────

async function openModal(id = null) {
    state.editingId = id;
    state.tags = [];

    document.getElementById('modalTitle').textContent = id ? 'Modifier la tâche' : 'Nouvelle tâche';
    document.getElementById('fTitle').value    = '';
    document.getElementById('fDesc').value     = '';
    document.getElementById('fPriority').value = 'medium';
    document.getElementById('fDueDate').value  = '';
    renderTagChips();

    if (id) {
        const t = await http('GET', `/tasks/${id}`);
        document.getElementById('fTitle').value    = t.title;
        document.getElementById('fDesc').value     = t.description ?? '';
        document.getElementById('fPriority').value = t.priority;
        document.getElementById('fDueDate').value  = t.due_date ?? '';
        state.tags = [...(t.tags ?? [])];
        renderTagChips();
    }

    document.getElementById('overlay').classList.add('open');
    setTimeout(() => document.getElementById('fTitle').focus(), 150);
}

function closeModal() {
    document.getElementById('overlay').classList.remove('open');
    state.editingId = null;
}

function onOverlayClick(e) {
    if (e.target === document.getElementById('overlay')) closeModal();
}

async function submitForm() {
    const title = document.getElementById('fTitle').value.trim();
    if (!title) { document.getElementById('fTitle').focus(); return; }

    const payload = {
        title,
        description: document.getElementById('fDesc').value.trim() || null,
        priority:    document.getElementById('fPriority').value,
        due_date:    document.getElementById('fDueDate').value || null,
        tags:        [...state.tags],
    };

    try {
        if (state.editingId) {
            await http('PATCH', `/tasks/${state.editingId}`, payload);
            showToast('Tâche modifiée', 'info');
        } else {
            await http('POST', '/tasks', payload);
            showToast('Tâche créée ✓', 'success');
        }
        closeModal();
        loadAll();
    } catch (e) {
        showToast('Erreur : ' + e.message, 'error');
    }
}

// ─── Tag chip input ───────────────────────────────────────────────────────────

function addTag(raw) {
    const tag = raw.trim().toLowerCase().replace(/,+$/, '');
    if (!tag || state.tags.includes(tag)) return false;
    state.tags.push(tag);
    renderTagChips();
    return true;
}

function removeTag(tag) {
    state.tags = state.tags.filter(t => t !== tag);
    renderTagChips();
}

function renderTagChips() {
    const wrap = document.getElementById('tagWrap');
    const chips = state.tags.map(t => `
        <span class="tag-chip">
            ${esc(t)}
            <button type="button" onclick="removeTag('${esc(t)}')">×</button>
        </span>`).join('');
    wrap.innerHTML = chips + `<input id="tagField" class="tag-field" type="text" placeholder="${state.tags.length ? '' : 'ex: travail, urgent…'}">`;

    const field = document.getElementById('tagField');
    field.addEventListener('keydown', e => {
        if (e.key === 'Enter' || e.key === ',') {
            e.preventDefault();
            if (addTag(field.value)) field.value = '';
        } else if (e.key === 'Backspace' && !field.value && state.tags.length) {
            state.tags.pop();
            renderTagChips();
        }
    });
    field.addEventListener('blur', () => {
        if (field.value && addTag(field.value)) field.value = '';
    });
}

// ─── Filters ─────────────────────────────────────────────────────────────────

document.getElementById('filters').addEventListener('click', e => {
    const btn = e.target.closest('.filter-btn');
    if (!btn) return;
    setFilter(btn.dataset.filter);
});

function setFilter(filter) {
    state.filter = filter;
    state.query  = '';
    document.getElementById('searchInput').value = '';
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.toggle('active', b.dataset.filter === filter));
    loadTasks();
}

function searchByTag(tag) {
    state.query = tag;
    document.getElementById('searchInput').value = tag;
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    document.querySelector('[data-filter="all"]').classList.add('active');
    state.filter = 'all';
    loadTasks();
}

// ─── Search ───────────────────────────────────────────────────────────────────

let debounce;
document.getElementById('searchInput').addEventListener('input', e => {
    clearTimeout(debounce);
    debounce = setTimeout(() => {
        state.query = e.target.value.trim();
        if (!state.query) {
            document.querySelector(`[data-filter="${state.filter}"]`)?.classList.add('active');
        } else {
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
        }
        loadTasks();
    }, 280);
});

// ─── Keyboard shortcuts ───────────────────────────────────────────────────────

document.addEventListener('keydown', e => {
    const inField = e.target.matches('input, textarea, select');
    const modalOpen = document.getElementById('overlay').classList.contains('open');
    if (e.key === 'Escape') closeModal();
    if (e.key === 'n' && !inField && !modalOpen) openModal();
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter' && modalOpen) submitForm();
});

// ─── Helpers ─────────────────────────────────────────────────────────────────

function esc(s) {
    return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function priorityLabel(p) {
    return { high: '🔴 Haute', medium: '🟡 Moyenne', low: '🟢 Basse' }[p] ?? p;
}

function fmtDate(iso) {
    const [y, m, d] = iso.split('-');
    return `${d}/${m}/${y}`;
}

function showToast(msg, type = 'info') {
    const el = document.createElement('div');
    el.className = `toast ${type}`;
    el.textContent = msg;
    document.getElementById('toasts').prepend(el);
    setTimeout(() => el.remove(), 3200);
}

// ─── Init ─────────────────────────────────────────────────────────────────────

loadAll();
