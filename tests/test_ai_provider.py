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


if __name__ == "__main__":
    unittest.main()
