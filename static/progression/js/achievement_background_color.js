document.addEventListener('DOMContentLoaded', () => {
    const hexInput = document.getElementById('id_tint_color');
    if (!hexInput) return;

    const modeInput = document.getElementById('id_tint_mode');
    const calendarYearInput = document.getElementById('id_calendar_year');
    const imageInput = document.getElementById('id_image');
    const previewRoot = document.querySelector('.field-preview .readonly');
    const existingPreviewImage = previewRoot?.querySelector('img');
    const existingImageUrl = existingPreviewImage?.src || '';

    const pickerLabel = document.createElement('label');
    pickerLabel.textContent = ' Färgväljare: ';
    pickerLabel.htmlFor = 'id_tint_color_picker';

    const picker = document.createElement('input');
    picker.type = 'color';
    picker.id = 'id_tint_color_picker';
    picker.setAttribute('aria-label', 'Välj färgning');
    picker.style.marginLeft = '0.5rem';
    pickerLabel.appendChild(picker);
    hexInput.insertAdjacentElement('afterend', pickerLabel);

    let previewImage = null;
    let tintLayer = null;

    if (previewRoot) {
        const wrapper = document.createElement('span');
        wrapper.style.cssText = 'display:inline-block;position:relative;width:200px;height:250px;overflow:hidden;isolation:isolate;';

        previewImage = document.createElement('img');
        previewImage.alt = 'Bakgrund';
        previewImage.style.cssText = 'position:absolute;inset:0;width:200px;height:250px;object-fit:contain;z-index:0;';
        if (existingImageUrl) {
            previewImage.src = existingImageUrl;
        } else {
            previewImage.style.display = 'none';
        }

        tintLayer = document.createElement('span');
        tintLayer.setAttribute('aria-hidden', 'true');
        tintLayer.style.cssText = 'position:absolute;inset:0;z-index:1;mask-size:contain;-webkit-mask-size:contain;mask-repeat:no-repeat;-webkit-mask-repeat:no-repeat;mask-position:center;-webkit-mask-position:center;';

        wrapper.append(previewImage, tintLayer);
        previewRoot.replaceChildren(wrapper);
    }

    const isHex = (value) => /^#[0-9a-fA-F]{6}$/.test(value);

    const updateMask = () => {
        if (!tintLayer) return;
        const source = previewImage?.src || '';
        const maskValue = source ? `url("${source}")` : 'none';
        tintLayer.style.maskImage = maskValue;
        tintLayer.style.webkitMaskImage = maskValue;
    };

    const updateBlendMode = () => {
        if (!tintLayer) return;
        tintLayer.style.mixBlendMode = modeInput?.value || 'color';
    };

    const updateTint = (value) => {
        if (!tintLayer) return;
        const hasColor = isHex(value);
        tintLayer.style.background = hasColor ? value : 'transparent';
        tintLayer.style.display = hasColor ? '' : 'none';
    };

    const syncFromText = () => {
        const value = hexInput.value.trim();
        if (isHex(value)) picker.value = value;
        updateTint(value);
    };

    const updateAvailability = () => {
        const isYearBackground = !calendarYearInput || calendarYearInput.value.trim() !== '';
        picker.disabled = !isYearBackground;
    };

    picker.value = isHex(hexInput.value.trim()) ? hexInput.value.trim() : '#000000';
    updateMask();
    updateBlendMode();
    syncFromText();
    updateAvailability();

    picker.addEventListener('input', () => {
        hexInput.value = picker.value.toUpperCase();
        updateTint(hexInput.value);
    });

    hexInput.addEventListener('input', syncFromText);
    modeInput?.addEventListener('change', updateBlendMode);
    calendarYearInput?.addEventListener('input', updateAvailability);

    imageInput?.addEventListener('change', () => {
        const file = imageInput.files?.[0];
        if (!file || !previewImage) return;

        const reader = new FileReader();
        reader.addEventListener('load', () => {
            previewImage.src = reader.result;
            previewImage.style.display = '';
            updateMask();
        });
        reader.readAsDataURL(file);
    });
});
