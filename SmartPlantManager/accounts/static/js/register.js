function strength(v) {
    const box = document.getElementById('strength-box');
    
    if (!v) {
        box.style.display = 'none';
        return;
    }

    box.style.display = 'block';

    const pwLen = v.length >= 8;
    const pwNum = /\d/.test(v);
    let level = 0;
    
    // Sicurezza della password
    if (v.length < 6)
        level = 1;

    else if (!pwLen || !pwNum)
        level = 2;

    else if (/[A-Z]/.test(v) && /[^A-Za-z0-9]/.test(v))
        level = 4;

    else
        level = 3;

    const colors = ['var(--border)', 'var(--red)', 'var(--amber)', 'var(--green)', 'var(--green)'];
    const labels = ['', 'Troppo corta', 'Debole', 'Buona', 'Ottima'];

    // Aggiorna i 4 segmenti della barra
    for (let i = 1; i <= 4; i++) {
        const bar = document.getElementById('bar-' + i);
        bar.style.background = (i <= level) ? colors[level] : 'var(--border)';
    }

    // Aggiorna l'etichetta
    const labelEl = document.getElementById('sl');
    labelEl.textContent = labels[level];
    labelEl.style.color = colors[level];
}