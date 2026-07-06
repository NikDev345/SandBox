// Tool-specific JS for AI Text Summarizer - scoped under .text-summarizer-root
(function () {

  // ─── Hidden state ─────────────────────────────────────────────────────────────
  let extractedPdfText = "";
  let pdfMeta = { filename: "", words: 0, chars: 0, uploadedAt: "" };

  // ─── Toast ────────────────────────────────────────────────────────────────────
  function toast(message, opts) {
    try {
      if (window.nicegui && typeof window.nicegui.toast === "function") {
        window.nicegui.toast(message, opts || {});
        return;
      }
    } catch (e) {}
    const id = "ts-toast";
    let el = document.getElementById(id);
    if (!el) {
      el = document.createElement("div");
      el.id = id;
      Object.assign(el.style, {
        position: "fixed", right: "16px", bottom: "16px",
        padding: "10px 14px", background: "rgba(0,0,0,0.82)",
        color: "white", borderRadius: "8px", zIndex: 99999,
        maxWidth: "320px", fontSize: "13px",
      });
      document.body.appendChild(el);
    }
    el.textContent = message;
    el.style.display = "block";
    setTimeout(() => { el.style.display = "none"; }, 3000);
  }

  // ─── Elements ─────────────────────────────────────────────────────────────────
  const root = document.querySelector(".text-summarizer-root");
  if (!root) return;

  const fileInput         = root.querySelector("#fileInput");
  const uploadInitial     = root.querySelector("#uploadInitial");
  const uploadStatus      = root.querySelector("#uploadStatus");
  const statusFileName    = root.querySelector("#statusFileName");
  const statusWords       = root.querySelector("#statusWords");
  const statusChars       = root.querySelector("#statusChars");
  const statusTime        = root.querySelector("#statusTime");
  const manualTextCard    = root.querySelector("#manualTextCard");
  const inputText         = root.querySelector("#inputText");
  const additionalInstr   = root.querySelector("#additionalInstructions");
  const summaryLength     = root.querySelector("#summaryLength");
  const summaryText       = root.querySelector("#summaryText");
  const emptyState        = root.querySelector("#emptyState");
  const textCounts        = root.querySelector("#textCounts");
  const lastSaved         = root.querySelector("#lastSaved");

  // ─── Helpers ──────────────────────────────────────────────────────────────────
  function updateCounts() {
    const v = (inputText && inputText.value) || "";
    const chars = v.length;
    const words = v.trim() ? v.trim().split(/\s+/).length : 0;
    if (textCounts) textCounts.textContent = `${chars} characters · ${words} words`;
  }

  function hasPdf() {
    return extractedPdfText.length > 0;
  }

  function authHeaders(extra) {
    const token = localStorage.getItem("access_token");
    return Object.assign(token ? { Authorization: "Bearer " + token } : {}, extra || {});
  }

  function showUploadStatus() {
    if (uploadInitial)   uploadInitial.style.display   = "none";
    if (uploadStatus)    uploadStatus.style.display    = "block";
    if (manualTextCard)  manualTextCard.style.display  = "none";
  }

  function showUploadInitial() {
    if (uploadInitial)   uploadInitial.style.display   = "block";
    if (uploadStatus)    uploadStatus.style.display    = "none";
    if (manualTextCard)  manualTextCard.style.display  = "block";
  }

  function populateStatusCard() {
    if (statusFileName) statusFileName.textContent = pdfMeta.filename;
    if (statusWords)    statusWords.textContent    = pdfMeta.words.toLocaleString();
    if (statusChars)    statusChars.textContent    = pdfMeta.chars.toLocaleString();
    if (statusTime)     statusTime.textContent     = pdfMeta.uploadedAt;
  }

  // ─── Manual text counter ──────────────────────────────────────────────────────
  if (inputText) inputText.addEventListener("input", updateCounts);

  // ─── Quick examples ───────────────────────────────────────────────────────────
  root.querySelectorAll("[data-example]").forEach((btn) => {
    btn.addEventListener("click", () => {
      if (inputText) inputText.value = btn.getAttribute("data-example") || "";
      updateCounts();
    });
  });

  // ─── Upload & Extract ─────────────────────────────────────────────────────────
  const uploadBtn = root.querySelector("[data-upload]");
  if (uploadBtn) {
    uploadBtn.addEventListener("click", async () => {
      if (!fileInput || !fileInput.files?.length) { toast("No file selected"); return; }

      const file = fileInput.files[0];
      const formData = new FormData();
      formData.append("file", file, file.name);

      uploadBtn.disabled = true;
      toast("Extracting document…");

      try {
        const res = await fetch("/summarizer/extract", {
          method: "POST",
          headers: authHeaders(),
          body: formData,
          credentials: "include",
        });
        if (!res.ok) throw new Error(await res.text());

        const data = await res.json();
        const raw  = (data.text || "").trim();

        if (!raw) { toast("Could not extract text from this file."); return; }

        // Store in memory only — never touch any textarea
        extractedPdfText = raw;
        pdfMeta = {
          filename:   file.name,
          words:      raw.trim().split(/\s+/).length,
          chars:      raw.length,
          uploadedAt: new Date().toISOString().slice(0, 19).replace("T", " ") + " UTC",
        };

        populateStatusCard();
        showUploadStatus();
        toast("Document extracted successfully");

      } catch (err) {
        toast("Failed to extract document");
        console.error(err);
      } finally {
        uploadBtn.disabled = false;
      }
    });
  }

  // ─── Remove File ──────────────────────────────────────────────────────────────
  root.addEventListener("click", (e) => {
    if (!e.target.closest("[data-remove-file]")) return;
    extractedPdfText = "";
    pdfMeta = { filename: "", words: 0, chars: 0, uploadedAt: "" };
    if (fileInput) fileInput.value = "";
    showUploadInitial();
    // Do NOT clear inputText or additionalInstructions
    toast("File removed");
  });

  // ─── Generate Summary ─────────────────────────────────────────────────────────
  const generateBtn = root.querySelector("[data-generate]");
  if (generateBtn) {
    generateBtn.addEventListener("click", async () => {
      const sourceText = hasPdf() ? extractedPdfText : (inputText?.value?.trim() || "");
      if (!sourceText) { toast("Please add text or upload a document first"); return; }

      const instructions = (additionalInstr?.value || "").trim();
      const length       = summaryLength?.value || "medium";

      const textPayload  = instructions
        ? `[Instructions: ${instructions}]\n\n${sourceText}`
        : sourceText;

      generateBtn.disabled = true;
      toast("Generating summary…");

      try {
        const res = await fetch("/summarizer/generate", {
          method: "POST",
          headers: authHeaders({ "Content-Type": "application/json" }),
          body: JSON.stringify({ text: textPayload, length }),
          credentials: "include",
        });
        if (!res.ok) throw new Error(await res.text());

        const data      = await res.json();
        const generated = data.summary || "";

        if (summaryText) summaryText.value = generated;
        if (lastSaved)   lastSaved.textContent = new Date().toISOString().slice(0, 19).replace("T", " ");
        if (emptyState)  emptyState.style.display = generated ? "none" : "flex";
        toast("Summary generated");

      } catch (err) {
        toast("Failed to generate summary");
        console.error(err);
      } finally {
        generateBtn.disabled = false;
      }
    });
  }

  // ─── Copy ─────────────────────────────────────────────────────────────────────
  const copyBtn = root.querySelector("[data-copy]");
  if (copyBtn) {
    copyBtn.addEventListener("click", async () => {
      if (!summaryText?.value) { toast("Nothing to copy"); return; }
      try {
        await navigator.clipboard.writeText(summaryText.value);
        toast("Copied to clipboard");
      } catch (e) { toast("Copy failed"); }
    });
  }

  // ─── Download PDF ─────────────────────────────────────────────────────────────
  root.querySelectorAll("[data-download]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      if (!summaryText?.value) { toast("No summary available"); return; }
      try {
        const res = await fetch("/summarizer/download", {
          method: "POST",
          headers: authHeaders({ "Content-Type": "application/json" }),
          body: JSON.stringify({ summary: summaryText.value }),
          credentials: "include",
        });
        if (!res.ok) throw new Error(await res.text());
        const blob = await res.blob();
        const url  = window.URL.createObjectURL(blob);
        const a    = document.createElement("a");
        a.href = url;
        a.download = `summary-${Date.now()}.pdf`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
        toast("PDF downloaded");
      } catch (err) {
        toast("Download failed");
        console.error(err);
      }
    });
  });

  // ─── Clear All ────────────────────────────────────────────────────────────────
  const clearBtn = root.querySelector("[data-clear]");
  if (clearBtn) {
    clearBtn.addEventListener("click", () => {
      extractedPdfText = "";
      pdfMeta = { filename: "", words: 0, chars: 0, uploadedAt: "" };
      if (fileInput)       fileInput.value       = "";
      if (inputText)       inputText.value       = "";
      if (additionalInstr) additionalInstr.value = "";
      if (summaryText)     summaryText.value     = "";
      if (emptyState)      emptyState.style.display = "flex";
      showUploadInitial();
      updateCounts();
    });
  }

  // ─── Init ─────────────────────────────────────────────────────────────────────
  updateCounts();

})();