"""Read-only GitHub REST/GraphQL client; writes are reserved for Publisher."""

import json
import re
import base64
import io
import zipfile
from urllib.error import HTTPError
from urllib.parse import quote, urlencode, urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener, urlopen


class _SafeRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if urlparse(newurl).scheme != "https":
            raise ValueError("Refusing non-HTTPS GitHub download redirect")
        redirected = super().redirect_request(req, fp, code, msg, headers, newurl)
        if redirected and urlparse(newurl).netloc != urlparse(req.full_url).netloc:
            redirected.remove_header("Authorization")
        return redirected


class GitHub:
    def __init__(self, repository: str, token: str, api_url: str = "https://api.github.com"):
        self.repository = repository
        self.token = token
        self.api_url = api_url.rstrip("/")
        self.base = f"{self.api_url}/repos/{repository}"

    def request(self, method: str, path: str, data: dict | None = None,
                accept: str = "application/vnd.github+json") -> tuple[object, dict]:
        url = path if path.startswith("https://") else self.api_url + path
        expected = urlparse(self.api_url)
        parsed = urlparse(url)
        if (parsed.scheme, parsed.netloc) != (expected.scheme, expected.netloc):
            raise ValueError("GitHub API URL has an unexpected host")
        payload = json.dumps(data).encode() if data is not None else None
        headers = {"Accept": accept, "Authorization": f"Bearer {self.token}",
                   "User-Agent": "repo-agent", "X-GitHub-Api-Version": "2022-11-28"}
        if payload is not None:
            headers["Content-Type"] = "application/json"
        req = Request(url, data=payload, headers=headers, method=method)
        try:
            with urlopen(req, timeout=30) as response:
                raw = response.read()
                return (json.loads(raw) if raw else None), dict(response.headers)
        except HTTPError as exc:
            detail = exc.read(500).decode("utf-8", "replace")
            raise RuntimeError(f"GitHub API {method} {parsed.path}: HTTP {exc.code}: {detail}") from exc

    def get(self, suffix: str, params: dict | None = None) -> object:
        path = self.base + suffix
        if params:
            path += "?" + urlencode(params)
        return self.request("GET", path)[0]

    def pages(self, suffix: str, params: dict | None = None, max_pages: int = 10) -> list:
        path = self.base + suffix + "?" + urlencode({"per_page": 100, **(params or {})})
        items: list = []
        for _ in range(max_pages):
            page, headers = self.request("GET", path)
            if not isinstance(page, list):
                raise TypeError("Expected a paginated list")
            items.extend(page)
            match = re.search(r'<([^>]+)>; rel="next"', headers.get("Link") or headers.get("link", ""))
            if not match:
                return items
            path = match.group(1)
        raise RuntimeError(f"GitHub pagination exceeded {max_pages} pages")

    def graphql(self, query: str, variables: dict) -> dict:
        result, _ = self.request("POST", "/graphql", {"query": query, "variables": variables})
        if not isinstance(result, dict) or result.get("errors"):
            raise RuntimeError(f"GitHub GraphQL error: {result.get('errors') if isinstance(result, dict) else result}")
        return result["data"]

    def repository_info(self) -> dict:
        return self.get("")

    def list_files(self, ref: str = "", prefix: str = "") -> list[str]:
        branch = ref or self.repository_info()["default_branch"]
        tree = self.get(f"/git/trees/{quote(branch, safe='')}", {"recursive": 1})
        if tree.get("truncated"):
            raise RuntimeError("GitHub tree was truncated; narrow to another ref")
        return [item["path"] for item in tree["tree"]
                if item["type"] == "blob" and item["path"].startswith(prefix)]

    def read_file(self, path: str, ref: str = "") -> str:
        if not path or path.startswith("/") or ".." in path.split("/"):
            raise ValueError("Expected a relative repository path")
        encoded = "/".join(quote(part, safe="") for part in path.split("/"))
        data = self.get(f"/contents/{encoded}", {"ref": ref} if ref else None)
        if not isinstance(data, dict) or data.get("type") != "file":
            raise ValueError("Path is not a file")
        if data.get("size", 0) > 1_000_000:
            raise ValueError("File exceeds 1 MB")
        if data.get("encoding") != "base64":
            raise ValueError("GitHub did not provide text file content")
        return base64.b64decode(data["content"]).decode("utf-8", "replace")

    def search_code(self, query: str, page: int = 1) -> object:
        if not query or len(query) > 200:
            raise ValueError("Search query must contain 1-200 characters")
        if page < 1:
            raise ValueError("page must be positive")
        return self.request("GET", "/search/code?" + urlencode(
            {"q": f"repo:{self.repository} {query}", "per_page": 100, "page": page}))[0]

    def compare(self, base: str, head: str) -> object:
        if not base or not head:
            raise ValueError("Two refs are required")
        return self.get(f"/compare/{quote(base, safe='')}...{quote(head, safe='')}")

    def download(self, suffix: str, max_bytes: int = 10_000_000) -> bytes:
        """Fetch a GitHub download while dropping the token on cross-host redirects."""
        req = Request(self.base + suffix,
                      headers={"Authorization": f"Bearer {self.token}",
                               "Accept": "application/vnd.github+json",
                               "User-Agent": "repo-agent"})
        try:
            with build_opener(_SafeRedirect()).open(req, timeout=30) as response:
                data = response.read(max_bytes + 1)
        except HTTPError as exc:
            raise RuntimeError(f"GitHub download {suffix}: HTTP {exc.code}") from exc
        if len(data) > max_bytes:
            raise ValueError("Download exceeds size limit")
        return data

    def job_logs(self, job_id: int) -> str:
        return self.download(f"/actions/jobs/{job_id}/logs", 2_000_000).decode("utf-8", "replace")

    def artifact(self, artifact_id: int, path: str = "") -> object:
        archive = self.download(f"/actions/artifacts/{artifact_id}/zip")
        with zipfile.ZipFile(io.BytesIO(archive)) as bundle:
            names = [item.filename for item in bundle.infolist() if not item.is_dir()]
            if not path:
                return names
            if path not in names:
                raise ValueError("Artifact path not found")
            item = bundle.getinfo(path)
            if item.file_size > 1_000_000:
                raise ValueError("Artifact member exceeds 1 MB")
            return bundle.read(item).decode("utf-8", "replace")
