document.addEventListener("DOMContentLoaded", () => {
    const colorInput = document.getElementById("id_tint_color");
    const modeInput = document.getElementById("id_tint_mode");
    const preview = document.querySelector("[data-achievement-background-preview]");

    if (!colorInput || !modeInput || !preview) {
        return;
    }

    const updatePreview = () => {
        const color = colorInput.value.trim();
        preview.style.backgroundColor = color || "transparent";
        preview.style.backgroundBlendMode = color ? (modeInput.value || "color") : "normal";
    };

    colorInput.addEventListener("input", updatePreview);
    colorInput.addEventListener("change", updatePreview);
    modeInput.addEventListener("change", updatePreview);
    updatePreview();
});
