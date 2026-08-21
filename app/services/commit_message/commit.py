from app.models.commit import CommitMessageRequest, CommitMessageResponse, CommitSuggestion, GitData, CommitLLMResponse
from pathlib import Path
import subprocess, re, json
from typing import Literal, List
from app.services.LLM_Gateway.llm_config import gateway
from app.router_llm.gateway import LLMRequest
from app.services.tool_service import ToolService
from app.services.tool_executor import ExecutionService
from sqlalchemy.orm import Session

class NotGitRepositoryError(Exception):
    """Raised when the given directory is not a valid Git repository."""
    pass

class CommitMessageGenerator:
    
    
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
                cwd=repo,
                capture_output=True,
                text=True,
                check=True,
                encoding = "utf-8",
                errors = "replace"
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
            encoding="utf-8",
            errors="replace",
            check=False,
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
                encoding="utf-8",
                errors="replace",
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
        MAX_DIFF_CHARS = 12000
        diff = git_data.diff[:MAX_DIFF_CHARS]
        
        return f"""You are an expert software engineer who writes clear, concise Git commit messages.

            Return ONLY valid JSON:

            {{
            "suggestions": [
                {{"message": "string"}}
            ]
            }}

            Rules:
            - Exactly {suggestions} items
            - No markdown
            - No explanation

            Branch:
            {git_data.branch}

            Style:
            {style_desc}
            
            Git Diff:
            {diff}
            
            """
        
    @staticmethod
    async def _generate_commit_message(prompt: str, expected_count: int) -> List[CommitSuggestion]:

        llm_response = await gateway.generate(
            LLMRequest(
                prompt=prompt,
                temperature=0.2,
                tool_slug="commit_msg",
                response_schema=CommitLLMResponse
            )
        )

        if not llm_response or not llm_response.text:
            raise RuntimeError("Empty response from LLM")
        
        parsed = llm_response.text
        if isinstance(parsed, str):
            parsed = json.loads(parsed)

        if not isinstance(parsed, dict):
            raise RuntimeError("Invalid structured response")

        data = CommitLLMResponse(**parsed)

        if len(data.suggestions) < expected_count:
            raise RuntimeError("LLM returned fewer suggestions than expected")

        return data.suggestions[:expected_count]
    # main function--------------------------------------------------------------------------------
    @staticmethod
    async def generate(request: CommitMessageRequest, user_id: str, db: Session,)->CommitMessageResponse:
        from app.services.credit_service import enforce_credit_limit
        enforce_credit_limit(db, user_id)
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

        commit_suggestions = await CommitMessageGenerator._generate_commit_message(
            prompt,
            request.suggestions
        )
        
        tool = ToolService.get_tool_by_slug(
                db=db,
                slug="commit_msg",
            )
        tool_id = tool.id if tool else "commit_msg"
        execution_id = None
        try:
            execution = ExecutionService.create_execution(
                db=db,
                user_id=user_id,
                tool_id=tool_id,
                user_input=request.model_dump_json(),
                output=json.dumps([c.model_dump() for c in commit_suggestions])
            )
            execution_id = execution.id
        except Exception as e:
            print(f"Execution save failed: {e}") 

        # Build response
        return CommitMessageResponse(
            repository_name=git_data.repository_name,
            branch=git_data.branch,
            diff_type=git_data.diff_type,
            files_changed=len(git_data.changed_files),
            suggestions=commit_suggestions,
            execution_id=execution_id,
        )