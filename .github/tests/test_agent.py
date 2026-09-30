import unittest
from unittest.mock import Mock

from repo_agent.github import GitHub, _SafeRedirect
from repo_agent.publisher import Publisher
from repo_agent.request import normalize
from repo_agent.routing import skip_reason
from repo_agent.runner import resolve_model
from repo_agent.tools import window, build_tools
from repo_agent.observability import LangfuseTracing
from urllib.request import Request
from types import SimpleNamespace
from unittest.mock import patch


BASE = {"repository": {"full_name": "owner/repo"}, "sender": {"id": 42}}


class EventTests(unittest.TestCase):
    def test_issue_comment_on_pr_keeps_thread_target(self):
        event = {**BASE, "action": "created",
                 "issue": {"id": 4, "number": 12, "title": "PR", "pull_request": {}},
                 "comment": {"id": 99, "body": "What changed?", "html_url": "https://github.com/owner/repo/pull/12#issuecomment-99"}}
        request = normalize("issue_comment", event)
        self.assertEqual((request.target_kind, request.target_number, request.event_id),
                         ("pull_request", 12, "99"))

    def test_unsupported_event_is_rejected(self):
        with self.assertRaises(ValueError):
            normalize("issues", {**BASE, "action": "closed"})

    def test_discussion_reply_uses_comment_node(self):
        event = {**BASE, "action": "created",
                 "discussion": {"id": 2, "number": 8},
                 "comment": {"id": 3, "node_id": "DC_123", "body": "Why?",
                             "html_url": "https://github.com/owner/repo/discussions/8#discussioncomment-3"}}
        request = normalize("discussion_comment", event)
        self.assertEqual((request.target_kind, request.target_node_id), ("discussion_comment", "DC_123"))


class RemoteCodeTests(unittest.TestCase):
    def test_remote_path_rejects_traversal(self):
        gh = GitHub("owner/repo", "token")
        with self.assertRaises(ValueError):
            gh.read_file("../outside")

    def test_offset_exposes_later_content(self):
        text = "x" * 30000 + "tail"
        self.assertTrue(window(text, 30000).endswith("tail"))
        gh = GitHub("owner/repo", "token")
        gh.read_file = Mock(return_value=text)
        read_file = next(item for item in build_tools(gh) if item.name == "read_file")
        self.assertTrue(read_file.invoke({"path": "README.md", "offset": 30000}).endswith("tail"))

    def test_agent_tools_are_read_only_and_remote(self):
        gh = GitHub("owner/repo", "token")
        gh.get = Mock(return_value=[{"sha": "abc"}])
        tools = build_tools(gh)
        self.assertFalse(any(item.name.startswith(("create_", "update_", "delete_", "publish_"))
                             for item in tools))
        log = next(item for item in tools if item.name == "git_log")
        log.invoke({"ref": "main", "page": 2})
        gh.get.assert_called_with("/commits", {"per_page": 100, "page": 2, "sha": "main"})

    def test_missing_issue_is_reported_to_agent(self):
        gh = GitHub("owner/repo", "token")
        gh.get = Mock(side_effect=RuntimeError("GitHub API GET /issues/1: HTTP 404"))
        get_issue = next(item for item in build_tools(gh) if item.name == "get_issue")
        result = get_issue.invoke({"number": 1})
        self.assertIn("HTTP 404", result)
        self.assertIn("Try another source", result)


class ApiTests(unittest.TestCase):
    def test_download_redirect_drops_token(self):
        request = Request("https://api.github.com/repos/owner/repo/actions/jobs/1/logs",
                          headers={"Authorization": "Bearer secret"})
        redirected = _SafeRedirect().redirect_request(
            request, None, 302, "Found", {}, "https://objects.example.com/log")
        self.assertNotIn("Authorization", redirected.headers)

    def test_paginated_results_follow_next_link(self):
        gh = GitHub("owner/repo", "token")
        gh.request = Mock(side_effect=[
            ([{"id": 1}], {"Link": '<https://api.github.com/repos/owner/repo/issues?page=2>; rel="next"'}),
            ([{"id": 2}], {}),
        ])
        self.assertEqual([item["id"] for item in gh.pages("/issues")], [1, 2])
        self.assertEqual(gh.request.call_count, 2)

    def test_latest_issue_comment_follows_last_page(self):
        gh = GitHub("owner/repo", "token")
        gh.request = Mock(side_effect=[
            ([{"id": 1}], {"Link": '<https://api.github.com/repos/owner/repo/issues/12/comments?per_page=1&page=3>; rel="last"'}),
            ([{"id": 3, "user": {"id": 42}}], {}),
        ])
        self.assertEqual(gh.latest_issue_comment(12)["id"], 3)
        self.assertEqual(gh.request.call_count, 2)

    def test_duplicate_reply_skips_publish(self):
        gh = Mock()
        request = normalize("issues", {**BASE, "action": "opened",
                                       "issue": {"id": 5, "number": 7, "title": "Help",
                                                 "html_url": "https://github.com/owner/repo/issues/7"}})
        gh.pages.return_value = [{"body": "answer\n\n<!-- repo-agent:issues:5 -->"}]
        self.assertEqual(Publisher(gh).publish(request, "another answer", False),
                         "Already published for this event")
        gh.request.assert_not_called()

    def test_dry_run_never_reads_or_writes_github(self):
        gh = Mock()
        request = normalize("issues", {**BASE, "action": "opened",
                                       "issue": {"id": 5, "number": 7, "title": "Help",
                                                 "html_url": "https://github.com/owner/repo/issues/7"}})
        self.assertIn("answer", Publisher(gh).publish(request, "answer", True))
        gh.assert_not_called()


