(() => {
    const dialog = document.querySelector("[data-confirm-dialog]");
    if (!dialog || typeof dialog.showModal !== "function") {
        return;
    }

    const title = dialog.querySelector("[data-confirm-dialog-title]");
    const message = dialog.querySelector("[data-confirm-dialog-message]");
    const confirmButton = dialog.querySelector("[data-confirm-dialog-confirm]");
    const cancelButtons = dialog.querySelectorAll("[data-confirm-dialog-cancel]");

    let pendingAction = null;
    let trigger = null;
    const bypassForms = new WeakSet();

    function closeDialog() {
        if (dialog.open) {
            dialog.close();
        }
    }

    function openDialog(element, action) {
        trigger = element;
        pendingAction = action;
        title.textContent = element.dataset.confirmTitle || "Bekräfta";
        message.textContent = element.dataset.confirmMessage || "";
        confirmButton.textContent = element.dataset.confirmActionLabel || "Fortsätt";
        dialog.dataset.confirmVariant = element.dataset.confirmVariant || "";
        dialog.showModal();
        confirmButton.focus();
    }

    cancelButtons.forEach((button) => {
        button.addEventListener("click", closeDialog);
    });

    dialog.addEventListener("cancel", () => {
        pendingAction = null;
    });

    dialog.addEventListener("close", () => {
        pendingAction = null;
        if (trigger && document.contains(trigger)) {
            trigger.focus();
        }
        trigger = null;
    });

    confirmButton.addEventListener("click", () => {
        const action = pendingAction;
        pendingAction = null;
        closeDialog();
        if (action) {
            action();
        }
    });

    document.addEventListener("click", (event) => {
        const element = event.target.closest("a[data-confirm-message]");
        if (!element) {
            return;
        }

        event.preventDefault();
        openDialog(element, () => {
            window.location.assign(element.href);
        });
    });

    document.addEventListener("submit", (event) => {
        const form = event.target;
        if (!(form instanceof HTMLFormElement) || !form.dataset.confirmMessage) {
            return;
        }
        if (bypassForms.has(form)) {
            bypassForms.delete(form);
            return;
        }

        event.preventDefault();
        openDialog(form, () => {
            bypassForms.add(form);
            form.requestSubmit();
        });
    });
})();
