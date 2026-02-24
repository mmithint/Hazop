const submitBtn = document.getElementById("submitCauses");
const loadingOverlay = document.getElementById("loadingOverlay");

submitBtn.addEventListener("click", async () => {
    // Collect checked causes grouped by deviation
    const confirmedCauses = {};
    document.querySelectorAll(".accordion-item").forEach((item) => {
        const deviation = item.querySelector(".accordion-button").textContent.trim();
        // Remove the badge count from the text
        const deviationName = deviation.replace(/\s*\d+\s*$/, "").trim();
        const checked = item.querySelectorAll(".cause-check:checked");
        if (checked.length > 0) {
            confirmedCauses[deviationName] = Array.from(checked).map((cb) => cb.value);
        }
    });

    if (Object.keys(confirmedCauses).length === 0) {
        showToast("Warning", "Please select at least one cause.", "danger");
        return;
    }

    // Show loading overlay
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span> Generating Worksheet...';
    if (loadingOverlay) {
        loadingOverlay.classList.remove("d-none");
    }

    try {
        const response = await fetch("/api/confirm-causes", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ confirmed_causes: confirmedCauses }),
        });

        const result = await response.json();
        if (!response.ok) throw new Error(result.error || "Worksheet generation failed");

        window.location.href = result.redirect;
    } catch (err) {
        if (loadingOverlay) {
            loadingOverlay.classList.add("d-none");
        }
        submitBtn.disabled = false;
        submitBtn.innerHTML = 'Continue <i class="bi bi-arrow-right"></i>';
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
