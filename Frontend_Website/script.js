/* ============================================================
   VisualMatch — script.js
   Handles: upload, drag-drop, preview, API call, results
   ============================================================ */

const API_URL = "http://127.0.0.1:8000/api/validate";

// ── DOM References ─────────────────────────────────────────
const imageInput    = document.getElementById("imageInput");
const dropZone      = document.getElementById("dropZone");
const previewArea   = document.getElementById("previewArea");
const previewImg    = document.getElementById("previewImg");
const previewMeta   = document.getElementById("previewMeta");
const removeBtn     = document.getElementById("removeBtn");
const validateBtn   = document.getElementById("validateBtn");

const uploadSection  = document.querySelector(".upload-section");
const loadingSection = document.getElementById("loadingSection");
const resultsSection = document.getElementById("resultsSection");
const errorSection   = document.getElementById("errorSection");
const resultsGrid    = document.getElementById("resultsGrid");
const resultsSub     = document.getElementById("resultsSub");
const errorMsg       = document.getElementById("errorMsg");
const queryThumb     = document.getElementById("queryThumb");

let selectedFile = null;

// ── Drag & Drop ────────────────────────────────────────────
dropZone.addEventListener("click", () => imageInput.click());

dropZone.addEventListener("dragover", (e) => {
  e.preventDefault();
  dropZone.classList.add("drag-over");
});

dropZone.addEventListener("dragleave", () => {
  dropZone.classList.remove("drag-over");
});

dropZone.addEventListener("drop", (e) => {
  e.preventDefault();
  dropZone.classList.remove("drag-over");
  const file = e.dataTransfer.files[0];
  if (file && file.type.startsWith("image/")) {
    handleFileSelect(file);
  } else {
    showInlineError("Please drop a valid image file.");
  }
});

imageInput.addEventListener("change", () => {
  if (imageInput.files.length > 0) {
    handleFileSelect(imageInput.files[0]);
  }
});

// ── File Selection ─────────────────────────────────────────
function handleFileSelect(file) {
  selectedFile = file;

  const reader = new FileReader();
  reader.onload = (e) => {
    previewImg.src = e.target.result;
    dropZone.style.display = "none";
    previewArea.style.display = "flex";

    const sizeKB = (file.size / 1024).toFixed(1);
    const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
    const displaySize = file.size > 1024 * 1024 ? `${sizeMB} MB` : `${sizeKB} KB`;

    previewMeta.innerHTML = `
      <strong>${escapeHTML(file.name)}</strong>
      Type: ${file.type}<br>
      Size: ${displaySize}
    `;
  };
  reader.readAsDataURL(file);

  validateBtn.disabled = false;
}

// ── Remove Image ───────────────────────────────────────────
removeBtn.addEventListener("click", () => {
  selectedFile = null;
  imageInput.value = "";
  previewImg.src = "";
  previewArea.style.display = "none";
  dropZone.style.display = "flex";
  validateBtn.disabled = true;
});

// ── Upload & Validate ──────────────────────────────────────
async function uploadImage() {
  if (!selectedFile) return;

  queryThumb.src = previewImg.src;

  showSection("loading");

  const formData = new FormData();
  formData.append("file", selectedFile);

  try {
    const response = await fetch(API_URL, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      let detail = `Server error: ${response.status} ${response.statusText}`;
      try {
        const errData = await response.json();
        detail = errData.detail || errData.message || detail;
      } catch (_) {}
      throw new Error(detail);
    }

    const data = await response.json();

    if (!data.similar_images || !Array.isArray(data.similar_images)) {
      throw new Error("Unexpected response format from server.");
    }

    displayResults(data);

  } catch (err) {
    showError(err.message || "Unable to connect to the server. Make sure the backend is running at " + API_URL);
  }
}

