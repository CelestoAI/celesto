import json
import math
import os
import unittest
from unittest.mock import Mock, patch

from models import disposition, questions, validate_answers
from review import Review, parse_pr, validate_findings

ENV = {
    "LLM_API_KEY": "test",
    "LLM_BASE_URL": "https://example.test/v1",
    "INVESTIGATOR_MODEL": "investigator",
    "EVALUATOR_MODEL": "evaluator",
    "TYPESAFE_API_KEY": "test",
}
FINDING = {
    "id": "F1",
    "title": "Missing guard",
    "location": "app.py:12",
    "claim": "Null input fails",
    "evidence_ids": ["E1"],
}


class Contracts(unittest.TestCase):
    def test_public_pr_validation(self):
        self.assertEqual(parse_pr("https://github.com/org/repo/pull/12"), ("org", "repo", "12"))
        for url in [
            "http://github.com/o/r/pull/1",
            "https://github.com.evil/o/r/pull/1",
            "https://github.com/o/r/pull/1?x=1",
            "https://github.com/../r/pull/1",
            "https://github.com/o/r/pull/1;touch bad",
        ]:
            with self.subTest(url=url), self.assertRaises(ValueError):
                parse_pr(url)

    def test_evidence_reference_is_required(self):
        with self.assertRaises(ValueError):
            validate_findings({"findings": [dict(FINDING)]}, [{"id": "E2"}])
        self.assertEqual(validate_findings({"findings": [dict(FINDING)]}, [{"id": "E1"}])[0]["id"], "F1")

    def test_rubric_rejects_missing_answers_and_bad_distribution(self):
        rubric = questions([FINDING])
        with self.assertRaises(ValueError):
            validate_answers({}, rubric)
        answers = {
            key: {"choice": "yes", "probabilities": {"yes": 1, "no": 0, "unknown": 0}, "confidence": 1}
            for key in rubric
        }
        validate_answers(answers, rubric, jev=True)
        answers[next(iter(rubric))]["confidence"] = math.nan
        with self.assertRaises(ValueError):
            validate_answers(answers, rubric, jev=True)

    def test_unknown_is_not_a_supported_finding(self):
        answers = {key: {"choice": "yes"} for key in questions([FINDING])}
        self.assertEqual(disposition(FINDING, answers), "supported")
        answers["F1_supported"] = {"choice": "unknown"}
        self.assertEqual(disposition(FINDING, answers), "needs evidence")
        answers["F1_introduced"] = {"choice": "no"}
        self.assertEqual(disposition(FINDING, answers), "dismissed")


@patch.dict(os.environ, ENV)
class Workflow(unittest.TestCase):
    def setUp(self):
        self.pr = {
            "base": {"sha": "a" * 40},
            "head": {"sha": "b" * 40},
            "title": "Example change",
            "changed_files": 1,
            "additions": 8,
            "deletions": 2,
        }

    def execute(self, candidates=True, install_failure=False, evaluator_failure=False, recipe=None):
        client = Mock()
        client.__enter__ = Mock(return_value=client)
        client.__exit__ = Mock(return_value=False)
        client.get.return_value.is_error = False
        client.get.return_value.json.return_value = self.pr
        sandboxes = []

        def create(_provider):
            box = Mock()
            box.run.side_effect = lambda command: {
                "stdout": "observed",
                "stderr": "",
                "exit_code": 1 if install_failure and "install-deps" in command else 0,
            }
            sandboxes.append(box)
            return box

        captured = []

        def evaluate(packet, rubric, kind):
            captured.append((kind, json.dumps(packet, sort_keys=True)))
            if evaluator_failure and kind == "jev":
                raise RuntimeError("Provider unavailable")
            return {
                "model": kind,
                "seconds": 1,
                "usage": {},
                "answers": {key: {"choice": "unknown"} for key in rubric},
            }

        job = Review("https://github.com/org/repo/pull/1", "local")
        with (
            patch("review.httpx.Client", return_value=client),
            patch("review.Sandbox", side_effect=create),
            patch.object(
                job,
                "agent",
                side_effect=[
                    recipe
                    if recipe is not None
                    else {"runnable": True, "install": "install-deps", "test": "test-suite", "notes": ""},
                    {"findings": [dict(FINDING)] if candidates else []},
                ],
            ),
            patch("review.evaluate", side_effect=evaluate),
            patch(
                "review.llm",
                return_value=({"review": "Needs more evidence."}, {"seconds": 1, "model": "writer"}),
            ),
            patch("review.Path.mkdir"),
            patch("review.Path.write_text"),
        ):
            job.run()
        return job.snapshot(), sandboxes, captured

    def test_identical_packet_and_cleanup(self):
        state, boxes, packets = self.execute()
        self.assertEqual(state["status"], "complete")
        self.assertEqual(len(boxes), 3)
        self.assertEqual(packets[0][1], packets[1][1])
        self.assertEqual(len(state["evidence_sha256"]), 64)
        for box in boxes:
            box.close.assert_called_once()
        self.assertEqual(state["lanes"]["jev"]["findings"][0]["disposition"], "needs evidence")

    def test_no_findings_does_not_claim_a_comparison(self):
        state, _, packets = self.execute(candidates=False)
        self.assertEqual(packets, [])
        self.assertEqual(state["lanes"]["jev"]["status"], "skipped")

    def test_missing_lockfile_caveats_preserved_without_blocking_tests(self):
        recipe = {
            "runnable": True,
            "install": "install-deps",
            "test": "test-suite",
            "notes": "Follow CI",
            "test_scope": "Unit tests only; KVM e2e excluded",
            "warnings": ["No uv.lock; Python dependencies are unpinned"],
        }
        state, boxes, packets = self.execute(recipe=recipe)
        self.assertEqual(state["status"], "complete")
        self.assertEqual(state["test_results"]["PR"]["status"], "passed")
        self.assertEqual(json.loads(packets[0][1])["recipe"], recipe)
        self.assertTrue(any(event["title"] == "Environment caveat" for event in state["events"]))
        self.assertEqual(len(boxes), 3)

    def test_real_environment_blocker_stops_and_cleans_up(self):
        state, boxes, packets = self.execute(
            recipe={
                "runnable": False,
                "notes": "All tests require an unavailable private service",
            }
        )
        self.assertIn("unavailable private service", state["error"])
        self.assertEqual(len(boxes), 1)
        self.assertEqual(packets, [])
        boxes[0].close.assert_called_once()

    def test_install_failure_is_not_reported_as_test_regression(self):
        state, boxes, _ = self.execute(install_failure=True)
        self.assertEqual(state["test_results"]["PR"]["status"], "environment failed")
        self.assertFalse(
            any("test-suite" in call.args[0] for box in boxes for call in box.run.call_args_list)
        )

    def test_one_evaluator_failure_preserves_other_lane_and_cleanup(self):
        state, boxes, _ = self.execute(evaluator_failure=True)
        self.assertEqual(state["status"], "partial")
        self.assertEqual(state["lanes"]["llm"]["status"], "complete")
        self.assertEqual(state["lanes"]["jev"]["status"], "error")
        for box in boxes:
            box.close.assert_called_once()

    def test_cancel_before_creation(self):
        job = Review("https://github.com/org/repo/pull/1", "local")
        job.cancelled.set()
        with patch("review.Sandbox") as factory, self.assertRaises(InterruptedError):
            job.create("PR", "a" * 40, "org", "repo")
        factory.assert_not_called()


if __name__ == "__main__":
    unittest.main()
