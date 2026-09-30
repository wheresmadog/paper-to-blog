"""Check whether an issue event still represents the latest user activity."""

from .github import GitHub
from .request import AgentRequest


def skip_reason(request: AgentRequest, gh: GitHub, agent_author_id: int | None) -> str | None:
    if request.target_kind != "issue":
        return None
    latest = gh.latest_issue_comment(request.target_number)
    if request.event_name == "issues" and latest:
        return "a newer comment exists"
    if request.event_name == "issue_comment":
        if not latest:
            return "the triggering comment is no longer present"
        if latest.get("id") != request.comment_id:
            return "a newer comment event exists"
    if agent_author_id is not None and latest and latest.get("user", {}).get("id") == agent_author_id:
        return "the latest comment is from the agent account"
    return None