// ── Display Results ────────────────────────────────────────
function displayResults(data) {
  resultsGrid.innerHTML = "";

  // ── Verdict Banner ───────────────────────────────────────
  const verdict = data.verdict || "UNKNOWN";
  const topScore = data.top_score || 0;

  const verdictColors = {
    "SAFE TO MINT": "#47ff8f",
    "MEDIUM":       "#e8ff47",
    "RISKY":        "#ffaa47",
    "NOT SAFE":     "#ff4747"
  };

  const verdictColor = verdictColors[verdict] || "#ffffff";

  const existingBanner = document.getElementById("verdictBanner");
  if (existingBanner) existingBanner.remove();

  const banner = document.createElement("div");
  banner.id = "verdictBanner";
  banner.style.cssText = `
    padding: 16px 24px;
    margin-bottom: 24px;
    border-radius: 8px;
    border: 2px solid ${verdictColor};
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: ${verdictColor}18;
  `;

  banner.innerHTML = `
    <div>
      <div style="font-size:11px; font-family:var(--font-mono); color:${verdictColor}; letter-spacing:0.15em; text-transform:uppercase; margin-bottom:4px;">Safety Verdict</div>
      <div style="font-size:24px; font-weight:800; color:${verdictColor};">${verdict}</div>
    </div>
    <div style="text-align:right;">
      <div style="font-size:11px; font-family:var(--font-mono); color:var(--muted); margin-bottom:4px;">Top similarity</div>
      <div style="font-size:32px; font-weight:800; color:${verdictColor};">${topScore}%</div>
    </div>
  `;

  resultsGrid.parentElement.insertBefore(banner, resultsGrid);

  const images = data.similar_images.slice(0, 5);

  if (images.length === 0) {
    resultsGrid.innerHTML = `
      <div style="grid-column:1/-1; text-align:center; padding:40px; color:var(--muted); font-family:var(--font-mono); font-size:13px;">
        No similar images found in the database.
      </div>
    `;
    resultsSub.textContent = "No matches found";
    showSection("results");
    return;
  }

  resultsSub.textContent = `${images.length} match${images.length !== 1 ? "es" : ""} found`;

  images.forEach((img, index) => {
    const score = typeof img.similarity_score === "number" ? img.similarity_score : 0;
    const pct   = (score * 100).toFixed(1);
    const label = getMatchLabel(score);

    const card = document.createElement("div");
    card.className = "result-card";
    card.style.animationDelay = `${0.05 + index * 0.07}s`;

    const imgSrc = img.image_url || img.path || img.url || "";
    const imgHTML = imgSrc
      ? `<img src="${escapeHTML(imgSrc)}" alt="${escapeHTML(img.filename || "Match")}" loading="lazy" onerror="this.parentElement.innerHTML='<div class=\\'img-placeholder\\'>◈</div>'">`
      : `<div class="img-placeholder">◈</div>`;

    card.innerHTML = `
      <div class="result-rank">${index + 1}</div>
      <div class="result-img-wrap">${imgHTML}</div>
      <div class="result-body">
        <div class="result-filename">${escapeHTML(img.filename || "unknown")}</div>
        <div class="result-score-row">
          <div class="result-pct">${pct}%</div>
          <div class="result-label">${label}</div>
        </div>
        <div class="score-bar">
          <div class="score-fill" style="width:${pct}%;"></div>
        </div>
      </div>
    `;

    resultsGrid.appendChild(card);
  });

  showSection("results");
}

// ── Helpers ────────────────────────────────────────────────
function getMatchLabel(score) {
  if (score >= 0.90) return "Exact";
  if (score >= 0.75) return "High";
  if (score >= 0.55) return "Medium";
  if (score >= 0.35) return "Low";
  return "Weak";
}

function showSection(name) {
  uploadSection.style.display  = name === "upload"  ? "block" : "none";
  loadingSection.style.display = name === "loading" ? "flex"  : "none";
  resultsSection.style.display = name === "results" ? "block" : "none";
  errorSection.style.display   = name === "error"   ? "flex"  : "none";
}

function showError(msg) {
  errorMsg.textContent = msg;
  showSection("error");
}

function showInlineError(msg) {
  const toast = document.createElement("p");
  toast.style.cssText = `
    color: var(--error);
    font-family: var(--font-mono);
    font-size: 11px;
    margin-top: 8px;
  `;
  toast.textContent = msg;
  dropZone.appendChild(toast);
  setTimeout(() => toast.remove(), 3000);
}

function resetAll() {
  selectedFile = null;
  imageInput.value = "";
  previewImg.src = "";
  queryThumb.src = "";
  previewArea.style.display = "none";
  dropZone.style.display = "flex";
  validateBtn.disabled = true;
  resultsGrid.innerHTML = "";
  const existingBanner = document.getElementById("verdictBanner");
  if (existingBanner) existingBanner.remove();
  showSection("upload");
}

function escapeHTML(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// ── Init ───────────────────────────────────────────────────
showSection("upload");