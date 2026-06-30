#!/usr/bin/env python3
"""Tests Accio AI Provider Manager."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest import mock

BASE = Path(__file__).resolve().parent.parent
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from Motor_Tecnico.accio_engine.ai_provider.config import load_config  # noqa: E402
from Motor_Tecnico.accio_engine.ai_provider import manager as ai_provider  # noqa: E402


class AIProviderTests(unittest.TestCase):
    def test_load_config_defaults(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            cfg = load_config()
        self.assertEqual(cfg.provider, "litellm")
        self.assertFalse(cfg.configured)

    def test_load_config_from_env(self):
        env = {
            "ACCIO_AI_PROVIDER": "litellm",
            "ACCIO_AI_BASE_URL": "http://codito:4000",
            "ACCIO_AI_MODEL": "qwen2.5-coder:7b",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            cfg = load_config()
        self.assertTrue(cfg.configured)
        self.assertEqual(cfg.base_url, "http://codito:4000")
        self.assertEqual(cfg.chat_completions_url, "http://codito:4000/v1/chat/completions")

    def test_llm_available_needs_base_url(self):
        with mock.patch.dict(os.environ, {"AI_ASSISTANT_ENABLED": "true", "ACCIO_AI_BASE_URL": ""}, clear=True):
            self.assertFalse(ai_provider.llm_available("easytech", {"enabled": True}))

    def test_assistant_enabled_env_false(self):
        with mock.patch.dict(os.environ, {"AI_ASSISTANT_ENABLED": "false"}, clear=True):
            self.assertFalse(ai_provider.assistant_enabled())

    def test_provider_disabled(self):
        with mock.patch.dict(os.environ, {"ACCIO_AI_PROVIDER": "disabled", "ACCIO_AI_ENABLED": "true"}, clear=True):
            self.assertFalse(ai_provider.llm_available("easytech"))
            status = ai_provider.provider_status()
        self.assertEqual(status["provider"], "disabled")
        self.assertIsNotNone(status.get("unavailable_reason"))

    @mock.patch("Motor_Tecnico.accio_engine.ai_provider.manager.litellm_client.chat_completions")
    def test_complete_normalized(self, chat):
        env = {
            "ACCIO_AI_BASE_URL": "http://codito:4000",
            "ACCIO_AI_ENABLED": "true",
        }
        chat.return_value = {
            "choices": [{"message": {"role": "assistant", "content": "OK"}}],
            "usage": {"prompt_tokens": 3, "completion_tokens": 2},
            "model": "qwen2.5-coder:14b",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            result = ai_provider.complete("easytech", [{"role": "user", "content": "test"}])
        self.assertEqual(result.content, "OK")
        self.assertEqual(result.provider, "litellm")

    @mock.patch("Motor_Tecnico.accio_engine.ai_provider.manager._openai_complete")
    @mock.patch("Motor_Tecnico.accio_engine.ai_provider.manager._litellm_complete")
    def test_openai_fallback_on_litellm_failure(self, litellm_complete, openai_complete):
        env = {
            "ACCIO_AI_BASE_URL": "http://codito:4000",
            "ACCIO_AI_ENABLED": "true",
            "OPENAI_API_KEY": "sk-testkey123456789",
            "ACCIO_AI_OPENAI_FALLBACK": "true",
        }
        litellm_complete.side_effect = RuntimeError("litellm down")
        openai_complete.return_value = (
            {"role": "assistant", "content": "fallback"},
            "gpt-4o-mini",
            {"prompt_tokens": 1, "completion_tokens": 1},
            "openai",
        )
        with mock.patch.dict(os.environ, env, clear=True):
            result = ai_provider.complete("easytech", [{"role": "user", "content": "test"}])
        self.assertEqual(result.provider, "openai")
        self.assertEqual(result.content, "fallback")

    @mock.patch("Motor_Tecnico.accio_engine.ai_provider.manager.litellm_client.ping")
    def test_provider_status_reachable(self, ping):
        env = {"ACCIO_AI_BASE_URL": "http://codito:4000", "ACCIO_AI_PROVIDER": "litellm"}
        with mock.patch.dict(os.environ, env, clear=True):
            ping.return_value = {"ok": True, "models": ["qwen2.5-coder:14b"]}
            status = ai_provider.provider_status()
        self.assertTrue(status["configured"])
        self.assertTrue(status["reachable"])
        self.assertEqual(status["provider"], "litellm")

    @mock.patch("Motor_Tecnico.accio_engine.ai_provider.manager.litellm_client.chat_completions")
    def test_chat_completion_returns_message(self, chat):
        env = {
            "ACCIO_AI_BASE_URL": "http://codito:4000",
            "AI_ASSISTANT_ENABLED": "true",
        }
        chat.return_value = {
            "choices": [{"message": {"role": "assistant", "content": "Hola"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
        }
        with mock.patch.dict(os.environ, env, clear=True):
            msg, model, cost = ai_provider.chat_completion(
                "easytech",
                [{"role": "user", "content": "test"}],
            )
        self.assertEqual(msg["content"], "Hola")
        self.assertIsNotNone(cost)


if __name__ == "__main__":
    unittest.main()
