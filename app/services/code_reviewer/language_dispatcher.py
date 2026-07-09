import re

class LanguageDispatcher:
    
    # Constants
    PYTHON_SECURITY_PATTERNS = [
        {
            "rule": "eval_usage",
            "severity": "critical",
            "pattern": r"\beval\s*\(",
            "message": "Use of eval() detected."
        },
        {
            "rule": "exec_usage",
            "severity": "critical",
            "pattern": r"\bexec\s*\(",
            "message": "Use of exec() detected."
        },
        {
            "rule": "os_system",
            "severity": "high",
            "pattern": r"os\.system\s*\(",
            "message": "Use of os.system() detected."
        },
        {
            "rule": "subprocess_shell_true",
            "severity": "critical",
            "pattern": r"subprocess\.(run|call|Popen|check_call|check_output)\s*\([^)]*shell\s*=\s*True",
            "message": "subprocess(shell=True) detected."
        },
        {
            "rule": "pickle_load",
            "severity": "high",
            "pattern": r"pickle\.loads?\s*\(",
            "message": "Unsafe pickle deserialization."
        },
        {
            "rule": "yaml_load",
            "severity": "high",
            "pattern": r"yaml\.load\s*\(",
            "message": "Unsafe yaml.load(). Use yaml.safe_load()."
        },
        {
            "rule": "md5",
            "severity": "medium",
            "pattern": r"hashlib\.md5\s*\(",
            "message": "Weak hash algorithm MD5."
        },
        {
            "rule": "sha1",
            "severity": "medium",
            "pattern": r"hashlib\.sha1\s*\(",
            "message": "Weak hash algorithm SHA1."
        },
        {
            "rule": "hardcoded_password",
            "severity": "critical",
            "pattern": r"(?i)(password|passwd|pwd)\s*=\s*['\"].+['\"]",
            "message": "Possible hardcoded password."
        },
        {
            "rule": "hardcoded_secret",
            "severity": "critical",
            "pattern": r"(?i)(secret|api[_-]?key|token|access[_-]?key)\s*=\s*['\"].+['\"]",
            "message": "Possible hardcoded secret."
        }
    ]
    
    JAVASCRIPT_SECURITY_PATTERNS = [
        {
            "rule": "eval_usage",
            "severity": "critical",
            "pattern": r"\beval\s*\(",
            "message": "Use of eval() detected."
        },
        {
            "rule": "new_function",
            "severity": "critical",
            "pattern": r"new\s+Function\s*\(",
            "message": "Dynamic code execution using new Function()."
        },
        {
            "rule": "document_write",
            "severity": "high",
            "pattern": r"document\.write\s*\(",
            "message": "Use of document.write() detected."
        },
        {
            "rule": "inner_html",
            "severity": "high",
            "pattern": r"\.innerHTML\s*=",
            "message": "Assignment to innerHTML detected."
        },
        {
            "rule": "outer_html",
            "severity": "high",
            "pattern": r"\.outerHTML\s*=",
            "message": "Assignment to outerHTML detected."
        },
        {
            "rule": "child_process_exec",
            "severity": "critical",
            "pattern": r"child_process\.(exec|execSync)\s*\(",
            "message": "Use of child_process.exec()/execSync() detected."
        },
        {
            "rule": "set_timeout_string",
            "severity": "medium",
            "pattern": r"setTimeout\s*\(\s*['\"]",
            "message": "String passed to setTimeout()."
        },
        {
            "rule": "set_interval_string",
            "severity": "medium",
            "pattern": r"setInterval\s*\(\s*['\"]",
            "message": "String passed to setInterval()."
        },
        {
            "rule": "hardcoded_password",
            "severity": "critical",
            "pattern": r"(?i)(password|passwd|pwd)\s*[:=]\s*['\"].+['\"]",
            "message": "Possible hardcoded password."
        },
        {
            "rule": "hardcoded_secret",
            "severity": "critical",
            "pattern": r"(?i)(secret|api[_-]?key|token|access[_-]?key)\s*[:=]\s*['\"].+['\"]",
            "message": "Possible hardcoded secret."
        }
    ]
    
    JAVA_SECURITY_PATTERNS = [
        {
            "rule": "runtime_exec",
            "severity": "critical",
            "pattern": r"Runtime\s*\.\s*getRuntime\s*\(\s*\)\s*\.\s*exec\s*\(",
            "message": "Runtime.exec() detected."
        },
        {
            "rule": "process_builder",
            "severity": "high",
            "pattern": r"new\s+ProcessBuilder\s*\(",
            "message": "ProcessBuilder detected."
        },
        {
            "rule": "object_input_stream",
            "severity": "critical",
            "pattern": r"ObjectInputStream\s*\(",
            "message": "Java deserialization detected."
        },
        {
            "rule": "md5",
            "severity": "medium",
            "pattern": r"MessageDigest\s*\.\s*getInstance\s*\(\s*\"MD5\"\s*\)",
            "message": "Weak hashing algorithm MD5."
        },
        {
            "rule": "sha1",
            "severity": "medium",
            "pattern": r"MessageDigest\s*\.\s*getInstance\s*\(\s*\"SHA-?1\"\s*\)",
            "message": "Weak hashing algorithm SHA1."
        },
        {
            "rule": "hardcoded_password",
            "severity": "critical",
            "pattern": r"(?i)(password|passwd|pwd)\s*=.*\".+\"",
            "message": "Possible hardcoded password."
        },
        {
            "rule": "hardcoded_secret",
            "severity": "critical",
            "pattern": r"(?i)(secret|api[_-]?key|token|access[_-]?key)\s*=.*\".+\"",
            "message": "Possible hardcoded secret."
        }
    ]
    
    C_SECURITY_PATTERNS = [
        {
            "rule": "system_call",
            "severity": "critical",
            "pattern": r"\bsystem\s*\(",
            "message": "Use of system() detected."
        },
        {
            "rule": "popen",
            "severity": "high",
            "pattern": r"\bpopen\s*\(",
            "message": "Use of popen() detected."
        },
        {
            "rule": "gets",
            "severity": "critical",
            "pattern": r"\bgets\s*\(",
            "message": "Unsafe gets() detected."
        },
        {
            "rule": "strcpy",
            "severity": "high",
            "pattern": r"\bstrcpy\s*\(",
            "message": "Unsafe strcpy() detected."
        },
        {
            "rule": "strcat",
            "severity": "high",
            "pattern": r"\bstrcat\s*\(",
            "message": "Unsafe strcat() detected."
        },
        {
            "rule": "sprintf",
            "severity": "medium",
            "pattern": r"\bsprintf\s*\(",
            "message": "sprintf() detected. Consider snprintf()."
        },
        {
            "rule": "scanf_string",
            "severity": "medium",
            "pattern": r'\bscanf\s*\(\s*"%s"',
            "message": "scanf(\"%s\") may cause buffer overflow."
        },
        {
            "rule": "hardcoded_password",
            "severity": "critical",
            "pattern": r'(?i)(password|passwd|pwd)\s*=.*".+"',
            "message": "Possible hardcoded password."
        },
        {
            "rule": "hardcoded_secret",
            "severity": "critical",
            "pattern": r'(?i)(secret|api[_-]?key|token|access[_-]?key)\s*=.*".+"',
            "message": "Possible hardcoded secret."
        }
    ]
    
    CSHARP_SECURITY_PATTERNS = [
        {
            "rule": "process_start",
            "severity": "critical",
            "pattern": r"\bProcess\s*\.\s*Start\s*\(",
            "message": "Process.Start() detected."
        },
        {
            "rule": "binary_formatter",
            "severity": "critical",
            "pattern": r"\bBinaryFormatter\b",
            "message": "BinaryFormatter is insecure and obsolete."
        },
        {
            "rule": "deserializer",
            "severity": "high",
            "pattern": r"\bNetDataContractSerializer\b",
            "message": "Unsafe deserialization detected."
        },
        {
            "rule": "md5",
            "severity": "medium",
            "pattern": r"\bMD5(Create)?\s*\(",
            "message": "Weak hashing algorithm MD5."
        },
        {
            "rule": "sha1",
            "severity": "medium",
            "pattern": r"\bSHA1(Create)?\s*\(",
            "message": "Weak hashing algorithm SHA1."
        },
        {
            "rule": "hardcoded_password",
            "severity": "critical",
            "pattern": r'(?i)(password|passwd|pwd)\s*=.*".+"',
            "message": "Possible hardcoded password."
        },
        {
            "rule": "hardcoded_secret",
            "severity": "critical",
            "pattern": r'(?i)(secret|api[_-]?key|token|access[_-]?key)\s*=.*".+"',
            "message": "Possible hardcoded secret."
        }
    ]
    
    GO_SECURITY_PATTERNS = [
        {
            "rule": "exec_command",
            "severity": "critical",
            "pattern": r"\bexec\.Command\s*\(",
            "message": "exec.Command() detected."
        },
        {
            "rule": "exec_command_context",
            "severity": "critical",
            "pattern": r"\bexec\.CommandContext\s*\(",
            "message": "exec.CommandContext() detected."
        },
        {
            "rule": "md5",
            "severity": "medium",
            "pattern": r"\bmd5\.(New|Sum)\s*\(",
            "message": "Weak hashing algorithm MD5."
        },
        {
            "rule": "sha1",
            "severity": "medium",
            "pattern": r"\bsha1\.(New|Sum)\s*\(",
            "message": "Weak hashing algorithm SHA1."
        },
        {
            "rule": "insecure_tls",
            "severity": "critical",
            "pattern": r"InsecureSkipVerify\s*:\s*true",
            "message": "TLS certificate verification disabled."
        },
        {
            "rule": "hardcoded_password",
            "severity": "critical",
            "pattern": r'(?i)(password|passwd|pwd)\s*:?=\s*".+"',
            "message": "Possible hardcoded password."
        },
        {
            "rule": "hardcoded_secret",
            "severity": "critical",
            "pattern": r'(?i)(secret|api[_-]?key|token|access[_-]?key)\s*:?=\s*".+"',
            "message": "Possible hardcoded secret."
        }
    ]
 
    RUST_SECURITY_PATTERNS = [
        {
            "rule": "command_new",
            "severity": "critical",
            "pattern": r"\bCommand::new\s*\(",
            "message": "Process execution using Command::new()."
        },
        {
            "rule": "unsafe_block",
            "severity": "high",
            "pattern": r"\bunsafe\s*\{",
            "message": "Unsafe block detected."
        },
        {
            "rule": "transmute",
            "severity": "critical",
            "pattern": r"\bmem::transmute\s*\(",
            "message": "Use of mem::transmute() detected."
        },
        {
            "rule": "md5",
            "severity": "medium",
            "pattern": r"\bmd5::",
            "message": "Weak hashing algorithm MD5."
        },
        {
            "rule": "sha1",
            "severity": "medium",
            "pattern": r"\bsha1::",
            "message": "Weak hashing algorithm SHA1."
        },
        {
            "rule": "hardcoded_password",
            "severity": "critical",
            "pattern": r'(?i)(password|passwd|pwd)\s*=.*".+"',
            "message": "Possible hardcoded password."
        },
        {
            "rule": "hardcoded_secret",
            "severity": "critical",
            "pattern": r'(?i)(secret|api[_-]?key|token|access[_-]?key)\s*=.*".+"',
            "message": "Possible hardcoded secret."
        }
    ]
 
    PHP_SECURITY_PATTERNS = [
        {
            "rule": "eval_usage",
            "severity": "critical",
            "pattern": r"\beval\s*\(",
            "message": "Use of eval() detected."
        },
        {
            "rule": "exec_usage",
            "severity": "critical",
            "pattern": r"\bexec\s*\(",
            "message": "Use of exec() detected."
        },
        {
            "rule": "shell_exec",
            "severity": "critical",
            "pattern": r"\bshell_exec\s*\(",
            "message": "Use of shell_exec() detected."
        },
        {
            "rule": "system_usage",
            "severity": "critical",
            "pattern": r"\bsystem\s*\(",
            "message": "Use of system() detected."
        },
        {
            "rule": "passthru",
            "severity": "critical",
            "pattern": r"\bpassthru\s*\(",
            "message": "Use of passthru() detected."
        },
        {
            "rule": "proc_open",
            "severity": "critical",
            "pattern": r"\bproc_open\s*\(",
            "message": "Use of proc_open() detected."
        },
        {
            "rule": "popen",
            "severity": "high",
            "pattern": r"\bpopen\s*\(",
            "message": "Use of popen() detected."
        },
        {
            "rule": "unserialize",
            "severity": "critical",
            "pattern": r"\bunserialize\s*\(",
            "message": "Unsafe unserialize() detected."
        },
        {
            "rule": "md5",
            "severity": "medium",
            "pattern": r"\bmd5\s*\(",
            "message": "Weak hashing algorithm MD5."
        },
        {
            "rule": "sha1",
            "severity": "medium",
            "pattern": r"\bsha1\s*\(",
            "message": "Weak hashing algorithm SHA1."
        },
        {
            "rule": "hardcoded_password",
            "severity": "critical",
            "pattern": r'(?i)(password|passwd|pwd)\s*=>?\s*["\'].+["\']',
            "message": "Possible hardcoded password."
        },
        {
            "rule": "hardcoded_secret",
            "severity": "critical",
            "pattern": r'(?i)(secret|api[_-]?key|token|access[_-]?key)\s*=>?\s*["\'].+["\']',
            "message": "Possible hardcoded secret."
        }
    ]
 
    HTML_SECURITY_PATTERNS = [
        {
            "rule": "script_tag",
            "severity": "medium",
            "pattern": r"<script\b",
            "message": "Script tag detected."
        },
        {
            "rule": "inline_event_handler",
            "severity": "high",
            "pattern": r"\bon(click|load|error|mouseover|mouseout|keyup|keydown|submit|change|focus|blur)\s*=",
            "message": "Inline JavaScript event handler detected."
        },
        {
            "rule": "javascript_url",
            "severity": "critical",
            "pattern": r"javascript:",
            "message": "javascript: URL detected."
        },
        {
            "rule": "iframe",
            "severity": "medium",
            "pattern": r"<iframe\b",
            "message": "iframe detected."
        },
        {
            "rule": "target_blank",
            "severity": "medium",
            "pattern": r'target\s*=\s*["\']_blank["\']',
            "message": "target=\"_blank\" detected. Ensure rel=\"noopener noreferrer\" is used."
        },
        {
            "rule": "mixed_content",
            "severity": "high",
            "pattern": r'http://',
            "message": "Insecure HTTP resource detected."
        },
        {
            "rule": "password_input",
            "severity": "low",
            "pattern": r'<input[^>]*type\s*=\s*["\']password["\']',
            "message": "Password input detected."
        }
    ]
 
    CSS_SECURITY_PATTERNS = [
        {
            "rule": "expression_usage",
            "severity": "critical",
            "pattern": r"\bexpression\s*\(",
            "message": "CSS expression() detected."
        },
        {
            "rule": "behavior_property",
            "severity": "high",
            "pattern": r"\bbehavior\s*:",
            "message": "CSS behavior property detected."
        },
        {
            "rule": "javascript_url",
            "severity": "critical",
            "pattern": r"url\s*\(\s*['\"]?\s*javascript:",
            "message": "JavaScript URL detected inside CSS."
        },
        {
            "rule": "http_import",
            "severity": "high",
            "pattern": r'@import\s+["\']http://',
            "message": "Insecure HTTP @import detected."
        },
        {
            "rule": "http_resource",
            "severity": "medium",
            "pattern": r'url\s*\(\s*["\']?http://',
            "message": "Insecure HTTP resource detected."
        },
        {
            "rule": "remote_import",
            "severity": "low",
            "pattern": r"@import",
            "message": "External stylesheet import detected."
        }
    ]
 
    JSON_SECURITY_PATTERNS = [
        {
            "rule": "hardcoded_password",
            "severity": "critical",
            "pattern": r'(?i)"(password|passwd|pwd)"\s*:\s*".+"',
            "message": "Possible hardcoded password."
        },
        {
            "rule": "hardcoded_secret",
            "severity": "critical",
            "pattern": r'(?i)"(secret|api[_-]?key|token|access[_-]?key)"\s*:\s*".+"',
            "message": "Possible hardcoded secret."
        },
        {
            "rule": "private_key",
            "severity": "critical",
            "pattern": r"-----BEGIN (RSA|EC|OPENSSH|PRIVATE) KEY-----",
            "message": "Private key detected."
        },
        {
            "rule": "aws_access_key",
            "severity": "critical",
            "pattern": r"AKIA[0-9A-Z]{16}",
            "message": "Possible AWS Access Key detected."
        },
        {
            "rule": "jwt_token",
            "severity": "high",
            "pattern": r"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+",
            "message": "Possible JWT token detected."
        },
        {
            "rule": "connection_string",
            "severity": "high",
            "pattern": r'(?i)(connectionstring|connection_string|database_url|db_url)"?\s*:\s*".+"',
            "message": "Database connection string detected."
        }
    ]
 
    XML_SECURITY_PATTERNS = [
        {
            "rule": "doctype_declaration",
            "severity": "high",
            "pattern": r"<!DOCTYPE",
            "message": "DOCTYPE declaration detected."
        },
        {
            "rule": "external_entity",
            "severity": "critical",
            "pattern": r"<!ENTITY",
            "message": "External entity (XXE) detected."
        },
        {
            "rule": "system_entity",
            "severity": "critical",
            "pattern": r'SYSTEM\s+["\']',
            "message": "SYSTEM entity detected."
        },
        {
            "rule": "public_entity",
            "severity": "critical",
            "pattern": r'PUBLIC\s+["\']',
            "message": "PUBLIC entity detected."
        },
        {
            "rule": "hardcoded_password",
            "severity": "critical",
            "pattern": r'(?i)<(password|passwd|pwd)>.*?</\1>',
            "message": "Possible hardcoded password."
        },
        {
            "rule": "hardcoded_secret",
            "severity": "critical",
            "pattern": r'(?i)<(secret|api[_-]?key|token|access[_-]?key)>.*?</\1>',
            "message": "Possible hardcoded secret."
        },
        {
            "rule": "private_key",
            "severity": "critical",
            "pattern": r"-----BEGIN (RSA|EC|OPENSSH|PRIVATE) KEY-----",
            "message": "Private key detected."
        },
        {
            "rule": "aws_access_key",
            "severity": "critical",
            "pattern": r"AKIA[0-9A-Z]{16}",
            "message": "Possible AWS Access Key detected."
        },
        {
            "rule": "jwt_token",
            "severity": "high",
            "pattern": r"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+",
            "message": "Possible JWT token detected."
        }
    ]
 
    YAML_SECURITY_PATTERNS = [
        {
            "rule": "python_object",
            "severity": "critical",
            "pattern": r"!!python/object",
            "message": "Unsafe Python object deserialization detected."
        },
        {
            "rule": "python_object_apply",
            "severity": "critical",
            "pattern": r"!!python/object/apply",
            "message": "Unsafe python object apply detected."
        },
        {
            "rule": "python_object_new",
            "severity": "critical",
            "pattern": r"!!python/object/new",
            "message": "Unsafe python object new detected."
        },
        {
            "rule": "hardcoded_password",
            "severity": "critical",
            "pattern": r'(?i)(password|passwd|pwd)\s*:\s*.+',
            "message": "Possible hardcoded password."
        },
        {
            "rule": "hardcoded_secret",
            "severity": "critical",
            "pattern": r'(?i)(secret|api[_-]?key|token|access[_-]?key)\s*:\s*.+',
            "message": "Possible hardcoded secret."
        },
        {
            "rule": "private_key",
            "severity": "critical",
            "pattern": r"-----BEGIN (RSA|EC|OPENSSH|PRIVATE) KEY-----",
            "message": "Private key detected."
        },
        {
            "rule": "aws_access_key",
            "severity": "critical",
            "pattern": r"AKIA[0-9A-Z]{16}",
            "message": "Possible AWS Access Key detected."
        },
        {
            "rule": "jwt_token",
            "severity": "high",
            "pattern": r"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+",
            "message": "Possible JWT token detected."
        },
        {
            "rule": "database_url",
            "severity": "high",
            "pattern": r'(?i)(database_url|db_url|connection_string)\s*:\s*.+',
            "message": "Database connection string detected."
        }
    ]
 
    SQL_SECURITY_PATTERNS = [
        {
            "rule": "drop_table",
            "severity": "critical",
            "pattern": r"\bDROP\s+TABLE\b",
            "message": "DROP TABLE statement detected."
        },
        {
            "rule": "drop_database",
            "severity": "critical",
            "pattern": r"\bDROP\s+DATABASE\b",
            "message": "DROP DATABASE statement detected."
        },
        {
            "rule": "truncate_table",
            "severity": "high",
            "pattern": r"\bTRUNCATE\b",
            "message": "TRUNCATE statement detected."
        },
        {
            "rule": "delete_without_where",
            "severity": "critical",
            "pattern": r"(?i)^\s*DELETE\s+FROM\s+\w+\s*;?\s*$",
            "message": "DELETE statement without WHERE clause."
        },
        {
            "rule": "update_without_where",
            "severity": "critical",
            "pattern": r"(?i)^\s*UPDATE\s+\w+\s+SET\s+.+;?\s*$",
            "message": "UPDATE statement may be missing a WHERE clause."
        },
        {
            "rule": "union_select",
            "severity": "high",
            "pattern": r"\bUNION\s+SELECT\b",
            "message": "UNION SELECT detected."
        },
        {
            "rule": "select_all",
            "severity": "low",
            "pattern": r"\bSELECT\s+\*\b",
            "message": "SELECT * detected."
        },
        {
            "rule": "execute_immediate",
            "severity": "high",
            "pattern": r"\bEXECUTE\s+IMMEDIATE\b",
            "message": "Dynamic SQL execution detected."
        },
        {
            "rule": "exec",
            "severity": "high",
            "pattern": r"\bEXEC\b",
            "message": "EXEC statement detected."
        },
        {
            "rule": "xp_cmdshell",
            "severity": "critical",
            "pattern": r"\bxp_cmdshell\b",
            "message": "xp_cmdshell detected."
        }
    ]
 
    DOCKERFILE_SECURITY_PATTERNS = [
        {
            "rule": "latest_tag",
            "severity": "medium",
            "pattern": r"^FROM\s+.+:latest\b",
            "message": "Avoid using the 'latest' image tag."
        },
        {
            "rule": "root_user",
            "severity": "critical",
            "pattern": r"^USER\s+root\b",
            "message": "Container is running as root."
        },
        {
            "rule": "add_instruction",
            "severity": "low",
            "pattern": r"^ADD\s+",
            "message": "Prefer COPY instead of ADD unless extraction is required."
        },
        {
            "rule": "curl_pipe_shell",
            "severity": "critical",
            "pattern": r"curl.+\|\s*(bash|sh)",
            "message": "curl piped directly to shell."
        },
        {
            "rule": "wget_pipe_shell",
            "severity": "critical",
            "pattern": r"wget.+\|\s*(bash|sh)",
            "message": "wget piped directly to shell."
        },
        {
            "rule": "sudo_usage",
            "severity": "medium",
            "pattern": r"\bsudo\b",
            "message": "Avoid sudo inside Dockerfile."
        },
        {
            "rule": "chmod_777",
            "severity": "high",
            "pattern": r"chmod\s+777\b",
            "message": "chmod 777 gives full permissions."
        },
        {
            "rule": "expose_ssh",
            "severity": "medium",
            "pattern": r"^EXPOSE\s+22\b",
            "message": "SSH port exposed."
        },
        {
            "rule": "hardcoded_password",
            "severity": "critical",
            "pattern": r'(?i)(password|passwd|pwd)=.+',
            "message": "Possible hardcoded password."
        },
        {
            "rule": "hardcoded_secret",
            "severity": "critical",
            "pattern": r'(?i)(secret|api[_-]?key|token|access[_-]?key)=.+',
            "message": "Possible hardcoded secret."
        }
    ]
 
    @staticmethod
    def _python_security_scan(file):

        findings = []

        code = file["code"]

        lines = code.splitlines()

        for line_number, line in enumerate(lines, start=1):

            for rule in LanguageDispatcher.PYTHON_SECURITY_PATTERNS:

                if re.search(rule["pattern"], line):

                    findings.append({
                        "file": file["path"] or file["filename"],
                        "language": "python",
                        "line": line_number,
                        "severity": rule["severity"],
                        "rule": rule["rule"],
                        "message": rule["message"],
                        "snippet": line.strip()
                    })

        return findings
    
    @staticmethod
    def _javascript_security_scan(file):

        findings = []

        code = file["code"]

        for line_number, line in enumerate(code.splitlines(), start=1):

            for rule in LanguageDispatcher.JAVASCRIPT_SECURITY_PATTERNS:

                if re.search(rule["pattern"], line):

                    findings.append({
                        "file": file["path"] or file["filename"],
                        "language": "javascript",
                        "line": line_number,
                        "severity": rule["severity"],
                        "rule": rule["rule"],
                        "message": rule["message"],
                        "snippet": line.strip()
                    })

        return findings
    
    @staticmethod
    def _typescript_security_scan(file):
        return LanguageDispatcher._javascript_security_scan(file)
    
    @staticmethod
    def _java_security_scan(file):

        findings = []

        code = file["code"]

        for line_number, line in enumerate(code.splitlines(), start=1):

            for rule in LanguageDispatcher.JAVA_SECURITY_PATTERNS:

                if re.search(rule["pattern"], line):

                    findings.append({
                        "file": file["path"] or file["filename"],
                        "language": "java",
                        "line": line_number,
                        "severity": rule["severity"],
                        "rule": rule["rule"],
                        "message": rule["message"],
                        "snippet": line.strip()
                    })

        return findings
    
    @staticmethod
    def _c_security_scan(file):

        findings = []

        code = file["code"]

        for line_number, line in enumerate(code.splitlines(), start=1):

            for rule in LanguageDispatcher.C_SECURITY_PATTERNS:

                if re.search(rule["pattern"], line):

                    findings.append({
                        "file": file["path"] or file["filename"],
                        "language": "c",
                        "line": line_number,
                        "severity": rule["severity"],
                        "rule": rule["rule"],
                        "message": rule["message"],
                        "snippet": line.strip()
                    })

        return findings
    
    @staticmethod
    def _cpp_security_scan(file):
        return LanguageDispatcher._c_security_scan(file)
    
    @staticmethod
    def _csharp_security_scan(file):

        findings = []

        for line_number, line in enumerate(file["code"].splitlines(), start=1):

            for rule in LanguageDispatcher.CSHARP_SECURITY_PATTERNS:

                if re.search(rule["pattern"], line):

                    findings.append({
                        "file": file["path"] or file["filename"],
                        "language": "c#",
                        "line": line_number,
                        "severity": rule["severity"],
                        "rule": rule["rule"],
                        "message": rule["message"],
                        "snippet": line.strip()
                    })

        return findings
    
    @staticmethod
    def _go_security_scan(file):

        findings = []

        for line_number, line in enumerate(file["code"].splitlines(), start=1):

            for rule in LanguageDispatcher.GO_SECURITY_PATTERNS:

                if re.search(rule["pattern"], line):

                    findings.append({
                        "file": file["path"] or file["filename"],
                        "language": "go",
                        "line": line_number,
                        "severity": rule["severity"],
                        "rule": rule["rule"],
                        "message": rule["message"],
                        "snippet": line.strip()
                    })

        return findings
    
    @staticmethod
    def _rust_security_scan(file):

        findings = []

        for line_number, line in enumerate(file["code"].splitlines(), start=1):

            for rule in LanguageDispatcher.RUST_SECURITY_PATTERNS:

                if re.search(rule["pattern"], line):

                    findings.append({
                        "file": file["path"] or file["filename"],
                        "language": "rust",
                        "line": line_number,
                        "severity": rule["severity"],
                        "rule": rule["rule"],
                        "message": rule["message"],
                        "snippet": line.strip()
                    })

        return findings
    
    @staticmethod
    def _php_security_scan(file):

        findings = []

        for line_number, line in enumerate(file["code"].splitlines(), start=1):

            for rule in LanguageDispatcher.PHP_SECURITY_PATTERNS:

                if re.search(rule["pattern"], line):

                    findings.append({
                        "file": file["path"] or file["filename"],
                        "language": "php",
                        "line": line_number,
                        "severity": rule["severity"],
                        "rule": rule["rule"],
                        "message": rule["message"],
                        "snippet": line.strip()
                    })

        return findings
    
    @staticmethod
    def _html_security_scan(file):

        findings = []

        for line_number, line in enumerate(file["code"].splitlines(), start=1):

            for rule in LanguageDispatcher.HTML_SECURITY_PATTERNS:

                if re.search(rule["pattern"], line, re.IGNORECASE):

                    findings.append({
                        "file": file["path"] or file["filename"],
                        "language": "html",
                        "line": line_number,
                        "severity": rule["severity"],
                        "rule": rule["rule"],
                        "message": rule["message"],
                        "snippet": line.strip()
                    })

        return findings
    
    @staticmethod
    def _css_security_scan(file):

        findings = []

        for line_number, line in enumerate(file["code"].splitlines(), start=1):

            for rule in LanguageDispatcher.CSS_SECURITY_PATTERNS:

                if re.search(rule["pattern"], line, re.IGNORECASE):

                    findings.append({
                        "file": file["path"] or file["filename"],
                        "language": "css",
                        "line": line_number,
                        "severity": rule["severity"],
                        "rule": rule["rule"],
                        "message": rule["message"],
                        "snippet": line.strip()
                    })

        return findings
    
    @staticmethod
    def _json_security_scan(file):

        findings = []

        for line_number, line in enumerate(file["code"].splitlines(), start=1):

            for rule in LanguageDispatcher.JSON_SECURITY_PATTERNS:

                if re.search(rule["pattern"], line):

                    findings.append({
                        "file": file["path"] or file["filename"],
                        "language": "json",
                        "line": line_number,
                        "severity": rule["severity"],
                        "rule": rule["rule"],
                        "message": rule["message"],
                        "snippet": line.strip()
                    })

        return findings
    
    @staticmethod
    def _xml_security_scan(file):

        findings = []

        for line_number, line in enumerate(file["code"].splitlines(), start=1):

            for rule in LanguageDispatcher.XML_SECURITY_PATTERNS:

                if re.search(rule["pattern"], line, re.IGNORECASE):

                    findings.append({
                        "file": file["path"] or file["filename"],
                        "language": "xml",
                        "line": line_number,
                        "severity": rule["severity"],
                        "rule": rule["rule"],
                        "message": rule["message"],
                        "snippet": line.strip()
                    })

        return findings
    
    @staticmethod
    def _yaml_security_scan(file):

        findings = []

        for line_number, line in enumerate(file["code"].splitlines(), start=1):

            for rule in LanguageDispatcher.YAML_SECURITY_PATTERNS:

                if re.search(rule["pattern"], line):

                    findings.append({
                        "file": file["path"] or file["filename"],
                        "language": "yaml",
                        "line": line_number,
                        "severity": rule["severity"],
                        "rule": rule["rule"],
                        "message": rule["message"],
                        "snippet": line.strip()
                    })

        return findings
    
    @staticmethod
    def _sql_security_scan(file):

        findings = []

        for line_number, line in enumerate(file["code"].splitlines(), start=1):

            for rule in LanguageDispatcher.SQL_SECURITY_PATTERNS:

                if re.search(rule["pattern"], line, re.IGNORECASE):

                    findings.append({
                        "file": file["path"] or file["filename"],
                        "language": "sql",
                        "line": line_number,
                        "severity": rule["severity"],
                        "rule": rule["rule"],
                        "message": rule["message"],
                        "snippet": line.strip()
                    })

        return findings
    
    @staticmethod
    def _dockerfile_security_scan(file):

        findings = []

        for line_number, line in enumerate(file["code"].splitlines(), start=1):

            for rule in LanguageDispatcher.DOCKERFILE_SECURITY_PATTERNS:

                if re.search(rule["pattern"], line, re.IGNORECASE):

                    findings.append({
                        "file": file["path"] or file["filename"],
                        "language": "dockerfile",
                        "line": line_number,
                        "severity": rule["severity"],
                        "rule": rule["rule"],
                        "message": rule["message"],
                        "snippet": line.strip()
                    })

        has_user = re.search(
            r"^\s*USER\s+",
            file["code"],
            re.MULTILINE | re.IGNORECASE
        )

        if not has_user:

            findings.append({
                "file": file["path"] or file["filename"],
                "language": "dockerfile",
                "line": None,
                "severity": "medium",
                "rule": "missing_user",
                "message": "Dockerfile does not specify a USER. Container will run as root by default.",
                "snippet": ""
            })

        return findings
    
    @staticmethod
    def _vue_security_scan(file):

        findings = []

        findings.extend(
            LanguageDispatcher._html_security_scan(file)
        )

        findings.extend(
            LanguageDispatcher._javascript_security_scan(file)
        )

        findings.extend(
            LanguageDispatcher._css_security_scan(file)
        )

        return findings
    
    @staticmethod
    def _svelte_security_scan(file):

        findings = []

        findings.extend(
            LanguageDispatcher._html_security_scan(file)
        )

        findings.extend(
            LanguageDispatcher._javascript_security_scan(file)
        )

        findings.extend(
            LanguageDispatcher._css_security_scan(file)
        )

        return findings