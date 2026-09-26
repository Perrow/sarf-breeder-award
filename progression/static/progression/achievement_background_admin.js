document.addEventListener("DOMContentLoaded", () => {
    const colorInput = document.getElementById("id_tint_color");
    const modeInput = document.getElementById("id_tint_mode");

    if (!colorInput || !modeInput) {
        return;
    }

    const updatePreview = () => {
        const color = colorInput.value.trim();
        document
            .querySelectorAll("[data-achievement-background-preview] [data-background-tint]")
            .forEach((tint) => {
                tint.style.background = color || "transparent";
                tint.style.mixBlendMode = modeInput.value || "color";
                tint.style.display = color ? "" : "none";
            });
    };

    colorInput.addEventListener("input", updatePreview);
    colorInput.addEventListener("change", updatePreview);
    modeInput.addEventListener("change", updatePreview);
    updatePreview();
});
