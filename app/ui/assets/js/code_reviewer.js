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

        // Buttons
        reviewButton: document.getElementById("start-review-btn"),

        recentButton: document.getElementById("btn-recent"),

        historyButton: document.getElementById("btn-history"),

        exportButton: document.getElementById("btn-export"),

        copyButton: document.getElementById("btn-copy-review"),

        downloadButton: document.getElementById("btn-download-json"),

        reReviewButton: document.getElementById("btn-re-review"),

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

}

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
    const language = detectLanguage(file.name);

    if (!file) return;

    const content = await file.text();
    AppState.inputType = "file";
    AppState.files = [{
        name: file.name,
        path: file.name,
        content: content,
        language: language
    }];

    AppState.currentFile = AppState.files[0];

    editor.setValue(content, -1);

    updateProjectStats();

    enableReviewButton();

    detectLanguage(file.name);

    renderProjectTree();

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

    const content = AppState.currentFile.content;

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

        item.textContent = file.name;

        item.onclick = () => {

            editor.setValue(file.content, -1);

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

async function startReview() {

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

        console.log(result);

        AppState.reviewResult = result.review;

        renderReview(result.review);

    }

    catch (e) {

        console.log(JSON.stringify(e, null, 2));

        alert(e);

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

            review_type: document.getElementById("review-type").value,

            language: file.language,

            code: file.content,

            filename: file.name,

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

function renderReview(review) {

    console.log(review);

    renderSummary(review);

}

function renderSummary(review) {

    const ai = review.ai_analysis;

    if (Elements.summary) {

        let text = "";

        if (ai.summary) {

            text += ai.summary.overview || "";

            if (ai.summary.architecture) {

                text += "\n\n## Architecture\n";

                text += ai.summary.architecture;

            }

            if (ai.summary.modules?.length) {

                text += "\n\n## Modules\n";

                ai.summary.modules.forEach(module => {

                    text += `- ${module}\n`;

                });

            }

        }

        Elements.summary.innerHTML = marked.parse(text);

    }

}

}