import unittest

from config import jev_provider, llm_config


class ProviderConfig(unittest.TestCase):
    def test_gateway_jev_requires_no_typesafe_key(self):
        self.assertEqual(jev_provider({"AI_GATEWAY_API_KEY": "gateway"}), "gateway")

    def test_explicit_typesafe_does_not_fallback_to_gateway(self):
        with self.assertRaisesRegex(ValueError, "TYPESAFE_API_KEY"):
            jev_provider({"JEV_PROVIDER": "typesafe", "AI_GATEWAY_API_KEY": "gateway"})

    def test_both_keys_prefer_direct_openai(self):
        result = llm_config({"OPENAI_API_KEY": "direct", "AI_GATEWAY_API_KEY": "gateway"})
        self.assertEqual(result["base_url"], "https://api.openai.com/v1")
        self.assertEqual(result["api_key"], "direct")
        self.assertEqual(result["models"]["EVALUATOR"], "gpt-5.6-luna")

    def test_gateway_selection_pairs_correct_key_and_model(self):
        result = llm_config(
            {"LLM_PROVIDER": "gateway", "OPENAI_API_KEY": "direct", "AI_GATEWAY_API_KEY": "gateway"}
        )
        self.assertEqual(result["api_key"], "gateway")
        self.assertEqual(result["models"]["INVESTIGATOR"], "openai/gpt-5.6-luna")

    def test_custom_endpoint_never_inherits_provider_secrets(self):
        with self.assertRaisesRegex(ValueError, "LLM_API_KEY"):
            llm_config({"LLM_BASE_URL": "https://example.test/v1", "OPENAI_API_KEY": "direct"})

    def test_explicit_provider_does_not_fallback(self):
        with self.assertRaisesRegex(ValueError, "OPENAI_API_KEY"):
            llm_config({"LLM_PROVIDER": "openai", "AI_GATEWAY_API_KEY": "gateway"})
