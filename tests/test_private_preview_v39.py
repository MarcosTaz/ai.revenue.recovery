"""V39 synthetic-only live integration tests. No external traffic or real data."""
import os
import unittest
from unittest.mock import patch

class TestPrivatePreview(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        env=patch.dict(os.environ,{"AERVIND_NO_SEND_HOLD":"ACTIVE","AERVIND_ENV":"preview"})
        env.start()
        cls.addClassCleanup(env.stop)
        from api.index import app,EXAMPLE
        cls.client=app.test_client()
        cls.example=EXAMPLE
    def test_health(self):
        r=self.client.get("/api/health")
        self.assertEqual(r.status_code,200)
        self.assertFalse(r.json["customer_data_allowed"])
        self.assertEqual(r.json["external_send"],"HOLD")
    def test_real_engine(self):
        r=self.client.post("/api/evaluate",json=self.example)
        self.assertEqual(r.status_code,200,r.json)
        self.assertIn("evaluation",r.json)
        self.assertIn("management_truth",r.json)
        self.assertIn("workflow",r.json)
    def test_case_export(self):
        r=self.client.post("/api/case-export",json={"payload":self.example})
        self.assertEqual(r.status_code,200,r.json)
        self.assertIn("case",r.json)
    def test_customer_data_blocked(self):
        r=self.client.post("/api/evaluate",json={"real":True})
        self.assertEqual(r.status_code,403)
    def test_package_requires_review(self):
        r=self.client.post("/api/claim-package",json={"payload":self.example,"human_release_confirmed":False})
        self.assertEqual(r.status_code,422)
    def test_static(self):
        for path in ("/","/app.css","/app.js"):
            with self.subTest(path=path):
                r=self.client.get(path)
                self.assertEqual(r.status_code,200)
                self.assertEqual(r.headers.get("Cache-Control"),"no-store")
    def test_cross_origin_denied(self):
        r=self.client.post("/api/evaluate",json=self.example,headers={"Origin":"https://outside.invalid"})
        self.assertEqual(r.status_code,403)
    def test_hold_fail_closed(self):
        with patch.dict(os.environ,{"AERVIND_NO_SEND_HOLD":"INACTIVE"}):
            self.assertEqual(self.client.get("/api/health").status_code,503)
if __name__=="__main__":unittest.main()
