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
SERVING_DIR = CANDIDATE_DIR / "serving"
STOCK_CONTROL_DIR = CANDIDATE_DIR / "stock-control"
EVIDENCE_DIR = CANDIDATE_DIR / "evidence"
SERVING_PROFILE = SERVING_DIR / "profile.env"
SERVING_ACTIVATION = SERVING_DIR / "activation.yaml"
SERVING_PATCH = SERVING_DIR / "deployments-patch.yaml"
PREPARE = CANDIDATE_DIR / "prepare_candidate.py"
VENDORED_EXTENSION = ROOT / "llm-test/lanes/dsv41/vendor/extensions/cooperative_moe"


class Dsv41CandidateContractTests(unittest.TestCase):
    def test_candidate_is_separate_blocked_and_unqualified(self):
        lock = json.loads(LOCK_PATH.read_text())
        self.assertEqual(lock["schemaVersion"], 5)
        self.assertEqual(lock["recipe"]["reviewedRevision"], "f083d7e4ccc8cc1083ef739945a3114f54a8bef5")
        self.assertEqual(lock["adoption"]["status"], "runtime-current")
        self.assertFalse(lock["adoption"]["reviewedRuntimeChanged"])
        self.assertTrue(lock["adoption"]["reviewedOptionalRuntimeChanged"])
        candidate = lock["runtimeCandidates"]["cooperativeMoe"]
        self.assertEqual(candidate["status"], "serving-validated-unapproved")
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
        self.assertEqual(
            provenance["compilerIdentity"],
            "nvcc: NVIDIA (R) Cuda compiler driver; Cuda compilation tools, release 13.0, V13.0.88; Build cuda_13.0.r13.0/compiler.36424714_0",
        )
        self.assertEqual(
            provenance["buildLogSha256"],
            "c3b122a7ddaf2aa684ce9a8326e6d385bb18ca1a17e0dbb25f91ec3a6c4f2059",
        )
        self.assertEqual(candidate["qualification"], {
            "chronometerGpu54": "pass",
            "promotionApproved": False,
            "servingAB": "pass",
            "sextantGpu54": "pass",
        })
        self.assertEqual(candidate["gpuGateEvidence"], {
            "chronometer": {
                "bundleStaged": True, "checks": 54,
                "distributedServingVerified": False,
                "numericalScreenReferencePeakPercent": 0.3,
                "strictPostBf16Differences": 3912212,
                "strictRawDifferences": 6124458,
            },
            "sextant": {
                "bundleStaged": True, "checks": 54,
                "distributedServingVerified": False,
                "numericalScreenReferencePeakPercent": 0.3,
                "strictPostBf16Differences": 3912165,
                "strictRawDifferences": 6124464,
            },
        })
        serving = candidate["servingEvidence"]
        self.assertEqual(serving["protocol"], {
            "maxCompletionTokens": 400, "repetitions": 3,
            "streaming": True, "thinking": False,
        })
        self.assertEqual(serving["runtime"], {
            "activationHashesLogged": True, "bothRanksActivated": True,
            "cooperativeRuntimeLogged": True, "externalHealthHttpStatus": 200,
            "externalModelsHttpStatus": 200, "nonThinkingSmokeCompletionTokens": 323,
            "packedEngram": True, "readinessSucceeded": True,
            "selectedProfile": "cooperative", "zeroRestarts": True,
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
        self.assertEqual(
            hashlib.sha256(STOCK_MANIFEST.read_bytes()).hexdigest(),
            "8a3f14eb5ffcab2ca280d41211bbc956c829b10d248c348a021e4916fc4544d8",
        )

    def test_recorded_evidence_matches_lock_and_checksums(self):
        lock = json.loads(LOCK_PATH.read_text())
        candidate = lock["runtimeCandidates"]["cooperativeMoe"]
        sums = {}
        for line in (EVIDENCE_DIR / "SHA256SUMS").read_text().splitlines():
            digest, name = line.split(None, 1)
            sums[name] = digest
            self.assertEqual(hashlib.sha256((EVIDENCE_DIR / name).read_bytes()).hexdigest(), digest)
        provenance = candidate["localCandidate"]["buildProvenance"]
        self.assertEqual(sums["cooperative_moe-build.log"], provenance["buildLogSha256"])
        compiler = (EVIDENCE_DIR / "compiler-identity.txt").read_text()
        for fragment in provenance["compilerIdentity"].split("; "):
            self.assertIn(fragment, compiler)
        for node in ("chronometer", "sextant"):
            records = []
            for line in (EVIDENCE_DIR / f"gate-{node}.log").read_text().splitlines():
                if line.startswith("{"):
                    record = json.loads(line)
                    if record.get("stage") == "complete":
                        records.append(record)
            self.assertTrue(records)
            record = records[-1]
            evidence = candidate["gpuGateEvidence"][node]
            self.assertEqual(record["status"], "pass")
            self.assertEqual(record["checks"], evidence["checks"])
            self.assertEqual(record["strict_raw_failed_elements_retained"], evidence["strictRawDifferences"])
            self.assertEqual(record["strict_post_bf16_failed_elements_retained"], evidence["strictPostBf16Differences"])
            self.assertEqual(record["numerical_screen"], "0.3% of reference peak; strict differences retained")
            self.assertFalse(record["distributed_serving_verified"])

        summary = json.loads((EVIDENCE_DIR / "serving-summary.json").read_text())
        serving = candidate["servingEvidence"]
        profiles = {
            "serving-stock-matched.jsonl": ("stock-matched", "stock_matched", "matchedStock"),
            "serving-cooperative.jsonl": ("cooperative", "cooperative", "cooperative"),
            "serving-stock-operational.jsonl": (
                "stock-operational", "stock_operational", "supplementalStockOperational"
            ),
        }
        for filename, (profile, summary_key, lock_key) in profiles.items():
            records = [json.loads(line) for line in (EVIDENCE_DIR / filename).read_text().splitlines()]
            c1 = [record for record in records if record["kind"] == "c1"]
            c2 = [record for record in records if record["kind"] == "c2"]
            self.assertEqual([record["rep"] for record in c1], [1, 2, 3])
            self.assertEqual([record["rep"] for record in c2], [1, 2, 3])
            self.assertTrue(all(record["result"]["completion_tokens"] == 400 for record in c1))
            self.assertTrue(all(
                result["completion_tokens"] == 400
                for record in c2 for result in record["results"]
            ))
            recorded_summary = records[-1]
            self.assertEqual(recorded_summary["kind"], "summary")
            self.assertEqual(recorded_summary["profile"], profile)
            self.assertEqual(recorded_summary["summary"], summary[summary_key])
            self.assertEqual(recorded_summary["summary"]["c1"]["median"], serving[lock_key]["c1MedianTokensPerSecond"])
            self.assertEqual(recorded_summary["summary"]["c2"]["median"], serving[lock_key]["c2MedianTokensPerSecond"])
        self.assertEqual(summary["matched_change_percent"]["c1"], serving["matchedGainPercent"]["c1MedianTokensPerSecond"])
        self.assertEqual(summary["matched_change_percent"]["c2"], serving["matchedGainPercent"]["c2MedianTokensPerSecond"])
        self.assertEqual(set(sums), {
            "benchmark.py", "compiler-identity.txt", "cooperative_moe-build.log",
            "gate-chronometer.log", "gate-sextant.log", "README.md",
            "serving-cooperative.jsonl", "serving-stock-matched.jsonl",
            "serving-stock-operational.jsonl", "serving-summary.json",
        })

    def test_benchmark_is_repo_relative_and_exposes_auditable_options(self):
        text = (EVIDENCE_DIR / "benchmark.py").read_text()
        self.assertIn('parser.add_argument("--profile", required=True', text)
        self.assertIn('parser.add_argument("--url", required=True', text)
        self.assertIn('parser.add_argument("--output", required=True', text)
        self.assertIn('SEEDS = (11, 23, 47)', text)
        self.assertIn('max_tokens=400', text)
        self.assertNotIn("/home/", text)

    def test_serving_profile_has_exact_candidate_settings(self):
        settings = {}
        for line in SERVING_PROFILE.read_text().splitlines():
            if line and not line.startswith("#"):
                key, value = line.split("=", 1)
                self.assertNotIn(key, settings)
                settings[key] = value
        expected = {
            "MAX_NUM_SEQS": "2",
            "MAX_NUM_BATCHED_TOKENS": "3072",
            "EXL3_TEMP_ROWS_FUSED": "8",
            "LONG_PREFILL_TOKEN_THRESHOLD": "2816",
            "GLM53_WARMUP_MAX_CONCURRENCY": "2",
            "DSV41_EXL3_SERIAL_STREAMS": "1",
            "VLLM_DISABLE_SHARED_EXPERTS_STREAM": "1",
        }
        self.assertEqual({key: settings[key] for key in expected}, expected)
        for key, value in {
            "MAX_MODEL_LEN": "600000", "PORT": "8000", "DSPARK_TOKENS": "3",
            "MODEL_DIR": "/model", "ENGRAM_MOUNT": "/engram-src",
            "DSV41_PACKED_DIR": "/engram-packed",
        }.items():
            self.assertEqual(settings[key], value)

    def test_serving_activation_is_fail_closed_and_hash_complete(self):
        text = SERVING_ACTIVATION.read_text()
        self.assertIn("set -euo pipefail", text)
        self.assertIn("expected_stock=ccdc69bfa04bff4870c3e555736a990fde6448ddb329441c4e0a27d6fc41078d", text)
        self.assertIn('(cd "$stage" && sha256sum -c "$sums")', text)
        self.assertIn('install -m 0444 "$stage/exl3-cooperative.py" "$stock"', text)
        self.assertIn('exec "/opt/dsv41/launch/${rank}.sh"', text)
        self.assertIn("candidate activation hashes rank=$rank stock_sha256=", text)
        self.assertIn('"$stage/test_cuda_integration.py" "$stage/test_exl3_overlay.py"', text)
        for line in (CANDIDATE_DIR / "SHA256SUMS").read_text().splitlines():
            self.assertIn(f"    {line}", text)
        self.assertNotIn("WARN", text)
        self.assertNotIn("|| cp", text)

    def test_serving_patch_is_rank_symmetric_and_zero_replica(self):
        text = SERVING_PATCH.read_text()
        self.assertEqual(text.count("kind: Deployment"), 2)
        self.assertEqual(text.count("replicas: 0"), 2)
        self.assertEqual(text.count("name: dsv41-exl3-coop-candidate-profile"), 2)
        self.assertEqual(text.count("name: dsv41-coop-activation"), 2)
        self.assertEqual(text.count("mountPath: /opt/dsv41-candidate"), 2)
        self.assertIn('["/bin/bash", "/opt/dsv41-candidate/activate.sh", "head"]', text)
        self.assertIn('["/bin/bash", "/opt/dsv41-candidate/activate.sh", "worker"]', text)
        self.assertEqual(text.count("args: []"), 2)
        self.assertNotIn('["/bin/bash", "-lc"]', text)
        self.assertNotIn('args: ["/opt/dsv41-candidate/activate.sh"', text)

    def test_serving_overlay_renders_original_deployment_names(self):
        kubectl = shutil.which("kubectl")
        if kubectl is None:
            self.skipTest("kubectl is unavailable")
        proc = subprocess.run(
            [kubectl, "kustomize", str(SERVING_DIR), "--load-restrictor=LoadRestrictionsNone"],
            cwd=ROOT, capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        rendered = proc.stdout
        self.assertEqual(rendered.count("name: dsv41-exl3-head\n"), 1)
        self.assertEqual(rendered.count("name: dsv41-exl3-worker\n"), 1)
        self.assertNotIn("dsv41-exl3-head-coop-candidate", rendered)
        self.assertEqual(rendered.count("replicas: 0"), 2)
        self.assertEqual(rendered.count("name: dsv41-exl3-coop-candidate-profile"), 3)
        self.assertEqual(rendered.count("path: /var/lib/llm-test/jit-cache/vllm-cache"), 2)
        self.assertEqual(rendered.count("claimName: dsv41-engram-packed-"), 2)
        self.assertEqual(rendered.count("containerPort: 8000"), 2)
        self.assertEqual(rendered.count("- /opt/dsv41-candidate/activate.sh"), 2)
        self.assertIn(
            "args: []\n        command:\n        - /bin/bash\n"
            "        - /opt/dsv41-candidate/activate.sh\n        - head",
            rendered,
        )
        self.assertIn(
            "args: []\n        command:\n        - /bin/bash\n"
            "        - /opt/dsv41-candidate/activate.sh\n        - worker",
            rendered,
        )
        self.assertIn("readinessProbe:", rendered)

    def test_stock_control_renders_matched_profile_without_candidate_activation(self):
        kubectl = shutil.which("kubectl")
        if kubectl is None:
            self.skipTest("kubectl is unavailable")
        proc = subprocess.run(
            [kubectl, "kustomize", str(STOCK_CONTROL_DIR), "--load-restrictor=LoadRestrictionsNone"],
            cwd=ROOT, capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        rendered = proc.stdout
        self.assertEqual(rendered.count("name: dsv41-exl3-head\n"), 1)
        self.assertEqual(rendered.count("name: dsv41-exl3-worker\n"), 1)
        self.assertEqual(rendered.count("replicas: 0"), 2)
        self.assertEqual(rendered.count("name: dsv41-exl3-stock-matched-profile"), 3)
        self.assertNotIn("dsv41-coop-activation", rendered)
        self.assertNotIn("/opt/dsv41-candidate/activate.sh", rendered)
        self.assertEqual(rendered.count('cp /opt/dsv41/exl3.py "$SITE/model_executor/layers/quantization/exl3.py"'), 2)
        for setting in ("MAX_NUM_SEQS=2", "MAX_NUM_BATCHED_TOKENS=3072", "LONG_PREFILL_TOKEN_THRESHOLD=2816"):
            self.assertIn(setting, rendered)

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
        self.assertIn("SHA256SUMS: |\n", text)
        self.assertNotIn("SHA256SUMS: |-", text)
        self.assertIn('while read -r _ file || [ -n "${file:-}" ]; do', text)
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
