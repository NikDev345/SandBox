from __future__ import annotations
from app.models.docker_gen import *
from pathlib import Path
from collections import Counter
from app.services.docker_generator.utils import *
import json, re, tomllib

class DockerService:
    
    _VERSION_RE = re.compile(r"(\d+)(?:\.(\d+))?")
    
    @staticmethod
    def _scan_project(project_root: Path) -> dict:
        project_root = Path(project_root).resolve()
        
        if not project_root.exists():
            raise FileNotFoundError(f"Project root does not exist: {project_root}")
        
        if not project_root.is_dir():
            raise NotADirectoryError(f"{project_root} is not a directory")
        
        files : list[Path] = []
        directories : list[Path] = []
        extensions: Counter[str] = Counter()
        manifest_files: dict[str, Path] = {}
        
        stack = [project_root]
        
        while stack:
            curr = stack.pop()
            
            try:
                for entry in curr.iterdir():
                    if entry.is_dir():
                        if entry.name in IGNORED_DIRECTORIES:
                            continue
                        
                        directories.append(entry.relative_to(project_root))
                        stack.append(entry)
                        
                    elif entry.is_file():
                        if entry.name.startswith(".") and entry.name not in {".env", ".well-known", ".env.example", ".python-version"}:
                            continue
                        relative_path = entry.relative_to(project_root)
                        files.append(relative_path)
                        
                        ext = entry.suffix.lower()
                        if ext:
                            extensions[ext] += 1
                            
                        if entry.name in MANIFEST_FILES:
                            manifest_files[entry.name] = relative_path
            
            except (PermissionError, OSError):
                continue
            
        return {
            "root": project_root,
            "files": files,
            "directories": directories,
            "extensions": dict(extensions),
            "manifest_files": manifest_files,
        }
        
    @staticmethod
    def _detect_language(context: dict) -> str | None:
        manifest_files: dict[str, Path] = context.get("manifest_files", {})
        extensions: dict[str, Path] = context.get("extensions", {})
        files: list[Path] = context.get("files", [])
        
        # first priority: manifest files
        
        for manifest, language in MANIFEST_LANGUAGE_MAP.items():
            if manifest in manifest_files:
                context["language"] = language
                return language
            
        # special case : .NET project
        for file in files:
            if Path(file).suffix.lower() == '.csproj':
                context["language"] = 'dotnet'
                return 'dotnet'
            
        # second priority : Extension counts
        
        language_counts: dict[str, int] = {}
        
        for extension, count in extensions.items():
            language = EXTENSION_LANGUAGE_MAP.get(extension.lower())
            
            if language is None:
                continue
            
            language_counts[language] = (
                language_counts.get(language, 0) + count
            )
            
        if language_counts:
            detected = max(language_counts.items(), key=lambda item: item[1])[0]
            context['language'] = detected
            return detected
        
        # priority 3 : unknown
        
        context['language'] = None
        return None
        
    @staticmethod
    def _detect_framework(context: dict) -> str | None:
        language = context.get('language')
        manifests = context.get('manifest_files', {})
        root: Path = context['root']
        
        framework = None
        
        try:
            
            # python
            if language == 'python':
                if 'requirements.txt' in manifests:
                    text = (root / manifests["requirements.txt"]).read_text(
                        encoding="utf-8",
                        errors="ignore",
                    ).lower()
                    
                    for pkg, fw in PYTHON_FRAMEWORKS.items():
                        if re.search(rf"^\s*{re.escape(pkg)}([<>=~!].*)?$",
                                     text,
                                     re.MULTILINE):
                            framework = fw
                            break
                        
                elif "pyproject.toml" in manifests:
                    data = tomllib.loads(
                        (root / manifests["pyproject.toml"]).read_text(
                            encoding="utf-8",
                            errors="ignore"
                        )
                    )
                    
                    blob = str(data).lower()
                    
                    for pkg, fw in PYTHON_FRAMEWORKS.items():
                        if pkg in blob:
                            framework = fw
                            break

                elif "Pipfile" in manifests:
                    text = (root / manifests["Pipfile"]).read_text(
                        encoding="utf-8",
                        errors="ignore"
                    ).lower()

                    for pkg, fw in PYTHON_FRAMEWORKS.items():
                        if pkg in text:
                            framework = fw
                            break
                        
            # --------------------------------------------------------
            # Node
            # --------------------------------------------------------
            elif language == "node":

                path = manifests.get("package.json")
                if path:
                    package = json.loads(
                        (root / path).read_text(
                            encoding="utf-8",
                            errors="ignore"
                        )
                    )

                    deps = {}
                    deps.update(package.get("dependencies", {}))
                    deps.update(package.get("devDependencies", {}))

                    for pkg, fw in NODE_FRAMEWORKS.items():
                        if pkg in deps:
                            framework = fw
                            break

            # --------------------------------------------------------
            # Java
            # --------------------------------------------------------
            elif language == "java":

                for name in ("pom.xml", "build.gradle", "build.gradle.kts"):
                    if name in manifests:
                        text = (root / manifests[name]).read_text(
                            encoding="utf-8",
                            errors="ignore"
                        ).lower()

                        for token, fw in JAVA_FRAMEWORKS.items():
                            if token in text:
                                framework = fw
                                break

                    if framework:
                        break

            # --------------------------------------------------------
            # Go
            # --------------------------------------------------------
            elif language == "go":

                path = manifests.get("go.mod")
                if path:
                    text = (root / path).read_text(
                        encoding="utf-8",
                        errors="ignore"
                    ).lower()

                    for token, fw in GO_FRAMEWORKS.items():
                        if token.lower() in text:
                            framework = fw
                            break

            # --------------------------------------------------------
            # Rust
            # --------------------------------------------------------
            elif language == "rust":

                path = manifests.get("Cargo.toml")
                if path:
                    text = (root / path).read_text(
                        encoding="utf-8",
                        errors="ignore"
                    ).lower()

                    for token, fw in RUST_FRAMEWORKS.items():
                        if token.lower() in text:
                            framework = fw
                            break

            # --------------------------------------------------------
            # PHP
            # --------------------------------------------------------
            elif language == "php":

                path = manifests.get("composer.json")
                if path:
                    composer = json.loads(
                        (root / path).read_text(
                            encoding="utf-8",
                            errors="ignore"
                        )
                    )

                    deps = {}
                    deps.update(composer.get("require", {}))
                    deps.update(composer.get("require-dev", {}))

                    for pkg, fw in PHP_FRAMEWORKS.items():
                        if pkg in deps:
                            framework = fw
                            break

            # --------------------------------------------------------
            # Ruby
            # --------------------------------------------------------
            elif language == "ruby":

                path = manifests.get("Gemfile")
                if path:
                    text = (root / path).read_text(
                        encoding="utf-8",
                        errors="ignore"
                    ).lower()

                    for token, fw in RUBY_FRAMEWORKS.items():
                        if token in text:
                            framework = fw
                            break

            # --------------------------------------------------------
            # Dart
            # --------------------------------------------------------
            elif language == "dart":

                path = manifests.get("pubspec.yaml")
                if path:
                    text = (root / path).read_text(
                        encoding="utf-8",
                        errors="ignore"
                    ).lower()

                    for token, fw in DART_FRAMEWORKS.items():
                        if token in text:
                            framework = fw
                            break

        except (OSError,
    json.JSONDecodeError,
    tomllib.TOMLDecodeError,):
            framework = None

        context["framework"] = framework
        return framework
    
    @staticmethod
    def _normalize(version: str) -> str:
        match = DockerService._VERSION_RE.search(version)
        if not match: return None
        
        major = match.group(1)
        minor = match.group(2)
        
        if minor:
            return f"{major}.{minor}"
        
        return major
    
    @staticmethod
    def _detect_runtime(context: dict) -> str | None:
        language = context.get("language")
        manifests = context.get("manifest_files", {})
        root: Path = context.get("root")
        
        runtime = None
        
        try:

            # ------------------------------------------------------
            # Python
            # ------------------------------------------------------
            if language == "python":

                python_version = root / ".python-version"
                if python_version.exists():
                    runtime = DockerService._normalize(
                        python_version.read_text().strip()
                    )

                elif (root / "runtime.txt").exists():
                    text = (root / "runtime.txt").read_text().strip()
                    runtime = DockerService._normalize(text)

                elif "pyproject.toml" in manifests:

                    data = tomllib.loads(
                        (root / manifests["pyproject.toml"]).read_text(
                            encoding="utf-8",
                            errors="ignore"
                        )
                    )

                    blob = str(data)

                    m = re.search(
                        r'(\d+\.\d+)',
                        blob
                    )

                    if m:
                        runtime = DockerService._normalize(m.group())

            # ------------------------------------------------------
            # Node
            # ------------------------------------------------------
            elif language == "node":

                if "package.json" in manifests:

                    package = json.loads(
                        (root / manifests["package.json"]).read_text(
                            encoding="utf-8",
                            errors="ignore"
                        )
                    )

                    engine = (
                        package.get("engines", {})
                        .get("node")
                    )

                    if engine:
                        runtime = DockerService._normalize(engine)

            # ------------------------------------------------------
            # Java
            # ------------------------------------------------------
            elif language == "java":

                for file in (
                    "pom.xml",
                    "build.gradle",
                    "build.gradle.kts",
                ):

                    if file not in manifests:
                        continue

                    text = (
                        root / manifests[file]
                    ).read_text(
                        encoding="utf-8",
                        errors="ignore"
                    )

                    patterns = [
                        r"<java\.version>(.*?)</java\.version>",
                        r"<maven\.compiler\.source>(.*?)</maven\.compiler\.source>",
                        r"<maven\.compiler\.target>(.*?)</maven\.compiler\.target>",
                        r"JavaVersion\.VERSION_(\d+)",
                        r"sourceCompatibility\s*=\s*JavaVersion\.VERSION_(\d+)",
                    ]

                    for p in patterns:
                        m = re.search(p, text)
                        if m:
                            runtime = DockerService._normalize(m.group(1))
                            break

                    if runtime:
                        break

            # ------------------------------------------------------
            # Go
            # ------------------------------------------------------
            elif language == "go":

                if "go.mod" in manifests:

                    text = (
                        root / manifests["go.mod"]
                    ).read_text(
                        encoding="utf-8",
                        errors="ignore"
                    )

                    m = re.search(r"go\s+([\d.]+)", text)

                    if m:
                        runtime = DockerService._normalize(m.group(1))

            # ------------------------------------------------------
            # Rust
            # ------------------------------------------------------
            elif language == "rust":

                if "Cargo.toml" in manifests:

                    text = (
                        root / manifests["Cargo.toml"]
                    ).read_text(
                        encoding="utf-8",
                        errors="ignore"
                    )

                    m = re.search(
                        r'rust-version\s*=\s*"([^"]+)"',
                        text
                    )

                    if m:
                        runtime = DockerService._normalize(m.group(1))

            # ------------------------------------------------------
            # PHP
            # ------------------------------------------------------
            elif language == "php":

                if "composer.json" in manifests:

                    composer = json.loads(
                        (root / manifests["composer.json"]).read_text(
                            encoding="utf-8",
                            errors="ignore"
                        )
                    )

                    php = (
                        composer.get("require", {})
                        .get("php")
                    )

                    if php:
                        runtime = DockerService._normalize(php)

            # ------------------------------------------------------
            # Ruby
            # ------------------------------------------------------
            elif language == "ruby":

                if "Gemfile" in manifests:

                    text = (
                        root / manifests["Gemfile"]
                    ).read_text(
                        encoding="utf-8",
                        errors="ignore"
                    )

                    m = re.search(
                        r'ruby\s+"([\d.]+)"',
                        text
                    )

                    if m:
                        runtime = DockerService._normalize(m.group(1))

            # ------------------------------------------------------
            # Dart
            # ------------------------------------------------------
            elif language == "dart":

                if "pubspec.yaml" in manifests:

                    text = (
                        root / manifests["pubspec.yaml"]
                    ).read_text(
                        encoding="utf-8",
                        errors="ignore"
                    )

                    m = re.search(
                        r'sdk:\s*"([^"]+)"',
                        text
                    )

                    if m:
                        runtime = DockerService._normalize(m.group(1))

        except (
            FileNotFoundError,
            json.JSONDecodeError,
            tomllib.TOMLDecodeError,
            OSError,
        ):
            runtime = None

        context["runtime"] = runtime
        return runtime
    
    @staticmethod
    def _detect_entrypoint(context: dict) -> str | None:
        language = context.get("language")
        framework = context.get("framework")
        files = context.get("files", [])
        manifests = context.get("manifest_files", {})
        root: Path = context.get("root")
        
        file_set = {str(f).replace("\\", "/"): f for f in files}

        entrypoint = None
        
        # --------------------------------------------------------
        # Python
        # --------------------------------------------------------
        if language == "python":

            if framework == "django":
                for f in files:
                    if f.name == "manage.py":
                        entrypoint = str(f).replace("\\", "/")
                        break

            if entrypoint is None:

                if framework == "fastapi":
                    candidates = [
                        "main.py",
                        "app.py",
                        "server.py",
                        "run.py",
                        "asgi.py",
                    ]

                elif framework == "flask":
                    candidates = [
                        "app.py",
                        "run.py",
                        "main.py",
                        "server.py",
                    ]

                else:
                    candidates = [
                        "main.py",
                        "app.py",
                        "server.py",
                        "run.py",
                        "manage.py",
                        "wsgi.py",
                        "asgi.py",
                    ]

                for candidate in candidates:
                    for f in files:
                        if f.name == candidate:
                            entrypoint = str(f).replace("\\", "/")
                            break
                    if entrypoint:
                        break

            # fallback → first root-level python file
            if entrypoint is None:
                for f in files:
                    if f.suffix == ".py" and len(f.parts) == 1:
                        entrypoint = str(f)
                        break

        # --------------------------------------------------------
        # Node
        # --------------------------------------------------------
        elif language == "node":

            package = manifests.get("package.json")

            if package:

                try:
                    data = json.loads(
                        (root / package).read_text(
                            encoding="utf-8",
                            errors="ignore",
                        )
                    )

                    if "main" in data:
                        entrypoint = data["main"]

                    elif "scripts" in data:

                        start = data["scripts"].get("start")

                        if start:
                            m = re.search(
                                r'([\w./-]+\.(?:js|mjs|cjs|ts))',
                                start,
                            )

                            if m:
                                entrypoint = m.group(1)

                except Exception:
                    pass

            if entrypoint is None:

                candidates = [
                    "index.js",
                    "server.js",
                    "app.js",
                    "main.js",
                    "src/index.js",
                    "src/server.js",
                    "index.ts",
                    "server.ts",
                    "app.ts",
                    "main.ts",
                    "src/index.ts",
                    "src/server.ts",
                ]

                for c in candidates:
                    if c in file_set:
                        entrypoint = c
                        break

        # --------------------------------------------------------
        # Java
        # --------------------------------------------------------
        elif language == "java":

            if framework == "springboot":
                entrypoint = "app.jar"

        # --------------------------------------------------------
        # Go
        # --------------------------------------------------------
        elif language == "go":

            if "main.go" in file_set:
                entrypoint = "main.go"

            else:
                for f in files:
                    if (
                        f.name == "main.go"
                        and len(f.parts) >= 3
                        and f.parts[0] == "cmd"
                    ):
                        entrypoint = str(f).replace("\\", "/")
                        break

        # --------------------------------------------------------
        # Rust
        # --------------------------------------------------------
        elif language == "rust":

            if "src/main.rs" in file_set:
                entrypoint = "src/main.rs"

            else:
                for f in files:
                    if (
                        len(f.parts) >= 3
                        and f.parts[0] == "src"
                        and f.parts[1] == "bin"
                        and f.suffix == ".rs"
                    ):
                        entrypoint = str(f).replace("\\", "/")
                        break

        # --------------------------------------------------------
        # PHP
        # --------------------------------------------------------
        elif language == "php":

            if framework == "laravel":
                if "artisan" in file_set:
                    entrypoint = "artisan"

            elif "index.php" in file_set:
                entrypoint = "index.php"

        # --------------------------------------------------------
        # Ruby
        # --------------------------------------------------------
        elif language == "ruby":

            if framework == "rails":
                if "bin/rails" in file_set:
                    entrypoint = "bin/rails"

            elif framework == "sinatra":
                if "app.rb" in file_set:
                    entrypoint = "app.rb"

        # --------------------------------------------------------
        # Dart
        # --------------------------------------------------------
        elif language == "dart":

            if "lib/main.dart" in file_set:
                entrypoint = "lib/main.dart"

        context["entrypoint"] = entrypoint
        return entrypoint
    
    @staticmethod
    def _detect_start_command(context: dict) -> list[str] | None:
        """
        Generate the application start command.

        Returns a list suitable for Docker CMD.
        """

        language = context.get("language")
        framework = context.get("framework")
        entrypoint = context.get("entrypoint")
        port = context.get("port") or 8000
        manifests = context.get("manifest_files", {})
        root: Path = context["root"]

        command = None

        # --------------------------------------------------------
        # Python
        # --------------------------------------------------------

        if language == "python":

            if framework == "fastapi" and entrypoint:

                module = (
                    Path(entrypoint)
                    .with_suffix("")
                    .as_posix()
                    .replace("/", ".")
                )

                command = [
                    "uvicorn",
                    f"{module}:app",
                    "--host",
                    "0.0.0.0",
                    "--port",
                    str(port),
                ]

            elif framework == "django":

                command = [
                    "python",
                    "manage.py",
                    "runserver",
                    f"0.0.0.0:{port}",
                ]

            elif framework == "streamlit" and entrypoint:

                command = [
                    "streamlit",
                    "run",
                    entrypoint,
                    "--server.port",
                    str(port),
                    "--server.address",
                    "0.0.0.0",
                ]

            elif framework == "gradio" and entrypoint:

                command = [
                    "python",
                    entrypoint,
                ]

            elif entrypoint:

                command = [
                    "python",
                    entrypoint,
                ]

        # --------------------------------------------------------
        # Node
        # --------------------------------------------------------

        elif language == "node":

            package = manifests.get("package.json")

            if package:

                try:
                    data = json.loads(
                        (root / package).read_text(
                            encoding="utf-8",
                            errors="ignore",
                        )
                    )

                    if "start" in data.get("scripts", {}):

                        command = [
                            "npm",
                            "start",
                        ]

                except (
                    FileNotFoundError,
                    json.JSONDecodeError,
                    OSError,
                ):
                    pass

            if command is None and entrypoint:

                command = [
                    "node",
                    entrypoint,
                ]

        # --------------------------------------------------------
        # Java
        # --------------------------------------------------------

        elif language == "java":

            command = [
                "java",
                "-jar",
                "app.jar",
            ]

        # --------------------------------------------------------
        # Go
        # --------------------------------------------------------

        elif language == "go":

            command = [
                "./app",
            ]

        # --------------------------------------------------------
        # Rust
        # --------------------------------------------------------

        elif language == "rust":

            command = [
                "./app",
            ]

        # --------------------------------------------------------
        # PHP
        # --------------------------------------------------------

        elif language == "php":

            if framework == "laravel":

                command = [
                    "php",
                    "artisan",
                    "serve",
                    "--host=0.0.0.0",
                    f"--port={port}",
                ]

            elif entrypoint:

                command = [
                    "php",
                    entrypoint,
                ]

        # --------------------------------------------------------
        # Ruby
        # --------------------------------------------------------

        elif language == "ruby":

            if framework == "rails":

                command = [
                    "bundle",
                    "exec",
                    "rails",
                    "server",
                    "-b",
                    "0.0.0.0",
                ]

        # --------------------------------------------------------
        # Dart
        # --------------------------------------------------------

        elif language == "dart":

            if framework == "flutter":

                command = [
                    "flutter",
                    "run",
                    "-d",
                    "web-server",
                    "--web-hostname",
                    "0.0.0.0",
                    "--web-port",
                    str(port),
                ]

        context["start_command"] = command
        return command
    
    @staticmethod
    def _detect_port(context: dict) -> int | None:
        language = context.get("language")
        framework = context.get("framework")
        manifests = context.get("manifest_files", {})
        entrypoint = context.get("entrypoint")
        root: Path = context["root"]

        port = None

        try:

            # --------------------------------------------------------
            # Priority 1 : Framework configuration
            # --------------------------------------------------------

            # Spring Boot
            if framework == "springboot":

                for file in (
                    "application.properties",
                    "application.yml",
                    "application.yaml",
                ):

                    config_file = None

                    for f in context["files"]:
                        if f.name == file:
                            config_file = root / f
                            break

                    if config_file is None:
                        continue

                    if not path.exists():
                        continue

                    text = path.read_text(
                        encoding="utf-8",
                        errors="ignore",
                    )

                    m = re.search(
                        r"server\.port\s*=\s*(\d+)",
                        text,
                    )

                    if not m:
                        m = re.search(
                            r"server:\s*(?:\r?\n\s+.*)*?\r?\n\s*port:\s*(\d+)",
                            text,
                            re.MULTILINE,
                        )

                    if m:
                        port = int(m.group(1))
                        break

            # Next.js
            elif framework == "nextjs":

                package = manifests.get("package.json")

                if package:

                    data = json.loads(
                        (root / package).read_text(
                            encoding="utf-8",
                            errors="ignore",
                        )
                    )

                    start = (
                        data.get("scripts", {})
                        .get("start", "")
                    )

                    m = re.search(
                        r"-p\s+(\d+)",
                        start,
                    )

                    if m:
                        port = int(m.group(1))

            # --------------------------------------------------------
            # Priority 2 : Entrypoint
            # --------------------------------------------------------

            if port is None and entrypoint:

                path = root / entrypoint

                if path.exists():

                    text = path.read_text(
                        encoding="utf-8",
                        errors="ignore",
                    )

                    if language == "python":

                        patterns = [
                            r"uvicorn\.run\([\s\S]*?port\s*=\s*(\d+)",
                            r"\.run\([\s\S]*?port\s*=\s*(\d+)",
                            r"server_port\s*=\s*(\d+)",
                        ]

                        for p in patterns:
                            m = re.search(p, text)
                            if m:
                                port = int(m.group(1))
                                break

                    elif language == "node":

                        patterns = [
                            r"\.listen\(\s*(\d+)",
                            r"listen\(\s*process\.env\.PORT\s*\|\|\s*(\d+)",
                        ]

                        for p in patterns:
                            m = re.search(p, text)
                            if m:
                                port = int(m.group(1))
                                break

                    elif language == "go":

                        m = re.search(
                            r'ListenAndServe\(":(\d+)"',
                            text,
                        )

                        if m:
                            port = int(m.group(1))

                    elif language == "rust":

                        m = re.search(
                            r'127\.0\.0\.1:(\d+)',
                            text,
                        )

                        if m:
                            port = int(m.group(1))

            # --------------------------------------------------------
            # Priority 3 : Framework defaults
            # --------------------------------------------------------

            if port is None:
                port = FRAMEWORK_DEFAULT_PORTS.get(framework)

        except (
            FileNotFoundError,
            json.JSONDecodeError,
            OSError,
            tomllib.TOMLDecodeError,
        ):
            port = FRAMEWORK_DEFAULT_PORTS.get(framework)

        context["port"] = port
        return port
    
    @staticmethod
    def _generate_dockerfile(context: dict) -> str:

        language = context["language"]
        runtime = context.get("runtime")
        port = context.get("port")
        command = context.get("start_command")
        manifests = context.get("manifest_files", {})

        if language is None:
            raise ValueError("Unsupported language.")

        cmd = json.dumps(command)
        dockerfile = ""
        
        has_wrapper = any(
            f.name == "gradlew"
            for f in context["files"]
        )
        if has_wrapper:
            build_cmd = "RUN ./gradlew build -x test"
        else:
            build_cmd = "RUN gradle build -x test"
            
        if "pnpm-lock.yaml" in manifests:
            install_cmd = "RUN pnpm install"

        elif "yarn.lock" in manifests:
            install_cmd = "RUN yarn install"

        elif "package-lock.json" in manifests:
            install_cmd = "RUN npm ci"

        else:
            install_cmd = "RUN npm install"
            
        # ==========================================================
        # Python
        # ==========================================================

        if language == "python":

            runtime = runtime or "3.12"

            dockerfile = [
                f"FROM python:{runtime}-slim",
                "",
                "WORKDIR /app",
                "",
            ]

            if "requirements.txt" in manifests:

                dockerfile.extend([
                    "COPY requirements.txt .",
                    "RUN pip install --no-cache-dir -r requirements.txt",
                    "",
                ])

            elif "pyproject.toml" in manifests:

                dockerfile.extend([
                    "COPY pyproject.toml .",
                    "COPY . .",
                    "RUN pip install .",
                    "",
                ])

            else:

                dockerfile.extend([
                    "COPY . .",
                    "",
                ])

            if "pyproject.toml" not in manifests:
                dockerfile.extend([
                    "COPY . .",
                    "",
                ])

            if port:
                dockerfile.append(f"EXPOSE {port}")

            dockerfile.extend([
                "",
                f"CMD {cmd}",
            ])

        # ==========================================================
        # Node
        # ==========================================================

        elif language == "node":

            runtime = runtime or "22"

            dockerfile = [
                f"FROM node:{runtime}-alpine",
                "",
                "WORKDIR /app",
                "",
                "COPY package*.json ./",
                install_cmd,
                "",
                "COPY . .",
                "",
            ]

            if port:
                dockerfile.append(f"EXPOSE {port}")

            dockerfile.extend([
                "",
                f"CMD {cmd}",
            ])

        # ==========================================================
        # Java
        # ==========================================================

        elif language == "java":

            runtime = runtime or "21"

            if "pom.xml" in manifests:

                dockerfile = [
                    f"FROM eclipse-temurin:{runtime}-jdk",
                    "",
                    "WORKDIR /app",
                    "",
                    "COPY pom.xml .",
                    "COPY src ./src",
                    "",
                    "RUN mvn clean package -DskipTests",
                    "",
                ]

                if port:
                    dockerfile.append(f"EXPOSE {port}")

                dockerfile.extend([
                    "",
                    'CMD ["java","-jar","target/app.jar"]'
                ])

            elif (
                "build.gradle" in manifests
                or "build.gradle.kts" in manifests
            ):

                dockerfile = [
                    f"FROM eclipse-temurin:{runtime}-jdk",
                    "",
                    "WORKDIR /app",
                    "",
                    "COPY . .",
                    "",
                    build_cmd,
                    "",
                ]

                if port:
                    dockerfile.append(f"EXPOSE {port}")

                dockerfile.extend([
                    "",
                    'CMD ["java","-jar","build/libs/app.jar"]'
                ])

        # ==========================================================
        # Go
        # ==========================================================

        elif language == "go":

            runtime = runtime or "1.24"

            dockerfile = [
                f"FROM golang:{runtime}-alpine AS builder",
                "",
                "WORKDIR /app",
                "",
                "COPY . .",
                "",
                "RUN go build -o app .",
                "",
                "FROM alpine",
                "",
                "WORKDIR /app",
                "",
                "COPY --from=builder /app/app .",
                "",
            ]

            if port:
                dockerfile.append(f"EXPOSE {port}")

            dockerfile.extend([
                "",
                f"CMD {cmd}",
            ])

        # ==========================================================
        # Rust
        # ==========================================================

        elif language == "rust":

            dockerfile = [
                "FROM rust:latest AS builder",
                "",
                "WORKDIR /app",
                "",
                "COPY . .",
                "",
                "RUN cargo build --release",
                "",
                "FROM debian:bookworm-slim",
                "",
                "WORKDIR /app",
                "",
                "COPY --from=builder /app/target/release/app .",
                "",
            ]

            if port:
                dockerfile.append(f"EXPOSE {port}")

            dockerfile.extend([
                "",
                f"CMD {cmd}",
            ])

        # ==========================================================
        # PHP
        # ==========================================================

        elif language == "php":

            runtime = runtime or "8.3"

            dockerfile = [
                f"FROM php:{runtime}-cli",
                "",
                "WORKDIR /app",
                "",
                "COPY . .",
                "",
            ]

            if port:
                dockerfile.append(f"EXPOSE {port}")

            dockerfile.extend([
                "",
                f"CMD {cmd}",
            ])

        # ==========================================================
        # Ruby
        # ==========================================================

        elif language == "ruby":

            runtime = runtime or "3.3"

            dockerfile = [
                f"FROM ruby:{runtime}",
                "",
                "WORKDIR /app",
                "",
                "COPY . .",
                "",
                "RUN bundle install",
                "",
            ]

            if port:
                dockerfile.append(f"EXPOSE {port}")

            dockerfile.extend([
                "",
                f"CMD {cmd}",
            ])

        # ==========================================================
        # Dart
        # ==========================================================

        elif language == "dart":

            runtime = runtime or "stable"

            dockerfile = [
                f"FROM dart:{runtime}",
                "",
                "WORKDIR /app",
                "",
                "COPY . .",
                "",
            ]

            if port:
                dockerfile.append(f"EXPOSE {port}")

            dockerfile.extend([
                "",
                f"CMD {cmd}",
            ])

        else:
            raise ValueError("Unsupported language.")

        dockerfile = "\n".join(dockerfile)

        context["dockerfile"] = dockerfile

        return dockerfile
    
    @staticmethod
    def _generate_quick_start(context: dict) -> list[QuickStartStep]:
        """
        Generate Docker quick start commands.
        """

        port = context.get("port", 8000)
        shell = context.get("shell", "sh")

        image_name = context.get("image_name")
        container_name = context.get("container_name")

        if not image_name:

            project = context["root"].name

            image_name = project.lower()
            image_name = image_name.replace("_", "-")
            image_name = image_name.replace(" ", "-")

            image_name = re.sub(
                r"[^a-z0-9._-]",
                "",
                image_name,
            )

            image_name = image_name.strip("-.")

            if not image_name:
                image_name = "app"

            context["image_name"] = image_name

        if not container_name:
            container_name = image_name
            context["container_name"] = container_name

        quick_start = [

            QuickStartStep(
                title="Build Docker Image",
                command=f"docker build -t {image_name} .",
            ),

            QuickStartStep(
                title="Run Docker Container",
                command=(
                    f"docker run -d "
                    f"--name {container_name} "
                    f"-p {port}:{port} "
                    f"{image_name}"
                ),
            ),

            QuickStartStep(
                title="Verify Running",
                command="docker ps",
            ),

            QuickStartStep(
                title="View Logs",
                command=f"docker logs -f {container_name}",
            ),

            QuickStartStep(
                title="Open Shell",
                command=f"docker exec -it {container_name} {shell}",
            ),

            QuickStartStep(
                title="Stop Container",
                command=f"docker stop {container_name}",
            ),

            QuickStartStep(
                title="Remove Container",
                command=f"docker rm {container_name}",
            ),

            QuickStartStep(
                title="Remove Image",
                command=f"docker rmi {image_name}",
            ),
        ]

        context["quick_start"] = quick_start

        return quick_start  
    
    @staticmethod
    def generate(project_root: Path) -> DockerfileGeneratorResponse:

        # --------------------------------------------------------
        # Scan project
        # --------------------------------------------------------

        context = DockerService._scan_project(project_root)

        # --------------------------------------------------------
        # Detection pipeline
        # --------------------------------------------------------

        DockerService._detect_language(context)

        if context.get("language") is None:
            raise ValueError("Unsupported project.")

        DockerService._detect_framework(context)
        DockerService._detect_runtime(context)
        DockerService._detect_entrypoint(context)
        DockerService._detect_port(context)
        DockerService._detect_start_command(context)

        # --------------------------------------------------------
        # Validation
        # --------------------------------------------------------

        if context.get("start_command") is None:
            raise ValueError("Unable to determine application start command.")

        if context.get("port") is None:
            raise ValueError("Unable to determine application port.")

        # --------------------------------------------------------
        # Generation
        # --------------------------------------------------------

        dockerfile = DockerService._generate_dockerfile(context)
        quick_start = DockerService._generate_quick_start(context)

        # --------------------------------------------------------
        # Final validation
        # --------------------------------------------------------

        if not dockerfile:
            raise ValueError("Failed to generate Dockerfile.")

        if not quick_start:
            raise ValueError("Failed to generate Quick Start guide.")

        return DockerfileGeneratorResponse(
            dockerfile=dockerfile,
            quick_start=quick_start,
        )