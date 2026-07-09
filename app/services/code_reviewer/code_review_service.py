from sqlalchemy.orm import Session
from app.services.tool_executor import ExecutionService
from app.services.tool_service import ToolService
from app.services.gemini_service import GeminiService
import json, os, tempfile, shutil, zipfile
from pygments.lexers import guess_lexer
from fastapi import UploadFile, File
from tree_sitter import Parser
from tree_sitter_language_pack import get_language
from tree_sitter_language_pack import get_parser
from language_dispatcher import LanguageDispatcher

class CodeReviewService:
    LANGUAGE_TO_EXTENSIONS = {
        "python": [".py"],
        "python 3": [".py"],
        "java": [".java"],
        "javascript": [".js", ".mjs", ".cjs"],
        "typescript": [".ts", ".tsx"],
        "c": [".c", ".h"],
        "c++": [".cpp", ".cc", ".cxx", ".hpp", ".h"],
        "cpp": [".cpp", ".cc", ".cxx", ".hpp", ".h"],
        "c#": [".cs"],
        "go": [".go"],
        "rust": [".rs"],
        "php": [".php"],
        "html": [".html", ".htm"],
        "css": [".css"],
        "json": [".json"],
        "xml": [".xml"],
        "yaml": [".yaml", ".yml"],
        "sql": [".sql"],
        "markdown": [".md", ".markdown"],
        "dockerfile": ["Dockerfile"],
        "vue": [".vue"],
        "svelte": [".svelte"]
    }
    
    EXT_TO_LANG = {
            ext: lang 
            for lang, extensions in LANGUAGE_TO_EXTENSIONS.items()
            for ext in extensions
        }
    
    supported_extensions = {
        ext
        for extensions in LANGUAGE_TO_EXTENSIONS.values()
        for ext in extensions
    }
    
    FUNCTION_NODE_TYPES = {
        "python": {
            "function_definition",
        },
        "java": {
            "method_declaration",
            "constructor_declaration",
        },
        "javascript": {
            "function_declaration",
            "function_expression",
            "arrow_function",
            "method_definition",
        },
        "typescript": {
            "function_declaration",
            "function_expression",
            "arrow_function",
            "method_definition",
        },
        "c": {
            "function_definition",
        },
        "cpp": {
            "function_definition",
        },
        "go": {
            "function_declaration",
            "method_declaration",
        },
        "rust": {
            "function_item",
        },
    }
    
    CLASS_NODE_TYPES = {
        "python": {
            "class_definition",
        },
        "java": {
            "class_declaration",
        },
        "javascript": {
            "class_declaration",
        },
        "typescript": {
            "class_declaration",
        },
        "csharp": {
            "class_declaration",
        },
        "cpp": {
            "class_specifier",
        },
        "php": {
            "class_declaration",
        },
        "ruby": {
            "class",
        },
        "kotlin": {
            "class_declaration",
        },
        "swift": {
            "class_declaration",
        },
        "dart": {
            "class_definition",
        },
    }
    
    COMMENT_NODE_TYPES = {
        "python": {"comment"},
        "java": {"line_comment", "block_comment"},
        "javascript": {"comment"},
        "typescript": {"comment"},
        "c": {"comment"},
        "cpp": {"comment"},
        "go": {"comment"},
        "rust": {"line_comment", "block_comment"},
    }
    
    IMPORT_NODE_TYPES = {
        "python": {
            "import_statement",
            "import_from_statement",
        },

        "java": {
            "import_declaration",
        },

        "javascript": {
            "import_statement",
        },

        "typescript": {
            "import_statement",
        },

        "c": {
            "preproc_include",
        },

        "cpp": {
            "preproc_include",
        },

        "go": {
            "import_declaration",
            "import_spec",
        },

        "rust": {
            "use_declaration",
        },

        "php": {
            "require_expression",
            "require_once_expression",
            "include_expression",
            "include_once_expression",
            "namespace_use_declaration",
        },

        "html": set(),

        "css": set(),

        "json": set(),

        "xml": set(),

        "yaml": set(),

        "sql": set(),

        "markdown": set(),

        "dockerfile": set(),

        "vue": {
            "import_statement",
        },

        "svelte": {
            "import_statement",
        },
    }
    
    
    @staticmethod
    def review():
        pass
    
    @staticmethod
    def _process_code_snippet(code: str, lang: str = None):
        
        new_code = code.strip()
        if not new_code:
            raise ValueError("Code cannot be empty.")
        
        if lang:
            lang = lang.strip().lower()
        # identify the code language
        try:
            if not lang or lang == 'auto': 
                lexer = guess_lexer(new_code)
                lang = lexer.name.lower().strip()
        except Exception:
            lang = 'text'
            
        ext = CodeReviewService.LANGUAGE_TO_EXTENSIONS.get(lang, [".txt"])[0]
        
        filename = f"main{ext}"
        
        line_count = len(new_code.splitlines())
        char_count = len(new_code)
        size_bytes = len(new_code.encode('utf-8'))
        
        file = {
            "filename": filename,
            "extension": ext,
            "language": lang,
            "code": new_code,
            "line_count": line_count,
            "character_count": char_count,
            "size": size_bytes,
            "source": "snippet",
            "path": None
        }
        
        return [file]
         
    
    @staticmethod
    def _process_single_file(filename: str, code: str):
        
        if not filename:
            raise ValueError("File missing")
        
        if "." not in filename: #Eg: README -> Invalid code file
            raise ValueError("Invalid Code File")
        
        _, ext = os.path.splitext(filename) # main.py -> ['main', 'py']
        ext = ext.lower() # .py
        
        # searching for the extension in dictionary to check if language is supported or not
        if ext not in CodeReviewService.EXT_TO_LANG:
            raise ValueError("Language not supported")
        
        # windows newline = \n, linux newline = \r\n, so preventin g conflict for different os
        code = code.replace("\r\n", "\n").replace("\r", "\n")
        code = code.strip()
        
        if not code:
            raise ValueError("No code to review")
        
        language = CodeReviewService.EXT_TO_LANG[ext]
        
        file = {
            "filename": filename,
            "extension": ext,
            "language": language,
            "code": code,
            "line_count": len(code.splitlines()),
            "character_count": len(code),
            "size": len(code.encode('utf-8')),
            "source": "file",
            "path": filename
        }
        
        return [file]
    
    @staticmethod
    def _process_multiple_files(files: list): # files -> [{filename: ..., code: ...}, ...]
        if not files:
            raise ValueError("No files uploaded")
        
        processed_files = []
        
        for index, file in enumerate(files):
            if not isinstance(file, dict):
                raise ValueError(f"Invalid file object at index {index}.")

            if "filename" not in file:
                raise ValueError(f"Missing filename in file at index {index}.")

            if "code" not in file:
                raise ValueError(f"Missing code in file at index {index}.")

            if not file["filename"]:
                raise ValueError(f"Filename cannot be empty (index {index}).")

            if not file["code"]:
                raise ValueError(f"Code cannot be empty (index {index}).")

            processed_file = CodeReviewService._process_single_file(file["filename"], file["code"])

            processed_files.append(processed_file[0])

        return processed_files    
    
    @staticmethod
    def _process_zip(zip_path: str):
        
        if not zip_path:
            raise ValueError("Zip File Missing")
        
        if not os.path.isfile(zip_path):
            raise ValueError("ZIP file does not exist.")
        
        if os.path.splitext(zip_path)[1].lower() != ".zip":
            raise ValueError("Please upload a valid ZIP file.")

        if not zipfile.is_zipfile(zip_path):
            raise ValueError("Invalid ZIP file.")

        processed_files = []

        IGNORE_FOLDERS = {
            ".git",
            "venv",
            "__pycache__",
            "node_modules",
            ".idea",
            ".vscode",
            "dist",
            "build",
            "target",
            "coverage"
        }

        with tempfile.TemporaryDirectory() as temp_dir:

            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(temp_dir)

            for root, dirs, files in os.walk(temp_dir):

                dirs[:] = [
                    d for d in dirs
                    if d not in IGNORE_FOLDERS
                ]

                for file in files:

                    ext = os.path.splitext(file)[1].lower()

                    if ext not in CodeReviewService.supported_extensions:
                        continue

                    file_path = os.path.join(root, file)

                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            code = f.read()

                    except UnicodeDecodeError:
                        try:
                            with open(file_path, "r", encoding="utf-8-sig") as f:
                                code = f.read()

                        except UnicodeDecodeError:
                            try:
                                with open(file_path, "r", encoding="latin-1") as f:
                                    code = f.read()

                            except Exception:
                                continue

                    review_file = CodeReviewService._process_single_file(
                        filename=file,
                        code=code
                    )[0]

                    review_file["path"] = os.path.relpath(
                        file_path,
                        temp_dir
                    )

                    processed_files.append(review_file)

        if not processed_files:
            raise ValueError("No supported source files found in the ZIP.")

        return processed_files
    
    @staticmethod
    def _collect_errors(node, file, errors):
        if node.type == "ERROR" or node.has_error:
            errors.append({
                "file": file["path"] or file["filename"],
                "language": file["language"],
                "line": node.start_point[0] + 1,
                "column": node.start_point[1] + 1,
                "severity": "error",
                "type": "Syntax Error",
                "message": f"Invalid syntax near '{node.type}'"
            })
        
        for child in node.children:
            CodeReviewService._collect_errors(child, file, errors)
        
    @staticmethod
    def _syntax_check(files: list):
        syntax_errors = []
        
        for file in files:
            language = file["language"]
            try:
                parser = get_parser(language)
            except Exception:
                continue
            
            tree = parser.parse(file['code'].encode("utf-8"))
            
            if not tree.root_node.has_error:
                continue
            
            CodeReviewService._collect_errors(tree.root_node, file, syntax_errors)
            
        return syntax_errors
    
    # this function can count object, class, functions or any statement in a code file
    # the node_types tell the function what to count. Eg import statement, functions, classes, comments
    @staticmethod
    def count_ast_nodes(root, node_types):
        count = 0
        stack = [root]
        while stack:
            node = stack.pop()
            if node.type in node_types:
                count += 1
            stack.extend(node.children)
        return count
    
    @staticmethod
    def _file_statistics(files):
        
        stats = []
        
        for file in files:
            language = file["language"]

            try:
                parser = get_parser(language)
            except Exception:
                continue
            code = file['code']
            tree = parser.parse(code.encode("utf-8"))
            root = tree.root_node

            total_lines = file['line_count']
            blank_lines = sum(1 for line in code.splitlines() if not line.strip())
            functions = CodeReviewService.count_ast_nodes(root, CodeReviewService.FUNCTION_NODE_TYPES.get(language, set()))
            classes = CodeReviewService.count_ast_nodes(root, CodeReviewService.CLASS_NODE_TYPES.get(language, set()))
            comments = CodeReviewService.count_ast_nodes(root, CodeReviewService.COMMENT_NODE_TYPES.get(language, set()))
            imports = CodeReviewService.count_ast_nodes(root, CodeReviewService.IMPORT_NODE_TYPES.get(language, set()))
            
            stats.append({
                "filename": file["filename"],
                "functions": functions,
                "classes": classes,
                "comments": comments,
                "imports": imports,
                "blank_lines": blank_lines,
                "total_lines": total_lines,
                "character_count": file["character_count"],
                "size": file["size"],
                "language": file["language"],
            })

        return stats
    
    @staticmethod
    def _security_scan(files):

        findings = []

        for file in files:

            language = file["language"]

            if language == "python":
                findings.extend(LanguageDispatcher._python_security_scan(file))

            elif language == "java":
                findings.extend(LanguageDispatcher._java_security_scan(file))

            elif language == "javascript":
                findings.extend(LanguageDispatcher._javascript_security_scan(file))

            elif language == "typescript":
                findings.extend(LanguageDispatcher._typescript_security_scan(file))

            elif language in ("cpp", "c++"):
                findings.extend(LanguageDispatcher._cpp_security_scan(file))

            elif language == "c":
                findings.extend(LanguageDispatcher._c_security_scan(file))

            elif language == "c#":
                findings.extend(LanguageDispatcher._csharp_security_scan(file))

            elif language == "go":
                findings.extend(LanguageDispatcher._go_security_scan(file))

            elif language == "rust":
                findings.extend(LanguageDispatcher._rust_security_scan(file))

            elif language == "php":
                findings.extend(LanguageDispatcher._php_security_scan(file))

            elif language == "html":
                findings.extend(LanguageDispatcher._html_security_scan(file))

            elif language == "css":
                findings.extend(LanguageDispatcher._css_security_scan(file))

            elif language == "json":
                findings.extend(LanguageDispatcher._json_security_scan(file))

            elif language == "xml":
                findings.extend(LanguageDispatcher._xml_security_scan(file))

            elif language == "yaml":
                findings.extend(LanguageDispatcher._yaml_security_scan(file))

            elif language == "sql":
                findings.extend(LanguageDispatcher._sql_security_scan(file))

            elif language == "dockerfile":
                findings.extend(LanguageDispatcher._dockerfile_security_scan(file))

            elif language == "vue":
                findings.extend(LanguageDispatcher._vue_security_scan(file))

            elif language == "svelte":
                findings.extend(LanguageDispatcher._svelte_security_scan(file))

        return findings
                    
    @staticmethod
    def _complexity_analysis(files):
        pass
            
    @staticmethod
    def _process_input(input_type: str):
        if input_type == 'snippet':
            res = CodeReviewService._process_code_snippet()