function formatPlant(p) {
    const isOnline = p.last_seen ? (Date.now() - p.last_seen) < 120000 : false; 
    
    const th = p.params || {};
    const t = p.sensors.temperature;
    const h = p.sensors.humidity;
    const s = p.sensors.soil;

    let tStatus = 'ok', hStatus = 'ok', sStatus = 'ok';
    if (t != null && th.temp_min !== undefined && th.temp_max !== undefined) {
        if (t < th.temp_min || t > th.temp_max) tStatus = 'alarm';
        else if (t < th.temp_min * 1.05 || t > th.temp_max * 0.95) tStatus = 'warning';
    }
    if (h != null && th.humidity_min !== undefined && th.humidity_max !== undefined) {
        if (h < th.humidity_min || h > th.humidity_max) hStatus = 'alarm';
        else if (h < th.humidity_min * 1.05 || h > th.humidity_max * 0.95) hStatus = 'warning';
    }
    if (s != null && th.soil_min !== undefined && th.soil_max !== undefined) {
        if (s < th.soil_min || s > th.soil_max) sStatus = 'alarm';
        else if (s < th.soil_min * 1.1 || s > th.soil_max * 0.9) sStatus = 'warning';
    }

    let score = 100;
    if (tStatus === 'alarm') score -= 30; else if (tStatus === 'warning') score -= 10;
    if (hStatus === 'alarm') score -= 20; else if (hStatus === 'warning') score -= 5;
    if (sStatus === 'alarm') score -= 40; else if (sStatus === 'warning') score -= 15;
    if (!isOnline) score -= 20;
    if (t == null || h == null || s == null) score = 0; 
    
    const batt = p.sensors.battery;
    let bStatus = 'ok';
    if (batt != null) {
        if (batt < 10) { score -= 10; bStatus = 'alarm'; }
        else if (batt < 20) { score -= 5; bStatus = 'warning'; }
    }

    const hasAlarm = (tStatus === 'alarm' || hStatus === 'alarm' || sStatus === 'alarm' || bStatus === 'alarm' || !isOnline);

    let lastSeenText = 'Nessun dato';
    if (p.last_seen) {
        const mins = Math.floor((Date.now() - p.last_seen) / 60000);
        lastSeenText = mins < 2 ? 'Adesso' : mins < 60 ? `${mins} min fa` : `${Math.floor(mins/60)} h fa`;
    }

    return { ...p, isOnline, health: Math.max(0, score), hasAlarm, lastSeenText, tStatus, hStatus, sStatus, bStatus };
}

async function fetchPlantData(url, callback) {
    try {
        const res = await fetch(url, { headers: { 'Accept': 'application/json' } });
        if (!res.ok) throw new Error('Network error');
        const data = await res.json();
        callback(data);
    } catch (error) {
        console.error("Errore fetch dati:", error);
    }
}

function startPolling(url, callback, interval = 30000) {
    fetchPlantData(url, callback);
    return setInterval(() => fetchPlantData(url, callback), interval);
}