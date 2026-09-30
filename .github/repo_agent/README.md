# Repository agent

This directory contains the same Python application used by Actions and local replay. Its tools read repository code, history, and platform resources through remote GitHub APIs. The model can only read; publishing is handled after the agent returns an answer.

## Configure Actions

- Set repository variable `REPO_AGENT_USER_ID` to the **numeric** GitHub user ID allowed to trigger replies. Only that GitHub identity triggers the Actions job.
- Set secret `OPENAI_API_KEY`.
- Optionally set `REPO_AGENT_MODEL` (default: `openai:gpt-4.1-mini`).
- The workflow has read access to contents, Actions, and checks, and write access to issue, PR, and discussion replies.
- Workflow code is checked out from the default branch; event content and remote repository resources are treated as data.
- Supported events include newly opened issues and discussions, new issue/PR conversation comments, new PR line comments, and new discussion comments.
- Replies go to the originating issue or PR conversation, PR line thread, discussion, or discussion comment thread.
- A hidden event marker prevents duplicate publication on replay.
## Local replay

Run from `.github` with a saved GitHub webhook JSON payload:

```sh
export GITHUB_TOKEN=... OPENAI_API_KEY=...
uv sync --frozen
uv run --frozen python -m repo_agent \
  --event-name issue_comment \
  --event-file ../fixtures/issue-comment.json \
  --dry-run --debug
```

Use `--publish` only when you intend to post. `--output-dir` defaults to `.github/agent-output`, where the process saves `event.json`, `metadata.json` (including default branch SHA and model), `trace.jsonl`, `answer.md`, and, for dry runs, `proposed-reply.md`. Keep those files private: they may contain repository or issue content. CI uploads them for seven days. Use the same `.github/uv.lock`, model, and event fixture to reproduce a CI run. GitHub data and model responses can still change between runs.

REST list tools accept `page`, and discussion tools accept GraphQL cursors. Long tool results are returned in character windows with an `offset` argument for subsequent windows. It can read bounded Actions job logs and text members of artifact ZIPs. Use a token with access to the repository resources you want to inspect; GitHub secrets are never readable as plaintext. Binary files, LFS content, and wiki history need separate access paths.
