function strength(v) {
  const box = document.getElementById('strength-box');
  
  // Se il campo è vuoto, nascondi l'indicatore
  if (!v) {
    box.style.display = 'none';
    return;
  }
  box.style.display = 'block';

  const pwLen = v.length >= 8;
  const pwNum = /\d/.test(v);
  
  let level = 0;
  
  // Logica di forza della password (identica al file React)
  if (v.length < 6) {
    level = 1;
  } else if (!pwLen || !pwNum) {
    level = 2;
  } else if (/[A-Z]/.test(v) && /[^A-Za-z0-9]/.test(v)) {
    level = 4;
  } else {
    level = 3;
  }

  // Colori mappati sulle variabili CSS del base.css
  const colors = ['var(--border)', 'var(--red)', 'var(--amber)', 'var(--green)', 'var(--green)'];
  const labels = ['', 'Troppo corta', 'Debole', 'Buona', 'Ottima'];

  // Aggiorna i 4 segmenti della barra
  for (let i = 1; i <= 4; i++) {
    const bar = document.getElementById('bar-' + i);
    bar.style.background = (i <= level) ? colors[level] : 'var(--border)';
  }

  // Aggiorna l'etichetta di testo
  const labelEl = document.getElementById('sl');
  labelEl.textContent = labels[level];
  labelEl.style.color = colors[level];
}