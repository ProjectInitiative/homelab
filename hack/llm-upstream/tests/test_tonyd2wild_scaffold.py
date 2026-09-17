from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[3]
LANE = ROOT / "llm-test/tonyd2wild-glm53"
DOWNLOAD = LANE / "05-tonyd2wild-download.yaml"
SERVING = LANE / "12-tonyd2wild-glm53.yaml"
README = LANE / "README.md"


class Tonyd2wildScaffoldTests(unittest.TestCase):
    def test_download_is_inert_pinned_and_non_destructive(self):
        text = DOWNLOAD.read_text()
        self.assertEqual(text.count("kind: Job"), 1)
        self.assertEqual(text.count("suspend: true"), 1)
        self.assertEqual(text.count("ttlSecondsAfterFinished: 259200"), 1)
        self.assertIn(
            "glm53-cache-puller:v5@sha256:4ac2072503bd68a509e556c1e1970ba498c4c7d632205879be623126b53e49ec",
            text,
        )
        for revision in (
            "c245560b6d7e62c329cd3042343b358a4279affd",
            "80b6d18d77e3020f2384597081d405f19893f101",
            "dc77ff1c99eeb2df044ee3d4f0094eb033fee410",
        ):
            self.assertIn(revision, text)
        self.assertNotIn("DELETE_MODELS", text)
        self.assertNotIn("DELETE_REPOS", text)
        self.assertNotRegex(text, r"\brm\s+(?:-[^\n ]*r[^\n ]*|--recursive)\b")
        self.assertIn(
            """- name: HF_TOKEN
              valueFrom:
                secretKeyRef:
                  name: huggingface
                  key: HF_TOKEN
                  optional: true""",
            text,
        )
        self.assertNotIn("HF_TOKEN=", text)

    def test_serving_is_zero_scaled_and_immutable(self):
        text = SERVING.read_text()
        self.assertEqual(text.count("kind: Deployment"), 2)
        self.assertEqual(len(re.findall(r"^spec:\n  replicas: 0$", text, re.MULTILINE)), 2)
        self.assertEqual(
            text.count(
                "ghcr.io/tonyd2wild/vllm-glm53-flash:sm121-v11-dflash2@sha256:4def0ef644cb2e9814136dcffd5e385e21bc594f48f3b292234051904abe85a6"
            ),
            4,
        )
        self.assertEqual(text.count("--host 0.0.0.0 --port 8000"), 2)
        self.assertEqual(text.count("claimName: model-cache"), 2)
        self.assertIn("--headless", text)

    def test_known_activation_blockers_are_documented(self):
        text = README.read_text()
        self.assertIn("replicas: 0", text)
        self.assertIn("suspend: true", text)
        self.assertIn("9acb1fbbf6c1a9924651fd8694aa197a266cd6b6", text)
        self.assertIn("port `8000`", text)
        self.assertIn("worker before its head", text)
        self.assertIn("192.168.192.x", text)
        self.assertIn("sparse_attn_indexer_kpool.py", text)
        self.assertIn("multimodal behavior", text)
        self.assertIn("remains unqualified", text)


if __name__ == "__main__":
    unittest.main()
