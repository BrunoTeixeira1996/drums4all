import tempfile
import unittest
from pathlib import Path

import app as drums4all


class ApiTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        drums4all.app.config["TABS"] = Path(self.tmp.name)
        drums4all.seed()
        self.client = drums4all.app.test_client()

    def tearDown(self):
        self.tmp.cleanup()

    def test_seeds_examples(self):
        titles = [t["title"] for t in self.client.get("/api/tabs").json]
        self.assertIn("Basic rock", titles)
        self.assertEqual(len(titles), 5)

    def test_create_save_delete(self):
        r = self.client.post("/api/tabs", json={"text": "Title: My Groove Ç\nS|o-o-|\n"})
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.json["id"], "my-groove-c")
        # same title gets a new id instead of overwriting
        self.assertEqual(self.client.post("/api/tabs", json={"text": "Title: My Groove Ç\n"}).json["id"], "my-groove-c-2")

        r = self.client.put("/api/tabs/my-groove-c", json={"text": "Title: Another\nB|o---|\n"})
        self.assertEqual(r.json["title"], "Another")
        self.assertEqual((Path(self.tmp.name) / "my-groove-c.txt").read_text(), "Title: Another\nB|o---|\n")
        self.assertEqual(self.client.get("/api/tabs/my-groove-c").json["text"], "Title: Another\nB|o---|\n")

        self.assertEqual(self.client.delete("/api/tabs/my-groove-c").status_code, 204)
        self.assertEqual(self.client.get("/api/tabs/my-groove-c").status_code, 404)

    def test_folders(self):
        r = self.client.post("/api/tabs", json={"text": "Title: Singles\nS|o-o-|\n", "folder": "exercises"})
        self.assertEqual(r.json, {"id": "exercises/singles", "title": "Singles", "folder": "exercises"})
        self.assertTrue((Path(self.tmp.name) / "exercises" / "singles.txt").exists())
        listed = {t["id"]: t["folder"] for t in self.client.get("/api/tabs").json}
        self.assertEqual(listed["exercises/singles"], "exercises")
        self.assertEqual(listed["rock"], "")
        self.assertEqual(self.client.get("/api/tabs/exercises/singles").json["text"], "Title: Singles\nS|o-o-|\n")
        self.assertEqual(self.client.put("/api/tabs/exercises/singles", json={"text": "Title: Singles\n"}).status_code, 200)

        # a folder is removed once its last tab is deleted
        self.assertEqual(self.client.post("/api/tabs", json={"text": "Title: Singles\n", "folder": "exercises"}).json["id"],
                         "exercises/singles-2")
        self.assertEqual(self.client.delete("/api/tabs/exercises/singles").status_code, 204)
        self.assertEqual(self.client.delete("/api/tabs/exercises/singles-2").status_code, 204)
        self.assertFalse((Path(self.tmp.name) / "exercises").exists())
        self.assertEqual(self.client.post("/api/tabs", json={"text": "", "folder": "../x"}).status_code, 400)
        self.assertEqual(self.client.post("/api/tabs", json={"text": "", "folder": "a/b"}).status_code, 400)
        self.assertEqual(self.client.get("/api/tabs/a/b/c").status_code, 404)
        self.assertEqual(self.client.get("/api/tabs/../app").status_code, 404)

    def test_rejects_bad_input(self):
        self.assertEqual(self.client.put("/api/tabs/rock", json={"nope": 1}).status_code, 400)
        self.assertEqual(self.client.put("/api/tabs/nao-existe", json={"text": ""}).status_code, 404)
        self.assertEqual(self.client.get("/api/tabs/..%2Fapp").status_code, 404)
        self.assertEqual(self.client.get("/api/tabs/.hidden").status_code, 404)

    def test_serves_page(self):
        r = self.client.get("/")
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"<title>drums4all</title>", r.data)
        r.close()


if __name__ == "__main__":
    unittest.main()
