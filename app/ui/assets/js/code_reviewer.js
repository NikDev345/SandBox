if (window.__CODE_REVIEWER_INITIALIZED__) {
    console.log("Code Reviewer already initialized.");
} else {

window.__CODE_REVIEWER_INITIALIZED__ = true;

/*****************************************************************
 * GLOBAL STATE
 *****************************************************************/


const AppState = {

    inputType: "snippet",

    language: "auto",

    reviewType: "general",

    projectName: "",

    files: [],

    currentFile: null,

    reviewResult: null,

    isReviewing: false,

    projectStats: {
        files: 0,
        folders: 0,
        functions: 0,
        classes: 0,
        loc: 0
    }

};

/*****************************************************************
 * DOM ELEMENTS
 *****************************************************************/

/*****************************************************************
 * INITIALIZATION
 *****************************************************************/

let editor;
waitForPage();

function waitForPage() {

    const required = [
        "editor",
        "file-upload",
        "start-review-btn"
    ];

    const ready = required.every(id => document.getElementById(id));

    if (!ready) {
        setTimeout(waitForPage, 100);
        return;
    }

    initialize();

}

let Elements = {};
function initialize(){
    Elements = {

        // Upload
        uploadTab: document.getElementById("tab-upload"),
        snippetTab: document.getElementById("tab-snippet"),

        uploadSection: document.getElementById("upload-section"),

        dropZone: document.getElementById("project-dropzone"),

        fileUpload: document.getElementById("file-upload"),

        snippetContainer: document.getElementById("snippet-dropzone"),

        snippetInput: document.getElementById("snippet-input"),

        language: document.getElementById("snippet-language"),

        activeFilePath: document.getElementById("active-file-path"),
        statTokens: document.getElementById("stat-tokens"),
        statExecTime: document.getElementById("stat-exec-time"),

        // Buttons
        reviewButton: document.getElementById("start-review-btn"),

        recentButton: document.getElementById("btn-recent"),

        historyButton: document.getElementById("btn-history"),

        exportButton: document.getElementById("btn-export"),

        copyButton: document.getElementById("btn-copy-review"),

        downloadButton: document.getElementById("btn-download-json"),

        // Editor
        editor: document.getElementById("editor"),

        // Tree
        projectTree: document.querySelector(".file-tree"),

        // Status Bar
        languageStatus: document.getElementById("status-lang"),

        cursorStatus: document.getElementById("status-cursor"),

        lineStatus: document.getElementById("status-lines"),

        encodingStatus: document.getElementById("status-encoding"),

        statFiles: document.getElementById("stat-files"),

        statFolders: document.getElementById("stat-folders"),

        statFunctions: document.getElementById("stat-functions"),

        statClasses: document.getElementById("stat-classes"),

        statLOC: document.getElementById("stat-loc"),

        summary: document.getElementById("summary"),

        overallScore: document.getElementById("overallScore"),

        grade: document.getElementById("grade"),

        verdict: document.getElementById("verdict"),

        correctnessBar: document.getElementById("correctnessBar"),
        correctnessValue: document.getElementById("correctnessValue"),

        securityBar: document.getElementById("securityBar"),
        securityValue: document.getElementById("securityValue"),

        performanceBar: document.getElementById("performanceBar"),
        performanceValue: document.getElementById("performanceValue"),

        maintainabilityBar: document.getElementById("maintainabilityBar"),
        maintainabilityValue: document.getElementById("maintainabilityValue"),

        readabilityBar: document.getElementById("readabilityBar"),
        readabilityValue: document.getElementById("readabilityValue"),

    };

    initializeEditor();
    registerEvents();
    disableReviewButton();

    document
    .getElementById("ctx-open")
    .onclick=()=>{

        const file=
            document
            .getElementById(
                "file-context-menu"
            )
            .dataset.file;

        openFile(file);

    };

    document
    .getElementById("tab-ai-report")
    .onclick = showAIReport;

    document
    .getElementById("tab-local-report")
    .onclick = showLocalReport;

    document
    .getElementById("tab-source")
    .onclick = showSourceCode;
    }

    document.addEventListener("click",()=>{
        document
        .getElementById("file-context-menu")
        .style.display="none";
    });
/*****************************************************************
 * REGISTER EVENTS
 *****************************************************************/
function showUploadMode() {

    AppState.inputType = "project";

    Elements.uploadTab.classList.add("active");
    Elements.snippetTab.classList.remove("active");

    Elements.dropZone.style.display = "flex";
    Elements.snippetContainer.style.display = "none";

}

function showSnippetMode() {

    AppState.inputType = "snippet";

    Elements.snippetTab.classList.add("active");
    Elements.uploadTab.classList.remove("active");

    Elements.dropZone.style.display = "none";
    Elements.snippetContainer.style.display = "block";
}

function languageChanged() {

    const language = Elements.language.value.toLowerCase();

    setEditorLanguage(language);

}

function registerEvents() {

    document.addEventListener("click", (e) => {

        if (e.target.closest("#tab-upload")) {
            console.log("Upload Tab");
            showUploadMode();
            return;
        }

        if (e.target.closest("#tab-snippet")) {
            console.log("Snippet Tab");
            showSnippetMode();
            return;
        }

        if (e.target.closest("#start-review-btn")) {
            startReview();
            return;
        }

    });

    Elements.fileUpload?.addEventListener(
        "change",
        handleFileUpload
    );

    Elements.language?.addEventListener(
        "change",
        languageChanged
    );

}

/*****************************************************************
 * ace EDITOR
 *****************************************************************/

function initializeEditor() {

    editor = ace.edit("editor");

    editor.setTheme("ace/theme/monokai");

    editor.session.setMode("ace/mode/python");

    editor.setOptions({

        fontSize: 14,

        showPrintMargin: false,

        wrap: true,

        tabSize: 4,

        useSoftTabs: true,

        highlightActiveLine: true
    });

    editor.session.on("change", () => {

        const lines = editor.session.getLength();

        if (Elements.lineStatus) {
            Elements.lineStatus.textContent = `${lines} Lines`;
        }

    });

}

function setEditorLanguage(language) {

    const modes = {

        python: "python",
        java: "java",
        javascript: "javascript",
        typescript: "typescript",
        html: "html",
        css: "css",
        sql: "sql",
        php: "php",
        go: "golang",
        rust: "rust",
        c: "c_cpp",
        "c++": "c_cpp",
        csharp: "csharp"

    };

    editor.session.setMode(
        "ace/mode/" + (modes[language] || "text")
    );

}


/*****************************************************************
 * BUTTON STATE
 *****************************************************************/

function disableReviewButton(){

    if (Elements.reviewButton) {
        Elements.reviewButton.disabled = true;
    }

}

function enableReviewButton(){

    if (Elements.reviewButton) {
        Elements.reviewButton.disabled = false;
    }

}

/*****************************************************************
 * EVENT HANDLERS
 *****************************************************************/

async function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    const language = detectLanguage(file.name);
    const content = await file.text();

    AppState.inputType = "file";
    AppState.files = [{
        filename: file.name,
        path: file.name,
        code: content,
        language: language
    }];

    setActiveFile(AppState.files[0]);

    updateProjectStats();
    enableReviewButton();
    renderProjectTree();

    // Update dropzone to show uploaded file info
    const lines = content.split("\n").length;
    const sizeKB = (file.size / 1024).toFixed(1);
    const ext = getFileExtension(file.name);

    const dropContent = document.getElementById("dropzone-content");
    if (dropContent) {
        dropContent.innerHTML = `
            <div class="upload-icon-ring" style="background:rgba(34,197,94,0.1);box-shadow:0 0 0 1px rgba(34,197,94,0.25);">
                <svg viewBox="0 0 24 24" style="width:28px;height:28px;stroke:#22c55e;fill:none;stroke-width:2;stroke-linecap:round;">
                    <polyline points="20 6 9 17 4 12"/>
                </svg>
            </div>
            <span class="upload-title" style="color:var(--success,#22c55e);">File ready — ${escapeHtml(file.name)}</span>
            <div style="display:flex;gap:12px;margin-top:4px;flex-wrap:wrap;justify-content:center;">
                <span class="upload-subtitle">${ext} &nbsp;·&nbsp; ${lines.toLocaleString()} lines &nbsp;·&nbsp; ${sizeKB} KB</span>
            </div>
            <span class="upload-subtitle" style="margin-top:6px;color:var(--text-muted);">Click to replace file</span>
        `;
    }
}