class RoutingTests(unittest.TestCase):
    def setUp(self):
        self.request = normalize("issue_comment", {**BASE, "action": "created",
            "issue": {"id": 4, "number": 12},
            "comment": {"id": 99, "body": "Question", "html_url": "https://github.com/owner/repo/issues/12#issuecomment-99"}})

    def test_skips_agent_as_latest_author(self):
        gh = Mock()
        gh.latest_issue_comment.return_value = {"id": 99, "user": {"id": 777}}
        self.assertIn("agent account", skip_reason(self.request, gh, 777))

    def test_skips_stale_comment(self):
        gh = Mock()
        gh.latest_issue_comment.return_value = {"id": 100, "user": {"id": 42}}
        self.assertIn("newer", skip_reason(self.request, gh, 777))

    def test_keeps_current_user_comment(self):
        gh = Mock()
        gh.latest_issue_comment.return_value = {"id": 99, "user": {"id": 42}}
        self.assertIsNone(skip_reason(self.request, gh, 777))

    def test_opened_issue_skips_if_comment_arrived(self):
        request = normalize("issues", {**BASE, "action": "opened",
            "issue": {"id": 4, "number": 12, "title": "Question",
                      "html_url": "https://github.com/owner/repo/issues/12"}})
        gh = Mock()
        gh.latest_issue_comment.return_value = {"id": 99, "user": {"id": 42}}
        self.assertIn("newer", skip_reason(request, gh, 777))


class LangfuseTests(unittest.TestCase):
    def test_no_credentials_disables_langfuse(self):
        with patch.dict("os.environ", {}, clear=True):
            self.assertIsNone(LangfuseTracing.from_environment(None))

    def test_partial_credentials_fail(self):
        with patch.dict("os.environ", {"LANGFUSE_PUBLIC_KEY": "pk"}, clear=True):
            with self.assertRaises(ValueError):
                LangfuseTracing.from_environment(None)

    def test_visible_trace_passes_gate(self):
        client = Mock()
        client.api.observations.get_many.return_value = SimpleNamespace(data=[{"id": "obs"}])
        tracing = LangfuseTracing(client, SimpleNamespace(last_trace_id="abc"), None)
        self.assertEqual(tracing.verify(), "abc")
        client.flush.assert_called_once()
        client.api.observations.get_many.assert_called_with(trace_id="abc", limit=1)

    def test_config_attaches_callback_and_event_identity(self):
        request = normalize("issues", {**BASE, "action": "opened",
            "issue": {"id": 4, "number": 12, "title": "Question",
                      "html_url": "https://github.com/owner/repo/issues/12"}})
        handler = Mock()
        config = LangfuseTracing(Mock(), handler, request).config()
        self.assertEqual(config["callbacks"], [handler])
        self.assertEqual(config["metadata"]["event_id"], "4")

    def test_missing_trace_fails_gate(self):
        tracing = LangfuseTracing(Mock(), SimpleNamespace(last_trace_id=None), None)
        with self.assertRaisesRegex(RuntimeError, "trace ID"):
            tracing.verify()

    def test_uningested_trace_fails_after_deadline(self):
        client = Mock()
        client.api.observations.get_many.return_value = SimpleNamespace(data=[])
        tracing = LangfuseTracing(client, SimpleNamespace(last_trace_id="abc"), None)
        with patch("repo_agent.observability.time.monotonic", side_effect=[0, 61]):
            with self.assertRaisesRegex(RuntimeError, "not visible"):
                tracing.verify()


class ModelTests(unittest.TestCase):
    def test_luna_uses_responses_api_for_tools(self):
        with patch("langchain_openai.ChatOpenAI") as chat_model:
            self.assertIs(resolve_model("openai:gpt-6-luna"), chat_model.return_value)
        chat_model.assert_called_once_with(model="gpt-6-luna", use_responses_api=True)


if __name__ == "__main__":
    unittest.main()
