#!/usr/bin/env python3
"""env_loader carga capas .env en orden."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from Motor_Tecnico.accio_engine import env_loader  # noqa: E402


class EnvLoaderTests(unittest.TestCase):
    def test_loads_all_layers_last_wins(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            secrets = root / "deploy" / "secrets"
            secrets.mkdir(parents=True)
            (secrets / ".env.prod").write_text("ACCIO_TEST_LAYER=prod\nACCIO_TEST_KEY=from_prod\n", encoding="utf-8")
            (root / ".env").write_text("ACCIO_TEST_KEY=from_root\n", encoding="utf-8")
            os.environ["ACCIO_ENV"] = "prod"
            env_loader.load_accio_env(root)
            self.assertEqual(os.environ.get("ACCIO_TEST_LAYER"), "prod")
            self.assertEqual(os.environ.get("ACCIO_TEST_KEY"), "from_root")


if __name__ == "__main__":
    unittest.main()
