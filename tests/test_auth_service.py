#!/usr/bin/env python3
"""Tests auth_service — Entregable 2."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from werkzeug.security import generate_password_hash

from Motor_Tecnico.accio_engine import auth_service


class TestAuthService(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "auth.db"
        patcher = patch.object(auth_service, "AUTH_DB", self.db_path)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_role_permissions_spec(self):
        self.assertIn("config", auth_service.role_permissions("tenant_admin"))
        self.assertNotIn("platform", auth_service.role_permissions("tenant_admin"))
        self.assertIn("platform", auth_service.role_permissions("super_admin"))
        self.assertNotIn("config", auth_service.role_permissions("marketing_operator"))
        self.assertNotIn("publish", auth_service.role_permissions("viewer"))

    def test_authenticate_and_tenant_access(self):
        auth_service._ensure_db()
        import sqlite3

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO users (id, email, name, password_hash, global_role, is_active, created_at, updated_at)
                VALUES ('u1', 'op@test.local', 'Operador', ?, NULL, 1, 't', 't')
                """,
                (generate_password_hash("secret123"),),
            )
            conn.execute(
                "INSERT INTO user_tenants (user_id, tenant_id, role) VALUES ('u1', 'easytech', 'marketing_operator')"
            )
            conn.commit()

        user = auth_service.authenticate("op@test.local", "secret123", "easytech")
        self.assertIsNotNone(user)
        self.assertEqual(user["role"], "marketing_operator")
        self.assertTrue(auth_service.can_access_tenant("u1", "easytech"))
        self.assertFalse(auth_service.can_access_tenant("u1", "relatic"))
        self.assertEqual(auth_service.allowed_tenants("u1"), ["easytech"])


if __name__ == "__main__":
    unittest.main()
