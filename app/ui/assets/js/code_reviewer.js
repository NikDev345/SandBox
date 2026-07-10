let editor = null;
let improvedEditor = null;
let reviewData = null;

const tabs = {};

document.addEventListener("DOMContentLoaded", () => {

    initializeMonaco();

    initializeEvents();

    initializeTabs();

    updateLineCount();

});

function initializeMonaco() {

    if (window.__sandbox_monaco_initialized) {
        return;
    }

    window.__sandbox_monaco_initialized = true;

    require.config({
        paths: {
            vs: "https://cdn.jsdelivr.net/npm/monaco-editor@0.52.2/min/vs"
        }
    });

    require(["vs/editor/editor.main"], () => {

        monaco.editor.defineTheme("sandbox-dark", {
            base: "vs-dark",
            inherit: true,
            rules: [],
            colors: {}
        });

        monaco.editor.defineTheme("sandbox-light", {
            base: "vs",
            inherit: true,
            rules: [],
            colors: {}
        });

        const theme =
            document.documentElement.dataset.theme === "light"
                ? "sandbox-light"
                : "sandbox-dark";

        monaco.editor.setTheme(theme);

        editor = monaco.editor.create(
            document.getElementById("editor"),
            {
                value: "",
                language: "python",
                theme,
                automaticLayout: true,
                minimap: { enabled: false },
                fontSize: 15,
                fontFamily: "JetBrains Mono",
                wordWrap: "on",
                tabSize: 4,
                scrollBeyondLastLine: false
            }
        );

        improvedEditor = monaco.editor.create(
            document.getElementById("improvedCode"),
            {
                value: "",
                language: "python",
                theme,
                readOnly: true,
                automaticLayout: true,
                minimap: { enabled: false },
                fontSize: 15,
                fontFamily: "JetBrains Mono",
                wordWrap: "on",
                scrollBeyondLastLine: false
            }
        );

        editor.onDidChangeModelContent(updateLineCount);

    });

}

function initializeEvents() {

    document
        .getElementById("reviewBtn")
        .addEventListener("click", reviewCode);

    document
        .getElementById("copyBtn")
        .addEventListener("click", copyReview);

    document
        .getElementById("downloadBtn")
        .addEventListener("click", downloadReview);

    document
        .getElementById("clearBtn")
        .addEventListener("click", clearReview);

    document
        .getElementById("codeFile")
        .addEventListener("change", uploadFile);

}

function initializeTabs() {

    document.querySelectorAll(".tab-btn").forEach(button => {

        tabs[button.dataset.tab] = button;

        button.addEventListener("click", () => {

            document
                .querySelectorAll(".tab-btn")
                .forEach(btn => btn.classList.remove("active"));

            document
                .querySelectorAll(".tab-content")
                .forEach(tab => tab.classList.remove("active"));

            button.classList.add("active");

            document
                .getElementById(button.dataset.tab + "Tab")
                .classList.add("active");

        });

    });

}

function updateLineCount() {

    if (!editor) return;

    const lines = editor.getModel().getLineCount();

    document.getElementById("lineCount").textContent =
        `${lines} Lines`;

}

async function uploadFile(event) {

    const file = event.target.files[0];

    if (!file) return;

    const text = await file.text();

    editor.setValue(text);

    const ext = file.name
        .split(".")
        .pop()
        .toLowerCase();

    const languageMap = {
        py: "python",
        java: "java",
        js: "javascript",
        ts: "typescript",
        cpp: "cpp",
        c: "c",
        cs: "csharp",
        go: "go",
        rs: "rust",
        php: "php",
        sql: "sql",
        html: "html",
        css: "css",
        json: "json"
    };

    const language =
        languageMap[ext] || "plaintext";

    monaco.editor.setModelLanguage(
        editor.getModel(),
        language
    );

    monaco.editor.setModelLanguage(
        improvedEditor.getModel(),
        language
    );

    const select =
        document.getElementById("languageSelect");

    if (select.querySelector(`option[value="${language}"]`))
        select.value = language;
    else
        select.value = "auto";

    showToast(`${file.name} loaded successfully.`, "success");

}

