import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "sync.py"
SPEC = importlib.util.spec_from_file_location("llm_upstream_sync", SCRIPT)
SYNC = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(SYNC)


def run(*args, cwd):
    return subprocess.run(args, cwd=cwd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


class SyncTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.source = self.root / "source"
        self.source.mkdir()
        run("git", "init", "-q", cwd=self.source)
        run("git", "config", "user.name", "fixture", cwd=self.source)
        run("git", "config", "user.email", "fixture@example.invalid", cwd=self.source)
        run("git", "remote", "add", "origin", "https://example.invalid/upstream.git/", cwd=self.source)
        (self.source / "runtime.sh").write_text("echo fixture\n")
        (self.source / "not-selected.txt").write_text("must not be copied\n")
        run("git", "add", ".", cwd=self.source)
        run("git", "commit", "-qm", "fixture", cwd=self.source)
        self.revision = self.git_sha("HEAD")
        (self.source / "README.md").write_text("documentation only\n")
        run("git", "add", "README.md", cwd=self.source)
        run("git", "commit", "-qm", "docs", cwd=self.source)
        self.reviewed_revision = self.git_sha("HEAD")

        self.lanes = self.root / "llm-test" / "lanes"
        lane = self.lanes / "fixture"
        vendor = lane / "vendor"
        vendor.mkdir(parents=True)
        (lane / "serve.yaml").write_text(
            "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: fixture-head\n"
            "spec:\n  replicas: 0\n---\napiVersion: apps/v1\nkind: Deployment\n"
            "metadata:\n  name: fixture-worker\nspec:\n  replicas: 0\n"
        )
        digest = hashlib.sha256(b"echo fixture\n").hexdigest()
        (vendor / "runtime.sh").write_text("echo fixture\n")
        source_record = {
            "repo": "https://example.invalid/upstream.git",
            "revision": self.revision,
            "files": {"runtime.sh": digest},
        }
        (vendor / "SOURCE.json").write_text(json.dumps(source_record))
        model_revision = "2" * 40
        image_digest = "sha256:" + "1" * 64
        bundle = {
            "recipeRevision": self.revision,
            "imageDigest": image_digest,
            "modelRevisions": {"weights": model_revision},
        }
        lock = {
            "schemaVersion": 2,
            "lane": "fixture",
            "recipe": {
                "repo": "https://example.invalid/upstream.git",
                "runtimeBaseline": self.revision,
                "reviewedRevision": self.reviewed_revision,
                "vendorRevision": self.revision,
                "reviewedChangeSummary": "one docs commit",
                "files": {"runtime.sh": digest},
                "requiredRuntimeReferences": [],
            },
            "image": {
                "ref": "example.invalid/image:test",
                "digest": image_digest,
                "provenanceStatus": "fixture provenance",
                "recipeRevision": self.revision,
            },
            "models": {"weights": {"repo": "example/model", "revision": model_revision}},
            "bundle": bundle,
            "adoption": {
                "status": "runtime-current",
                "reason": "reviewed change is documentation only",
                "reviewedRevision": self.reviewed_revision,
                "reviewedRuntimeChanged": False,
                **bundle,
            },
            "safety": {
                "desiredReplicas": 0,
                "activationOrder": ["worker", "head"],
                "deploymentEnabled": False,
            },
        }
        (lane / "upstream.lock.json").write_text(json.dumps(lock))
        contract = {
            "schemaVersion": 1,
            "lane": "fixture",
            "fileAssertions": [{"path": "llm-test/lanes/fixture/serve.yaml", "text": "replicas: 0", "count": 2}],
            "servingManifests": ["llm-test/lanes/fixture/serve.yaml"],
            "preservedPolicy": ["fixture remains inert"],
            "adoptionBlockers": [],
        }
        (lane / "contract.json").write_text(json.dumps(contract))
        (lane / "drift.md").write_text("placeholder\n")
        self.old_root, self.old_lanes = SYNC.ROOT, SYNC.LANES
        SYNC.ROOT, SYNC.LANES = self.root, self.lanes

    def git_sha(self, revision):
        return subprocess.check_output(["git", "rev-parse", revision], cwd=self.source, text=True).strip()

    def tearDown(self):
        SYNC.ROOT, SYNC.LANES = self.old_root, self.old_lanes
        self.temporary.cleanup()

    def test_update_selectively_exports_hashes_and_resets_adoption(self):
        SYNC.update_lane("fixture", self.revision, self.reviewed_revision, str(self.source), True)
        lane = self.lanes / "fixture"
        self.assertEqual((lane / "vendor/runtime.sh").read_text(), "echo fixture\n")
        self.assertFalse((lane / "vendor/not-selected.txt").exists())
        lock = json.loads((lane / "upstream.lock.json").read_text())
        self.assertEqual(lock["adoption"]["status"], "pending-review")
        self.assertTrue(lock["adoption"]["reviewedRuntimeChanged"])
        self.assertIn("default runtime files changed: none", lock["recipe"]["reviewedChangeSummary"])
        self.assertEqual(SYNC.verify_lane("fixture"), [])

    def test_rejects_traversal_and_symlinked_lane(self):
        for name in ("../fixture", "fixture/child", "/tmp/fixture", "fixture..evil"):
            with self.assertRaisesRegex(SYNC.Error, "unsafe lane name"):
                SYNC.checked_lane_dir(name)
        external = self.root / "external"
        external.mkdir()
        (self.lanes / "linked").symlink_to(external, target_is_directory=True)
        with self.assertRaisesRegex(SYNC.Error, "non-symlink"):
            SYNC.checked_lane_dir("linked")

    def test_rejects_symlinked_vendor_and_nested_vendor_file(self):
        lane = self.lanes / "fixture"
        vendor = lane / "vendor"
        moved = lane / "vendor-real"
        vendor.rename(moved)
        vendor.symlink_to(moved, target_is_directory=True)
        with self.assertRaisesRegex(SYNC.Error, "symlinked path"):
            SYNC.lane_paths("fixture")
        vendor.unlink()
        moved.rename(vendor)
        (vendor / "runtime.sh").unlink()
        (vendor / "runtime.sh").symlink_to(self.source / "runtime.sh")
        with self.assertRaisesRegex(SYNC.Error, "symlinked vendor file"):
            SYNC.inventory_files(vendor)

    def test_vendor_inventory_ignores_python_cache_artifacts(self):
        vendor = self.lanes / "fixture/vendor"
        cache = vendor / "nested/__pycache__"
        cache.mkdir(parents=True)
        (cache / "runtime.cpython-313.pyc").write_bytes(b"transient")
        (vendor / "orphan.pyc").write_bytes(b"transient")
        self.assertEqual(SYNC.inventory_files(vendor), {"runtime.sh"})
        self.assertEqual(SYNC.verify_lane("fixture"), [])

    def test_wrong_remote_is_rejected(self):
        run("git", "remote", "set-url", "origin", "https://example.invalid/wrong.git", cwd=self.source)
        with self.assertRaisesRegex(SYNC.Error, "origin URL does not match"):
            SYNC.update_lane("fixture", self.revision, self.reviewed_revision, str(self.source), True)

    def test_source_json_repo_must_match_lock(self):
        source_path = self.lanes / "fixture/vendor/SOURCE.json"
        source = json.loads(source_path.read_text())
        source["repo"] = "https://example.invalid/wrong.git"
        source_path.write_text(json.dumps(source))
        self.assertTrue(
            any("SOURCE.json does not match" in item for item in SYNC.verify_lane("fixture"))
        )

    def test_git_replacement_refs_are_ignored(self):
        (self.source / "runtime.sh").write_text("echo malicious replacement\n")
        run("git", "add", "runtime.sh", cwd=self.source)
        run("git", "commit", "-qm", "replacement target", cwd=self.source)
        replacement = self.git_sha("HEAD")
        run("git", "replace", self.revision, replacement, cwd=self.source)
        blob = SYNC.git("show", f"{self.revision}:runtime.sh", cwd=self.source)
        self.assertEqual(blob, b"echo fixture\n")

    def test_unreachable_vendor_revision_is_rejected(self):
        run("git", "checkout", "-q", "--orphan", "unrelated", cwd=self.source)
        for path in self.source.iterdir():
            if path.name != ".git" and path.is_file():
                path.unlink()
        (self.source / "runtime.sh").write_text("unrelated\n")
        run("git", "add", "-A", cwd=self.source)
        run("git", "commit", "-qm", "unrelated", cwd=self.source)
        unrelated = self.git_sha("HEAD")
        with self.assertRaisesRegex(SYNC.Error, "not reachable"):
            SYNC.update_lane("fixture", unrelated, self.reviewed_revision, str(self.source), True)

    def test_runtime_baseline_must_be_in_reviewed_history(self):
        run("git", "checkout", "-q", "--orphan", "bad-baseline", cwd=self.source)
        for path in self.source.iterdir():
            if path.name != ".git" and path.is_file():
                path.unlink()
        (self.source / "runtime.sh").write_text("unrelated baseline\n")
        run("git", "add", "-A", cwd=self.source)
        run("git", "commit", "-qm", "bad baseline", cwd=self.source)
        bad_baseline = self.git_sha("HEAD")
        lock_path = self.lanes / "fixture/upstream.lock.json"
        lock = json.loads(lock_path.read_text())
        lock["recipe"]["runtimeBaseline"] = bad_baseline
        lock["image"]["recipeRevision"] = bad_baseline
        lock["bundle"]["recipeRevision"] = bad_baseline
        lock["adoption"]["recipeRevision"] = bad_baseline
        lock["adoption"]["status"] = "pending-review"
        lock["adoption"]["reviewedRuntimeChanged"] = True
        lock["adoption"]["reason"] = "fixture pending review"
        lock_path.write_text(json.dumps(lock))
        with self.assertRaisesRegex(SYNC.Error, "runtime baseline is not an ancestor"):
            SYNC.update_lane("fixture", self.revision, self.reviewed_revision, str(self.source), True)

    def test_exact_replicas_path_rejects_false_positive(self):
        false_positive = (
            "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  replicas: 0\n"
            "spec:\n  template:\n    spec:\n      replicas: 0\n"
        )
        with self.assertRaisesRegex(SYNC.Error, "spec.replicas"):
            SYNC.deployment_spec_replicas(false_positive)
        nested_zero = "kind: Deployment\nspec:\n  replicas: 1\n  template:\n    spec:\n      replicas: 0\n"
        self.assertEqual(SYNC.deployment_spec_replicas(nested_zero), 1)

    def test_strict_schema_rejects_missing_contract_field(self):
        contract = json.loads((self.lanes / "fixture/contract.json").read_text())
        del contract["servingManifests"]
        with self.assertRaisesRegex(SYNC.Error, "expected keys"):
            SYNC.check_contract(contract, "fixture")

    def test_unsafe_inventory_path_is_rejected(self):
        lock = json.loads((self.lanes / "fixture/upstream.lock.json").read_text())
        lock["recipe"]["files"] = {"../escape": "0" * 64}
        with self.assertRaisesRegex(SYNC.Error, "unsafe inventory path"):
            SYNC.check_lock(lock, "fixture")

    def test_v3_candidate_cannot_skip_gpu_gates_or_approval(self):
        lock = json.loads((self.lanes / "fixture/upstream.lock.json").read_text())
        lock["schemaVersion"] = 3
        lock["recipe"]["optionalRuntimeReferences"] = ["runtime.sh"]
        lock["adoption"]["reviewedOptionalRuntimeChanged"] = True
        lock["runtimeCandidates"] = {
            "candidate": {
                "upstreamRevision": self.reviewed_revision,
                "mode": "optional-off-by-default",
                "status": "built-unqualified",
                "requiredFiles": ["runtime.sh"],
                "upstreamArtifact": {
                    "sha256": "3" * 64,
                    "availability": "unavailable-in-git-and-releases",
                },
                "localCandidate": {
                    "binarySha256": "4" * 64,
                    "pristineRuntimeSha256": "5" * 64,
                    "runtimeSha256": "6" * 64,
                    "buildProvenance": {
                        "exllamaRepo": "https://example.invalid/exllamav3.git",
                        "exllamaRevision": "7" * 40,
                        "archiveFilename": "input.tgz",
                        "archiveSha256": "8" * 64,
                        "imageDigest": "sha256:" + "9" * 64,
                        "buildScript": "extension/build.sh",
                        "buildScriptSha256": "b" * 64,
                        "buildCommand": "bash extension/build.sh input output",
                        "compilerIdentity": None,
                        "buildLogSha256": None,
                    },
                },
                "qualification": {
                    "chronometerGpu54": "pending",
                    "sextantGpu54": "pending",
                    "servingAB": "pending",
                    "promotionApproved": False,
                },
            }
        }
        SYNC.check_lock(lock, "fixture")
        candidate = lock["runtimeCandidates"]["candidate"]
        candidate["qualification"]["servingAB"] = "pass"
        with self.assertRaisesRegex(SYNC.Error, "before both GPU gates"):
            SYNC.check_lock(lock, "fixture")
        candidate["qualification"].update({
            "chronometerGpu54": "pass", "sextantGpu54": "pass",
        })
        candidate["status"] = "qualified"
        with self.assertRaisesRegex(SYNC.Error, "pending build provenance"):
            SYNC.check_lock(lock, "fixture")
        candidate["localCandidate"]["buildProvenance"].update({
            "compilerIdentity": "nvcc fixture",
            "buildLogSha256": "a" * 64,
        })
        with self.assertRaisesRegex(SYNC.Error, "before all gates and approval"):
            SYNC.check_lock(lock, "fixture")

        lock["schemaVersion"] = 4
        candidate["status"] = "gpu-gated-unqualified"
        candidate["qualification"]["servingAB"] = "pending"
        result = {
            "bundleStaged": True,
            "checks": 54,
            "strictRawDifferences": 10,
            "strictPostBf16Differences": 8,
            "numericalScreenReferencePeakPercent": 0.3,
            "distributedServingVerified": False,
        }
        candidate["gpuGateEvidence"] = {
            "chronometer": dict(result), "sextant": dict(result),
        }
        SYNC.check_lock(lock, "fixture")
        candidate["status"] = "qualified"
        with self.assertRaisesRegex(SYNC.Error, "before all gates and approval"):
            SYNC.check_lock(lock, "fixture")
        candidate["qualification"]["servingAB"] = "pass"
        with self.assertRaisesRegex(SYNC.Error, "before all gates and approval"):
            SYNC.check_lock(lock, "fixture")
        candidate["qualification"]["promotionApproved"] = True
        SYNC.check_lock(lock, "fixture")
        candidate["gpuGateEvidence"]["sextant"]["distributedServingVerified"] = True
        with self.assertRaisesRegex(SYNC.Error, "must be staged and not serving-verified"):
            SYNC.check_lock(lock, "fixture")

        candidate["gpuGateEvidence"]["sextant"]["distributedServingVerified"] = False
        lock["schemaVersion"] = 5
        candidate["status"] = "serving-validated-unapproved"
        candidate["qualification"]["promotionApproved"] = False
        candidate["servingEvidence"] = {
            "matchedStock": {
                "c1MedianTokensPerSecond": 10.0, "c2MedianTokensPerSecond": 20.0,
            },
            "cooperative": {
                "c1MedianTokensPerSecond": 12.0, "c2MedianTokensPerSecond": 25.0,
            },
            "supplementalStockOperational": {
                "c1MedianTokensPerSecond": 11.0, "c2MedianTokensPerSecond": 19.0,
            },
            "matchedGainPercent": {
                "c1MedianTokensPerSecond": 20.0, "c2MedianTokensPerSecond": 25.0,
            },
            "protocol": {
                "repetitions": 3, "maxCompletionTokens": 400,
                "streaming": True, "thinking": False,
            },
            "runtime": {
                "selectedProfile": "cooperative", "bothRanksActivated": True,
                "activationHashesLogged": True, "cooperativeRuntimeLogged": True,
                "packedEngram": True, "readinessSucceeded": True, "zeroRestarts": True,
                "externalHealthHttpStatus": 200, "externalModelsHttpStatus": 200,
                "nonThinkingSmokeCompletionTokens": 323,
            },
        }
        SYNC.check_lock(lock, "fixture")
        candidate["qualification"]["servingAB"] = "pending"
        with self.assertRaisesRegex(SYNC.Error, "serving-validated state is inconsistent"):
            SYNC.check_lock(lock, "fixture")
        candidate["qualification"]["servingAB"] = "pass"
        candidate["qualification"]["chronometerGpu54"] = "pending"
        with self.assertRaisesRegex(SYNC.Error, "before both GPU gates"):
            SYNC.check_lock(lock, "fixture")
        candidate["qualification"]["chronometerGpu54"] = "pass"
        candidate["localCandidate"]["buildProvenance"]["compilerIdentity"] = None
        with self.assertRaisesRegex(SYNC.Error, "serving-validated state is inconsistent"):
            SYNC.check_lock(lock, "fixture")
        candidate["localCandidate"]["buildProvenance"]["compilerIdentity"] = "nvcc fixture"
        candidate["qualification"]["promotionApproved"] = True
        with self.assertRaisesRegex(SYNC.Error, "serving-validated state is inconsistent"):
            SYNC.check_lock(lock, "fixture")

    def test_drift_report_is_deterministic(self):
        SYNC.report_lane("fixture", False)
        first = (self.lanes / "fixture/drift.md").read_bytes()
        SYNC.report_lane("fixture", True)
        self.assertEqual(first, (self.lanes / "fixture/drift.md").read_bytes())


if __name__ == "__main__":
    unittest.main()