function detectLanguage(filename) {

    const ext = filename.split(".").pop().toLowerCase();

    const map = {
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
        css: "css"
    };

    const language = map[ext] || "text";

    Elements.language.value = language;

    setEditorLanguage(language);

    return language;
}

function updateProjectStats() {

    if (!AppState.currentFile) return;

    const content = AppState.currentFile.code;

    const lines = content.split("\n").length;

    Elements.statFiles.textContent = AppState.files.length;

    Elements.statFolders.textContent = 0;

    Elements.statFunctions.textContent =
        (content.match(/\b(function|def)\b/g) || []).length;

    Elements.statClasses.textContent =
        (content.match(/\bclass\b/g) || []).length;

    Elements.statLOC.textContent = lines;

}

function renderProjectTree() {

    if (!Elements.projectTree) return;

    Elements.projectTree.innerHTML = "";

    AppState.files.forEach(file => {

        const item = document.createElement("div");

        item.className = "tree-item";

        item.textContent = file.filename;

        item.onclick = () => {

            editor.setValue(file.code, -1);

            AppState.currentFile = file;

        };

        Elements.projectTree.appendChild(item);

    });

}

function handleFolderUpload(event){

    console.log("Folder Upload");

}

function handleZipUpload(event){

    console.log("ZIP Upload");

}

