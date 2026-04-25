const _cfg = document.getElementById('js-config').dataset;
const CSRF = _cfg.csrf;
const DEVICE_ID = _cfg.deviceId;
const URL_HOME_DATA = _cfg.urlHomeData;
const URL_SOGLIE = _cfg.urlSoglie;
const URL_IRRIGAZIONE = _cfg.urlIrrigazione;
const URL_ELIMINA = _cfg.urlElimina;
const URL_AGGIORNA = _cfg.urlAggiorna;

let currentPlant = null;
let activeTab = 'sensori';
let inlineChart = null;
let activeChartKey = null;
let newProfileImageBase64 = null;

const sunlightLabels = { 'full sun': 'Luce diretta', 'part shade': 'Parziale', 'full shade': 'Ombra' };

document.addEventListener('DOMContentLoaded', () => {
    startPolling(URL_HOME_DATA, (data) => {
        if (data.plants && data.plants[DEVICE_ID]) {
            currentPlant = formatPlant(data.plants[DEVICE_ID]);
            updateHeader();
            
            // Refresh del contenuto del tab solo se siamo nei sensori.
            if (activeTab === 'sensori') {
                renderDetailTabs();
                if (activeChartKey) showChart(activeChartKey, false);
            }
        } else {
            // Se la pianta è eliminata, torna alla home
            window.location.replace("/home/");
        }
    }, 30000);

    document.querySelectorAll('.tab').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            e.currentTarget.classList.add('active');
            activeTab = e.currentTarget.dataset.tab;
            renderDetailTabs();
        });
    });
});

function updateHeader() {
    if (!currentPlant) 
        return;

    const p = currentPlant;

    document.getElementById('det-online-dot').style.background = p.isOnline ? 'var(--green)' : 'var(--red)';
    document.getElementById('det-online-text').textContent = p.isOnline ? 'Online adesso' : `Offline (${p.lastSeenText})`;
    document.getElementById('det-online-text').style.color = p.isOnline ? 'var(--green)' : 'var(--red)';

    const ring = document.getElementById('det-health-ring');
    const hColor = p.health >= 80 ? 'var(--green)' : p.health >= 50 ? 'var(--amber)' : 'var(--red)';
    ring.style.borderColor = hColor;
    ring.style.color = hColor;
    ring.style.background = `color-mix(in srgb, ${hColor} 15%, transparent)`;
    ring.querySelector('.val').textContent = p.health;
}

