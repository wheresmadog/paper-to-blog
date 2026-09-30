"""Optional Langfuse tracing with a checked ingestion gate."""

import os
import time

from .request import AgentRequest


VISIBILITY_TIMEOUT_SECONDS = 60


class LangfuseTracing:
    def __init__(self, client, handler, request: AgentRequest):
        self.client = client
        self.handler = handler
        self.request = request

    @classmethod
    def from_environment(cls, request: AgentRequest):
        public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
        secret_key = os.getenv("LANGFUSE_SECRET_KEY")
        if not public_key and not secret_key:
            return None
        if not public_key or not secret_key:
            raise ValueError("Set both LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY")

        from langfuse import get_client
        from langfuse.langchain import CallbackHandler

        client = get_client()
        if not client.auth_check():
            raise RuntimeError("Langfuse authentication failed")
        return cls(client, CallbackHandler(), request)

    def config(self) -> dict:
        return {
            "callbacks": [self.handler],
            "run_name": "repo-agent-answer",
            "metadata": {
                "langfuse_user_id": str(self.request.sender_id),
                "langfuse_session_id": f"{self.request.repository}:{self.request.target_kind}:{self.request.target_number}",
                "langfuse_tags": ["repo-agent", self.request.event_name],
                "repository": self.request.repository,
                "event_id": self.request.event_id,
                "source_url": self.request.source_url,
            },
        }

    def flush(self) -> None:
        self.client.flush()

    def verify(self) -> str:
        """Fail closed if the trace is not queryable before publishing."""
        trace_id = self.handler.last_trace_id
        if not trace_id:
            raise RuntimeError("Langfuse did not provide a trace ID")
        self.flush()
        deadline = time.monotonic() + VISIBILITY_TIMEOUT_SECONDS
        last_error = None
        while True:
            try:
                result = self.client.api.observations.get_many(trace_id=trace_id, limit=1)
                if result.data:
                    return trace_id
            except Exception as exc:
                last_error = exc
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                detail = f"; last read error: {last_error}" if last_error else ""
                raise RuntimeError(
                    f"Langfuse trace {trace_id} was not visible within {VISIBILITY_TIMEOUT_SECONDS}s{detail}"
                )
            time.sleep(min(3, remaining))
