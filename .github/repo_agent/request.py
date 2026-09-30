"""Normalize GitHub webhook payloads into one request shape."""

from dataclasses import dataclass
from typing import Any
import re


@dataclass(frozen=True)
class AgentRequest:
    event_name: str
    event_id: str
    repository: str
    sender_id: int
    target_kind: str
    target_number: int
    target_node_id: str | None
    comment_id: int | None
    source_url: str
    question: str


def normalize(event_name: str, event: dict[str, Any]) -> AgentRequest:
    repo = event.get("repository") or {}
    repository = repo.get("full_name", "")
    if not isinstance(repository, str) or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ValueError("Event must contain repository.full_name")
    sender_id = (event.get("sender") or {}).get("id")
    if not isinstance(sender_id, int):
        raise ValueError("Event must contain sender.id")
    action = event.get("action")
    target: dict[str, Any]
    comment = event.get("comment") or {}
    comment_id = comment.get("id") if isinstance(comment.get("id"), int) else None
    node_id = None

    if event_name == "issues" and action == "opened":
        target = event["issue"]
        kind = "issue"
        source = target
    elif event_name == "issue_comment" and action == "created":
        target = event["issue"]
        kind = "pull_request" if "pull_request" in target else "issue"
        source = comment
    elif event_name == "pull_request_review_comment" and action == "created":
        target = event["pull_request"]
        kind = "review_comment"
        source = comment
    elif event_name == "discussion" and action == "created":
        target = event["discussion"]
        kind = "discussion"
        source = target
        node_id = target.get("node_id")
    elif event_name == "discussion_comment" and action == "created":
        target = event["discussion"]
        kind = "discussion_comment"
        source = comment
        node_id = comment.get("node_id")
    else:
        raise ValueError(f"Unsupported event/action: {event_name}/{action}")

    number = target.get("number")
    if not isinstance(number, int) or number <= 0:
        raise ValueError("Event target must have a positive number")
    if kind in {"review_comment", "discussion_comment"} and not comment_id:
        raise ValueError("Comment event must have comment.id")
    if kind.startswith("discussion") and not node_id:
        raise ValueError("Discussion event must have a node_id")
    body = source.get("body") or ""
    title = target.get("title") or ""
    question = "\n\n".join(x for x in (title if source is target else "", body) if x).strip()
    if not question:
        raise ValueError("Event has no question text")
    source_url = source.get("html_url") or target.get("html_url") or ""
    if not source_url.startswith("https://github.com/"):
        raise ValueError("Event has no GitHub source URL")
    event_id = str(comment_id or target.get("id") or "")
    if not event_id:
        raise ValueError("Event has no stable id")
    return AgentRequest(event_name, event_id, repository, sender_id, kind,
                        number, node_id, comment_id, source_url, question)
