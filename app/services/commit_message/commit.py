from app.models.commit import CommitMessageRequest, CommitMessageResponse, CommitSuggestion, GitData
from pathlib import Path
import subprocess, re
from typing import Literal, List
from app.services.gemini_service import GeminiService

class NotGitRepositoryError(Exception):
    """Raised when the given directory is not a valid Git repository."""
    pass

class CommitMessageGenerator:
    
    client = GeminiService()
    
    STYLE_MAP = {
        "conventional": "Use the Conventional Commits specification (feat:, fix:, docs:, refactor:, test:, chore:, perf:, ci:, build:).",
        "normal": "Write concise, plain-English Git commit messages.",
        "emoji": "Prefix each commit message with an appropriate Git emoji followed by a concise description.",
    }
    
    @staticmethod
    def _validate_git_repo(repo_path: str) -> Path:
        # Validate that the given path is a valid Git repository
        repo = Path(repo_path).expanduser().resolve()
        
        if not repo.exists():
            raise FileNotFoundError(
                f"Repository path does not exist: {repo_path}"
            )
            
        if not repo.is_dir():
            raise NotADirectoryError(
                f"Repository path is not a directory: {repo_path}"
            )
            
        try:
            result = subprocess.run(
                [
                    "git",
                    "-C",
                    str(repo),
                    "rev-parse",
                    "--is-inside-work-tree",
                ],
                capture_output=True,
                text=True,
                check=True
            )
            
            if result.stdout.strip().lower() != "true":
                raise NotGitRepositoryError(
                    f"{repo} is not a Git Repository!"
                )
        except subprocess.CalledProcessError as e:
            raise NotGitRepositoryError(
                f"{repo} is not a Git Repository"
            ) from e
            
        return repo
    
    @staticmethod
    def _determine_diff_type(repo: Path, requested_diff_type: Literal["auto", "staged","unstaged"]) -> Literal["staged", "unstaged"]:
        # Determine which Git diff should be analyzed
        if requested_diff_type not in {"auto", "staged", "unstaged"}:
            raise ValueError(f"Invalid diff type: {requested_diff_type}")
        if requested_diff_type != "auto":
            return requested_diff_type
        
        result = subprocess.run(
            ["git", "diff", "--cached", "--quiet"],
            cwd=repo,
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 1:
            return "staged"
        
        if result.returncode == 0:
            return "unstaged"
        
        raise RuntimeError(
            f"Failed to determine diff type.\n"
            f"Git exited with code {result.returncode}.\n"
            f"{result.stderr.strip()}"
        )
        
    @staticmethod
    def _collect_git_data(repo: Path, diff_type: Literal["staged", "unstaged"]) -> GitData: 
        
        # a common function for running git command
        def _run_git(*args: str) -> str:
            result = subprocess.run(
                ["git", *args],
                cwd=repo,
                capture_output=True,
                text=True,
            )
            
            if result.returncode != 0:
                raise RuntimeError(
                    f"Failed to collect git data.\n\n"
                    f"Command: git {' '.join(args)}\n"
                    f"{result.stderr.strip()}"
                )
                
            return result.stdout.strip()
        
        diff_args = ["diff"]
        if diff_type == "staged":
            diff_args.append("--cached")

        return GitData(
            repository_name=repo.name,
            branch=_run_git("branch", "--show-current"),
            diff_type=diff_type,
            changed_files=_run_git(*diff_args, "--name-only").splitlines(),
            diff=_run_git(*diff_args),
        )
        
    @staticmethod
    def _validate_diff(git_data: GitData):
        if not git_data.diff.strip():
            raise ValueError(
                "No changes found to generate a commit message."
            )
            
    @staticmethod
    def _build_prompt(git_data: GitData, style: Literal["conventional", "normal", "emoji"], suggestions: int):
        
        style_desc = CommitMessageGenerator.STYLE_MAP[style]
        
        return f"""You are an expert software engineer who writes clear, concise Git commit messages.

            Generate exactly {suggestions} Git commit message(s).

            Style:
            {style_desc}

            Rules:
            - Base every message only on the Git diff.
            - Do NOT invent changes.
            - Return ONLY the commit messages.
            - One per line.
            - Ensure each suggestion is unique.

            Branch:
            {git_data.branch}

            Git Diff:
            {git_data.diff}
            """
        
    @staticmethod
    def _generate_commit_message(prompt):
        try:
            response = CommitMessageGenerator.client.generate(prompt)
            if isinstance(response, str):
                return response.strip()
            return response.text.strip()
        except Exception as e:
            raise RuntimeError(
                f"Failed to generate commit messages. : str{e}"
            ) from e
            
    @staticmethod
    def _parse_commit_message(raw_text: str, expected_count: int) -> List[CommitSuggestion]:
        
        messages = []
        seen = set()
        
        for line in raw_text.splitlines():
            message = re.sub(
                r"^\s*(?:[-*•]|\d+[.)])\s*",
                "",
                line.strip(),
            )

            
            if not message or message in seen:
                continue
            
            seen.add(message)
            messages.append(message)
            
        if len(messages) < expected_count:
            raise RuntimeError(
                "AI returned fewer commit messages than expected."
            )
            
        return [
            CommitSuggestion(
                message=message
            )  for message in messages[:expected_count]
        ]
        
    # main function--------------------------------------------------------------------------------
    @staticmethod
    def generate(request: CommitMessageRequest, user_id: str,)->CommitMessageResponse:
        # Validate repository
        repo = CommitMessageGenerator._validate_git_repo(
            request.repository_path
        )

        # Determine which diff to analyze
        diff_type = CommitMessageGenerator._determine_diff_type(
            repo,
            request.diff_type,
        )

        # Collect Git data
        git_data = CommitMessageGenerator._collect_git_data(
            repo,
            diff_type,
        )

        # Ensure there is something to generate a commit message for
        CommitMessageGenerator._validate_diff(
            git_data,
        )

        # Build AI prompt
        prompt = CommitMessageGenerator._build_prompt(
            git_data=git_data,
            style=request.style,
            suggestions=request.suggestions,
        )

        # Generate commit messages
        raw_response = CommitMessageGenerator._generate_commit_message(
            prompt,
        )

        # Parse AI response
        commit_suggestions = CommitMessageGenerator._parse_commit_message(
            raw_response,
            request.suggestions,
        )

        # Build response
        return CommitMessageResponse(
            repository_name=git_data.repository_name,
            branch=git_data.branch,
            diff_type=git_data.diff_type,
            files_changed=len(git_data.changed_files),
            suggestions=commit_suggestions,
        )