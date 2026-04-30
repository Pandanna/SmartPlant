document.getElementById('avatar-input').addEventListener('change', function(e) {
    const file = e.target.files[0];

    if (!file) 
        return;

    const reader = new FileReader();

    reader.onload = function(ev) {
        const img = new Image();

        img.onload = function() {
            const canvas = document.createElement('canvas');
            const size = 256;
            canvas.width = size; canvas.height = size;
            const ctx = canvas.getContext('2d');
            const min = Math.min(img.width, img.height);
            const sx = (img.width - min) / 2;
            const sy = (img.height - min) / 2;
            ctx.drawImage(img, sx, sy, min, min, 0, 0, size, size);
            const b64 = canvas.toDataURL('image/jpeg', 0.85).split(',')[1];
            document.getElementById('avatar-data').value = b64;
            const preview = document.getElementById('avatar-preview');
            const initial = document.getElementById('avatar-initial');
            preview.src = 'data:image/jpeg;base64,' + b64;
            preview.style.display = 'block';

            if (initial) 
                initial.style.display = 'none';
        };

        img.src = ev.target.result;
    };
    
    reader.readAsDataURL(file);
});