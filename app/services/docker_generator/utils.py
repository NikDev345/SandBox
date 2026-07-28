PYTHON_FRAMEWORKS = {
    "fastapi": "fastapi",
    "flask": "flask",
    "django": "django",
    "streamlit": "streamlit",
    "gradio": "gradio",
    "litestar": "litestar",
    "falcon": "falcon",
    "tornado": "tornado",
    "bottle": "bottle",
    "aiohttp": "aiohttp",
    "dash": "dash",
}

NODE_FRAMEWORKS = {
    "express": "express",
    "next": "nextjs",
    "nextjs": "nextjs",
    "next.js": "nextjs",
    "@nestjs/core": "nestjs",
    "@nestjs/common": "nestjs",
    "koa": "koa",
    "fastify": "fastify",
    "hono": "hono",
    "sails": "sails",
    "@adonisjs/core": "adonis",
    "vue": "vue",
    "react": "react",
    "angular": "angular",
    "@angular/core": "angular",
    "nuxt": "nuxt",
    "vite": "vite",
}

JAVA_FRAMEWORKS = {
    "spring-boot": "springboot",
    "spring.boot": "springboot",
    "quarkus": "quarkus",
    "micronaut": "micronaut",
}

GO_FRAMEWORKS = {
    "github.com/gin-gonic/gin": "gin",
    "github.com/gofiber/fiber": "fiber",
    "github.com/gofiber/fiber/v2": "fiber",
    "github.com/labstack/echo": "echo",
    "github.com/go-chi/chi": "chi",
    "github.com/astaxie/beego": "beego",
    "github.com/beego/beego": "beego",
}

RUST_FRAMEWORKS = {
    "actix-web": "actix",
    "rocket": "rocket",
    "axum": "axum",
    "warp": "warp",
}

PHP_FRAMEWORKS = {
    "laravel/framework": "laravel",
    "symfony/framework-bundle": "symfony",
    "codeigniter4/framework": "codeigniter",
}

RUBY_FRAMEWORKS = {
    "rails": "rails",
    "sinatra": "sinatra",
}

DART_FRAMEWORKS = {
    "flutter": "flutter",
    "dart_frog": "dart_frog",
}

IGNORED_DIRECTORIES = {
        ".git",
        ".github",
        ".idea",
        ".vscode",
        "node_modules",
        "__pycache__",
        "venv",
        ".venv",
        "env",
        "dist",
        "build",
        "target",
        "out",
        "coverage",
        ".cache",
    }

MANIFEST_FILES = {
        "requirements.txt",
        "pyproject.toml",
        "package.json",
        "package-lock.json",
        "pnpm-lock.yaml",
        "yarn.lock",
        "go.mod",
        "Cargo.toml",
        "pom.xml",
        "build.gradle",
        "build.gradle.kts",
        "composer.json",
        "Gemfile",
        "pubspec.yaml",
        "Dockerfile",
        "docker-compose.yml",
        "docker-compose.yaml",
        "README.md",
        ".env.example",
        ".csproj",
    }

MANIFEST_LANGUAGE_MAP = {
        "requirements.txt": "python",
        "pyproject.toml": "python",
        "Pipfile": "python",

        "package.json": "node",

        "go.mod": "go",

        "Cargo.toml": "rust",

        "pom.xml": "java",
        "build.gradle": "java",
        "build.gradle.kts": "java",

        "composer.json": "php",

        "Gemfile": "ruby",

        "pubspec.yaml": "dart",
    }

EXTENSION_LANGUAGE_MAP = {
        ".py": "python",

        ".js": "node",
        ".mjs": "node",
        ".cjs": "node",
        ".ts": "node",
        ".tsx": "node",

        ".java": "java",

        ".go": "go",

        ".rs": "rust",

        ".php": "php",

        ".rb": "ruby",

        ".dart": "dart",

        ".cs": "dotnet",

        ".kt": "kotlin",

        ".scala": "scala",

        ".swift": "swift",

        ".c": "c",
        ".cpp": "cpp",
        ".cc": "cpp",
        ".cxx": "cpp",
    }

FRAMEWORK_DEFAULT_PORTS = {
        "fastapi": 8000,
        "flask": 5000,
        "django": 8000,
        "streamlit": 8501,
        "gradio": 7860,
        "express": 3000,
        "nextjs": 3000,
        "nestjs": 3000,
        "springboot": 8080,
        "gin": 8080,
        "fiber": 3000,
        "echo": 1323,
        "laravel": 8000,
        "rails": 3000,
        "flutter": 8080,
    }