function inputTypeChanged(){

    if (!Elements.inputType) return;

    AppState.inputType = Elements.inputType.value;

}

function setReviewButtonLoading(isLoading){

    if (!Elements.reviewButton) return;

    if (isLoading) {

        if (!Elements.reviewButton.dataset.originalContent) {
            Elements.reviewButton.dataset.originalContent =
                Elements.reviewButton.innerHTML;
        }

        Elements.reviewButton.disabled = true;

        Elements.reviewButton.innerHTML = `
            <span class="btn-content">
                <span class="btn-spinner"></span> Reviewing...
            </span>
        `;

    } else {

        if (Elements.reviewButton.dataset.originalContent) {
            Elements.reviewButton.innerHTML =
                Elements.reviewButton.dataset.originalContent;
        }

        Elements.reviewButton.disabled = false;

    }

}

async function startReview() {

    if (AppState.isReviewing) return;

    AppState.isReviewing = true;
    setReviewButtonLoading(true);

    try {

        const payload = buildRequest();

        console.log(payload);

        const response = await fetch("/code-review/review", {

            method: "POST",

            credentials: "include",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify(payload)

        });

        if (!response.ok) {

            const err = await response.json();

            console.log(JSON.stringify(err, null, 2));

            alert(err.detail);

            return;

        }

        const result = await response.json();
        console.log("FULL RESULT:", result);
        console.log("META:", result.review?.meta);

        AppState.reviewResult = result.review;
        document.getElementById("upload-section").style.display = "none";
        document.getElementById("reviewer-workspace").style.display = "flex"
        renderReview(result.review);

    }

    catch (e) {

        console.log(JSON.stringify(e, null, 2));

        alert(e);

    }

    finally {

        AppState.isReviewing = false;
        setReviewButtonLoading(false);

    }

}

function buildRequest() {

    if (AppState.inputType === "snippet") {

        return {

            input_type: "snippet",

            language: Elements.language.value,

            code: editor.getValue(),

            filename: null,

            files: null,

            zip_path: null

        };

    }

    if (AppState.inputType === "file") {

        const file = AppState.currentFile;

        return {

            input_type: "file",

            review_type: "AI",

            language: file.language,

            code: file.code,

            filename: file.filename,

            files: null,

            zip_path: null

        };

    }

    if (AppState.inputType === "multiple") {

        return {

            input_type: "multiple",

            language: "auto",

            code: null,

            filename: null,

            files: AppState.files.map(file => ({

                filename: file.name,

                code: file.content

            })),

            zip_path: null

        };

    }

    if (AppState.inputType === "zip") {

        return {

            input_type: "zip",

            language: "auto",

            code: null,

            filename: null,

            files: null,

            zip_path: AppState.zipPath

        };

    }

}

function renderMeta(meta){
    if (!meta) return;

    if (Elements.statTokens) {
        Elements.statTokens.textContent = (meta.tokens ?? 0).toLocaleString();
    }

    if (Elements.statExecTime) {
        Elements.statExecTime.textContent = `${meta.exec_time ?? 0}s`;
    }
}

function renderReview(review){
    renderProjectOverview(
        review.local_analysis
    );
    renderFileTree(AppState.files);
    renderSummary(
        review
    );
    renderScore(
        review
    );
    renderLocalAnalysis(
        review.local_analysis
    );
    renderAIReport(
        review.ai_analysis
    );
    renderMeta(review.meta);
    if (AppState.files.length > 0) {      // NEW — default active file
        setActiveFile(AppState.files[0]);
    }
    showAIReport();
}

