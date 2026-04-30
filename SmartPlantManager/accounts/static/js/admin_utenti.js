// Cambio tab
const tabBtns = document.querySelectorAll('.tab-btn');
const tabContents = document.querySelectorAll('.tab-content');

function switchTab(tabName) {
    tabBtns.forEach(b => b.classList.toggle('active', b.dataset.tab === tabName));
    tabContents.forEach(c => c.classList.toggle('active', c.id === 'tab-' + tabName));
}

tabBtns.forEach(btn => btn.addEventListener('click', () => switchTab(btn.dataset.tab)));

// Ripristina tab dopo redirect
const params = new URLSearchParams(window.location.search);

if (params.get('tab') === 'dispositivi') 
    switchTab('dispositivi');

// Mostra/nascondi PIN
function togglePin(id, pin) {
    const el = document.getElementById('pin-' + id);
    el.textContent = el.textContent === '••••••' ? pin : '••••••';
}

// Filtro dispositivi
let currentDeviceFilter = 'all';

document.querySelectorAll('.device-stat-card').forEach(card => {
    card.addEventListener('click', () => {
        const filter = card.dataset.filter;
        currentDeviceFilter = currentDeviceFilter === filter ? 'all' : filter;
        applyDeviceFilter();
    });
});

function applyDeviceFilter() {
    document.querySelectorAll('.device-stat-card').forEach(c =>
        c.classList.toggle('active', c.dataset.filter === currentDeviceFilter)
    );

    document.querySelectorAll('.device-row').forEach(row => {
        let show = true;
        
        if (currentDeviceFilter === 'online')    
            show = row.dataset.online === 'true';

        if (currentDeviceFilter === 'associati') 
            show = row.dataset.associato === 'true';

        if (currentDeviceFilter === 'liberi')    
            show = row.dataset.associato === 'false';

        row.style.display = show ? '' : 'none';
    });
}