#!/usr/bin/env python3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from Motor_Tecnico.accio_engine import auth_service, settings_center


class AuthUsersCrudTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.auth_db = Path(self.tmp.name) / "auth.db"
        self.p_auth = patch.object(auth_service, "AUTH_DB", self.auth_db)
        self.p_auth.start()
        auth_service._ensure_db()

    def tearDown(self):
        self.p_auth.stop()
        self.tmp.cleanup()

    def test_sync_create_update_delete_user(self):
        auth_service.sync_tenant_users(
            "easytech",
            [
                {
                    "id": "u1",
                    "email": "u1@test.local",
                    "name": "User One",
                    "role": "tenant_admin",
                    "active": True,
                    "password": "secret123",
                }
            ],
        )
        users = auth_service.list_tenant_users("easytech")
        self.assertEqual(len(users), 1)
        self.assertEqual(users[0]["email"], "u1@test.local")

        auth_service.sync_tenant_users(
            "easytech",
            [
                {
                    "id": "u1",
                    "email": "u1@test.local",
                    "name": "User One Updated",
                    "role": "viewer",
                    "active": True,
                }
            ],
        )
        users = auth_service.list_tenant_users("easytech")
        self.assertEqual(users[0]["name"], "User One Updated")
        self.assertEqual(users[0]["role"], "viewer")

        auth_service.sync_tenant_users("easytech", [])
        self.assertEqual(auth_service.list_tenant_users("easytech"), [])

    def test_save_users_writes_roles(self):
        with patch.object(settings_center, "_path") as mock_path:
            path = Path(self.tmp.name) / "users.json"
            mock_path.return_value = path
            with patch.object(settings_center, "rbac") as mock_rbac:
                mock_rbac.sanitize_users_for_api.side_effect = lambda d: d
                data = settings_center.save_users(
                    "easytech",
                    {
                        "users": [
                            {
                                "id": "u2",
                                "email": "u2@test.local",
                                "name": "U2",
                                "role": "marketing_operator",
                                "active": True,
                                "password": "pass1234",
                            }
                        ],
                        "roles": [
                            {"id": "tenant_admin", "label": "Admin", "permissions": ["*"]},
                        ],
                    },
                )
        self.assertEqual(len(data["users"]), 1)
        self.assertEqual(data["roles"][0]["id"], "tenant_admin")
        self.assertTrue(path.is_file())


if __name__ == "__main__":
    unittest.main()
