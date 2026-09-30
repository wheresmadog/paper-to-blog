"""Idempotent publishing to the originating GitHub thread."""

from .github import GitHub
from .request import AgentRequest


class Publisher:
    def __init__(self, gh: GitHub):
        self.gh = gh

    @staticmethod
    def marker(request: AgentRequest) -> str:
        return f"<!-- repo-agent:{request.event_name}:{request.event_id} -->"

    def _discussion_bodies(self, request: AgentRequest) -> list[str]:
        if request.target_kind == "discussion":
            query = """query($id:ID!,$after:String){node(id:$id){... on Discussion{comments(first:100,after:$after){nodes{body} pageInfo{hasNextPage endCursor}}}}}"""
            node_key = "comments"
        else:
            query = """query($id:ID!,$after:String){node(id:$id){... on DiscussionComment{replies(first:100,after:$after){nodes{body} pageInfo{hasNextPage endCursor}}}}}"""
            node_key = "replies"
        bodies = []
        cursor = None
        for _ in range(10):
            data = self.gh.graphql(query, {"id": request.target_node_id, "after": cursor})
            connection = data["node"][node_key]
            bodies.extend(item.get("body", "") for item in connection["nodes"])
            if not connection["pageInfo"]["hasNextPage"]:
                break
            cursor = connection["pageInfo"]["endCursor"]
        else:
            raise RuntimeError("Discussion pagination exceeded 10 pages")
        return bodies

    def already_published(self, request: AgentRequest) -> bool:
        marker = self.marker(request)
        if request.target_kind in {"issue", "pull_request"}:
            records = self.gh.pages(f"/issues/{request.target_number}/comments", max_pages=100)
            bodies = [item.get("body", "") for item in records]
        elif request.target_kind == "review_comment":
            records = self.gh.pages(f"/pulls/{request.target_number}/comments", max_pages=100)
            bodies = [item.get("body", "") for item in records]
        else:
            bodies = self._discussion_bodies(request)
        return any(marker in body for body in bodies)

    def publish(self, request: AgentRequest, answer: str, dry_run: bool) -> str:
        answer = answer.strip()
        if not answer or len(answer) > 60000:
            raise ValueError("Answer must contain 1-60000 characters")
        body = f"{answer}\n\n{self.marker(request)}"
        if dry_run:
            return body
        if self.already_published(request):
            return "Already published for this event"
        if request.target_kind in {"issue", "pull_request"}:
            result, _ = self.gh.request("POST", f"{self.gh.base}/issues/{request.target_number}/comments", {"body": body})
            return result["html_url"]
        if request.target_kind == "review_comment":
            result, _ = self.gh.request("POST", f"{self.gh.base}/pulls/{request.target_number}/comments/{request.comment_id}/replies", {"body": body})
            return result["html_url"]
        discussion_id = request.target_node_id
        reply_id = request.target_node_id if request.target_kind == "discussion_comment" else None
        if reply_id:
            query = """query($id:ID!){node(id:$id){... on DiscussionComment{discussion{id}}}}"""
            discussion_id = self.gh.graphql(query, {"id": reply_id})["node"]["discussion"]["id"]
        mutation = """mutation($id:ID!,$body:String!,$reply:ID){addDiscussionComment(input:{discussionId:$id,body:$body,replyToId:$reply}){comment{url}}}"""
        result = self.gh.graphql(mutation, {"id": discussion_id, "body": body, "reply": reply_id})
        return result["addDiscussionComment"]["comment"]["url"]
