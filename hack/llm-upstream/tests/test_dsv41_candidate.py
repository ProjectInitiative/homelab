import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
LOCK_PATH = ROOT / "llm-test/lanes/dsv41/upstream.lock.json"
STOCK_MANIFEST = ROOT / "llm-test/dsv41-parity/12-dsv41-parity.yaml"
CANDIDATE_DIR = ROOT / "llm-test/dsv41-parity/cooperative-moe-candidate"
CANDIDATE_MANIFEST = CANDIDATE_DIR / "01-stage-and-gate.yaml"
PREPARE = CANDIDATE_DIR / "prepare_candidate.py"
VENDORED_EXTENSION = ROOT / "llm-test/lanes/dsv41/vendor/extensions/cooperative_moe"


class Dsv41CandidateContractTests(unittest.TestCase):
    def test_candidate_is_separate_blocked_and_unqualified(self):
        lock = json.loads(LOCK_PATH.read_text())
        self.assertEqual(lock["schemaVersion"], 3)
        self.assertEqual(lock["recipe"]["reviewedRevision"], "f083d7e4ccc8cc1083ef739945a3114f54a8bef5")
        self.assertEqual(lock["adoption"]["status"], "runtime-current")
        self.assertFalse(lock["adoption"]["reviewedRuntimeChanged"])
        self.assertTrue(lock["adoption"]["reviewedOptionalRuntimeChanged"])
        candidate = lock["runtimeCandidates"]["cooperativeMoe"]
        self.assertEqual(candidate["status"], "built-unqualified")
        self.assertEqual(candidate["mode"], "optional-off-by-default")
        self.assertEqual(candidate["upstreamArtifact"]["availability"], "unavailable-in-git-and-releases")
        local = candidate["localCandidate"]
        self.assertEqual(local["binarySha256"], "16191d208101a3a04b021f8a2d0da360c5ebb710c0145b2e312052a02ce40305")
        self.assertEqual(local["pristineRuntimeSha256"], "9f1d10ffc39ac4433828a000c4932a4a773b00acadd80b46c7568f494a77b2fb")
        self.assertEqual(local["runtimeSha256"], "2d33c5cd57c447b4d6545abfb59356ca7ee9cefe8aa2e4fe2c2023fe09bf35de")
        provenance = local["buildProvenance"]
        self.assertEqual(provenance["exllamaRevision"], "02aef45cd681b960a00afcd0749a4ab99e6c1bfe")
        self.assertEqual(provenance["archiveFilename"], "dsv41-coop-build-input.tgz")
        self.assertEqual(provenance["archiveSha256"], "f0760e9cd4bd5019f87b38df6aa788123794fb541f2e58998eae52c8a0d5b32b")
        self.assertEqual(provenance["imageDigest"], lock["image"]["digest"])
        self.assertEqual(provenance["exllamaRepo"], "https://github.com/turboderp-org/exllamav3.git")
        self.assertEqual(provenance["buildScript"], "extensions/cooperative_moe/build.sh")
        self.assertEqual(provenance["buildScriptSha256"], "0eca829cf4045ea35c2b0a7a422eeef8abdabdedc68834084aad4f64a1f4b048")
        self.assertEqual(provenance["buildCommand"], "bash /work/input/extension/build.sh /work/input/upstream /work/output")
        self.assertIsNone(provenance["compilerIdentity"])
        self.assertIsNone(provenance["buildLogSha256"])
        self.assertEqual(candidate["qualification"], {
            "chronometerGpu54": "pending",
            "promotionApproved": False,
            "servingAB": "pending",
            "sextantGpu54": "pending",
        })

    def test_stock_lane_and_pins_are_unchanged(self):
        lock = json.loads(LOCK_PATH.read_text())
        stock = STOCK_MANIFEST.read_text()
        self.assertEqual(lock["image"]["digest"], "sha256:2f0cf3adc0f989c1d446be274df864eb799630175f604c3b22b71b7205971dce")
        self.assertEqual(lock["models"]["weights"]["revision"], "64ba41b6c916a587db06eae2e19b7845f7be6e6b")
        self.assertEqual(lock["models"]["native"]["revision"], "dba1be0a40aa45a94ad051997016db3960a90277")
        for value in ("MAX_MODEL_LEN=600000", "MAX_NUM_SEQS=8", "MAX_NUM_BATCHED_TOKENS=2048", "PORT=8000"):
            self.assertIn(value, stock)
        self.assertEqual(stock.count("spec:\n  replicas: 0"), 2)
        self.assertEqual(stock.count('cp /opt/dsv41/exl3.py "$SITE/model_executor/layers/quantization/exl3.py"'), 2)
        self.assertNotIn("exl3-cooperative.py", stock)

    def test_candidate_jobs_are_suspended_fail_closed_and_node_symmetric(self):
        text = CANDIDATE_MANIFEST.read_text()
        self.assertNotIn("kind: Deployment", text)
        self.assertEqual(text.count("kind: Job"), 4)
        self.assertEqual(text.count("suspend: true"), 4)
        self.assertEqual(text.count("ttlSecondsAfterFinished: 259200"), 4)
        self.assertEqual(text.count("activeDeadlineSeconds: 1800"), 4)
        self.assertEqual(text.count("backoffLimit: 0"), 4)
        self.assertEqual(text.count("automountServiceAccountToken: false"), 4)
        self.assertEqual(text.count("kubernetes.io/hostname: chronometer"), 2)
        self.assertEqual(text.count("kubernetes.io/hostname: sextant"), 2)
        self.assertEqual(text.count('nvidia.com/gpu: "1"'), 4)
        self.assertIn("set -euo pipefail", text)
        self.assertIn("sha256sum -c", text)
        self.assertIn("2d33c5cd57c447b4d6545abfb59356ca7ee9cefe8aa2e4fe2c2023fe09bf35de  runtime.py", text)
        for line in (CANDIDATE_DIR / "SHA256SUMS").read_text().splitlines():
            self.assertIn(f"    {line}", text)
        self.assertIn("'\"checks\": 54'", text)
        self.assertNotIn("binaryData:", text)

    def test_no_native_library_is_stored_in_repository(self):
        libraries = [path for path in ROOT.rglob("*.so") if ".git" not in path.parts]
        self.assertEqual(libraries, [])
        self.assertIn(
            "llm-test/lanes/*/vendor/**/*.so",
            (ROOT / ".gitignore").read_text().splitlines(),
        )

    def test_candidate_generator_patches_one_pin_without_mutating_inputs(self):
        spec = importlib.util.spec_from_file_location("dsv41_candidate_prepare", PREPARE)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        pristine_path = VENDORED_EXTENSION / "runtime.py"
        pristine = pristine_path.read_bytes()
        expected = pristine.replace(
            module.UPSTREAM_BINARY_SHA256.encode(), module.BINARY_SHA256.encode()
        )
        self.assertEqual(pristine.count(module.UPSTREAM_BINARY_SHA256.encode()), 1)
        self.assertEqual(hashlib.sha256(expected).hexdigest(), module.CANDIDATE_RUNTIME_SHA256)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifacts = root / "inputs"
            artifacts.mkdir()
            binary = artifacts / "cooperative_moe.so"
            binary.write_bytes(b"fixture-native")
            (artifacts / "runtime.py").write_bytes(pristine)
            (artifacts / "test_cuda_integration.py").write_bytes(
                (VENDORED_EXTENSION / "test_cuda_integration.py").read_bytes()
            )
            (artifacts / "test_exl3_overlay.py").write_bytes(
                (ROOT / "llm-test/lanes/dsv41/vendor/tests/test_exl3_overlay.py").read_bytes()
            )
            fixture_binary_sha = hashlib.sha256(binary.read_bytes()).hexdigest()
            fixture_runtime = pristine.replace(
                module.UPSTREAM_BINARY_SHA256.encode(), fixture_binary_sha.encode()
            )
            module.BINARY_SHA256 = fixture_binary_sha
            module.CANDIDATE_RUNTIME_SHA256 = hashlib.sha256(fixture_runtime).hexdigest()
            output = root / "bundle"
            module.make_bundle(
                ROOT / "llm-test/lanes/dsv41/vendor/overlay/exl3.py", artifacts, output
            )
            self.assertEqual((artifacts / "runtime.py").read_bytes(), pristine)
            self.assertEqual((output / "runtime.py").read_bytes(), fixture_runtime)
            self.assertEqual(hashlib.sha256((output / "exl3-cooperative.py").read_bytes()).hexdigest(), "b68bf2405d8d427407fcc18f728943cda964376a4c25637f5e9f5d791a3a6aac")
            self.assertEqual({path.name for path in output.iterdir()}, {
                "cooperative_moe.so", "runtime.py", "exl3-cooperative.py",
                "test_cuda_integration.py", "test_exl3_overlay.py",
            })
            with self.assertRaises(FileExistsError):
                module.make_bundle(
                    ROOT / "llm-test/lanes/dsv41/vendor/overlay/exl3.py", artifacts, output
                )
            binary.write_bytes(b"wrong")
            with self.assertRaises(ValueError):
                module.make_bundle(
                    ROOT / "llm-test/lanes/dsv41/vendor/overlay/exl3.py",
                    artifacts,
                    root / "other",
                )

    def test_vendored_build_script_on_nix_with_resolved_bash(self):
        bash = shutil.which("bash")
        self.assertIsNotNone(bash)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            upstream = root / "upstream/exllamav3/exllamav3_ext/quant"
            upstream.mkdir(parents=True)
            (upstream / "keep.h").write_text("// fixture\n")
            nvcc = root / "nvcc"
            nvcc.write_text(
                f"#!{bash}\nset -euo pipefail\nout=\n"
                "while [ $# -gt 0 ]; do\n"
                "  case \"$1\" in -o) out=$2; shift 2 ;; *) shift ;; esac\n"
                "done\nprintf stub > \"$out\"\n"
            )
            nvcc.chmod(nvcc.stat().st_mode | stat.S_IEXEC)
            output = root / "output"
            output.mkdir()
            env = os.environ.copy()
            env["NVCC"] = str(nvcc)
            proc = subprocess.run(
                [bash, str(VENDORED_EXTENSION / "build.sh"), str(root / "upstream"), str(output)],
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
            self.assertTrue((output / "cooperative_moe.so").is_file())
            self.assertTrue((output / "runtime.py").is_file())


if __name__ == "__main__":
    unittest.main()
