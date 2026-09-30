import unittest
from unittest.mock import Mock

from repo_agent.github import GitHub, _SafeRedirect
from repo_agent.publisher import Publisher
from repo_agent.request import normalize
from repo_agent.tools import window, build_tools
from urllib.request import Request


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


if __name__ == "__main__":
    unittest.main()
