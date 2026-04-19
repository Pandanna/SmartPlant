//  Configurazione API 
const _cfg = document.getElementById('js-config').dataset;
const CSRF = _cfg.csrf;
const URL_VALIDA = _cfg.urlValida;
const URL_ANALIZZA = _cfg.urlAnalizza;

let currentBase64 = null;
let selectedDevice = null;
let selectedPin = null;
let nickname = null;

//  Inizializzazione 
document.addEventListener('DOMContentLoaded', () => {
    // Listeners validazione Step 1
    document.getElementById('device-id-input').addEventListener('input', checkStep1);
    document.getElementById('device-pin-input').addEventListener('input', checkStep1);
    document.getElementById('nickname-input').addEventListener('input', checkStep1);

    // Gestione upload file
    document.getElementById('file-input').addEventListener('change', handleImageUpload);
});

function checkStep1() {
    const deviceOk = document.getElementById('device-id-input').value.trim().length > 0;
    const pinOk = document.getElementById('device-pin-input').value.trim().length === 6;
    const nameOk = document.getElementById('nickname-input').value.trim().length > 0;
    
    const ok = deviceOk && pinOk && nameOk;
    document.getElementById('btn-next-1').disabled = !ok;
    document.getElementById('btn-manual-1').disabled = !ok;
    
    // Se l'utente ricomincia a scrivere, nascondiamo l'errore precedente
    document.getElementById('step1-error').style.display = 'none';
}

async function validaStep1(isManual) {
    const btnNext = document.getElementById('btn-next-1');
    const btnManual = document.getElementById('btn-manual-1');
    const errBox = document.getElementById('step1-error');
    
    const deviceInput = document.getElementById('device-id-input');
    const pinInput = document.getElementById('device-pin-input');
    const nicknameInput = document.getElementById('nickname-input');
    
    if (!deviceInput || !pinInput || !nicknameInput || !errBox) {
        console.error("Elementi non trovati");
        return;
    }

    const deviceId = deviceInput.value.trim();
    const pin = pinInput.value.trim();
    const name = nicknameInput.value.trim();
    
    if (!deviceId || pin.length !== 6 || !name) {
        errBox.textContent = "Compila tutti i campi correttamente.";
        errBox.style.display = 'block';
        return;
    }

    // UI Loading
    errBox.style.display = 'none';
    btnNext.disabled = true;
    btnManual.disabled = true;
    const originalNextText = btnNext.textContent;
    btnNext.textContent = 'Verifica...';

    try {
        const res = await fetch(URL_VALIDA, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json', 
                'X-CSRFToken': CSRF || ''
            },
            body: JSON.stringify({ device_id: deviceId, pin: pin })
        });
        
        let data;
        try {
            data = await res.json();
        } catch (e) {
            throw new Error('Risposta del server non valida (JSON atteso).');
        }

        if (!res.ok) {
            throw new Error(data.error || 'Errore di validazione');
        }

        // Salvataggio globale immediato per sicurezza
        selectedDevice = deviceId;
        selectedPin = pin;
        nickname = name;

        // Se OK, procediamo
        if (isManual) {
            goToManual();
        } else {
            goToStep(2);
        }

    } catch (err) {
        errBox.textContent = err.message;
        errBox.style.display = 'block';
        btnNext.disabled = false;
        btnManual.disabled = false;
    } finally {
        if (btnNext) btnNext.textContent = originalNextText;
    }
}

