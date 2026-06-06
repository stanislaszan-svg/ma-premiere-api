const API = '';

// ─── State ───────────────────────────────────────────────────────────────────

const state = {
    tasks:     [],
    stats:     {},
    filter:    'all',
    query:     '',
    editingId: null,
    formTags:  [],
};

// ─── HTTP helper ─────────────────────────────────────────────────────────────

async function http(method, path, body = null) {
    const opts = { method, headers: { 'Content-Type': 'application/json' } };
    if (body) opts.body = JSON.stringify(body);
    const res = await fetch(API + path, opts);
    if (!res.ok) {
        const msg = await res.text();
        throw new Error(`${res.status} – ${msg}`);
    }
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
    } catch (e) {
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
    } catch (e) {
        showToast('Erreur de chargement : ' + e.message, 'error');
    }
}

// ─── Render stats ─────────────────────────────────────────────────────────────

function renderStats() {
    const s = state.stats;
    const overdue = s.due_date_summary?.overdue ?? 0;

    document.getElementById('statsGrid').innerHTML = [
        { icon: '📋', bg: '#eef2ff', color: '#6366f1', value: s.total   ?? 0, label: 'Total' },
        { icon: '✅', bg: '#ecfdf5', color: '#10b981', value: s.done    ?? 0, label: 'Terminées' },
        { icon: '⏳', bg: '#fffbeb', color: '#f59e0b', value: s.pending ?? 0, label: 'En cours' },
        { icon: '🚨', bg: '#fef2f2', color: '#ef4444', value: overdue,         label: 'En retard' },
    ].map(c => `
        <div class="stat-card">
            <div class="stat-icon" style="background:${c.bg}">${c.icon}</div>
            <div>
                <div class="stat-value" style="color:${c.color}">${c.value}</div>
                <div class="stat-label">${c.label}</div>
            </div>
        </div>`).join('');

    const bp = s.by_priority ?? {};
    const maxTotal = Math.max(...['high', 'medium', 'low'].map(k => bp[k]?.total ?? 0), 1);

    const priorityHtml = [
        { key: 'high',   label: 'Haute',   color: '#ef4444' },
        { key: 'medium', label: 'Moyenne', color: '#f59e0b' },
        { key: 'low',    label: 'Basse',   color: '#10b981' },
    ].map(({ key, label, color }) => {
        const d = bp[key] ?? { total: 0 };
        const pct = Math.round((d.total / maxTotal) * 100);
        return `
            <div class="priority-row">
                <span class="priority-label" style="color:${color}">${label}</span>
                <div class="bar-track"><div class="bar-fill" style="width:${pct}%;background:${color}"></div></div>
                <span class="bar-count">${d.total}</span>
            </div>`;
    }).join('');

    const bt = s.by_tag ?? {};
    // data-tag stocke la valeur brute — pas d'injection possible via onclick
    const tagHtml = Object.keys(bt).length
        ? Object.entries(bt).map(([tag, d]) => `
            <span class="tag-stat" data-tag="${esc(tag)}" title="${d.done}/${d.total} terminées">
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

// Event delegation — tags dans le dashboard
document.getElementById('statsDetail').addEventListener('click', e => {
    const el = e.target.closest('.tag-stat');
    if (!el) return;
    searchByTag(el.dataset.tag);
});

function updateCounts() {
    const s  = state.stats;
    const ds = s.due_date_summary ?? {};
    document.getElementById('cnt-all').textContent      = s.total      ?? 0;
    document.getElementById('cnt-done').textContent     = s.done       ?? 0;
    document.getElementById('cnt-overdue').textContent  = ds.overdue   ?? 0;
    document.getElementById('cnt-today').textContent    = ds.today     ?? 0;
    document.getElementById('cnt-upcoming').textContent = ds.upcoming  ?? 0;
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
        const cls   = t.due_date < today ? 'overdue' : t.due_date === today ? 'today' : '';
        const label = t.due_date === today ? "Aujourd'hui" : fmtDate(t.due_date);
        dueHtml = `<span class="due-badge ${cls}">📅 ${label}</span>`;
    }
    const tags = (t.tags ?? []).map(g => `<span class="tag-badge">${esc(g)}</span>`).join('');

    // data-action + data-id : pas d'injection possible
    const actionBtn = t.done
        ? `<button class="btn-icon reopen" data-action="reopen"   data-id="${t.id}" title="Rouvrir">↩</button>`
        : `<button class="btn-icon ok"     data-action="complete" data-id="${t.id}" title="Terminer">✓</button>`;

    return `
        <div class="task-card priority-${t.priority} ${t.done ? 'done' : ''}">
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
                    <button class="btn-icon"     data-action="edit"   data-id="${t.id}" title="Modifier">✎</button>
                    <button class="btn-icon del" data-action="delete" data-id="${t.id}" title="Supprimer">🗑</button>
                </div>
            </div>
        </div>`;
}

// Event delegation — boutons de carte
document.getElementById('tasksGrid').addEventListener('click', async e => {
    const btn = e.target.closest('[data-action]');
    if (!btn) return;
    const id = parseInt(btn.dataset.id);
    try {
        switch (btn.dataset.action) {
            case 'complete':
                await http('POST', `/tasks/${id}/complete`);
                showToast('Tâche terminée ✓', 'success');
                loadAll();
                break;
            case 'reopen':
                await http('POST', `/tasks/${id}/reopen`);
                showToast('Tâche réouverte', 'info');
                loadAll();
                break;
            case 'edit':
                openModal(id);
                break;
            case 'delete':
                if (!confirm('Supprimer cette tâche ?')) return;
                await http('DELETE', `/tasks/${id}`);
                showToast('Tâche supprimée', 'error');
                loadAll();
                break;
        }
    } catch (err) {
        showToast('Erreur : ' + err.message, 'error');
    }
});

// ─── Modal ────────────────────────────────────────────────────────────────────

async function openModal(id = null) {
    state.editingId = id;
    state.formTags  = [];

    document.getElementById('modalTitle').textContent = id ? 'Modifier la tâche' : 'Nouvelle tâche';
    document.getElementById('fTitle').value    = '';
    document.getElementById('fDesc').value     = '';
    document.getElementById('fPriority').value = 'medium';
    document.getElementById('fDueDate').value  = '';
    renderTagChips();

    if (id) {
        try {
            const t = await http('GET', `/tasks/${id}`);
            document.getElementById('fTitle').value    = t.title;
            document.getElementById('fDesc').value     = t.description ?? '';
            document.getElementById('fPriority').value = t.priority;
            document.getElementById('fDueDate').value  = t.due_date ?? '';
            state.formTags = [...(t.tags ?? [])];
            renderTagChips();
        } catch (e) {
            showToast('Impossible de charger la tâche', 'error');
            return;
        }
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
    if (!title) {
        document.getElementById('fTitle').focus();
        document.getElementById('fTitle').style.borderColor = 'var(--high)';
        setTimeout(() => document.getElementById('fTitle').style.borderColor = '', 1500);
        return;
    }

    const payload = {
        title,
        description: document.getElementById('fDesc').value.trim() || null,
        priority:    document.getElementById('fPriority').value,
        due_date:    document.getElementById('fDueDate').value || null,
        tags:        [...state.formTags],
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

function addFormTag(raw) {
    const tag = raw.trim().toLowerCase().replace(/,+$/, '');
    if (!tag || state.formTags.includes(tag)) return false;
    state.formTags.push(tag);
    renderTagChips();
    return true;
}

function renderTagChips() {
    const wrap = document.getElementById('tagWrap');
    if (!wrap) return;

    // Chips avec data-index — pas d'onclick inline
    const chips = state.formTags.map((t, i) => `
        <span class="tag-chip">
            ${esc(t)}
            <button type="button" class="rm-tag" data-index="${i}">×</button>
        </span>`).join('');

    wrap.innerHTML = chips + `<input id="tagField" class="tag-field" type="text"
        placeholder="${state.formTags.length ? '' : 'ex: travail, urgent…'}">`;

    // Event delegation sur le wrap
    wrap.querySelectorAll('.rm-tag').forEach(btn => {
        btn.addEventListener('mousedown', e => {
            e.preventDefault(); // empêche le blur du tagField de se déclencher avant
            state.formTags.splice(parseInt(btn.dataset.index), 1);
            renderTagChips();
            document.getElementById('tagField')?.focus();
        });
    });

    const field = document.getElementById('tagField');
    field.addEventListener('keydown', e => {
        if (e.key === 'Enter' || e.key === ',') {
            e.preventDefault();
            if (addFormTag(field.value)) field.value = '';
        } else if (e.key === 'Backspace' && !field.value && state.formTags.length) {
            state.formTags.pop();
            renderTagChips();
            document.getElementById('tagField')?.focus();
        }
    });
    field.addEventListener('blur', () => {
        if (field.value.trim()) addFormTag(field.value);
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
    document.querySelectorAll('.filter-btn').forEach(b =>
        b.classList.toggle('active', b.dataset.filter === filter));
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
    const inField   = e.target.matches('input, textarea, select');
    const modalOpen = document.getElementById('overlay').classList.contains('open');
    if (e.key === 'Escape') closeModal();
    if (e.key === 'n' && !inField && !modalOpen) openModal();
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter' && modalOpen) submitForm();
});

// ─── Helpers ─────────────────────────────────────────────────────────────────

function esc(s) {
    return String(s)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
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
