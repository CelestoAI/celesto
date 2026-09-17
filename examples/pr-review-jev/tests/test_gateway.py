import json
import os
import unittest
from unittest.mock import Mock, patch

from models import evaluate


class GatewayEvaluation(unittest.TestCase):
    @patch.dict(
        os.environ, {"AI_GATEWAY_API_KEY": "gateway-secret", "OPENAI_API_KEY": "openai-secret"}, clear=True
    )
    def test_fixed_helper_receives_only_gateway_secret_and_accepts_optional_confidence(self):
        rubric = {
            "check": {
                "type": "choice",
                "instructions": "Did it pass?",
                "criteria": {"yes": "Pass", "no": "Fail"},
            }
        }
        response = {
            "model": "typesafe-ai/jev",
            "answers": {"check": {"type": "choice", "choice": "yes", "probabilities": {"yes": 1, "no": 0}}},
            "usage": {},
            "sdk_seconds": 0.1,
        }
        with patch(
            "models.subprocess.run", return_value=Mock(returncode=0, stdout=json.dumps(response))
        ) as run:
            result = evaluate({"exit_code": 0}, rubric, "jev")
        self.assertEqual(result["provider"], "gateway")
        self.assertNotIn("confidence", result["answers"]["check"])
        self.assertNotIn("OPENAI_API_KEY", run.call_args.kwargs["env"])
        self.assertNotIn("gateway-secret", str(run.call_args.args))
        self.assertEqual(json.loads(run.call_args.kwargs["input"])["questions"], rubric)

    @patch.dict(os.environ, {"AI_GATEWAY_API_KEY": "secret"}, clear=True)
    def test_sdk_stderr_is_not_exposed(self):
        with (
            patch("models.subprocess.run", return_value=Mock(returncode=1, stderr="Authorization: secret")),
            self.assertRaises(RuntimeError) as error,
        ):
            evaluate({}, {}, "jev")
        self.assertNotIn("secret", str(error.exception))