//  Gestione Immagine 
function handleImageUpload(e) {
    const file = e.target.files[0]; 
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = ev => {
        const img = new Image();
        img.onload = () => {
            // Resize per non intasare l'API di Plant.id
            const canvas = document.createElement('canvas');
            const maxSize = 1200;
            let w = img.width, h = img.height;
            if (w > maxSize || h > maxSize) {
                if (w > h) { h = Math.round(h * maxSize / w); w = maxSize; }
                else       { w = Math.round(w * maxSize / h); h = maxSize; }
            }
            canvas.width = w; canvas.height = h;
            canvas.getContext('2d').drawImage(img, 0, 0, w, h);
            
            const jpegDataUrl = canvas.toDataURL('image/jpeg', 0.85);
            currentBase64 = jpegDataUrl.split(',')[1];
            
            // Aggiorna UI (Sia Step 2 che Manuale)
            const updatePreview = (pfx) => {
                const img = document.getElementById(`${pfx}preview-img`);
                const box = document.getElementById(`${pfx}preview-box`);
                const holder = document.getElementById(`${pfx}placeholder`);
                if (img) { img.src = jpegDataUrl; img.style.display = 'block'; }
                if (box) box.classList.add('has-photo');
                if (holder) holder.style.display = 'none';
            };

            updatePreview(''); 
            updatePreview('m-');
            
            document.getElementById('btn-next-2').disabled = false;
            
            // Notifica visiva solo nello step 2 se presente
            const step2Box = document.querySelector('#step-2 .preview-box');
            if (step2Box) {
                const check = step2Box.querySelector('.photo-badge');
                if (!check) {
                    const badge = document.createElement('div');
                    badge.className = 'photo-badge';
                    badge.style = "position:absolute; background:var(--green); color:white; padding:4px 8px; border-radius:10px; font-size:10px; bottom:10px; font-weight:600; text-transform:uppercase;";
                    badge.textContent = '✓ Foto acquisita';
                    step2Box.appendChild(badge);
                }
            }
        };
        img.src = ev.target.result;
    };
    reader.readAsDataURL(file);
}

//  Navigazione
function goToStep(n) {
    // Aggiorna UI Bar
    if (n <= 4) {
        document.getElementById('progress-bar').style.display = 'flex';
        for (let i = 1; i <= 4; i++) {
            const dot = document.getElementById(`dot-${i}`);
            const lbl = document.getElementById(`lbl-${i}`);
            if(dot) {
                dot.className = `step-dot ${i < n ? 'done' : i === n ? 'active' : ''}`;
                dot.textContent = i < n ? '✓' : i;
            }
            if(lbl) lbl.className = `step-label ${i === n ? 'active' : ''}`;
        }
        for (let i = 1; i <= 3; i++) {
            const line = document.getElementById(`line-${i}`);
            if(line) line.className = `step-line ${i < n ? 'done' : ''}`;
        }
    } else {
        document.getElementById('progress-bar').style.display = 'none';
    }

    // Salva stato intermedio
    if (n === 2) {
        selectedDevice = document.getElementById('device-id-input').value.trim();
        selectedPin = document.getElementById('device-pin-input').value.trim();
        nickname = document.getElementById('nickname-input').value.trim();
    }
    if (n === 3) {
        document.getElementById('sum-device').textContent = selectedDevice;
        document.getElementById('sum-nickname').textContent = nickname;
    }

    // Cambia schermata
    document.querySelectorAll('.step').forEach(s => s.classList.remove('active'));
    document.getElementById(`step-${n}`).classList.add('active');

    // Forza il ricalcolo della validità se torniamo allo step 1
    if (n === 1) checkStep1();
}

function goToManual() {
    // Assicuriamoci di prendere i valori attuali prima di cambiare schermata
    selectedDevice = document.getElementById('device-id-input').value.trim();
    selectedPin = document.getElementById('device-pin-input').value.trim();
    nickname = document.getElementById('nickname-input').value.trim();
    
    if(!selectedDevice || !selectedPin || !nickname) {
        alert("Inserisci ID dispositivo, PIN e nome della pianta prima di procedere.");
        return;
    }
    
    document.getElementById('progress-bar').style.display = 'none';
    document.querySelectorAll('.step').forEach(s => s.classList.remove('active'));
    document.getElementById('step-manual').classList.add('active');
}

