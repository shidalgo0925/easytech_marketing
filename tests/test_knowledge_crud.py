#!/usr/bin/env python3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from Motor_Tecnico.accio_engine import knowledge_api


class KnowledgeCrudTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.tenant_id = "testco"

        def fake_paths(tid):
            base = self.root / tid
            return {
                "knowledge_dir": base / "knowledge",
                "knowledge_manifest": base / "knowledge_manifest.json",
            }

        self.p_paths = patch.object(knowledge_api, "_paths", side_effect=fake_paths)
        self.p_paths.start()

    def tearDown(self):
        self.p_paths.stop()
        self.tmp.cleanup()

    def test_save_and_delete_article(self):
        saved = knowledge_api.save_article(
            self.tenant_id,
            {
                "slug": "en1",
                "title": "EN1 Test",
                "product": "en1",
                "tags": ["saas"],
                "body": "# EN1\n\nContenido de prueba.",
            },
        )
        self.assertEqual(saved["slug"], "en1")
        items = knowledge_api.list_knowledge(self.tenant_id)
        self.assertEqual(len(items), 1)
        self.assertTrue(items[0]["available"])

        loaded = knowledge_api.load_article("en1", self.tenant_id)
        self.assertIn("Contenido de prueba", loaded["body"])

        knowledge_api.delete_article("en1", self.tenant_id)
        self.assertEqual(knowledge_api.list_knowledge(self.tenant_id), [])


if __name__ == "__main__":
    unittest.main()
