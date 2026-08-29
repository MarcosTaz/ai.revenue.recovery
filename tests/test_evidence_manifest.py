import unittest

from govmargin.evidence_manifest import MAX_EVIDENCE_BYTES, build_evidence_manifest


class EvidenceManifestTests(unittest.TestCase):
    def kwargs(self):
        return dict(
            organization_id="org-a",
            evidence_id="ev-1",
            filename="contract.pdf",
            content_type="application/pdf",
            content=b"synthetic contract bytes",
            captured_at="2026-08-29T20:00:00+00:00",
        )

    def test_builds_immutable_hash_manifest(self):
        manifest = build_evidence_manifest(**self.kwargs())
        self.assertEqual(manifest.organization_id, "org-a")
        self.assertEqual(len(manifest.sha256), 64)
        self.assertEqual(manifest.byte_size, len(b"synthetic contract bytes"))

    def test_rejects_cross_platform_path_filename(self):
        for filename in ("../contract.pdf", "folder/contract.pdf", "folder\\contract.pdf"):
            data = self.kwargs()
            data["filename"] = filename
            with self.subTest(filename=filename), self.assertRaises(ValueError):
                build_evidence_manifest(**data)

    def test_rejects_unsupported_content_type(self):
        data = self.kwargs()
        data["content_type"] = "application/x-msdownload"
        with self.assertRaises(ValueError):
            build_evidence_manifest(**data)

    def test_rejects_empty_content(self):
        data = self.kwargs()
        data["content"] = b""
        with self.assertRaises(ValueError):
            build_evidence_manifest(**data)

    def test_rejects_oversized_content(self):
        data = self.kwargs()
        data["content"] = b"x" * (MAX_EVIDENCE_BYTES + 1)
        with self.assertRaises(ValueError):
            build_evidence_manifest(**data)

    def test_rejects_naive_capture_time(self):
        data = self.kwargs()
        data["captured_at"] = "2026-08-29T20:00:00"
        with self.assertRaises(ValueError):
            build_evidence_manifest(**data)

    def test_rejects_missing_tenant_identity(self):
        data = self.kwargs()
        data["organization_id"] = ""
        with self.assertRaises(ValueError):
            build_evidence_manifest(**data)


if __name__ == "__main__":
    unittest.main()