//  Integrazione API 
async function startAnalysis() {
    goToStep('loading');
    
    // Rotazione etichette di caricamento
    const labels = ['Riconoscimento specie...', 'Recupero parametri...', 'Configurazione dispositivo...'];
    let li = 0;
    const interval = setInterval(() => { li = (li + 1) % labels.length; document.getElementById('loading-label').textContent = labels[li]; }, 2000);

    try {
        const res = await fetch(URL_ANALIZZA, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CSRF },
            body: JSON.stringify({ image: currentBase64, device_id: selectedDevice, pin: selectedPin, nickname: nickname })
        });
        clearInterval(interval);
        const data = await res.json();
        
        if (!res.ok || data.error) throw new Error(data.error || 'Errore sconosciuto');
        showResult(data);
    } catch(err) {
        clearInterval(interval);
        document.getElementById('error-msg').textContent = err.message || 'Errore di rete.';
        document.querySelectorAll('.step').forEach(s => s.classList.remove('active'));
        document.getElementById('step-error').classList.add('active');
        document.getElementById('progress-bar').style.display = 'none';
    }
}

async function submitManual() {
    const common = document.getElementById('m-common').value.trim();
    if (!common) return alert('Inserisci il nome della pianta.');

    goToStep('loading');
    document.getElementById('loading-label').textContent = 'Salvataggio manuale...';

    const payload = {
        device_id: selectedDevice,
        pin: selectedPin,
        nickname: nickname,
        image: currentBase64 || '',
        manual: {
            common_name: common,
            species: common,
            confidence: 0,
            params: {
                temp_min: parseFloat(document.getElementById('m-tmin').value),
                temp_max: parseFloat(document.getElementById('m-tmax').value),
                humidity_min: parseFloat(document.getElementById('m-hmin').value),
                humidity_max: parseFloat(document.getElementById('m-hmax').value),
                soil_min: parseFloat(document.getElementById('m-smin')?.value || 30),
                soil_max: parseFloat(document.getElementById('m-smax')?.value || 80),
                sunlight: document.getElementById('m-sun').value,
                watering: document.getElementById('m-water').value
            }
        }
    };

    try {
        const res = await fetch(URL_ANALIZZA, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CSRF },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (!res.ok || data.error) throw new Error(data.error || 'Errore sconosciuto');
        showResult(data);
    } catch(e) {
        document.getElementById('error-msg').textContent = e.message;
        document.querySelectorAll('.step').forEach(s => s.classList.remove('active'));
        document.getElementById('step-error').classList.add('active');
    }
}

function showResult(data) {
    const wMap = { frequent: 'Frequente', average: 'Moderata', minimum: 'Scarsa', none: 'Minima' };
    
    document.getElementById('res-common').textContent = data.common_name;
    document.getElementById('res-scientific').textContent = data.species;
    document.getElementById('res-confidence').textContent = data.confidence === 0 ? 'Manuale' : `Confidenza ${data.confidence}%`;
    
    document.getElementById('res-tmin').textContent = data.params.temp_min + ' °C';
    document.getElementById('res-tmax').textContent = data.params.temp_max + ' °C';
    document.getElementById('res-hmin').textContent = data.params.humidity_min + ' %';
    document.getElementById('res-hmax').textContent = data.params.humidity_max + ' %';
    document.getElementById('res-smin').textContent = (data.params.soil_min || '20') + ' %'; // Fallback se non dal server
    document.getElementById('res-sun').textContent = data.params.sunlight;
    
    goToStep('result'); 
    
    // forziamo manualmente l'ultimo pallino del progresso come 'fatto'
    document.getElementById('dot-4').className = 'step-dot done';
    document.getElementById('dot-4').textContent = '✓';
}

function resetAll() {
    currentBase64 = null; selectedDevice = null; selectedPin = null; nickname = null;
    document.getElementById('file-input').value = '';

    // Reset inputs
    document.getElementById('device-id-input').value = '';
    document.getElementById('device-pin-input').value = '';
    document.getElementById('nickname-input').value = '';

    // Reset Preview Step 2
    document.getElementById('preview-img').style.display = 'none';
    document.getElementById('placeholder').style.display = 'flex';
    document.getElementById('preview-box').classList.remove('has-photo');
    const badge = document.querySelector('.photo-badge');
    if (badge) badge.remove();

    // Reset Preview Manuale
    document.getElementById('m-preview-img').style.display = 'none';
    document.getElementById('m-placeholder').style.display = 'flex';
    document.getElementById('m-preview-box').classList.remove('has-photo');

    document.getElementById('btn-next-2').disabled = true;

    goToStep(1);
}