function setActiveFile(file){
    if (!file) return;

    AppState.currentFile = file;

    editor.setValue(file.code, -1);
    setEditorLanguage(file.language);

    if (Elements.activeFilePath) {
        const display = (file.path || file.filename).replace(/\//g, " / ");
        Elements.activeFilePath.textContent = display;
    }
}

function renderAIReport(ai){

    const listContainer = document.getElementById("ai-analysis-accordions");

    listContainer.innerHTML = '<div class="review-accordions"></div>';
    const wrapper = listContainer.querySelector(".review-accordions");

    renderCategory(wrapper, "Logic Bugs", ai.logic_bugs, "cat-icon-logic", "L");
    renderCategory(wrapper, "Performance", ai.performance, "cat-icon-performance", "P");
    renderCategory(wrapper, "Readability", ai.readability, "cat-icon-readability", "R");
    renderCategory(wrapper, "Best Practices", ai.best_practices, "cat-icon-best-practices", "B");
    renderCategory(wrapper, "Refactoring", ai.refactoring, "cat-icon-refactoring", "F");
    renderCategory(wrapper, "Unit Tests", ai.unit_tests, "cat-icon-tests", "T");

    renderAIOverview(ai);

}

function renderAIOverview(ai){

    const counts = { critical:0, high:0, medium:0, low:0 };

    const severityBuckets = [
        ai.logic_bugs, ai.performance, ai.readability,
        ai.best_practices, ai.refactoring
    ];

    severityBuckets.forEach(list => {
        (list || []).forEach(item => {
            const sev = (item.severity || "medium").toLowerCase();
            if (counts[sev] !== undefined) counts[sev]++;
        });
    });

    const total =
        (ai.logic_bugs || []).length +
        (ai.performance || []).length +
        (ai.readability || []).length +
        (ai.best_practices || []).length +
        (ai.refactoring || []).length +
        (ai.unit_tests || []).length;

    document.getElementById("ai-total-count").textContent = total;

    document.getElementById("ai-overview-sub").textContent =
        total === 0
            ? "No AI findings detected"
            : `${total} findings across logic, performance, readability and more`;

    document.getElementById("ai-legend-critical").textContent = counts.critical;
    document.getElementById("ai-legend-high").textContent = counts.high;
    document.getElementById("ai-legend-medium").textContent = counts.medium;
    document.getElementById("ai-legend-low").textContent = counts.low;

    const sevTotal = counts.critical + counts.high + counts.medium + counts.low;

    setAIHealthSegment("ai-seg-critical", counts.critical, sevTotal);
    setAIHealthSegment("ai-seg-high", counts.high, sevTotal);
    setAIHealthSegment("ai-seg-medium", counts.medium, sevTotal);
    setAIHealthSegment("ai-seg-low", counts.low, sevTotal);

    setAIStatTile("ai-tile-logic", "ai-stat-logic", (ai.logic_bugs || []).length);
    setAIStatTile("ai-tile-performance", "ai-stat-performance", (ai.performance || []).length);
    setAIStatTile("ai-tile-readability", "ai-stat-readability", (ai.readability || []).length);
    setAIStatTile("ai-tile-best-practices", "ai-stat-best-practices", (ai.best_practices || []).length);
    setAIStatTile("ai-tile-refactoring", "ai-stat-refactoring", (ai.refactoring || []).length);
    setAIStatTile("ai-tile-tests", "ai-stat-tests", (ai.unit_tests || []).length);
}

function setAIHealthSegment(id, count, total){
    const el = document.getElementById(id);
    const pct = total > 0 ? (count / total) * 100 : 0;
    el.style.width = pct + "%";
}

function setAIStatTile(tileId, countId, count){
    document.getElementById(countId).textContent = count;

    const tile = document.getElementById(tileId);
    tile.classList.remove("has-issues", "clean");
    tile.classList.add(count > 0 ? "has-issues" : "clean");
}

function openFile(filename){

    const file =
        AppState.files.find(
            f=>f.filename===filename
        );

    if(!file) return;

    editor.setValue(
        file.code,
        -1
    );

    setEditorLanguage(
        file.language
    );
    setActiveFile(file);
    showSourceCode();
    AppState.currentFile=file;

}

function gotoIssue(file,line){

    openFile(file);

    editor.gotoLine(
        line,
        0,
        true
    );

    editor.scrollToLine(
        line,
        true,
        true
    );

    editor.session.highlightLines(
        line-1,
        line-1,
        "ace_active-line"
    );

    editor.focus();

}

function severityColor(level){

    switch(level){

        case "critical":
            return "#ef4444";

        case "high":
            return "#f97316";

        case "medium":
            return "#facc15";

        default:
            return "#22c55e";

    }

}

function getFileExtension(file){
    if(!file)
        return "📄";
    console.log(file);
    const ext=file.split(".").pop().toLowerCase()   ;

    switch(ext){
        case "py": return "PY";
        case "java": return "JAVA";
        case "js": return "JS";
        case "ts": return "TS";
        case "cpp": return "C++";
        case "cs": return "C#";
        case "go": return "Go";
        case "php": return "PHP";
        default: return "📄";

    }

}

function renderIssueAccordions(ai){

    const container =
        document.getElementById("review-accordions");

    container.innerHTML="";

    renderCategory(
        container,
        "Logic Bugs",
        ai.logic_bugs
    );

    renderCategory(
        container,
        "Performance",
        ai.performance
    );

    renderCategory(
        container,
        "Readability",
        ai.readability
    );

    renderCategory(
        container,
        "Best Practices",
        ai.best_practices
    );

    renderCategory(
        container,
        "Refactoring",
        ai.refactoring
    );

    renderCategory(
        container,
        "Unit Tests",
        ai.unit_tests
    );

}

function renderScore(review){

    const ai = review.ai_analysis;

    let score = 100;

    score -= ai.logic_bugs.length * 8;
    score -= ai.performance.length * 5;
    score -= ai.readability.length * 2;
    score -= ai.best_practices.length * 3;
    score -= ai.refactoring.length * 2;

    score = Math.max(score,0);

    Elements.overallScore.textContent = score;

    if(score>=90){

        Elements.grade.textContent="A";

        Elements.verdict.textContent="Excellent";

    }

    else if(score>=75){

        Elements.grade.textContent="B";

        Elements.verdict.textContent="Good";

    }

    else if(score>=60){

        Elements.grade.textContent="C";

        Elements.verdict.textContent="Needs Improvement";

    }

    else{

        Elements.grade.textContent="D";

        Elements.verdict.textContent="Poor";

    }

    setProgress(
        Elements.correctnessBar,
        100-ai.logic_bugs.length*10,
        Elements.correctnessValue
    );

    setProgress(
        Elements.securityBar,
        100-review.local_analysis.security.length*10,
        Elements.securityValue
    );

    setProgress(
        Elements.performanceBar,
        100-ai.performance.length*10,
        Elements.performanceValue
    );

    setProgress(
        Elements.maintainabilityBar,
        100-ai.refactoring.length*10,
        Elements.maintainabilityValue
    );

    setProgress(
        Elements.readabilityBar,
        100-ai.readability.length*10,
        Elements.readabilityValue
    );

}

function renderProjectOverview(local) {

    const stats = local.statistics[0];

    Elements.statFiles.textContent =
        local.project_structure.total_files;

    Elements.statFolders.textContent =
        local.project_structure.folders.length;

    Elements.statFunctions.textContent =
        stats.functions;

    Elements.statClasses.textContent =
        stats.classes;

    Elements.statLOC.textContent =
        stats.total_lines;

}

function renderSummary(review) {

    const ai = review.ai_analysis;

    let html = "";

    html += "<h4>AI Review Summary</h4>";

    const total =
        ai.logic_bugs.length +
        ai.performance.length +
        ai.readability.length +
        ai.best_practices.length +
        ai.refactoring.length +
        ai.unit_tests.length;

    html += `<p>${total} findings detected.</p>`;

    Elements.summary.innerHTML = html;

}

function showAIReport(){

    document.getElementById("ai-report-view").style.display="flex";
    document.getElementById("local-report-view").style.display="none";
    document.getElementById("source-view").style.display="none";

    document.getElementById("tab-ai-report").classList.add("active");
    document.getElementById("tab-local-report").classList.remove("active");
    document.getElementById("tab-source").classList.remove("active");
}

function showLocalReport(){

    document.getElementById("ai-report-view").style.display="none";
    document.getElementById("local-report-view").style.display="flex";
    document.getElementById("source-view").style.display="none";

    document.getElementById("tab-local-report").classList.add("active");
    document.getElementById("tab-ai-report").classList.remove("active");
    document.getElementById("tab-source").classList.remove("active");
}

function showSourceCode(){
    setTimeout(()=>{
        editor.resize();
    },100);

    document.getElementById("source-view").style.display="flex";
    document.getElementById("ai-report-view").style.display="none";
    document.getElementById("local-report-view").style.display="none";

    document.getElementById("tab-source").classList.add("active");
    document.getElementById("tab-ai-report").classList.remove("active");
    document.getElementById("tab-local-report").classList.remove("active");
}

function renderCategory(container, title, issues, iconClass, iconLetter){

    issues = issues || [];

    const details = document.createElement("details");
    details.className = "review-category";
    details.open = true;

    details.innerHTML = `
    <summary>
        <div class="summary-title">
            <span class="section-icon ${iconClass || ''}">${iconLetter || title.charAt(0)}</span>
            ${title}
        </div>
        <span class="issue-count ${issues.length === 0 ? '' : 'warning'}">${issues.length}</span>
    </summary>
    <div class="category-content"></div>
    `;

    const body = details.querySelector(".category-content");

    if (issues.length === 0) {

        body.innerHTML = `
            <p class="empty-issues">
                No issues found.
            </p>
        `;

    } else {

        issues.forEach(issue => {

            const sev = (issue.severity || "medium").toLowerCase();

            const card = document.createElement("div");
            card.className = "issue-card";
            card.innerHTML = `
                <div class="issue-header">
                    <span class="severity-badge ${sev}">${issue.severity || "-"}</span>
                    <span class="issue-file">${escapeHtml(issue.file)}${issue.line ? " : Line " + issue.line : ""}</span>
                </div>
                <h5 class="issue-title">${escapeHtml(issue.issue)}</h5>
                ${issue.suggestion ? `<div class="issue-recommendation"><strong>Fix:</strong> ${escapeHtml(issue.suggestion)}</div>` : ""}
            `;
            body.appendChild(card);
        });
    }

    container.appendChild(details);
}

function renderFileTree(files){

    const tree =
        document.querySelector(".file-tree");

    tree.innerHTML="";
    console.log(files);
    files.forEach(file=>{
        console.log(file);
        tree.innerHTML += `

        <li class="tree-file">

            <div
                class="tree-item-row"
                onclick="openFile('${file.filename}')"
                oncontextmenu="showFileMenu(event,'${file.filename}')">

                <span class="file-icon">

                    ${getFileExtension(file.filename)}

                </span>

                <span>

                    ${file.filename}

                </span>

            </div>

        </li>

        `;

    });

}

function showFileMenu(
event,
filename
){

    event.preventDefault();

    const menu =
        document.getElementById(
            "file-context-menu"
        );

    menu.style.left =
        event.pageX+"px";

    menu.style.top =
        event.pageY+"px";

    menu.style.display="block";

    menu.dataset.file=filename;

}

function renderLocalAnalysis(local){

    const container = document.getElementById("local-analysis");

    container.innerHTML = '<div class="review-accordions"></div>';
    const wrapper = container.querySelector(".review-accordions");

    renderSyntaxSection(wrapper, local.syntax);
    renderSecuritySection(wrapper, local.security);
    renderDuplicatesSection(wrapper, local.duplicates);
    renderDependenciesSection(wrapper, local.dependencies);
    renderComplexity(wrapper, local.complexity);

    renderLocalOverview(local);

}

function hotspotStatus(fn){
    const complexity = fn.cyclomatic_complexity || 0;
    const nesting = fn.nesting_depth || 0;

    if (complexity > 10 || nesting > 4) return "hot";
    if (complexity > 6 || nesting > 2) return "warm";
    return "cool";
}

function renderLocalOverview(local){

    const counts = { critical:0, high:0, medium:0, low:0 };

    (local.syntax || []).forEach(() => counts.critical++);

    (local.security || []).forEach(item => {
        const sev = (item.severity || "medium").toLowerCase();
        if (counts[sev] !== undefined) counts[sev]++;
    });

    (local.duplicates || []).forEach(item => {
        const sev = (item.severity || "medium").toLowerCase();
        if (counts[sev] !== undefined) counts[sev]++;
    });

    let hotspotCount = 0;

    (local.complexity || []).forEach(file => {
        (file.functions || []).forEach(fn => {
            const status = hotspotStatus(fn);
            if (status === "hot") { counts.high++; hotspotCount++; }
            else if (status === "warm") { counts.medium++; hotspotCount++; }
        });
    });

    const totalImports = (local.dependencies || [])
        .reduce((sum, f) => sum + (f.import_count || 0), 0);

    const total = counts.critical + counts.high + counts.medium + counts.low;

    document.getElementById("local-total-count").textContent = total;

    document.getElementById("local-overview-sub").textContent =
        total === 0
            ? "No local findings detected"
            : `${total} findings across syntax, security, duplicates and dependencies`;

    document.getElementById("legend-critical-count").textContent = counts.critical;
    document.getElementById("legend-high-count").textContent = counts.high;
    document.getElementById("legend-medium-count").textContent = counts.medium;
    document.getElementById("legend-low-count").textContent = counts.low;

    setHealthSegment("seg-critical", counts.critical, total);
    setHealthSegment("seg-high", counts.high, total);
    setHealthSegment("seg-medium", counts.medium, total);
    setHealthSegment("seg-low", counts.low, total);

    setStatTile("tile-syntax", "stat-syntax-count", (local.syntax || []).length);
    setStatTile("tile-security", "stat-security-count", (local.security || []).length);
    setStatTile("tile-duplicates", "stat-duplicates-count", (local.duplicates || []).length);
    setStatTile("tile-complexity", "stat-complexity-count", hotspotCount);

    document.getElementById("stat-dependencies-count").textContent = totalImports;

    const depTile = document.getElementById("tile-dependencies");
    depTile.classList.remove("has-issues", "clean");
    depTile.classList.add("clean");
}

function setHealthSegment(id, count, total){
    const el = document.getElementById(id);
    const pct = total > 0 ? (count / total) * 100 : 0;
    el.style.width = pct + "%";
}

function setStatTile(tileId, countId, count){
    document.getElementById(countId).textContent = count;

    const tile = document.getElementById(tileId);
    tile.classList.remove("has-issues", "clean");
    tile.classList.add(count > 0 ? "has-issues" : "clean");
}

function makeAccordion(title, count){
    const details = document.createElement("details");
    details.className = "review-category";
    details.open = true;

    details.innerHTML = `
    <summary>
        <div class="summary-title">${title}</div>
        <span class="issue-count ${count === 0 ? 'success' : 'warning'}">${count}</span>
    </summary>
    <div class="category-content"></div>
    `;

    return details;
}

function emptyState(body){
    body.innerHTML = `<p class="empty-issues">No issues found.</p>`;
}

/* ---------------- Syntax ---------------- */
function renderSyntaxSection(container, items){

    items = items || [];
    const details = makeAccordion("Syntax Errors", items.length);
    const body = details.querySelector(".category-content");

    if (items.length === 0) {
        emptyState(body);
    } else {
        items.forEach(item => {
            const card = document.createElement("div");
            card.className = "issue-card";
            card.innerHTML = `
                <div class="issue-header">
                    <span class="severity-badge ${item.severity || ''}">${item.severity || "error"}</span>
                    <span class="issue-file">${item.file || ""}${item.line ? " : Line " + item.line : ""}${item.column ? ", Col " + item.column : ""}</span>
                </div>
                <h5 class="issue-title">${item.type || "Syntax Error"}</h5>
                <div class="issue-desc">${item.message || ""}</div>
                <div class="local-meta-grid">
                    <div class="local-meta-item">
                        <span class="local-meta-label">Language</span>
                        <span class="local-meta-value">${item.language || "-"}</span>
                    </div>
                </div>
            `;
            body.appendChild(card);
        });
    }

    container.appendChild(details);
}

function renderSecuritySection(container, items){

    items = items || [];
    const details = makeAccordion("Security", items.length);
    const body = details.querySelector(".category-content");

    if (items.length === 0) {
        emptyState(body);
    } else {
        items.forEach(item => {
            const card = document.createElement("div");
            card.className = "issue-card";
            card.innerHTML = `
                <div class="issue-header">
                    <span class="severity-badge ${item.severity || ''}">${item.severity || "-"}</span>
                    <span class="issue-file">${item.file || ""}${item.line ? " : Line " + item.line : ""}</span>
                </div>
                <h5 class="issue-title">${formatRuleName(item.rule)}</h5>
                <div class="issue-desc">${item.message || ""}</div>
                ${item.snippet ? `
                <div class="code-snippet-block">
                    <code>${escapeHtml(item.snippet)}</code>
                </div>` : ""}
                <div class="local-meta-grid">
                    <div class="local-meta-item">
                        <span class="local-meta-label">Language</span>
                        <span class="local-meta-value">${item.language || "-"}</span>
                    </div>
                </div>
            `;
            body.appendChild(card);
        });
    }

    container.appendChild(details);
}

function formatRuleName(rule){
    if (!rule) return "Security Finding";
    return rule
        .split("_")
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(" ");
}

function escapeHtml(str){
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
}
/* ---------------- Duplicates ---------------- */
function renderDuplicatesSection(container, items){

    items = items || [];
    const details = makeAccordion("Duplicate Code", items.length);
    const body = details.querySelector(".category-content");

    if (items.length === 0) {
        emptyState(body);
    } else {
        items.forEach(item => {
            const card = document.createElement("div");
            card.className = "issue-card";
            card.innerHTML = `
                <div class="issue-header">
                    <span class="severity-badge ${item.severity || ''}">${item.severity || "-"}</span>
                    <span class="issue-file">${item.similarity}% similar</span>
                </div>
                <div class="duplicate-pair">
                    <div class="duplicate-loc">
                        <span class="local-meta-label">File 1</span>
                        <span class="local-meta-value">${item.file1} : L${item.start_line1}-${item.end_line1}</span>
                    </div>
                    <div class="duplicate-loc">
                        <span class="local-meta-label">File 2</span>
                        <span class="local-meta-value">${item.file2} : L${item.start_line2}-${item.end_line2}</span>
                    </div>
                </div>
            `;
            body.appendChild(card);
        });
    }

    container.appendChild(details);
}

/* ---------------- Dependencies ---------------- */
function renderDependenciesSection(container, items){

    items = items || [];
    const totalImports = items.reduce((sum, f) => sum + (f.import_count || 0), 0);
    const details = makeAccordion("Dependencies", totalImports);
    const body = details.querySelector(".category-content");

    if (items.length === 0 || totalImports === 0) {
        emptyState(body);
    } else {
        items.forEach(fileEntry => {
            if (!fileEntry.imports || fileEntry.imports.length === 0) return;

            const card = document.createElement("div");
            card.className = "issue-card";

            let importsHtml = fileEntry.imports.map(imp => `
                <div class="import-row">
                    <span class="import-line">L${imp.line}</span>
                    <code class="import-statement">${imp.statement}</code>
                </div>
            `).join("");

            card.innerHTML = `
                <div class="issue-header">
                    <span class="issue-file">${fileEntry.filename}</span>
                    <span class="severity-badge">${fileEntry.import_count} imports</span>
                </div>
                <div class="import-list">${importsHtml}</div>
            `;
            body.appendChild(card);
        });
    }

    container.appendChild(details);
}


function renderComplexity(container, data){

    const card = document.createElement("div");
    card.className = "local-card complexity-card";

    let html = `
    <h4>Complexity Analysis</h4>
    <div class="table-scroll-wrapper">
    <table class="review-table">
        <thead>
            <tr>
                <th>Function</th>
                <th>Lines</th>
                <th>Complexity</th>
                <th>Nesting</th>
                <th>Status</th>
            </tr>
        </thead>
        <tbody>
    `;

    (data || []).forEach(file => {
        (file.functions || []).forEach(fn => {
            const status = hotspotStatus(fn);
            const badgeClass = status === "hot" ? "hot" : (status === "warm" ? "warm" : "cool");
            const badgeLabel = status === "hot" ? "Hot" : (status === "warm" ? "Watch" : "Fine");
            html += `
            <tr>
                <td class="cx-fn">${fn.name || "Function"}</td>
                <td>${fn.function_length}</td>
                <td>${fn.cyclomatic_complexity}</td>
                <td>${fn.nesting_depth}</td>
                <td><span class="hotspot-badge ${badgeClass}">${badgeLabel}</span></td>
            </tr>
            `;
        });
    });

    html += `</tbody></table></div>`;

    card.innerHTML = html;
    container.appendChild(card);
}

function setProgress(bar,value,label){
    value=Math.max(0,Math.min(100,value));
    bar.style.width=value+"%";
    label.textContent=value+"%";

    bar.classList.remove("warn","danger");

    if (value < 50) {
        bar.classList.add("danger");
    } else if (value < 80) {
        bar.classList.add("warn");
    }
}

}