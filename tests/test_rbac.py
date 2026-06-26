#!/usr/bin/env python3
"""Tests RBAC — Fase C."""

import unittest
from unittest.mock import patch

from Motor_Tecnico.accio_engine import rbac


class TestRbac(unittest.TestCase):
    @patch("Motor_Tecnico.accio_engine.rbac.settings_center.load_users")
    def test_admin_has_all_permissions(self, mock_users):
        mock_users.return_value = {
            "roles": [{"id": "admin", "permissions": ["*"]}],
            "users": [],
        }
        self.assertTrue(rbac.has_permission("admin", "admin", "easytech"))
        self.assertTrue(rbac.has_permission("admin", "publish", "easytech"))

    @patch("Motor_Tecnico.accio_engine.rbac.settings_center.load_users")
    def test_viewer_read_only(self, mock_users):
        mock_users.return_value = {
            "roles": [
                {"id": "viewer", "permissions": ["read"]},
                {"id": "operator", "permissions": ["read", "publish", "config"]},
            ],
            "users": [],
        }
        self.assertTrue(rbac.has_permission("viewer", "read", "easytech"))
        self.assertFalse(rbac.has_permission("viewer", "config", "easytech"))
        self.assertFalse(rbac.has_permission("viewer", "publish", "easytech"))
        self.assertTrue(rbac.has_permission("operator", "publish", "easytech"))
        self.assertFalse(rbac.has_permission("operator", "admin", "easytech"))

    def test_permission_for_post_settings(self):
        self.assertEqual(
            rbac.permission_for_request("POST", "/accio/easytech/settings/backup", "easytech"),
            "admin",
        )
        self.assertEqual(
            rbac.permission_for_request("POST", "/accio/easytech/settings/empresa", "easytech"),
            "config",
        )
        self.assertEqual(
            rbac.permission_for_request("POST", "/accio/easytech/settings/empresas", "easytech"),
            "platform",
        )
        self.assertEqual(
            rbac.permission_for_request("POST", "/accio/easytech/settings/empresas/relatic/disable", "easytech"),
            "platform",
        )
        self.assertEqual(
            rbac.permission_for_request("POST", "/accio/easytech/run/publish-linkedin", "easytech"),
            "publish",
        )


if __name__ == "__main__":
    unittest.main()
