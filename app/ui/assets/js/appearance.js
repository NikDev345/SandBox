const THEME_KEY="sandbox-theme";const ACCENT_KEY="sandbox-accent";function applyTheme(theme){document.documentElement.setAttribute("data-theme",theme);}
function setTheme(theme){console.log("Theme selected:",theme);localStorage.setItem("sandbox-theme",theme);document.documentElement.setAttribute("data-theme",theme);}
function loadTheme(){const theme=localStorage.getItem(THEME_KEY)||"dark";applyTheme(theme);}
function applyAccent(color){document.documentElement.setAttribute("data-accent",color);}
function setAccent(color){localStorage.setItem(ACCENT_KEY,color);applyAccent(color);}
function loadAccent(){const color=localStorage.getItem(ACCENT_KEY)||"white";applyAccent(color);}
window.setTheme=setTheme;window.setAccent=setAccent;window.addEventListener("DOMContentLoaded",()=>{loadTheme();loadAccent();});window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change",()=>{const theme=localStorage.getItem(THEME_KEY);if(theme==="system"){applyTheme("system");}});