function renderDetailTabs() {
    if (!currentPlant) 
        return;

    const container = document.getElementById('tab-content-container');
    const p = currentPlant;
    const th = p.params || {};

    if (activeTab === 'sensori') {
        const tVal = p.sensors.temperature != null ? p.sensors.temperature.toFixed(1) : '—';
        const hVal = p.sensors.humidity != null ? p.sensors.humidity.toFixed(1) : '—';
        const sVal = p.sensors.soil != null ? p.sensors.soil.toFixed(1) : '—';
        const lVal = p.sensors.light != null ? Math.round(p.sensors.light) : '—';
        const bVal = p.sensors.battery != null ? Math.round(p.sensors.battery) : '—';
        const rVal = p.sensors.rain ? 'Sì' : 'No';

        container.innerHTML = `
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px;">
                <div class="card card-p pc-sensor-item ${p.tStatus}" style="cursor:pointer" onclick="showChart('temperature')">
                    <div style="font-size: 11px; color: var(--muted); text-transform: uppercase; margin-bottom: 8px;">🌡 Temperatura</div>
                    <div style="font-family: var(--mono); font-size: 32px; font-weight: 400; line-height: 1;">${tVal}<span style="font-size: 14px; color: var(--muted);">°C</span></div>
                    <div style="font-size: 11px; margin-top: 8px; color: var(--hint);">Range ideale: ${th.temp_min}°C - ${th.temp_max}°C</div>
                    ${p.tStatus !== 'ok' ? `<div style="font-size: 12px; font-weight: 500; margin-top: 8px; color: var(--${p.tStatus === 'alarm' ? 'red' : 'amber'});">Valore fuori soglia</div>` : ''}
                </div>
                <div class="card card-p pc-sensor-item ${p.hStatus}" style="cursor:pointer" onclick="showChart('humidity')">
                    <div style="font-size: 11px; color: var(--muted); text-transform: uppercase; margin-bottom: 8px;">💧 Umidità Aria</div>
                    <div style="font-family: var(--mono); font-size: 32px; font-weight: 400; line-height: 1;">${hVal}<span style="font-size: 14px; color: var(--muted);">%</span></div>
                    <div style="font-size: 11px; margin-top: 8px; color: var(--hint);">Range ideale: ${th.humidity_min}% - ${th.humidity_max}%</div>
                    ${p.hStatus !== 'ok' ? `<div style="font-size: 12px; font-weight: 500; margin-top: 8px; color: var(--${p.hStatus === 'alarm' ? 'red' : 'amber'});">Valore fuori soglia</div>` : ''}
                </div>
                <div class="card card-p pc-sensor-item ${p.sStatus}" style="cursor:pointer" onclick="showChart('soil')">
                    <div style="font-size: 11px; color: var(--muted); text-transform: uppercase; margin-bottom: 8px;">🪴 Umidità Suolo</div>
                    <div style="font-family: var(--mono); font-size: 32px; font-weight: 400; line-height: 1;">${sVal}<span style="font-size: 14px; color: var(--muted);">%</span></div>
                    <div style="font-size: 11px; margin-top: 8px; color: var(--hint);">Range ideale: ${th.soil_min}% - ${th.soil_max}%</div>
                    ${p.sStatus !== 'ok' ? `<div style="font-size: 12px; font-weight: 500; margin-top: 8px; color: var(--${p.sStatus === 'alarm' ? 'red' : 'amber'});">Valore fuori soglia</div>` : ''}
                </div>
                <div class="card card-p pc-sensor-item" style="cursor:pointer" onclick="showChart('light')">
                    <div style="font-size: 11px; color: var(--muted); text-transform: uppercase; margin-bottom: 8px;">☀️ Luminosità</div>
                    <div style="font-family: var(--mono); font-size: 32px; font-weight: 400; line-height: 1;">${lVal}<span style="font-size: 14px; color: var(--muted);"> lx</span></div>
                    <div style="font-size: 11px; margin-top: 8px; color: var(--hint);">Esposizione: ${sunlightLabels[th.sunlight] || th.sunlight}</div>
                </div>
                <div class="card card-p pc-sensor-item ${p.bStatus || ''}" style="cursor:pointer" onclick="showChart('battery')">
                    <div style="font-size: 11px; color: var(--muted); text-transform: uppercase; margin-bottom: 8px;">🔋 Batteria</div>
                    <div style="font-family: var(--mono); font-size: 32px; font-weight: 400; line-height: 1;">${bVal}<span style="font-size: 14px; color: var(--muted);">%</span></div>
                    <div style="font-size: 11px; margin-top: 8px; color: var(--hint);">${p.bStatus === 'alarm' ? 'Batteria scarica!' : p.bStatus === 'warning' ? 'Batteria bassa' : 'Livello OK'}</div>
                </div>
                <div class="card card-p pc-sensor-item">
                    <div style="font-size: 11px; color: var(--muted); text-transform: uppercase; margin-bottom: 8px;">🌧️ Pioggia</div>
                    <div style="font-family: var(--mono); font-size: 32px; font-weight: 400; line-height: 1; color: ${p.sensors.rain ? 'var(--blue)' : 'inherit'};">${rVal}</div>
                    <div style="font-size: 11px; margin-top: 8px; color: var(--hint);">${p.sensors.rain ? 'Irrigazione automatica sospesa' : 'Nessuna pioggia rilevata'}</div>
                </div>
            </div>
            
            <div id="chart-container" class="card card-p" style="display: none; margin-top: 12px; border-top: 3px solid var(--green);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; flex-wrap: wrap; gap: 8px;">
                    <h3 id="chart-title" style="font-family: var(--serif); font-size: 1.1rem; margin: 0;">Storico</h3>
                    
                    <div class="time-selector" style="display: flex; gap: 4px; background: var(--surface); padding: 3px; border-radius: 8px;">
                        <button class="btn-time ${currentChartInterval === 86400000 ? 'active' : ''}" onclick="updateChartInterval(86400000, this)">1g</button>
                        <button class="btn-time ${currentChartInterval === 604800000 ? 'active' : ''}" onclick="updateChartInterval(604800000, this)">7g</button>
                        <button class="btn-time ${currentChartInterval === 2592000000 ? 'active' : ''}" onclick="updateChartInterval(2592000000, this)">30g</button>
                    </div>

                    <button class="btn btn-ghost btn-sm" onclick="closeChart()">✕</button>
                </div>

                <div id="chart-stats" style="display: flex; gap: 16px; margin-bottom: 16px; padding: 8px; background: var(--card2); border-radius: 8px; border: 1px solid var(--border);">
                    <div style="flex: 1; text-align: center;">
                        <div style="font-size: 9px; color: var(--hint); text-transform: uppercase;">Min</div>
                        <div id="stat-min" style="font-family: var(--mono); font-size: 14px; font-weight: 500;">—</div>
                    </div>
                    <div style="width: 1px; background: var(--border);"></div>
                    <div style="flex: 1; text-align: center;">
                        <div style="font-size: 9px; color: var(--hint); text-transform: uppercase;">Media</div>
                        <div id="stat-avg" style="font-family: var(--mono); font-size: 14px; font-weight: 500;">—</div>
                    </div>
                    <div style="width: 1px; background: var(--border);"></div>
                    <div style="flex: 1; text-align: center;">
                        <div style="font-size: 9px; color: var(--hint); text-transform: uppercase;">Max</div>
                        <div id="stat-max" style="font-family: var(--mono); font-size: 14px; font-weight: 500;">—</div>
                    </div>
                </div>

                <div style="height: 200px; position: relative;">
                    <canvas id="inline-chart-canvas"></canvas>
                </div>
            </div>
        `;
    } 
    else if (activeTab === 'irrigazione') {
        const isAuto = th.auto_irrigation === true;
        const lastIrr = p.last_irrigation ? new Date(p.last_irrigation).toLocaleString('it-IT', {dateStyle:'short', timeStyle:'short'}) : 'Nessun intervento';
        
        let logsHtml = '<div style="color: var(--muted); font-size: 13px; padding: 1rem 0;">Nessun intervento registrato.</div>';
        if (p.irrigation_log && p.irrigation_log.length > 0) {
            logsHtml = p.irrigation_log.slice(0, 5).map(l => `
                <div style="display: flex; justify-content: space-between; border-bottom: 1px solid var(--border); padding: 8px 0; font-size: 13px;">
                    <div>
                        <div style="font-weight: 500;">${new Date(l.ts).toLocaleString('it-IT', {dateStyle:'short', timeStyle:'short'})}</div>
                        <div style="font-size: 11px; color: var(--muted);">${l.trigger === 'manuale' ? 'Manuale' : 'Automatica'}</div>
                    </div>
                    <div style="text-align: right; color: var(--muted); font-family: var(--mono);">${l.duration}s</div>
                </div>
            `).join('');
        }

        container.innerHTML = `
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px;">
                <div class="card card-p">
                    <h3 style="font-family: var(--serif); font-size: 1.1rem; margin-bottom: 16px;">Controllo</h3>
                    
                    <div style="display: flex; align-items: center; justify-content: space-between; padding: 12px; background: var(--card2); border: 1px solid var(--border); border-radius: 10px; margin-bottom: 16px;">
                        <div>
                            <div style="font-size: 13px; font-weight: 500;">Irrigazione Automatica</div>
                            <div style="font-size: 11px; color: var(--muted); margin-top: 2px;">${isAuto ? 'Attiva (gestita dal dispositivo)' : 'Disattivata'}</div>
                        </div>
                        <label style="position:relative; width:40px; height:22px; cursor:pointer;">
                            <input type="checkbox" id="auto-irr-toggle" style="opacity:0; width:0; height:0; position:absolute;" ${isAuto ? 'checked' : ''} onchange="toggleAutoIrr(this.checked)">
                            <span style="position:absolute; inset:0; border-radius:11px; background: ${isAuto ? 'var(--green)' : 'var(--border)'}; transition: background .2s;"></span>
                            <span style="position:absolute; top:3px; left:3px; width:16px; height:16px; border-radius:50%; background:#fff; transition: transform .2s; pointer-events:none; transform: ${isAuto ? 'translateX(18px)' : 'translateX(0)'};"></span>
                        </label>
                    </div>

                    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px;">
                        <div style="width: 40px; height: 40px; border-radius: 10px; background: var(--surface); display: flex; align-items: center; justify-content: center; font-size: 20px;">🚿</div>
                        <div>
                            <div style="font-size: 11px; color: var(--muted);">Ultimo intervento</div>
                            <div style="font-size: 13px; font-weight: 500;">${lastIrr}</div>
                        </div>
                    </div>

                    <div style="margin-bottom: 16px;">
                        <label>Durata (secondi)</label>
                        <input type="number" id="irr-duration" value="30" min="5" max="300" style="max-width: 120px;">
                    </div>

                    <button class="btn btn-blue" id="btn-irrigate" style="width: 100%; justify-content: center;" onclick="avviaIrrigazione()">
                        💧 Avvia irrigazione manuale
                    </button>
                </div>

                <div class="card card-p">
                    <h3 style="font-family: var(--serif); font-size: 1.1rem; margin-bottom: 12px;">Ultimi interventi</h3>
                    ${logsHtml}
                </div>
            </div>
        `;
    }
    else if (activeTab === 'impostazioni') {
        container.innerHTML = `
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px;">
                <div class="card card-p">
                    <h3 style="font-family: var(--serif); font-size: 1.1rem; margin-bottom: 16px;">Soglie Allarme</h3>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 12px;">
                        <div>
                            <label>Temp. Min (°C)</label>
                            <input type="number" id="cfg-tmin" value="${th.temp_min !== undefined ? th.temp_min : 15}">
                        </div>
                        <div>
                            <label>Temp. Max (°C)</label>
                            <input type="number" id="cfg-tmax" value="${th.temp_max !== undefined ? th.temp_max : 30}">
                        </div>
                        <div>
                            <label>Umidità Min (%)</label>
                            <input type="number" id="cfg-hmin" value="${th.humidity_min !== undefined ? th.humidity_min : 40}">
                        </div>
                        <div>
                            <label>Umidità Aria Max (%)</label>
                            <input type="number" id="cfg-hmax" value="${th.humidity_max !== undefined ? th.humidity_max : 70}">
                        </div>
                        <div>
                            <label>Umidità Suolo Min (%)</label>
                            <input type="number" id="cfg-smin" value="${th.soil_min !== undefined ? th.soil_min : 30}">
                        </div>
                        <div>
                            <label>Umidità Suolo Max (%)</label>
                            <input type="number" id="cfg-smax" value="${th.soil_max !== undefined ? th.soil_max : 80}">
                        </div>
                    </div>
                </div>

                <div class="card card-p">
                    <h3 style="font-family: var(--serif); font-size: 1.1rem; margin-bottom: 16px;">Preferenze Cura</h3>
                    <div style="margin-bottom: 12px;">
                        <label>Esposizione alla luce</label>
                        <select id="cfg-sun" style="width: 100%; padding: .75rem 1rem; border: 1px solid var(--border); border-radius: 10px; font-family: var(--sans); font-size: .95rem; background: var(--surface); color: var(--text); outline: none;">
                            <option value="full sun" ${th.sunlight === 'full sun' ? 'selected' : ''}>Luce diretta</option>
                            <option value="part shade" ${th.sunlight === 'part shade' ? 'selected' : ''}>Parziale</option>
                            <option value="full shade" ${th.sunlight === 'full shade' ? 'selected' : ''}>Ombra</option>
                        </select>
                    </div>
                    <div style="margin-bottom: 16px;">
                        <label>Frequenza irrigazione</label>
                        <select id="cfg-water" style="width: 100%; padding: .75rem 1rem; border: 1px solid var(--border); border-radius: 10px; font-family: var(--sans); font-size: .95rem; background: var(--surface); color: var(--text); outline: none;">
                            <option value="frequent" ${th.watering === 'frequent' ? 'selected' : ''}>Frequente</option>
                            <option value="average" ${th.watering === 'average' ? 'selected' : ''}>Moderata</option>
                            <option value="minimum" ${th.watering === 'minimum' ? 'selected' : ''}>Scarsa</option>
                            <option value="none" ${th.watering === 'none' ? 'selected' : ''}>Minima</option>
                        </select>
                    </div>
                    <button class="btn btn-primary" id="btn-save-cfg" style="width: 100%; justify-content: center;" onclick="salvaSoglie()">Salva Impostazioni</button>
                </div>
            </div>
        `;
    }
    else if (activeTab === 'profilo') {
        container.innerHTML = `
            <div class="card card-p">
                <h3 style="font-family: var(--serif); font-size: 1.1rem; margin-bottom: 16px;">Modifica Profilo</h3>
                
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 24px;">
                    <div>
                        <label>Foto della pianta</label>
                        <div class="preview-box" id="p-preview-box" onclick="document.getElementById('p-file-input').click()" style="height: 180px; width: 100%; max-width: 300px; margin-top: 8px;">
                            <img id="p-preview-img" src="${p.image ? 'data:image/jpeg;base64,' + p.image : 'https://images.unsplash.com/photo-1511489733334-b7c2d98e9af8?w=600&h=400&fit=crop&auto=format'}" alt="Anteprima">
                            <div class="preview-overlay" style="position: absolute; inset: 0; background: rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; color: #fff; opacity: 0; transition: opacity .2s; font-size: 13px; font-weight: 500;">
                                <span>Cambia Foto</span>
                            </div>
                        </div>
                        <input type="file" id="p-file-input" accept="image/*" style="display: none" onchange="handleProfileImage(event)">
                        <p style="font-size: 11px; color: var(--muted); margin-top: 8px;">Tocca l'immagine per caricarne una nuova.</p>
                    </div>

                    <div style="display: flex; flex-direction: column; gap: 16px;">
                        <div>
                            <label>Nome (Nickname)</label>
                            <input type="text" id="p-nickname" value="${p.nickname}" maxlength="80">
                        </div>
                        <div>
                            <label>Specie / Nome Comune</label>
                            <input type="text" id="p-species" value="${p.species || p.common_name}" maxlength="150">
                        </div>
                        <div style="margin-top: auto;">
                            <button class="btn btn-primary" id="btn-save-profile" style="width: 100%; justify-content: center;" onclick="salvaProfilo()">Salva Modifiche</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        const box = document.getElementById('p-preview-box');

        // opacità dell'immagine
        if (box) {
            const overlay = box.querySelector('.preview-overlay');
            box.onmouseenter = () => overlay.style.opacity = '1';
            box.onmouseleave = () => overlay.style.opacity = '0';
        }
    }
}

function handleProfileImage(e) {
    const file = e.target.files[0];

    if (!file) 
        return;

    const reader = new FileReader();

    reader.onload = ev => {
        const img = new Image();

        img.onload = () => {
            const canvas = document.createElement('canvas');
            const maxSize = 800;
            let w = img.width, h = img.height;

            if (w > maxSize || h > maxSize) {
                if (w > h) {
                    h = Math.round(h * maxSize / w); w = maxSize; 
                }
                else {
                    w = Math.round(w * maxSize / h); h = maxSize;
                }
            }

            canvas.width = w; canvas.height = h;
            canvas.getContext('2d').drawImage(img, 0, 0, w, h);
            
            const jpegDataUrl = canvas.toDataURL('image/jpeg', 0.85);
            newProfileImageBase64 = jpegDataUrl.split(',')[1];
            
            document.getElementById('p-preview-img').src = jpegDataUrl;
        };

        img.src = ev.target.result;
    };

    reader.readAsDataURL(file);
}

async function salvaProfilo() {
    const btn = document.getElementById('btn-save-profile');
    const nicknameVal = document.getElementById('p-nickname').value.trim();
    const speciesVal = document.getElementById('p-species').value.trim();

    if (!nicknameVal) 
        return alert("Il nome della pianta non può essere vuoto.");

    btn.textContent = 'Salvataggio...';
    btn.disabled = true;

    try {
        const payload = {
            device_id: DEVICE_ID,
            nickname: nicknameVal,
            species: speciesVal,
            image: newProfileImageBase64
        };

        const res = await fetch(URL_AGGIORNA, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CSRF },
            body: JSON.stringify(payload)
        });

        if (res.ok) {
            btn.textContent = '✓ Modifiche salvate';
            btn.style.background = 'var(--green)';
            
            // Aggiorna l'header e l'immagine principale senza ricaricare
            document.getElementById('det-name').textContent = nicknameVal;
            document.getElementById('det-species').textContent = speciesVal;
            if (newProfileImageBase64) {
                document.getElementById('det-img').src = 'data:image/jpeg;base64,' + newProfileImageBase64;
            }

            setTimeout(() => {
                btn.textContent = 'Salva Modifiche';
                btn.disabled = false;
                btn.style.background = '';
                newProfileImageBase64 = null;
            }, 3000);
        } 
        else { 
            throw new Error(); 
        }
    } 
    catch (error) {
        btn.textContent = '✗ Errore';
        setTimeout(() => { btn.textContent = 'Salva Modifiche'; btn.disabled = false; }, 2000);
    }
}

async function salvaSoglie() {
    const btn = document.getElementById('btn-save-cfg');
    btn.textContent = 'Salvataggio...';
    btn.disabled = true;

    try {
        const payload = {
            device_id: DEVICE_ID,
            temp_min: parseFloat(document.getElementById('cfg-tmin').value),
            temp_max: parseFloat(document.getElementById('cfg-tmax').value),
            humidity_min: parseFloat(document.getElementById('cfg-hmin').value),
            humidity_max: parseFloat(document.getElementById('cfg-hmax').value),
            soil_min: parseFloat(document.getElementById('cfg-smin')?.value || currentPlant.params.soil_min),
            soil_max: parseFloat(document.getElementById('cfg-smax')?.value || currentPlant.params.soil_max),
            sunlight: document.getElementById('cfg-sun').value,
            watering: document.getElementById('cfg-water').value,
            auto_irrigation: currentPlant.params.auto_irrigation
        };

        const res = await fetch(URL_SOGLIE, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CSRF },
            body: JSON.stringify(payload)
        });

        if (res.ok) {
            btn.textContent = '✓ Salvato';
            btn.style.background = 'var(--green)';
            btn.style.color = '#fff';
            fetchPlantData(URL_HOME_DATA, (data) => {
                if (data.plants && data.plants[DEVICE_ID]) {
                    currentPlant = formatPlant(data.plants[DEVICE_ID]);
                    updateHeader();
                    renderDetailTabs();

                    if (activeChartKey) 
                        showChart(activeChartKey, false);
                }
            });
        } 
        else { 
            throw new Error(); 
        }
    } 
    catch (error) {
        btn.textContent = '✗ Errore';
        setTimeout(() => { btn.textContent = 'Salva Impostazioni'; btn.disabled = false; }, 2000);
    }
}

async function toggleAutoIrr(isChecked) {
    const th = currentPlant.params;

    try {
        const res = await fetch(URL_SOGLIE, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CSRF },
            body: JSON.stringify({
                device_id: DEVICE_ID,
                temp_min: th.temp_min, temp_max: th.temp_max,
                humidity_min: th.humidity_min, humidity_max: th.humidity_max,
                sunlight: th.sunlight, watering: th.watering,
                auto_irrigation: isChecked
            })
        });

        if (res.ok) {
            fetchPlantData(URL_HOME_DATA, (data) => {
                if (data.plants && data.plants[DEVICE_ID]) {
                    currentPlant = formatPlant(data.plants[DEVICE_ID]);
                    updateHeader();
                    renderDetailTabs();

                    if (activeChartKey) 
                        showChart(activeChartKey, false);
                }
            });
        }
    } 
    catch (e) { 
        console.error(e); 
    }
}

async function avviaIrrigazione() {
    const btn = document.getElementById('btn-irrigate');
    const dur = parseInt(document.getElementById('irr-duration').value) || 30;
    
    btn.disabled = true;
    btn.innerHTML = '⏳ Invio comando...';
    
    try {
        const res = await fetch(URL_IRRIGAZIONE, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CSRF },
            body: JSON.stringify({ device_id: DEVICE_ID, duration: dur })
        });
        
        if (res.ok) {
            btn.innerHTML = '✓ Irrigazione avviata';
            setTimeout(() => { btn.disabled = false; btn.innerHTML = '💧 Avvia irrigazione manuale'; }, 3000);
            fetchPlantData(URL_HOME_DATA, (data) => {
                if (data.plants && data.plants[DEVICE_ID]) {
                    currentPlant = formatPlant(data.plants[DEVICE_ID]);
                    updateHeader();
                    renderDetailTabs();

                    if (activeChartKey) 
                        showChart(activeChartKey, false);
                }
            });
        } 
        else { 
            throw new Error(); 
        }
    } 
    catch (e) {
        btn.innerHTML = '✗ Errore';
        setTimeout(() => { btn.disabled = false; btn.innerHTML = '💧 Avvia irrigazione manuale'; }, 3000);
    }
}

function openDeleteModal() {
    if(confirm(`Sei sicuro di voler eliminare ${currentPlant.nickname}?`)) {
        fetch(URL_ELIMINA, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CSRF },
            body: JSON.stringify({ device_id: DEVICE_ID })
        }).then(res => {
            if(res.ok) 
                window.location.href = "/home/";
        });
    }
}

let currentChartInterval = 86400000; // Default 1 giorno

function showChart(key, smoothScroll = true, interval = null) {
    if (!currentPlant || !currentPlant.history) 
        return;
    
    activeChartKey = key;

    if (interval !== null) 
        currentChartInterval = interval;

    const container = document.getElementById('chart-container');
    const canvas = document.getElementById('inline-chart-canvas');
    
    if (container) {
        container.style.display = 'block';

        if (smoothScroll) 
            container.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    const intervalLabels = {
        86400000: 'Ultimo Giorno',
        604800000: 'Ultimi 7 Giorni',
        2592000000: 'Ultimi 30 Giorni'
    };

    const baseTitle = key === 'temperature' ? 'Temperatura (°C)' : 
                      key === 'battery' ? 'Batteria (%)' : 
                      key === 'soil' ? 'Umidità Suolo (%)' :
                      key === 'light' ? 'Luminosità (lx)' :
                      key === 'humidity' ? 'Umidità Aria (%)' :
                      'Umidità (%)';
    
    const title = `${baseTitle} - ${intervalLabels[currentChartInterval]}`;

    const color = key === 'temperature' ? '#c94f4f' : 
                  key === 'battery' ? '#2a6340' : 
                  key === 'soil' ? '#8b4513' :
                  key === 'light' ? '#e1b12c' :
                  '#4a9ed4';

    const bgColor = key === 'temperature' ? 'rgba(201,79,79,0.1)' : 
                    key === 'battery' ? 'rgba(42,99,64,0.1)' : 
                    key === 'soil' ? 'rgba(139,69,19,0.1)' :
                    key === 'light' ? 'rgba(225,177,44,0.1)' :
                    'rgba(74,158,212,0.1)';

    const unit = key === 'temperature' ? '°C' : 
                 key === 'light' ? 'lx' : '%';

    document.getElementById('chart-title').textContent = title;

    const startTime = Date.now() - currentChartInterval;
    const recent = currentPlant.history.filter(r => r.ts > startTime && r[key] !== undefined);

    // Calcolo statistiche
    if (recent.length > 0) {
        const vals = recent.map(r => r[key]);
        const min = Math.min(...vals);
        const max = Math.max(...vals);
        const avg = vals.reduce((a, b) => a + b, 0) / vals.length;

        document.getElementById('stat-min').textContent = (key === 'light' ? Math.round(min) : min.toFixed(1)) + unit;
        document.getElementById('stat-max').textContent = (key === 'light' ? Math.round(max) : max.toFixed(1)) + unit;
        document.getElementById('stat-avg').textContent = (key === 'light' ? Math.round(avg) : avg.toFixed(1)) + unit;
    } 
    else {
        document.getElementById('stat-min').textContent = '—';
        document.getElementById('stat-max').textContent = '—';
        document.getElementById('stat-avg').textContent = '—';
    }

    if (inlineChart) 
        inlineChart.destroy();

    if (typeof Chart === 'undefined') 
        return;

    // etichette temporali dinamiche
    const labelOptions = currentChartInterval <= 86400000 
        ? { hour: '2-digit', minute: '2-digit' }
        : { day: '2-digit', month: '2-digit', hour: '2-digit' };

    inlineChart = new Chart(canvas.getContext('2d'), {
        type: 'line',
        data: {
            labels: recent.map(r => new Date(r.ts).toLocaleTimeString('it-IT', labelOptions)),
            datasets: [{
                data: recent.map(r => r[key]),
                borderColor: color, backgroundColor: bgColor,
                borderWidth: 2, pointRadius: recent.length > 50 ? 0 : 2, tension: 0.4, fill: true
            }]
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: { legend: { display: false }, tooltip: { callbacks: { label: ctx => ctx.parsed.y + ' ' + unit } } },
            scales: {
                x: { ticks: { color: '#6e856e', font: { size: 10 }, maxTicksLimit: 6 }, grid: { color: '#263326' } },
                y: { 
                    min: key === 'battery' ? 0 : undefined,
                    max: key === 'battery' ? 100 : undefined,
                    ticks: { color: '#6e856e', font: { size: 10 } }, 
                    grid: { color: '#263326' } 
                }
            }
        }
    });
}

function updateChartInterval(ms, btn) {
    // Aggiorna pulsanti
    document.querySelectorAll('.btn-time').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    
    // Aggiorna grafico
    if (activeChartKey) {
        showChart(activeChartKey, false, ms);
    }
}

function closeChart() {
    document.getElementById('chart-container').style.display = 'none';
    if (inlineChart)
        inlineChart.destroy(); inlineChart = null; 
    
    activeChartKey = null;
}