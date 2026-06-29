#!/usr/bin/env python3
"""Tests del flujo editorial EM+Acción."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from Motor_Tecnico.accio_engine.editorial import (  # noqa: E402
    apply_status,
    can_transition,
    is_publishable,
    normalize_status,
)


class EditorialTests(unittest.TestCase):
    def test_legacy_pending_is_publishable(self):
        self.assertTrue(is_publishable("pending"))
        self.assertTrue(is_publishable("scheduled"))
        self.assertTrue(is_publishable("approved"))
        self.assertFalse(is_publishable("draft"))

    def test_transitions(self):
        self.assertTrue(can_transition("draft", "pending_approval"))
        self.assertTrue(can_transition("pending", "published"))
        self.assertFalse(can_transition("draft", "published"))

    def test_apply_status(self):
        post = {"id": "x", "status": "draft"}
        apply_status(post, "pending_approval")
        self.assertEqual(post["status"], "pending_approval")
        with self.assertRaises(ValueError):
            apply_status(post, "published")

    def test_normalize_unknown(self):
        self.assertEqual(normalize_status("unknown", default="scheduled"), "scheduled")


if __name__ == "__main__":
    unittest.main()
