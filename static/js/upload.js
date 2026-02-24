let selectedFile = null;

// DOM elements
const dropZone = document.getElementById("dropZone");
const pdfInput = document.getElementById("pdfInput");
const fileInfo = document.getElementById("fileInfo");
const fileName = document.getElementById("fileName");
const clearFile = document.getElementById("clearFile");
const analyzeBtn = document.getElementById("analyzeBtn");
const uploadSection = document.getElementById("uploadSection");
const loadingOverlay = document.getElementById("loadingOverlay");
const reviewSection = document.getElementById("reviewSection");
const backToUpload = document.getElementById("backToUpload");
const submitItems = document.getElementById("submitItems");

// Drop zone events
dropZone.addEventListener("click", () => pdfInput.click());

dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.classList.add("dragover");
});

dropZone.addEventListener("dragleave", () => {
    dropZone.classList.remove("dragover");
});

dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("dragover");
    const files = e.dataTransfer.files;
    if (files.length && files[0].type === "application/pdf") {
        setFile(files[0]);
    } else {
        showToast("Error", "Please drop a PDF file.", "danger");
    }
});

pdfInput.addEventListener("change", (e) => {
    if (e.target.files.length) {
        setFile(e.target.files[0]);
    }
});

clearFile.addEventListener("click", () => {
    selectedFile = null;
    pdfInput.value = "";
    fileInfo.classList.add("d-none");
    analyzeBtn.disabled = true;
});

function setFile(file) {
    selectedFile = file;
    fileName.textContent = file.name + " (" + (file.size / 1024 / 1024).toFixed(1) + " MB)";
    fileInfo.classList.remove("d-none");
    analyzeBtn.disabled = false;
}

// Analyze button
analyzeBtn.addEventListener("click", async () => {
    if (!selectedFile) return;

    const formData = new FormData();
    formData.append("file", selectedFile);

    uploadSection.classList.add("d-none");
    loadingOverlay.classList.remove("d-none");

    try {
        const response = await fetch("/api/extract", {
            method: "POST",
            body: formData,
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Extraction failed");
        }

        renderTables(data);
        loadingOverlay.classList.add("d-none");
        reviewSection.classList.remove("d-none");
        showToast("Success", "P&ID analysis complete!", "success");
    } catch (err) {
        loadingOverlay.classList.add("d-none");
        uploadSection.classList.remove("d-none");
        showToast("Error", err.message, "danger");
    }
});

// Back to upload
backToUpload.addEventListener("click", () => {
    reviewSection.classList.add("d-none");
    uploadSection.classList.remove("d-none");
});

// Render tables from extracted data
function renderTables(data) {
    renderEquipmentTable(data.major_equipment || []);
    renderInstrumentsTable(data.instruments_causes || []);
    renderSafetyTable(data.safety_devices || []);
}

function renderEquipmentTable(items) {
    const tbody = document.querySelector("#equipmentTable tbody");
    tbody.innerHTML = "";
    items.forEach((item) => {
        const row = createEditableRow([
            item.tag, item.name, item.type,
            item.upstream_equipment, item.downstream_equipment,
            item.operating_parameters, item.design_parameters,
        ]);
        tbody.appendChild(row);
    });
    document.getElementById("equipmentCount").textContent = items.length;
}

function renderInstrumentsTable(items) {
    const tbody = document.querySelector("#instrumentsTable tbody");
    tbody.innerHTML = "";
    items.forEach((item) => {
        const row = createEditableRow([
            item.tag, item.type, item.description,
            item.associated_equipment, item.position, item.line_service,
        ]);
        tbody.appendChild(row);
    });
    document.getElementById("instrumentsCount").textContent = items.length;
}

function renderSafetyTable(items) {
    const tbody = document.querySelector("#safetyTable tbody");
    tbody.innerHTML = "";
    items.forEach((item) => {
        const row = createEditableRow([
            item.tag, item.type, item.description,
            item.associated_equipment, item.position, item.line_service, item.setpoint,
        ]);
        tbody.appendChild(row);
    });
    document.getElementById("safetyCount").textContent = items.length;
}

function createEditableRow(values) {
    const tr = document.createElement("tr");
    values.forEach((val) => {
        const td = document.createElement("td");
        td.className = "editable-cell";
        const input = document.createElement("input");
        input.type = "text";
        input.value = val || "";
        td.appendChild(input);
        tr.appendChild(td);
    });
    // Delete button
    const td = document.createElement("td");
    td.className = "text-center";
    const btn = document.createElement("button");
    btn.className = "btn btn-outline-danger btn-delete-row";
    btn.innerHTML = '<i class="bi bi-trash"></i>';
    btn.addEventListener("click", () => {
        tr.remove();
        updateCounts();
    });
    td.appendChild(btn);
    tr.appendChild(td);
    return tr;
}

// Add row
function addRow(tableType) {
    let tbody, colCount;
    if (tableType === "equipment") {
        tbody = document.querySelector("#equipmentTable tbody");
        colCount = 7;
    } else if (tableType === "instruments") {
        tbody = document.querySelector("#instrumentsTable tbody");
        colCount = 6;
    } else {
        tbody = document.querySelector("#safetyTable tbody");
        colCount = 7;
    }
    const row = createEditableRow(new Array(colCount).fill(""));
    tbody.appendChild(row);
    updateCounts();
    // Focus first cell of new row
    row.querySelector("input").focus();
}

function updateCounts() {
    document.getElementById("equipmentCount").textContent =
        document.querySelectorAll("#equipmentTable tbody tr").length;
    document.getElementById("instrumentsCount").textContent =
        document.querySelectorAll("#instrumentsTable tbody tr").length;
    document.getElementById("safetyCount").textContent =
        document.querySelectorAll("#safetyTable tbody tr").length;
}

// Submit edited items
submitItems.addEventListener("click", async () => {
    const data = {
        major_equipment: collectTableData("equipmentTable", [
            "tag", "name", "type", "upstream_equipment",
            "downstream_equipment", "operating_parameters", "design_parameters",
        ]),
        instruments_causes: collectTableData("instrumentsTable", [
            "tag", "type", "description",
            "associated_equipment", "position", "line_service",
        ]),
        safety_devices: collectTableData("safetyTable", [
            "tag", "type", "description",
            "associated_equipment", "position", "line_service", "setpoint",
        ]),
        analysis_params: {
            max_pressure_gas: document.getElementById("maxPressureGas").value || "",
            max_pressure_liquid: document.getElementById("maxPressureLiquid").value || "",
            max_liquid_inventory: document.getElementById("maxLiquidInventory").value || "",
        },
    };

    try {
        const response = await fetch("/api/save-items", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
        });

        const result = await response.json();
        if (!response.ok) throw new Error(result.error);

        window.location.href = result.redirect;
    } catch (err) {
        showToast("Error", err.message, "danger");
    }
});

function collectTableData(tableId, keys) {
    const rows = document.querySelectorAll(`#${tableId} tbody tr`);
    return Array.from(rows).map((row) => {
        const inputs = row.querySelectorAll("input[type=text]");
        const obj = {};
        keys.forEach((key, i) => {
            obj[key] = inputs[i] ? inputs[i].value : "";
        });
        return obj;
    });
}

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