function showLoading(show) {

    document.getElementById("loadingCard").hidden = !show;

    document.getElementById("reviewBtn").disabled = show;

}

async function reviewCode() {

    if (!editor) return;

    const code = editor.getValue().trim();

    if (!code) {
        showToast("Please enter some code.", "error");
        return;
    }

    const language = document.getElementById("languageSelect").value;
    const reviewType = document.getElementById("reviewTypeSelect").value;

    showLoading(true);

    try {

        const response = await fetch("/code-review/review", {
            method: "POST",
            credentials: "include",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                code,
                language,
                review_type: reviewType
            })
        });

        const result = await response.json();

        if (!response.ok)
            throw new Error(result.detail || "Failed to review code.");

        reviewData = result.review;

        renderReview(reviewData);
        showToast("Code reviewed successfully.", "success");

    } catch (err) {

        console.error(err);

        showToast(err.message, "error");

    } finally {

        showLoading(false);

    }

}

function renderReview(review) {

    renderScore(review.score);

    renderSummary(review.summary);

    renderIssues(review.issues);

    renderSecurity(review.security);

    renderPerformance(review.performance);

    renderBestPractices(review.best_practices);

    renderSuggestions(review.suggestions);

    renderImprovedCode(
        review.improved_code,
        review.language
    );

    renderVerdict(review.verdict);

}

function renderScore(score) {

    document.getElementById("overallScore").textContent =
        `${(score.overall / 10).toFixed(1)}`;

    setProgress("correctnessScore", score.correctness);

    setProgress("securityScore", score.security);

    setProgress("performanceScore", score.performance);

    setProgress("maintainabilityScore", score.maintainability);

    setProgress("readabilityScore", score.readability);

}

function setProgress(id, value) {

    document.getElementById(id).style.width =
        `${value}%`;

}

function renderSummary(summary) {

    document.getElementById("summary").textContent =
        summary;

}

function renderSecurity(text) {

    document.getElementById("security").textContent =
        text;

}

function renderPerformance(text) {

    document.getElementById("performance").textContent =
        text;

}

function renderBestPractices(text) {

    document.getElementById("bestPractices").textContent =
        text;

}

function renderVerdict(text) {

    document.getElementById("verdict").textContent =
        text;

}

function renderSuggestions(items) {

    const ul =
        document.getElementById("suggestions");

    ul.innerHTML = "";

    if (!items.length) {

        ul.innerHTML = "<li>No suggestions.</li>";

        return;

    }

    items.forEach(item => {

        const li = document.createElement("li");

        li.textContent = item;

        ul.appendChild(li);

    });

}

function renderIssues(issues) {

    renderIssueList(
        "criticalIssues",
        issues.critical
    );

    renderIssueList(
        "highIssues",
        issues.high
    );

    renderIssueList(
        "mediumIssues",
        issues.medium
    );

    renderIssueList(
        "lowIssues",
        issues.low
    );

}

function renderIssueList(id, issues) {

    const ul =
        document.getElementById(id);

    ul.innerHTML = "";

    if (!issues.length) {

        ul.innerHTML =
            "<li>None</li>";

        return;

    }

    issues.forEach(issue => {

        const li =
            document.createElement("li");

        li.textContent = issue;

        ul.appendChild(li);

    });

}

function renderImprovedCode(code, language) {

    if (!improvedEditor) return;

    monaco.editor.setModelLanguage(
        improvedEditor.getModel(),
        language || "plaintext"
    );

    improvedEditor.setValue(code);

}

async function copyReview() {

    if (!reviewData) {
        showToast("No review available.", "error");
        return;
    }

    try {

        await navigator.clipboard.writeText(
            JSON.stringify(reviewData, null, 2)
        );

        showToast("Review copied to clipboard.", "success");

    } catch (err) {

        console.error(err);

        showToast("Failed to copy review.", "error");

    }

}

