"""CLI used unchanged in Actions and on a laptop."""

import argparse
import json
import os
import sys
from pathlib import Path
from urllib.parse import quote

from .github import GitHub
from .publisher import Publisher
from .request import normalize
from .routing import skip_reason
from .runner import run_agent


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event-name", required=True)
    parser.add_argument("--event-file", required=True, type=Path)
    parser.add_argument("--model", default=os.getenv("REPO_AGENT_MODEL") or "openai:gpt-6-luna")
    parser.add_argument("--output-dir", type=Path, default=Path("agent-output"))
    parser.add_argument("--debug", action="store_true")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--publish", action="store_true")
    mode.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    if args.publish and args.event_file.name.endswith(".example.json"):
        raise ValueError("Example event fixtures cannot be published; use a saved real event")

    event = json.loads(args.event_file.read_text())
    request = normalize(args.event_name, event)
    expected_repo = os.getenv("GITHUB_REPOSITORY")
    if expected_repo and request.repository != expected_repo:
        raise ValueError("Event repository does not match GITHUB_REPOSITORY")
    token = os.getenv("GITHUB_TOKEN", "")
    if not token:
        raise ValueError("GITHUB_TOKEN is required for GitHub resource tools")
    if not os.getenv("OPENAI_API_KEY") and args.model.startswith("openai:"):
        raise ValueError("OPENAI_API_KEY is required for the selected model")
    gh = GitHub(request.repository, token, os.getenv("GITHUB_API_URL", "https://api.github.com"))
    author_id_text = os.getenv("REPO_AGENT_AUTHOR_ID")
    author_id = int(author_id_text) if author_id_text else None
    example = args.event_file.name.endswith(".example.json")
    if not example:
        reason = skip_reason(request, gh, author_id)
        if reason:
            print(f"Skipping issue #{request.target_number}: {reason}")
            return 0
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    default_branch = gh.repository_info()["default_branch"]
    default_branch_sha = gh.get(f"/branches/{quote(default_branch, safe='')}")["commit"]["sha"]
    metadata = {"event_name": args.event_name, "event_id": request.event_id,
                "repository": request.repository, "sender_id": request.sender_id,
                "source_url": request.source_url,
                "default_branch": default_branch, "default_branch_sha": default_branch_sha,
                "model": args.model}
    (output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    (output / "event.json").write_text(json.dumps(event, indent=2) + "\n")
    answer = run_agent(request, gh, args.model, output / "trace.jsonl", args.debug)
    (output / "answer.md").write_text(answer + "\n")
    if args.publish:
        reason = skip_reason(request, gh, author_id)
        if reason:
            print(f"Skipping issue #{request.target_number}: {reason}")
            return 0
    result = Publisher(gh).publish(request, answer, dry_run=args.dry_run)
    if args.dry_run:
        (output / "proposed-reply.md").write_text(result + "\n")
        print(f"Proposed reply: {output / 'proposed-reply.md'}")
    else:
        print(f"Publish result: {result}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, RuntimeError) as exc:
        print(f"repo-agent: {exc}", file=sys.stderr)
        sys.exit(1)
