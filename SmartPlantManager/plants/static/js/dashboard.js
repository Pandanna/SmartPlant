const _cfg = document.getElementById('js-config').dataset;
const URL_HOME_DATA = _cfg.urlHomeData;

let plantsData = {};
let currentFilter = 'all';
let searchQuery = '';

document.addEventListener('DOMContentLoaded', () => {
    updateDate();
    
    startPolling(URL_HOME_DATA, (data) => {
        plantsData = data.plants || {};
        renderDashboard();
    }, 30000);

    const searchInput = document.getElementById('search-input');
    if(searchInput) {
        searchInput.addEventListener('input', (e) => {
            searchQuery = e.target.value.toLowerCase();
            renderDashboard();
        });
    }

    document.querySelectorAll('.stat-card').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const filter = e.currentTarget.dataset.filter;
            currentFilter = (currentFilter === filter) ? 'all' : filter;
            renderDashboard();
        });
    });

    const btnClear = document.getElementById('btn-clear-filter');
    if(btnClear) {
        btnClear.addEventListener('click', () => {
            currentFilter = 'all';
            document.getElementById('search-input').value = '';
            searchQuery = '';
            renderDashboard();
        });
    }
});

function updateDate() {
    const options = { weekday: 'long', day: 'numeric', month: 'long' };
    const dateEl = document.getElementById('current-date');
    if (dateEl) dateEl.textContent = new Date().toLocaleDateString('it-IT', options);
}

function renderDashboard() {
    const grid = document.getElementById('plants-grid');
    const emptyState = document.getElementById('empty-state');
    const filterStatus = document.getElementById('filter-status');
    const statGrid = document.querySelector('.stat-grid');
    
    if (!grid) return;

    const rawPlants = Object.values(plantsData);
    if (rawPlants.length === 0) {
        grid.style.display = 'none';
        emptyState.style.display = 'block';
        if(statGrid) statGrid.style.display = 'none';
        return;
    }

    grid.style.display = 'grid';
    emptyState.style.display = 'none';
    if(statGrid) statGrid.style.display = 'grid';

    const plants = rawPlants.map(formatPlant);

    const stats = {
        all: plants.length,
        healthy: plants.filter(p => p.health >= 80).length,
        water: plants.filter(p => p.hStatus !== 'ok').length,
        alarm: plants.filter(p => p.hasAlarm).length,
        offline: plants.filter(p => !p.isOnline).length
    };

    Object.keys(stats).forEach(key => {
        const el = document.getElementById(`stat-${key}`);
        if(el) el.textContent = stats[key];
    });

    document.querySelectorAll('.stat-card').forEach(card => {
        if(card.dataset.filter === currentFilter) card.classList.add('active');
        else card.classList.remove('active');
    });

    let filtered = plants;
    if (currentFilter !== 'all') {
        if (currentFilter === 'healthy') filtered = filtered.filter(p => p.health >= 80);
        if (currentFilter === 'water') filtered = filtered.filter(p => p.hStatus !== 'ok');
        if (currentFilter === 'alarm') filtered = filtered.filter(p => p.hasAlarm);
        if (currentFilter === 'offline') filtered = filtered.filter(p => !p.isOnline);
    }
    if (searchQuery) {
        filtered = filtered.filter(p => 
            (p.nickname || '').toLowerCase().includes(searchQuery) ||
            (p.species || '').toLowerCase().includes(searchQuery)
        );
    }

    if (currentFilter !== 'all' || searchQuery) {
        filterStatus.style.display = 'flex';
        const labels = { healthy: 'In salute', water: 'Da irrigare', alarm: 'In allarme', offline: 'Offline' };
        document.getElementById('filter-name').textContent = searchQuery ? `Ricerca: "${searchQuery}"` : labels[currentFilter];
        document.getElementById('filter-count').textContent = `${filtered.length} piante`;
    } else {
        filterStatus.style.display = 'none';
    }

    grid.innerHTML = '';
    filtered.forEach(p => {
        const card = document.createElement('div');
        card.className = `plant-card ${p.hasAlarm ? 'has-alarm' : p.health < 80 ? 'has-warn' : ''}`;
        
        card.onclick = () => {
            window.location.href = `/pianta/${p.device_id}/`;
        };

        const hColor = p.health >= 80 ? 'rgba(42,99,64,.85)' : p.health >= 50 ? 'rgba(160,95,10,.85)' : 'rgba(155,36,36,.85)';
        const imgUrl = p.image ? `data:image/jpeg;base64,${p.image}` : 'https://images.unsplash.com/photo-1511489733334-b7c2d98e9af8?w=600&h=400&fit=crop&auto=format';

        card.innerHTML = `
            <div class="pc-img-wrap">
                <img src="${imgUrl}" onerror="this.style.display='none'">
                <div class="pc-gradient"></div>
                <div class="pc-device-pill">
                    <div class="dot" style="background: ${p.isOnline ? 'var(--green)' : 'var(--red)'}; ${p.isOnline ? 'animation: pulse-dot 2s infinite;' : ''}"></div>
                    <span class="pc-device-id">${p.device_id}</span>
                </div>
                <div class="health-ring" style="background: ${hColor}">
                    <span class="val">${p.health}</span><span class="pct">%</span>
                </div>
                <div class="pc-title-area">
                    <div>
                        <div class="pc-name">${p.nickname}</div>
                        <div class="pc-species">${p.species || 'Specie non specificata'}</div>
                    </div>
                </div>
            </div>
            <div class="pc-body">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-size:11px; color:var(--muted)">📍 ${p.owner}</span>
                    <span style="font-size:11px; color:${p.isOnline ? 'var(--green)' : 'var(--red)'}">${p.isOnline ? 'Online' : p.lastSeenText + ' (Offline)'}</span>
                </div>
                <div class="pc-sensor-grid">
                    <div class="pc-sensor-item ${p.tStatus}">
                        <div class="pc-sensor-label">Temp.</div>
                        <div class="pc-sensor-val">${p.sensors.temperature != null ? p.sensors.temperature.toFixed(1)+'°C' : '—'}</div>
                    </div>
                    <div class="pc-sensor-item ${p.hStatus}">
                        <div class="pc-sensor-label">Umidità Aria</div>
                        <div class="pc-sensor-val">${p.sensors.humidity != null ? p.sensors.humidity.toFixed(1)+'%' : '—'}</div>
                    </div>
                    <div class="pc-sensor-item ${p.sStatus}">
                        <div class="pc-sensor-label">Umidità Suolo</div>
                        <div class="pc-sensor-val">${p.sensors.soil != null ? p.sensors.soil.toFixed(1)+'%' : '—'}</div>
                    </div>
                    <div class="pc-sensor-item" style="cursor:pointer">
                        <div class="pc-sensor-label">Luce</div>
                        <div class="pc-sensor-val">${p.sensors.light != null ? Math.round(p.sensors.light) : '—'}</div>
                    </div>
                    <div class="pc-sensor-item ${p.bStatus || ''}">
                        <div class="pc-sensor-label">Batteria</div>
                        <div class="pc-sensor-val">${p.sensors.battery != null ? Math.round(p.sensors.battery)+'%' : '—'}</div>
                    </div>
                    <div class="pc-sensor-item">
                        <div class="pc-sensor-label">Pioggia</div>
                        <div class="pc-sensor-val" style="color:${p.sensors.rain ? 'var(--blue)' : 'inherit'}">${p.sensors.rain ? 'Sì' : 'No'}</div>
                    </div>
                </div>
            </div>
        `;
        grid.appendChild(card);
    });
}