function downloadReview() {

    if (!reviewData) {
        showToast("No review available.", "error");
        return;
    }

    let markdown = "";

    markdown += "# Code Review\n\n";

    markdown += `**Overall Score:** ${(reviewData.score.overall / 10).toFixed(1)}/10\n\n`;

    markdown += "## Summary\n\n";
    markdown += `${reviewData.summary}\n\n`;

    markdown += "## Issues\n\n";

    markdown += "### Critical\n";
    reviewData.issues.critical.forEach(i => markdown += `- ${i}\n`);
    markdown += "\n";

    markdown += "### High\n";
    reviewData.issues.high.forEach(i => markdown += `- ${i}\n`);
    markdown += "\n";

    markdown += "### Medium\n";
    reviewData.issues.medium.forEach(i => markdown += `- ${i}\n`);
    markdown += "\n";

    markdown += "### Low\n";
    reviewData.issues.low.forEach(i => markdown += `- ${i}\n`);
    markdown += "\n";

    markdown += "## Security\n\n";
    markdown += reviewData.security + "\n\n";

    markdown += "## Performance\n\n";
    markdown += reviewData.performance + "\n\n";

    markdown += "## Best Practices\n\n";
    markdown += reviewData.best_practices + "\n\n";

    markdown += "## Suggestions\n\n";

    reviewData.suggestions.forEach(s => {
        markdown += `- ${s}\n`;
    });

    markdown += "\n";

    markdown += "## Improved Code\n\n";

    markdown += "```";
    markdown += reviewData.language;
    markdown += "\n";
    markdown += reviewData.improved_code;
    markdown += "\n```\n\n";

    markdown += "## Final Verdict\n\n";
    markdown += reviewData.verdict;

    const blob = new Blob(
        [markdown],
        {
            type: "text/markdown"
        }
    );

    const url = URL.createObjectURL(blob);

    const a = document.createElement("a");

    a.href = url;
    a.download = "code_review.md";

    document.body.appendChild(a);

    a.click();

    a.remove();

    URL.revokeObjectURL(url);
    showToast("Review downloaded successfully.", "success");

}

function clearReview() {

    reviewData = null;

    if (editor)
        editor.setValue("");

    if (improvedEditor)
        improvedEditor.setValue("");

    document.getElementById("summary").textContent = "";

    document.getElementById("security").textContent = "";

    document.getElementById("performance").textContent = "";

    document.getElementById("bestPractices").textContent = "";

    document.getElementById("verdict").textContent = "";

    document.getElementById("overallScore").textContent = "0.0";

    document.getElementById("lineCount").textContent = "0 Lines";

    [
        "criticalIssues",
        "highIssues",
        "mediumIssues",
        "lowIssues",
        "suggestions"
    ].forEach(id => {
        document.getElementById(id).innerHTML = "";
    });

    [
        "correctnessScore",
        "securityScore",
        "performanceScore",
        "maintainabilityScore",
        "readabilityScore"
    ].forEach(id => {
        document.getElementById(id).style.width = "0%";
    });

    document.getElementById("codeFile").value = "";

    showToast("Editor cleared.", "success");

}

function setEditorTheme(theme) {

    if (!window.monaco)
        return;

    monaco.editor.setTheme(
        theme === "light"
            ? "sandbox-light"
            : "sandbox-dark"
    );

}

const observer = new MutationObserver(() => {

    const theme =
        document.documentElement.dataset.theme;

    setEditorTheme(theme);

});

observer.observe(
    document.documentElement,
    {
        attributes: true,
        attributeFilter: ["data-theme"]
    }
);

window.addEventListener("resize", () => {

    if (editor)
        editor.layout();

    if (improvedEditor)
        improvedEditor.layout();

});

function showToast(message, type = "info") {
    const container = document.getElementById("toast-container");
    if (!container) return;

    const icons = {
        success: `<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>`,
        error:   `<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>`,
        info:    `<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><circle cx="12" cy="16" r="1" fill="currentColor"/></svg>`
    };

    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `${icons[type] || icons.info}<span>${escapeHtml(message)}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.classList.add("toast-exit");
        toast.addEventListener("animationend", () => toast.remove(), { once: true });
    }, 3500);
}

function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}