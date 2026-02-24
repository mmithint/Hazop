const otherCheckbox = document.getElementById("devOther");
const otherText = document.getElementById("otherText");
const submitBtn = document.getElementById("submitDeviations");
const loadingOverlay = document.getElementById("loadingOverlay");

// Enable/disable "Other" text input
otherCheckbox.addEventListener("change", () => {
    otherText.disabled = !otherCheckbox.checked;
    if (otherCheckbox.checked) otherText.focus();
});

// Submit deviations → generate causes
submitBtn.addEventListener("click", async () => {
    const checkboxes = document.querySelectorAll('#deviationGrid input[type="checkbox"]:checked');
    const deviations = Array.from(checkboxes)
        .map((cb) => cb.value)
        .filter((v) => v !== "Other");

    const otherVal = otherCheckbox.checked ? otherText.value.trim() : "";

    if (deviations.length === 0 && !otherVal) {
        showToast("Warning", "Please select at least one deviation.", "danger");
        return;
    }

    const payload = {
        deviations: deviations,
        other_text: otherVal,
    };

    // Show loading overlay
    loadingOverlay.classList.remove("d-none");
    submitBtn.disabled = true;

    try {
        const response = await fetch("/api/generate-causes", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });

        const result = await response.json();
        if (!response.ok) throw new Error(result.error);

        // Redirect to causes page
        window.location.href = result.redirect;
    } catch (err) {
        loadingOverlay.classList.add("d-none");
        submitBtn.disabled = false;
        showToast("Error", err.message, "danger");
    }
});

// Toast helper
function showToast(title, message, type) {
    const toast = document.getElementById("appToast");
    const toastTitle = document.getElementById("toastTitle");
    const toastBody = document.getElementById("toastBody");

    toast.className = "toast";
    if (type === "success") toast.classList.add("bg-success", "text-white");
    if (type === "danger") toast.classList.add("bg-danger", "text-white");

    toastTitle.textContent = title;
    toastBody.textContent = message;

    const bsToast = new bootstrap.Toast(toast, { delay: 4000 });
    bsToast.show();
}
