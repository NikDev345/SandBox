# minify.py — run once from your project root
# pip install jsmin csscompressor

from jsmin import jsmin
from csscompressor import compress
from pathlib import Path

files_js = [
    "app/ui/assets/js/dashboard.js",
    "app/ui/assets/js/settings.js",
    "app/ui/assets/js/appearance.js",
    "app/ui/assets/js/transitions.js",
]

files_css = [
    "app/ui/assets/css/dashboard.css",
    "app/ui/assets/css/tokens.css",
    "app/ui/assets/css/animations.css",
    "app/ui/assets/css/settings.css",
    "app/ui/assets/css/layout.css",
]

print("── Backing up originals ──")
for path in files_js + files_css:
    p = Path(path)
    if not p.exists():
        print(f"  SKIP (not found): {p.name}")
        continue
    backup = p.with_suffix(p.suffix + ".backup")
    backup.write_text(p.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"  Backed up: {p.name} → {backup.name}")

print("\n── Minifying JS ──")
for path in files_js:
    p = Path(path)
    if not p.exists():
        print(f"  SKIP (not found): {p.name}")
        continue
    original = p.read_text(encoding="utf-8")
    minified = jsmin(original)
    p.write_text(minified, encoding="utf-8")
    saved = len(original) - len(minified)
    print(f"  {p.name}: {len(original):,} → {len(minified):,} bytes (saved {saved:,})")

print("\n── Minifying CSS ──")
for path in files_css:
    p = Path(path)
    if not p.exists():
        print(f"  SKIP (not found): {p.name}")
        continue
    original = p.read_text(encoding="utf-8")
    minified = compress(original)
    p.write_text(minified, encoding="utf-8")
    saved = len(original) - len(minified)
    print(f"  {p.name}: {len(original):,} → {len(minified):,} bytes (saved {saved:,})")

print("\n── Done ──")
print("If anything breaks, restore .backup files and report the error.")