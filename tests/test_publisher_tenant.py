#!/usr/bin/env python3
"""Tests publisher_tenant — rutas y args."""

import unittest

from Motor_Tecnico.publisher_tenant import parse_tenant_arg, queue_path


class TestPublisherTenant(unittest.TestCase):
    def test_parse_tenant_arg(self):
        self.assertEqual(parse_tenant_arg(["--tenant-id=relatic", "--force"]), "relatic")
        self.assertEqual(parse_tenant_arg(["--force"]), "easytech")

    def test_queue_path_per_tenant(self):
        easy = queue_path("easytech")
        rel = queue_path("relatic")
        self.assertIn("easytech", str(easy))
        self.assertIn("relatic", str(rel))
        self.assertNotEqual(easy, rel)


if __name__ == "__main__":
    unittest.main()
