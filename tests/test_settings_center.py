#!/usr/bin/env python3
"""Tests Fase C — Configuration Center."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from werkzeug.security import generate_password_hash

from Motor_Tecnico.accio_engine import settings_center


class TestSettingsCenter(unittest.TestCase):
  def setUp(self):
    self.tmp = tempfile.TemporaryDirectory()
    self.tenant_root = Path(self.tmp.name) / "easytech"
    self.tenant_root.mkdir(parents=True)

  def tearDown(self):
    self.tmp.cleanup()

  @patch("Motor_Tecnico.accio_engine.settings_center.resolve_tenant")
  @patch("Motor_Tecnico.accio_engine.settings_center.knowledge_api.load_business_context")
  def test_products_seed_from_context(self, mock_ctx, mock_resolve):
    mock_ctx.return_value = {
      "productos_servicios": ["ERP Cloud", "Consultoría"],
      "cta_principal": "AGENDAR",
    }

    class FakeTenant:
      root = self.tenant_root

    mock_resolve.return_value = FakeTenant()
    data = settings_center.load_products("easytech")
    self.assertEqual(len(data["products"]), 2)
    self.assertTrue((self.tenant_root / "products.json").is_file())

  @patch("Motor_Tecnico.accio_engine.settings_center.resolve_tenant")
  def test_save_and_load_variables(self, mock_resolve):
    class FakeTenant:
      root = self.tenant_root

    mock_resolve.return_value = FakeTenant()
    with patch.object(settings_center.tenant_secrets, "save_settings_section") as mock_save:
      mock_save.return_value = {}
      with patch.object(settings_center.tenant_secrets, "list_namespace", return_value=[]):
        out = settings_center.save_variables(
          "easytech", {"plain": [{"key": "utm_campaign", "value": "test"}]}
        )
    self.assertEqual(out["plain"][0]["key"], "utm_campaign")
    raw = json.loads((self.tenant_root / "variables.json").read_text())
    self.assertEqual(raw["variables"][0]["value"], "test")

  @patch("Motor_Tecnico.accio_engine.settings_center.resolve_tenant")
  def test_user_login_password(self, mock_resolve):
    class FakeTenant:
      root = self.tenant_root

    mock_resolve.return_value = FakeTenant()
    users_path = self.tenant_root / "users.json"
    users_path.write_text(
      json.dumps(
        {
          "users": [
            {
              "id": "op1",
              "email": "op@test.com",
              "role": "operator",
              "name": "Operador",
              "active": True,
              "password_hash": generate_password_hash("secret123"),
            }
          ],
          "roles": [],
        }
      ),
      encoding="utf-8",
    )
    self.assertIsNotNone(settings_center.verify_user_login("easytech", "op@test.com", "secret123"))
    self.assertIsNotNone(settings_center.verify_user_login("easytech", "op1", "secret123"))
    self.assertIsNone(settings_center.verify_user_login("easytech", "op@test.com", "wrong"))


if __name__ == "__main__":
  unittest.main()
