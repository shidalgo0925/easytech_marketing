#!/usr/bin/env python3
"""Protección del super administrador de plataforma."""

import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from werkzeug.security import generate_password_hash

from Motor_Tecnico.accio_engine import auth_service


class TestPlatformProtection(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "auth.db"
        patcher = patch.object(auth_service, "AUTH_DB", self.db_path)
        patcher.start()
        self.addCleanup(patcher.stop)
        auth_service._ensure_db()
        now = "2026-06-26T00:00:00Z"
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO users (id, email, name, password_hash, global_role, is_active, created_at, updated_at)
                VALUES ('super1', 'super@test.local', 'Super', ?, 'super_admin', 1, ?, ?),
                       ('tenant1', 'admin@test.local', 'Admin', ?, NULL, 1, ?, ?)
                """,
                (
                    generate_password_hash("superpass"),
                    now,
                    now,
                    generate_password_hash("adminpass"),
                    now,
                    now,
                ),
            )
            conn.execute(
                "INSERT INTO user_tenants (user_id, tenant_id, role) VALUES ('super1', 'easytech', 'tenant_admin')"
            )
            conn.execute(
                "INSERT INTO user_tenants (user_id, tenant_id, role) VALUES ('tenant1', 'easytech', 'tenant_admin')"
            )
            conn.commit()

    def test_tenant_admin_cannot_modify_super_admin(self):
        with self.assertRaises(ValueError):
            auth_service.save_tenant_user(
                "easytech",
                user_id="super1",
                email="super@test.local",
                name="Hacked",
                role="tenant_admin",
                actor_is_platform=False,
            )

    def test_tenant_admin_cannot_remove_super_admin(self):
        auth_service.sync_tenant_users(
            "easytech",
            [
                {
                    "id": "tenant1",
                    "email": "admin@test.local",
                    "name": "Admin",
                    "role": "tenant_admin",
                    "active": True,
                }
            ],
            actor_is_platform=False,
        )
        users = auth_service.list_tenant_users("easytech")
        ids = {u["id"] for u in users}
        self.assertIn("super1", ids)

    def test_tenant_admin_cannot_remove_last_non_protected_admin(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM user_tenants WHERE user_id = 'super1'")
            conn.commit()
        with self.assertRaises(ValueError):
            auth_service.sync_tenant_users(
                "easytech",
                [
                    {
                        "id": "tenant1",
                        "email": "admin@test.local",
                        "name": "Admin",
                        "role": "viewer",
                        "active": True,
                    }
                ],
                actor_is_platform=False,
            )


if __name__ == "__main__":
    unittest.main()
