"""Read-only tools for the remote GitHub repository."""

import json
from urllib.parse import urlencode

from langchain.tools import tool

from .github import GitHub


WINDOW = 30000


def window(value: object, offset: int = 0) -> str:
    """Return a retrievable chunk of a tool result."""
    if offset < 0:
        raise ValueError("offset must be nonnegative")
    content = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, default=str)
    part = content[offset:offset + WINDOW]
    return f"[characters {offset}-{offset + len(part)} of {len(content)}; use offset={offset + len(part)} for more]\n{part}"


def build_tools(gh: GitHub):
    def fetch_page(suffix: str, number: int, params: dict | None = None):
        if number < 1:
            raise ValueError("page must be positive")
        return gh.get(suffix, {"per_page": 100, "page": number, **(params or {})})

    @tool
    def list_files(ref: str = "", prefix: str = "", offset: int = 0) -> str:
        """List files in a remote branch, tag, or commit; use offset for more."""
        return window(gh.list_files(ref, prefix), offset)

    @tool
    def read_file(path: str, ref: str = "", offset: int = 0) -> str:
        """Read a remote text file at a branch, tag, or commit."""
        return window(gh.read_file(path, ref), offset)

    @tool
    def search_files(query: str, page: int = 1, offset: int = 0) -> str:
        """Search remote code; increment page for more matching files."""
        return window(gh.search_code(query, page), offset)

    @tool
    def git_log(ref: str = "", page: int = 1, offset: int = 0) -> str:
        """List remote commits reachable from ref; page selects older results."""
        return window(fetch_page("/commits", page, {"sha": ref} if ref else None), offset)

    @tool
    def git_diff(base: str, head: str, offset: int = 0) -> str:
        """Compare remote refs, including changed files and patch excerpts."""
        return window(gh.compare(base, head), offset)

    @tool
    def read_file_at_ref(ref: str, path: str, offset: int = 0) -> str:
        """Read a remote file at a specific branch, tag, or commit."""
        return window(gh.read_file(path, ref), offset)

    @tool
    def branches_and_tags(page: int = 1, offset: int = 0) -> str:
        """List remote branches and tags; increment page for more."""
        return window({"branches": fetch_page("/branches", page), "tags": fetch_page("/tags", page)}, offset)

    @tool
    def get_issue(number: int, offset: int = 0) -> str:
        """Get an issue or PR issue record by number."""
        return window(gh.get(f"/issues/{number}"), offset)

    @tool
    def list_issues(state: str = "all", page: int = 1, offset: int = 0) -> str:
        """List remote issues and PR issue records; increment page for more."""
        if state not in {"open", "closed", "all"}:
            raise ValueError("state must be open, closed, or all")
        return window(fetch_page("/issues", page, {"state": state}), offset)

    @tool
    def list_issue_comments(number: int, page: int = 1, offset: int = 0) -> str:
        """Fetch issue or PR conversation comments; increment page for more."""
        return window(fetch_page(f"/issues/{number}/comments", page), offset)

    @tool
    def get_pull_request(number: int, offset: int = 0) -> str:
        """Get a PR's metadata, body, and branch SHAs."""
        return window(gh.get(f"/pulls/{number}"), offset)

    @tool
    def list_pr_files(number: int, page: int = 1, offset: int = 0) -> str:
        """Fetch changed files and patch excerpts; increment page for more."""
        return window(fetch_page(f"/pulls/{number}/files", page), offset)

    @tool
    def list_pr_reviews(number: int, page: int = 1, offset: int = 0) -> str:
        """Fetch PR reviews; increment page for more."""
        return window(fetch_page(f"/pulls/{number}/reviews", page), offset)

    @tool
    def list_pr_review_comments(number: int, page: int = 1, offset: int = 0) -> str:
        """Fetch PR line comments; increment page for more."""
        return window(fetch_page(f"/pulls/{number}/comments", page), offset)

    @tool
    def search_issues(query: str, page: int = 1, offset: int = 0) -> str:
        """Search remote issues and PRs; increment page for more."""
        if page < 1:
            raise ValueError("page must be positive")
        result = gh.request("GET", "/search/issues?" + urlencode(
            {"q": f"repo:{gh.repository} {query}", "per_page": 100, "page": page}))[0]
        return window(result, offset)

    @tool
    def list_releases(page: int = 1, offset: int = 0) -> str:
        """Fetch repository releases; increment page for more."""
        return window(fetch_page("/releases", page), offset)

    @tool
    def list_check_runs(ref: str, page: int = 1, offset: int = 0) -> str:
        """Fetch check runs for a remote SHA or branch; increment page for more."""
        return window(fetch_page(f"/commits/{ref}/check-runs", page), offset)

    @tool
    def list_workflow_runs(page: int = 1, offset: int = 0) -> str:
        """List GitHub Actions workflow runs; increment page for more."""
        return window(fetch_page("/actions/runs", page), offset)

    @tool
    def list_run_artifacts(run_id: int, page: int = 1, offset: int = 0) -> str:
        """List artifacts for a workflow run; increment page for more."""
        return window(fetch_page(f"/actions/runs/{run_id}/artifacts", page), offset)

    @tool
    def read_job_logs(job_id: int, offset: int = 0) -> str:
        """Read a remote Actions job log; use offset to read later portions."""
        return window(gh.job_logs(job_id), offset)

    @tool
    def read_artifact(artifact_id: int, path: str = "", offset: int = 0) -> str:
        """List files in an Actions artifact ZIP, or read one text member by path."""
        return window(gh.artifact(artifact_id, path), offset)

    @tool
    def list_discussions(first: int = 50, after: str = "", offset: int = 0) -> str:
        """List discussions via GraphQL; pass pageInfo.endCursor as after for more."""
        if not 1 <= first <= 100:
            raise ValueError("first must be 1-100")
        owner, repo = gh.repository.split("/", 1)
        query = """query($owner:String!,$repo:String!,$first:Int!,$after:String){repository(owner:$owner,name:$repo){discussions(first:$first,after:$after){nodes{id number title body url createdAt} pageInfo{hasNextPage endCursor}}}}"""
        return window(gh.graphql(query, {"owner": owner, "repo": repo, "first": first, "after": after or None}), offset)

    @tool
    def get_discussion(number: int, after: str = "", offset: int = 0) -> str:
        """Get a discussion and a page of comments; pass endCursor as after for more."""
        owner, repo = gh.repository.split("/", 1)
        query = """query($owner:String!,$repo:String!,$number:Int!,$after:String){repository(owner:$owner,name:$repo){discussion(number:$number){id number title body url comments(first:100,after:$after){nodes{id body url replies(first:100){nodes{id body url} pageInfo{hasNextPage endCursor}}} pageInfo{hasNextPage endCursor}}}}}"""
        return window(gh.graphql(query, {"owner": owner, "repo": repo, "number": number, "after": after or None}), offset)

    return [list_files, read_file, search_files, git_log, git_diff, read_file_at_ref,
            branches_and_tags, get_issue, list_issues, list_issue_comments,
            get_pull_request, list_pr_files, list_pr_reviews, list_pr_review_comments,
            search_issues, list_releases, list_check_runs, list_workflow_runs,
            list_run_artifacts, read_job_logs, read_artifact, list_discussions, get_discussion]
