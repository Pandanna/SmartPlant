const _notifCfg = document.getElementById('js-config').dataset;
const NOTIF_URL = _notifCfg.urlHomeData;

const NOTIF_ICONS = {
    temperature: '🌡️',
    humidity:    '💧',
    soil:        '🪴',
    battery:     '🔋',
    offline:     '📡',
};

document.addEventListener('DOMContentLoaded', () => {
    const btn   = document.getElementById('notif-btn');
    const panel = document.getElementById('notif-panel');
    if (!btn || !panel) return;

    btn.addEventListener('click', (e) => {
        e.stopPropagation();
        panel.style.display = panel.style.display === 'block' ? 'none' : 'block';
    });

    document.addEventListener('click', (e) => {
        if (!panel.contains(e.target) && e.target !== btn)
            panel.style.display = 'none';
    });

    startPolling(NOTIF_URL, (data) => {
        const plantsData = data.plants || {};
        document.dispatchEvent(new CustomEvent('plantDataUpdated', { detail: plantsData }));
        renderNotifications(plantsData);
    }, 30000);
});

function formatAlarmDate(lastSeenMs) {
    if (!lastSeenMs) return '';
    const d = new Date(lastSeenMs);
    const now = new Date();
    const sameDay = d.toDateString() === now.toDateString();
    const hh = String(d.getHours()).padStart(2, '0');
    const mm = String(d.getMinutes()).padStart(2, '0');
    if (sameDay) return `${hh}:${mm}`;
    const dd = String(d.getDate()).padStart(2, '0');
    const mo = String(d.getMonth() + 1).padStart(2, '0');
    return `${dd}/${mo} ${hh}:${mm}`;
}

function computeAlarms(plantsData) {
    const alarms = [];

    Object.values(plantsData)
        .sort((a, b) => (b.last_seen || 0) - (a.last_seen || 0))
        .forEach(p => {
            const f    = formatPlant(p);
            const th   = p.params  || {};
            const s    = p.sensors || {};
            const date = formatAlarmDate(p.last_seen);

            if (!f.isOnline) {
                alarms.push({ device_id: p.device_id, plant: f.nickname, type: 'offline',
                    msg: 'Dispositivo offline', date, lastSeen: p.last_seen || 0 });
            }
            if (f.tStatus === 'alarm' && s.temperature != null) {
                const high = s.temperature > th.temp_max;
                alarms.push({ device_id: p.device_id, plant: f.nickname, type: 'temperature',
                    msg: `Temp. ${high ? 'alta' : 'bassa'}: ${s.temperature.toFixed(1)}°C (${high ? 'max ' + th.temp_max : 'min ' + th.temp_min}°C)`,
                    date, lastSeen: p.last_seen || 0 });
            }
            if (f.hStatus === 'alarm' && s.humidity != null) {
                const high = s.humidity > th.humidity_max;
                alarms.push({ device_id: p.device_id, plant: f.nickname, type: 'humidity',
                    msg: `Umidità ${high ? 'alta' : 'bassa'}: ${s.humidity.toFixed(1)}% (${high ? 'max ' + th.humidity_max : 'min ' + th.humidity_min}%)`,
                    date, lastSeen: p.last_seen || 0 });
            }
            if (f.sStatus === 'alarm' && s.soil != null) {
                const high = s.soil > th.soil_max;
                alarms.push({ device_id: p.device_id, plant: f.nickname, type: 'soil',
                    msg: `Suolo ${high ? 'saturo' : 'secco'}: ${s.soil.toFixed(1)}% (${high ? 'max ' + th.soil_max : 'min ' + th.soil_min}%)`,
                    date, lastSeen: p.last_seen || 0 });
            }
            if (f.bStatus === 'alarm' && s.battery != null) {
                alarms.push({ device_id: p.device_id, plant: f.nickname, type: 'battery',
                    msg: `Batteria scarica: ${Math.round(s.battery)}%`,
                    date, lastSeen: p.last_seen || 0 });
            }
        });

    return alarms.sort((a, b) => b.lastSeen - a.lastSeen);
}

function renderNotifications(plantsData) {
    const badge = document.getElementById('notif-badge');
    const list  = document.getElementById('notif-list');
    if (!badge || !list) return;

    const alarms = computeAlarms(plantsData);

    if (alarms.length === 0) {
        badge.style.display = 'none';
        list.innerHTML = `
            <div style="padding: 2rem 1rem; text-align: center; color: var(--muted);">
                <div style="font-size: 1.5rem; margin-bottom: 6px;">✅</div>
                <div style="font-size: 13px;">Nessun allarme attivo</div>
            </div>`;
        return;
    }

    badge.textContent   = alarms.length;
    badge.style.display = 'flex';

    list.innerHTML = alarms.map(a => `
        <a href="/pianta/${a.device_id}/" style="
            display: flex; align-items: flex-start; gap: 10px;
            padding: .65rem 1rem; border-bottom: 1px solid var(--border);
            text-decoration: none; color: inherit; transition: background .12s;
        " onmouseover="this.style.background='var(--surface)'"
           onmouseout="this.style.background=''">
            <span style="font-size: 16px; flex-shrink: 0; padding-top: 2px;">${NOTIF_ICONS[a.type]}</span>
            <div style="flex: 1; min-width: 0;">
                <div style="display: flex; justify-content: space-between; align-items: baseline; gap: 6px;">
                    <div style="font-size: 13px; font-weight: 600; color: var(--text); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${a.plant}</div>
                    ${a.date ? `<div style="font-size: 11px; color: var(--hint); flex-shrink: 0; font-family: var(--mono);">${a.date}</div>` : ''}
                </div>
                <div style="font-size: 12px; color: var(--muted); margin-top: 1px;">${a.msg}</div>
            </div>
        </a>`).join('');
}
