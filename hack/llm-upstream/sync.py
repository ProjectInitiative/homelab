#!/usr/bin/env python3
"""Hermetic MiaAI recipe vendoring, reporting, and lane safety checks.

Only ``update`` uses the network (unless --source is supplied). Upstream files
are read as Git blobs and are never executed. Other commands are network-free.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import tempfile
from urllib.parse import urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parents[2]
LANES = ROOT / "llm-test" / "lanes"
FULL_SHA = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
LANE_NAME = re.compile(r"^[a-z0-9][a-z0-9-]*$")
IMAGE_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
REQUIRED_MODEL_ROLES = {"glm53": {"weights", "draft"}, "dsv41": {"weights", "native"}}
REQUIRED_RUNTIME_REFERENCES = {
    "glm53": {
        "files/chat_template.jinja", "overlay/exl3.py", "overlay/patch_adaptive_k.py",
        "overlay/patch_apc_no_store.py", "overlay/patch_cache_reset.py",
        "overlay/patch_default_max_new_tokens.py", "overlay/patch_dense_fp8.py",
        "overlay/patch_kv_capacity_log.py", "overlay/patch_scheduler_decode_floor.py",
        "scripts/boot-shape-warmup.sh",
    },
    "dsv41": {
        "overlay/exl3.py", "scripts/boot-shape-warmup.sh", "scripts/pack_engram.py",
        "scripts/prepare_engram_src.py",
    },
}
ADOPTION_STATUSES = {"pending-review", "provenance-blocked", "runtime-current"}
CANDIDATE_STATUSES = {"source-review-required", "built-unqualified", "qualified"}
QUALIFICATION_STATUSES = {"pending", "pass", "fail"}

LOCK_KEYS_V2 = {"schemaVersion", "lane", "recipe", "image", "models", "bundle", "adoption", "safety"}
LOCK_KEYS_V3 = LOCK_KEYS_V2 | {"runtimeCandidates"}
RECIPE_KEYS_V2 = {
    "repo", "runtimeBaseline", "reviewedRevision", "vendorRevision",
    "reviewedChangeSummary", "files", "requiredRuntimeReferences",
}
RECIPE_KEYS_V3 = RECIPE_KEYS_V2 | {"optionalRuntimeReferences"}
IMAGE_KEYS = {"ref", "digest", "provenanceStatus", "recipeRevision"}
MODEL_KEYS = {"repo", "revision"}
BUNDLE_KEYS = {"recipeRevision", "imageDigest", "modelRevisions"}
ADOPTION_KEYS_V2 = {
    "status", "reason", "reviewedRevision", "reviewedRuntimeChanged",
    "recipeRevision", "imageDigest", "modelRevisions",
}
ADOPTION_KEYS_V3 = ADOPTION_KEYS_V2 | {"reviewedOptionalRuntimeChanged"}
CANDIDATE_KEYS = {
    "upstreamRevision", "mode", "status", "requiredFiles", "upstreamArtifact",
    "localCandidate", "qualification",
}
UPSTREAM_ARTIFACT_KEYS = {"sha256", "availability"}
LOCAL_CANDIDATE_KEYS = {
    "binarySha256", "pristineRuntimeSha256", "runtimeSha256", "buildProvenance",
}
BUILD_PROVENANCE_KEYS = {
    "exllamaRepo", "exllamaRevision", "archiveFilename", "archiveSha256",
    "imageDigest", "buildScript", "buildScriptSha256", "buildCommand",
    "compilerIdentity", "buildLogSha256",
}
QUALIFICATION_KEYS = {"chronometerGpu54", "sextantGpu54", "servingAB", "promotionApproved"}
SAFETY_KEYS = {"desiredReplicas", "activationOrder", "deploymentEnabled"}
CONTRACT_KEYS = {
    "schemaVersion", "lane", "adoptionBlockers", "fileAssertions",
    "preservedPolicy", "servingManifests",
}
ASSERTION_KEYS = {"path", "text", "count"}


class Error(RuntimeError):
    pass


def exact_keys(value: object, keys: set[str], label: str) -> dict:
    if not isinstance(value, dict) or set(value) != keys:
        actual = sorted(value) if isinstance(value, dict) else type(value).__name__
        raise Error(f"{label}: expected keys {sorted(keys)}, got {actual}")
    return value


def nonempty_string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise Error(f"{label} must be a nonempty string")
    return value


def string_list(value: object, label: str, *, nonempty: bool = False) -> list[str]:
    if not isinstance(value, list) or (nonempty and not value):
        raise Error(f"{label} must be {'a nonempty' if nonempty else 'an'} array")
    if any(not isinstance(item, str) or not item for item in value):
        raise Error(f"{label} entries must be nonempty strings")
    return value


def load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        try:
            display = path.relative_to(ROOT)
        except ValueError:
            display = path
        raise Error(f"cannot read {display}: {exc}") from exc
    if not isinstance(value, dict):
        raise Error(f"{path} must contain a JSON object")
    return value


def dump_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f".tmp-{os.getpid()}")
    if temporary.exists() or temporary.is_symlink():
        raise Error(f"refusing existing temporary path {temporary}")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    os.replace(temporary, path)


def contained(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def checked_lane_dir(name: str) -> Path:
    if not isinstance(name, str) or not LANE_NAME.fullmatch(name):
        raise Error(f"unsafe lane name {name!r}")
    base = LANES.resolve(strict=True)
    candidate = LANES / name
    if candidate.is_symlink() or not candidate.is_dir():
        raise Error(f"lane must be a direct non-symlink directory: {name}")
    resolved = candidate.resolve(strict=True)
    if resolved.parent != base or not contained(resolved, base):
        raise Error(f"lane escapes lanes directory: {name}")
    return candidate


def checked_direct_child(parent: Path, name: str, *, must_exist: bool = True) -> Path:
    if PurePosixPath(name).name != name or name in ("", ".", ".."):
        raise Error(f"unsafe direct child {name!r}")
    child = parent / name
    if child.is_symlink():
        raise Error(f"symlinked path is forbidden: {child}")
    if must_exist and not child.exists():
        raise Error(f"required path is missing: {child}")
    parent_resolved = parent.resolve(strict=True)
    resolved = child.resolve(strict=must_exist)
    if resolved.parent != parent_resolved or not contained(resolved, parent_resolved):
        raise Error(f"path escapes parent: {child}")
    return child


def checked_relative_file(parent: Path, name: str, *, must_exist: bool = True) -> Path:
    relative = PurePosixPath(name)
    if relative.is_absolute() or not relative.parts or any(part in ("", ".", "..") for part in relative.parts):
        raise Error(f"unsafe relative path {name!r}")
    current = parent
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise Error(f"symlinked path is forbidden: {current}")
    parent_resolved = parent.resolve(strict=True)
    resolved = current.resolve(strict=must_exist)
    if not contained(resolved, parent_resolved):
        raise Error(f"path escapes parent: {current}")
    if must_exist and not current.is_file():
        raise Error(f"required regular file is missing: {current}")
    return current


def lane_paths(name: str) -> tuple[Path, Path, Path]:
    lane = checked_lane_dir(name)
    lock = checked_direct_child(lane, "upstream.lock.json")
    contract = checked_direct_child(lane, "contract.json")
    vendor = checked_direct_child(lane, "vendor")
    if not vendor.is_dir():
        raise Error(f"vendor must be a directory: {vendor}")
    return lock, contract, vendor


def safe_root_file(name: str) -> Path:
    relative = PurePosixPath(name)
    if relative.is_absolute() or any(part in ("", ".", "..") for part in relative.parts):
        raise Error(f"unsafe repository path {name!r}")
    current = ROOT
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise Error(f"symlinked repository path is forbidden: {current}")
    resolved = current.resolve(strict=True)
    root = ROOT.resolve(strict=True)
    if not contained(resolved, root) or not current.is_file():
        raise Error(f"repository path escapes root or is not a file: {name}")
    return current


def normalize_repo_url(value: object) -> str:
    raw = nonempty_string(value, "repository URL").strip()
    split = urlsplit(raw)
    if split.scheme.lower() != "https" or not split.hostname or split.username or split.password:
        raise Error("repository URL must be credential-free https")
    if split.query or split.fragment:
        raise Error("repository URL must not contain query or fragment")
    path = split.path.rstrip("/")
    if path.endswith(".git"):
        path = path[:-4]
    if not path or path == "/" or any(part in (".", "..") for part in path.split("/")):
        raise Error("repository URL has an unsafe path")
    netloc = split.hostname.lower()
    if split.port:
        netloc += f":{split.port}"
    return urlunsplit(("https", netloc, path, "", ""))


def check_lock(lock: dict, lane: str) -> None:
    schema = lock.get("schemaVersion")
    if schema not in (2, 3) or lock.get("lane") != lane:
        raise Error(f"{lane}: unsupported lock schema or lane")
    exact_keys(lock, LOCK_KEYS_V3 if schema == 3 else LOCK_KEYS_V2, f"{lane} lock")
    recipe = exact_keys(
        lock["recipe"], RECIPE_KEYS_V3 if schema == 3 else RECIPE_KEYS_V2,
        f"{lane} recipe",
    )
    normalize_repo_url(recipe["repo"])
    for field in ("runtimeBaseline", "reviewedRevision", "vendorRevision"):
        if not isinstance(recipe[field], str) or not FULL_SHA.fullmatch(recipe[field]):
            raise Error(f"{lane}: recipe.{field} must be a full lowercase Git SHA")
    nonempty_string(recipe["reviewedChangeSummary"], f"{lane} reviewedChangeSummary")
    files = recipe["files"]
    if not isinstance(files, dict) or not files:
        raise Error(f"{lane}: recipe.files must be a nonempty object")
    for name, digest in files.items():
        if not isinstance(name, str) or not SHA256.fullmatch(str(digest)):
            raise Error(f"{lane}: invalid inventory entry {name!r}")
        relative = PurePosixPath(name)
        if relative.is_absolute() or any(part in ("", ".", "..") for part in relative.parts):
            raise Error(f"{lane}: unsafe inventory path {name!r}")
    references = string_list(recipe["requiredRuntimeReferences"], f"{lane} requiredRuntimeReferences")
    if len(references) != len(set(references)) or any(name not in files for name in references):
        raise Error(f"{lane}: required runtime references must be unique inventory paths")
    required_references = REQUIRED_RUNTIME_REFERENCES.get(lane)
    if required_references is not None and set(references) != required_references:
        raise Error(f"{lane}: required runtime references must be {sorted(required_references)}")
    optional_references: list[str] = []
    if schema == 3:
        optional_references = string_list(
            recipe["optionalRuntimeReferences"], f"{lane} optionalRuntimeReferences"
        )
        if (
            not optional_references
            or len(optional_references) != len(set(optional_references))
            or any(name not in files for name in optional_references)
            or set(optional_references).intersection(references)
        ):
            raise Error(f"{lane}: optional runtime references must be unique, inventoried, and separate")

    image = exact_keys(lock["image"], IMAGE_KEYS, f"{lane} image")
    nonempty_string(image["ref"], f"{lane} image.ref")
    nonempty_string(image["provenanceStatus"], f"{lane} image.provenanceStatus")
    if not isinstance(image["digest"], str) or not IMAGE_DIGEST.fullmatch(image["digest"]):
        raise Error(f"{lane}: image digest must be immutable sha256")
    if image["recipeRevision"] != recipe["runtimeBaseline"]:
        raise Error(f"{lane}: image.recipeRevision must bind the runtime baseline")

    models = lock["models"]
    if not isinstance(models, dict) or not models:
        raise Error(f"{lane}: models must contain at least one role")
    required_roles = REQUIRED_MODEL_ROLES.get(lane)
    if required_roles is not None and set(models) != required_roles:
        raise Error(f"{lane}: model roles must be {sorted(required_roles)}")
    for role, details in models.items():
        if not isinstance(role, str) or not role:
            raise Error(f"{lane}: model role must be nonempty")
        details = exact_keys(details, MODEL_KEYS, f"{lane} model {role}")
        nonempty_string(details["repo"], f"{lane} model {role}.repo")
        if not isinstance(details["revision"], str) or not FULL_SHA.fullmatch(details["revision"]):
            raise Error(f"{lane}: model {role} revision must be a full SHA")

    model_revisions = {role: details["revision"] for role, details in models.items()}
    bundle = exact_keys(lock["bundle"], BUNDLE_KEYS, f"{lane} bundle")
    if bundle != {
        "recipeRevision": recipe["runtimeBaseline"],
        "imageDigest": image["digest"],
        "modelRevisions": model_revisions,
    }:
        raise Error(f"{lane}: compatibility bundle does not match active recipe/image/models")

    adoption = exact_keys(
        lock["adoption"], ADOPTION_KEYS_V3 if schema == 3 else ADOPTION_KEYS_V2,
        f"{lane} adoption",
    )
    if adoption["status"] not in ADOPTION_STATUSES:
        raise Error(f"{lane}: invalid adoption status")
    nonempty_string(adoption["reason"], f"{lane} adoption.reason")
    if not isinstance(adoption["reviewedRuntimeChanged"], bool):
        raise Error(f"{lane}: adoption.reviewedRuntimeChanged must be boolean")
    if schema == 3 and not isinstance(adoption["reviewedOptionalRuntimeChanged"], bool):
        raise Error(f"{lane}: adoption.reviewedOptionalRuntimeChanged must be boolean")
    if adoption["reviewedRevision"] != recipe["reviewedRevision"]:
        raise Error(f"{lane}: adoption reviewed revision is stale")
    adoption_binding = {
        "recipeRevision": adoption["recipeRevision"],
        "imageDigest": adoption["imageDigest"],
        "modelRevisions": adoption["modelRevisions"],
    }
    if adoption_binding != bundle:
        raise Error(f"{lane}: adoption binding does not match compatibility bundle")
    if adoption["status"] == "runtime-current":
        if adoption["reviewedRuntimeChanged"]:
            raise Error(f"{lane}: runtime-current cannot claim reviewed runtime drift")
        if schema == 2 and recipe["vendorRevision"] != recipe["runtimeBaseline"]:
            raise Error(f"{lane}: runtime-current requires vendor/runtime baseline equality")

    if schema == 3:
        candidates = lock["runtimeCandidates"]
        if not isinstance(candidates, dict) or not candidates:
            raise Error(f"{lane}: runtimeCandidates must be a nonempty object")
        for name, candidate in candidates.items():
            nonempty_string(name, f"{lane} candidate name")
            candidate = exact_keys(candidate, CANDIDATE_KEYS, f"{lane} candidate {name}")
            if candidate["upstreamRevision"] != recipe["reviewedRevision"]:
                raise Error(f"{lane}: candidate {name} revision is stale")
            if candidate["mode"] != "optional-off-by-default":
                raise Error(f"{lane}: candidate {name} must remain optional-off-by-default")
            if candidate["status"] not in CANDIDATE_STATUSES:
                raise Error(f"{lane}: candidate {name} has invalid status")
            required = string_list(candidate["requiredFiles"], f"{lane} candidate {name}.requiredFiles", nonempty=True)
            if set(required) != set(optional_references):
                raise Error(f"{lane}: candidate {name} required files do not match optional references")
            upstream_artifact = exact_keys(
                candidate["upstreamArtifact"], UPSTREAM_ARTIFACT_KEYS,
                f"{lane} candidate {name}.upstreamArtifact",
            )
            if not SHA256.fullmatch(str(upstream_artifact["sha256"])):
                raise Error(f"{lane}: candidate {name} upstream artifact hash is invalid")
            if upstream_artifact["availability"] != "unavailable-in-git-and-releases":
                raise Error(f"{lane}: candidate {name} upstream artifact availability must remain blocked")
            local = exact_keys(
                candidate["localCandidate"], LOCAL_CANDIDATE_KEYS,
                f"{lane} candidate {name}.localCandidate",
            )
            for field in ("binarySha256", "pristineRuntimeSha256", "runtimeSha256"):
                if not SHA256.fullmatch(str(local[field])):
                    raise Error(f"{lane}: candidate {name} local artifact hash is invalid")
            provenance = exact_keys(
                local["buildProvenance"], BUILD_PROVENANCE_KEYS,
                f"{lane} candidate {name}.buildProvenance",
            )
            normalize_repo_url(provenance["exllamaRepo"])
            if not FULL_SHA.fullmatch(str(provenance["exllamaRevision"])):
                raise Error(f"{lane}: candidate {name} ExLlama revision must be a full SHA")
            checked_name = PurePosixPath(str(provenance["archiveFilename"]))
            if checked_name.name != str(provenance["archiveFilename"]):
                raise Error(f"{lane}: candidate {name} archiveFilename must be a direct filename")
            if not SHA256.fullmatch(str(provenance["archiveSha256"])):
                raise Error(f"{lane}: candidate {name} archive hash is invalid")
            if not IMAGE_DIGEST.fullmatch(str(provenance["imageDigest"])):
                raise Error(f"{lane}: candidate {name} build image digest is invalid")
            nonempty_string(provenance["buildScript"], f"{lane} candidate {name}.buildScript")
            if not SHA256.fullmatch(str(provenance["buildScriptSha256"])):
                raise Error(f"{lane}: candidate {name} build script hash is invalid")
            nonempty_string(provenance["buildCommand"], f"{lane} candidate {name}.buildCommand")
            if provenance["compilerIdentity"] is not None:
                nonempty_string(provenance["compilerIdentity"], f"{lane} candidate {name}.compilerIdentity")
            if provenance["buildLogSha256"] is not None and not SHA256.fullmatch(str(provenance["buildLogSha256"])):
                raise Error(f"{lane}: candidate {name} build log hash is invalid")
            qualification = exact_keys(
                candidate["qualification"], QUALIFICATION_KEYS,
                f"{lane} candidate {name}.qualification",
            )
            for field in ("chronometerGpu54", "sextantGpu54", "servingAB"):
                if qualification[field] not in QUALIFICATION_STATUSES:
                    raise Error(f"{lane}: candidate {name} qualification {field} is invalid")
            if not isinstance(qualification["promotionApproved"], bool):
                raise Error(f"{lane}: candidate {name} promotionApproved must be boolean")
            gpu_complete = all(
                qualification[field] == "pass"
                for field in ("chronometerGpu54", "sextantGpu54")
            )
            if qualification["servingAB"] == "pass" and not gpu_complete:
                raise Error(f"{lane}: candidate {name} serving A/B cannot pass before both GPU gates")
            complete = gpu_complete and qualification["servingAB"] == "pass"
            provenance_complete = (
                provenance["compilerIdentity"] is not None
                and provenance["buildLogSha256"] is not None
            )
            if candidate["status"] == "qualified" and not provenance_complete:
                raise Error(f"{lane}: candidate {name} cannot be qualified with pending build provenance")
            if candidate["status"] == "qualified" and (not complete or not qualification["promotionApproved"]):
                raise Error(f"{lane}: candidate {name} cannot be qualified before all gates and approval")
            if candidate["status"] != "qualified" and qualification["promotionApproved"]:
                raise Error(f"{lane}: candidate {name} cannot be approved while unqualified")

    safety = exact_keys(lock["safety"], SAFETY_KEYS, f"{lane} safety")
    if safety != {"desiredReplicas": 0, "activationOrder": ["worker", "head"], "deploymentEnabled": False}:
        raise Error(f"{lane}: unsafe workload policy")


def check_contract(contract: dict, lane: str) -> None:
    exact_keys(contract, CONTRACT_KEYS, f"{lane} contract")
    if contract["schemaVersion"] != 1 or contract["lane"] != lane:
        raise Error(f"{lane}: unsupported contract schema or lane")
    string_list(contract["adoptionBlockers"], f"{lane} adoptionBlockers")
    string_list(contract["preservedPolicy"], f"{lane} preservedPolicy", nonempty=True)
    manifests = string_list(contract["servingManifests"], f"{lane} servingManifests", nonempty=True)
    if len(manifests) != len(set(manifests)):
        raise Error(f"{lane}: serving manifests must be unique")
    assertions = contract["fileAssertions"]
    if not isinstance(assertions, list) or not assertions:
        raise Error(f"{lane}: fileAssertions must be nonempty")
    for index, assertion in enumerate(assertions):
        exact_keys(assertion, ASSERTION_KEYS, f"{lane} assertion {index}")
        nonempty_string(assertion["path"], f"{lane} assertion {index}.path")
        nonempty_string(assertion["text"], f"{lane} assertion {index}.text")
        if not isinstance(assertion["count"], int) or isinstance(assertion["count"], bool) or assertion["count"] < 0:
            raise Error(f"{lane}: assertion count must be a nonnegative integer")


def inventory_files(vendor: Path) -> set[str]:
    found: set[str] = set()
    for directory, directories, files in os.walk(vendor, followlinks=False):
        directory_path = Path(directory)
        for name in directories:
            if (directory_path / name).is_symlink():
                raise Error(f"symlinked vendor directory is forbidden: {directory_path / name}")
        directories[:] = [name for name in directories if name != "__pycache__"]
        for name in files:
            path = directory_path / name
            if path.is_symlink():
                raise Error(f"symlinked vendor file is forbidden: {path}")
            if name.endswith(".pyc"):
                continue
            relative = path.relative_to(vendor).as_posix()
            if relative != "SOURCE.json":
                found.add(relative)
    return found


def top_level_value(document: str, key: str) -> str | None:
    matches = []
    pattern = re.compile(rf"^{re.escape(key)}:\s*([^#\n]+?)\s*(?:#.*)?$", re.MULTILINE)
    matches.extend(match.group(1).strip() for match in pattern.finditer(document))
    if len(matches) > 1:
        raise Error(f"duplicate top-level YAML key {key}")
    return matches[0] if matches else None


def deployment_spec_replicas(document: str) -> int:
    lines = document.splitlines()
    spec_indexes = [i for i, line in enumerate(lines) if re.fullmatch(r"spec:\s*(?:#.*)?", line)]
    if len(spec_indexes) != 1:
        raise Error("Deployment must contain exactly one top-level spec mapping")
    start = spec_indexes[0] + 1
    matches: list[str] = []
    for line in lines[start:]:
        if line and not line.startswith(" ") and not line.lstrip().startswith("#"):
            break
        match = re.fullmatch(r"  replicas:\s*([^#\s]+)\s*(?:#.*)?", line)
        if match:
            matches.append(match.group(1))
    if len(matches) != 1 or not re.fullmatch(r"[0-9]+", matches[0]):
        raise Error("Deployment spec.replicas must be one explicit integer")
    return int(matches[0])


def verify_required_references(vendor: Path, lock: dict) -> list[str]:
    failures: list[str] = []
    reference_sources = []
    for name in ("Dockerfile", "start.sh"):
        if name in lock["recipe"]["files"]:
            reference_sources.append(checked_relative_file(vendor, name).read_text(errors="replace"))
    combined = "\n".join(reference_sources)
    for name in lock["recipe"]["requiredRuntimeReferences"]:
        if Path(name).name not in combined:
            failures.append(f"required runtime file is not referenced by Dockerfile/start.sh: {name}")
    return failures


def verify_lane(lane: str) -> list[str]:
    lock_path, contract_path, vendor = lane_paths(lane)
    lock, contract = load_json(lock_path), load_json(contract_path)
    check_lock(lock, lane)
    check_contract(contract, lane)
    failures: list[str] = []
    expected = lock["recipe"]["files"]
    actual = inventory_files(vendor)
    if actual != set(expected):
        failures.append(f"vendor inventory differs: expected={sorted(expected)} actual={sorted(actual)}")
    for name, wanted in expected.items():
        try:
            path = checked_relative_file(vendor, name)
        except Error as exc:
            failures.append(str(exc))
            continue
        got = hashlib.sha256(path.read_bytes()).hexdigest()
        if got != wanted:
            failures.append(f"checksum mismatch: {name}: {got} != {wanted}")
    source_path = checked_relative_file(vendor, "SOURCE.json")
    source = load_json(source_path)
    if set(source) != {"repo", "revision", "files"}:
        failures.append("SOURCE.json has unexpected schema")
    else:
        try:
            repo_matches = normalize_repo_url(source["repo"]) == normalize_repo_url(lock["recipe"]["repo"])
        except Error:
            repo_matches = False
        if not repo_matches or source["revision"] != lock["recipe"]["vendorRevision"] or source["files"] != expected:
            failures.append("SOURCE.json does not match locked repo/vendor revision/files")
    failures.extend(verify_required_references(vendor, lock))

    for assertion in contract["fileAssertions"]:
        target = safe_root_file(assertion["path"])
        count = target.read_text().count(assertion["text"])
        if count != assertion["count"]:
            failures.append(
                f"assertion failed: {assertion['path']} contains {assertion['text']!r} "
                f"count={count}, expected={assertion['count']}"
            )
    for manifest in contract["servingManifests"]:
        text = safe_root_file(manifest).read_text()
        documents = re.split(r"(?m)^---\s*$", text)
        deployments = [doc for doc in documents if top_level_value(doc, "kind") == "Deployment"]
        if len(deployments) != 2:
            failures.append(f"{manifest}: expected exactly 2 serving Deployments, found {len(deployments)}")
            continue
        for document in deployments:
            try:
                replicas = deployment_spec_replicas(document)
            except Error as exc:
                failures.append(f"{manifest}: {exc}")
                continue
            if replicas != 0:
                failures.append(f"{manifest}: Deployment spec.replicas is {replicas}, expected 0")
    return failures


def git(*args: str, cwd: Path | None = None) -> bytes:
    result = subprocess.run(
        ["git", "--no-replace-objects", *args], cwd=cwd,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if result.returncode:
        raise Error(result.stderr.decode(errors="replace").strip() or "git command failed")
    return result.stdout


def git_is_ancestor(ancestor: str, descendant: str, repository: Path) -> bool:
    result = subprocess.run(
        ["git", "--no-replace-objects", "merge-base", "--is-ancestor", ancestor, descendant],
        cwd=repository, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if result.returncode not in (0, 1):
        raise Error(result.stderr.decode(errors="replace").strip() or "git ancestry check failed")
    return result.returncode == 0


def ensure_clean(force: bool) -> None:
    if not force and git("status", "--porcelain", cwd=ROOT).strip():
        raise Error("worktree is dirty; commit/stash unrelated changes or pass --force-dirty")


def update_lane(lane: str, revision: str, reviewed_revision: str | None, source: str | None, force: bool) -> None:
    if not FULL_SHA.fullmatch(revision):
        raise Error("--revision must be a full lowercase 40-character SHA")
    reviewed_revision = reviewed_revision or revision
    if not FULL_SHA.fullmatch(reviewed_revision):
        raise Error("--reviewed-revision must be a full lowercase 40-character SHA")
    ensure_clean(force)
    lock_path, _, vendor = lane_paths(lane)
    lane_dir = vendor.parent
    lock = load_json(lock_path)
    check_lock(lock, lane)
    paths = list(lock["recipe"]["files"])
    with tempfile.TemporaryDirectory(prefix=f"llm-{lane}-") as temporary:
        if source:
            repository = Path(source).resolve(strict=True)
        else:
            repository = Path(temporary) / "repository"
            git("clone", "--quiet", "--filter=blob:none", "--no-checkout", lock["recipe"]["repo"], str(repository))
        origin = git("remote", "get-url", "origin", cwd=repository).decode().strip()
        if normalize_repo_url(origin) != normalize_repo_url(lock["recipe"]["repo"]):
            raise Error("--source origin URL does not match locked recipe repo")
        resolved = git("rev-parse", "--verify", f"{revision}^{{commit}}", cwd=repository).decode().strip()
        resolved_reviewed = git("rev-parse", "--verify", f"{reviewed_revision}^{{commit}}", cwd=repository).decode().strip()
        baseline = lock["recipe"]["runtimeBaseline"]
        resolved_baseline = git("rev-parse", "--verify", f"{baseline}^{{commit}}", cwd=repository).decode().strip()
        if (resolved, resolved_reviewed, resolved_baseline) != (revision, reviewed_revision, baseline):
            raise Error("a locked/requested revision did not resolve exactly")
        if not git_is_ancestor(baseline, reviewed_revision, repository):
            raise Error("runtime baseline is not an ancestor of reviewed revision")
        if not git_is_ancestor(revision, reviewed_revision, repository):
            raise Error("vendor revision is not reachable from reviewed revision")
        ahead = git("rev-list", "--count", f"{baseline}..{reviewed_revision}", cwd=repository).decode().strip()
        behind = git("rev-list", "--count", f"{reviewed_revision}..{baseline}", cwd=repository).decode().strip()
        changed = set(git("diff", "--name-only", baseline, reviewed_revision, cwd=repository).decode().splitlines())
        selected_changed = sorted(changed.intersection(paths))
        if lock["schemaVersion"] == 3:
            default_changed = sorted(changed.intersection(lock["recipe"]["requiredRuntimeReferences"]))
            optional_changed = sorted(
                changed.intersection(lock["recipe"]["optionalRuntimeReferences"])
            )
        else:
            # Schema v2 has no separate optional inventory; preserve its
            # conservative behavior and require review for every export.
            default_changed = selected_changed
            optional_changed = []
        change_summary = (
            f"{ahead} commits ahead, {behind} behind runtime baseline; default runtime files changed: "
            f"{', '.join(default_changed) if default_changed else 'none'}; optional runtime files changed: "
            f"{', '.join(optional_changed) if optional_changed else 'none'}; "
            f"{len(changed - set(paths))} unselected paths changed"
        )
        staged = Path(temporary) / "vendor"
        hashes: dict[str, str] = {}
        for name in paths:
            blob = git("show", f"{revision}:{name}", cwd=repository)
            target = staged / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(blob)
            hashes[name] = hashlib.sha256(blob).hexdigest()
        source_record = {"repo": lock["recipe"]["repo"], "revision": revision, "files": hashes}
        dump_json(staged / "SOURCE.json", source_record)

        replacement = checked_direct_child(lane_dir, f".vendor-new-{os.getpid()}", must_exist=False)
        if replacement.exists() or replacement.is_symlink():
            raise Error("refusing existing vendor replacement directory")
        shutil.copytree(staged, replacement)
        checked_direct_child(lane_dir, "vendor")
        inventory_files(vendor)  # Reject nested symlinks before destructive replacement.
        shutil.rmtree(vendor)
        os.replace(replacement, vendor)
        lock["recipe"]["vendorRevision"] = revision
        lock["recipe"]["reviewedRevision"] = reviewed_revision
        lock["recipe"]["reviewedChangeSummary"] = change_summary
        lock["recipe"]["files"] = hashes
        adoption_update = {
            "reviewedRevision": reviewed_revision,
            "reviewedRuntimeChanged": bool(default_changed) if lock["schemaVersion"] == 3 else True,
        }
        if lock["schemaVersion"] == 3:
            adoption_update["reviewedOptionalRuntimeChanged"] = bool(optional_changed)
            if optional_changed:
                for candidate in lock["runtimeCandidates"].values():
                    candidate["upstreamRevision"] = reviewed_revision
                    candidate["status"] = "source-review-required"
                    candidate["qualification"] = {
                        "chronometerGpu54": "pending",
                        "sextantGpu54": "pending",
                        "servingAB": "pending",
                        "promotionApproved": False,
                    }
        if lock["schemaVersion"] == 2 or default_changed:
            adoption_update.update({
                "status": "pending-review",
                "reason": "runtime export changed; explicit compatibility review is required",
            })
        elif optional_changed:
            adoption_update.update({
                "status": "runtime-current",
                "reason": "default runtime unchanged; optional runtime candidate remains separately blocked",
            })
        lock["adoption"].update(adoption_update)
        dump_json(lock_path, lock)
    print(
        f"updated {lane} vendor to {revision}; default runtime adoption is "
        f"{lock['adoption']['status']}; no upstream content was executed"
    )


def adoption_summary(lock: dict) -> str:
    adoption = lock["adoption"]
    if adoption["status"] == "runtime-current":
        return f"CURRENT: {adoption['reason']}"
    return f"BLOCKED ({adoption['status']}): {adoption['reason']}"


def report_lane(lane: str, check: bool) -> None:
    lock_path, contract_path, _ = lane_paths(lane)
    lock, contract = load_json(lock_path), load_json(contract_path)
    check_lock(lock, lane)
    check_contract(contract, lane)
    recipe, image = lock["recipe"], lock["image"]
    current = lock["adoption"]["status"] == "runtime-current"
    lines = [
        f"# {lane} upstream drift report", "",
        "Generated by `python3 hack/llm-upstream/sync.py drift --lane " + lane + "`.",
        "This report is offline and does not authorize deployment.", "", "## Provenance", "",
        f"- Runtime baseline: `{recipe['runtimeBaseline']}`",
        f"- Last reviewed upstream HEAD: `{recipe['reviewedRevision']}`",
        f"- Reviewed range: {recipe['reviewedChangeSummary']}",
        f"- Vendored comparison snapshot: `{recipe['vendorRevision']}`",
        f"- Serving image: `{image['ref']}@{image['digest']}`",
        f"- Image provenance: **{image['provenanceStatus']}**",
        f"- Runtime adoption: **{adoption_summary(lock)}**", "", "## Preserved local contract", "",
    ]
    lines.extend(f"- {item}" for item in contract["preservedPolicy"])
    if lock["schemaVersion"] == 3:
        lines.extend(["", "## Optional runtime candidates", ""])
        for name, candidate in sorted(lock["runtimeCandidates"].items()):
            local = candidate["localCandidate"]
            qualification = candidate["qualification"]
            lines.extend([
                f"- `{name}`: **{candidate['status']}**, `{candidate['mode']}` at `{candidate['upstreamRevision']}`",
                f"  - Upstream artifact: `{candidate['upstreamArtifact']['sha256']}` ({candidate['upstreamArtifact']['availability']})",
                f"  - Local candidate binary: `{local['binarySha256']}`; patched runtime: `{local['runtimeSha256']}`; pristine runtime: `{local['pristineRuntimeSha256']}`",
                f"  - Build input: `{local['buildProvenance']['archiveFilename']}` / `{local['buildProvenance']['archiveSha256']}` at ExLlama `{local['buildProvenance']['exllamaRevision']}`",
                f"  - Build script: `{local['buildProvenance']['buildScript']}` / `{local['buildProvenance']['buildScriptSha256']}`",
                f"  - Build capture: compiler={local['buildProvenance']['compilerIdentity'] or 'pending'}, log-sha256={local['buildProvenance']['buildLogSha256'] or 'pending'}",
                f"  - Gates: chronometer-54={qualification['chronometerGpu54']}, sextant-54={qualification['sextantGpu54']}, serving-A/B={qualification['servingAB']}, promotion-approved={str(qualification['promotionApproved']).lower()}",
            ])
    candidate_blocked = lock["schemaVersion"] == 3 and any(
        candidate["status"] != "qualified"
        for candidate in lock["runtimeCandidates"].values()
    )
    lines.extend([
        "", "## " + (
            "Optional candidate blockers" if candidate_blocked
            else ("Review notes" if current else "Runtime adoption blockers")
        ), "",
    ])
    prefix = "BLOCKER" if candidate_blocked or not current else "NOTE"
    lines.extend(f"- **{prefix}:** {item}" for item in contract["adoptionBlockers"])
    lines.extend(["", "## Vendored files", ""])
    lines.extend(f"- `{name}` — `{digest}`" for name, digest in sorted(recipe["files"].items()))
    lines.append("")
    output = "\n".join(lines)
    path = checked_direct_child(lock_path.parent, "drift.md")
    if check:
        if path.read_text() != output:
            raise Error(f"{path.relative_to(ROOT)} is stale; run drift without --check")
    else:
        path.write_text(output)
        print(f"wrote {path.relative_to(ROOT)}")


def lanes(value: str) -> list[str]:
    if value != "all":
        checked_lane_dir(value)
        return [value]
    result = []
    for path in sorted(LANES.iterdir()):
        if path.is_symlink():
            raise Error(f"symlinked lane is forbidden: {path}")
        if path.is_dir():
            checked_lane_dir(path.name)
            result.append(path.name)
    if not result:
        raise Error("no lanes found")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate", aliases=["verify"], help="offline integrity and workload-contract validation")
    validate.add_argument("--lane", default="all")
    drift = sub.add_parser("drift", aliases=["report"], help="generate an offline deterministic drift report")
    drift.add_argument("--lane", default="all")
    drift.add_argument("--check", action="store_true")
    check = sub.add_parser("check", help="offline validate plus generated-drift check")
    check.add_argument("--lane", default="all")
    update = sub.add_parser("update", help="selectively vendor Git blobs; never deploys or executes them")
    update.add_argument("--lane", required=True)
    update.add_argument("--revision", required=True, help="full SHA to vendor")
    update.add_argument("--reviewed-revision", help="full reviewed HEAD when the runtime snapshot is older")
    update.add_argument("--source", help="existing Git checkout (makes update network-free)")
    update.add_argument("--force-dirty", action="store_true")
    args = parser.parse_args()
    try:
        if args.command in ("validate", "verify", "check"):
            failed = False
            for lane in lanes(args.lane):
                problems = verify_lane(lane)
                if problems:
                    failed = True
                    for problem in problems:
                        print(f"FAIL {lane}: {problem}")
                else:
                    print(f"INTEGRITY PASS {lane}: checksums and safety contract")
                    lock = load_json(lane_paths(lane)[0])
                    print(f"ADOPTION {lane}: {adoption_summary(lock)}")
                if args.command == "check":
                    report_lane(lane, True)
                    print(f"DRIFT PASS {lane}: report is current")
            return 1 if failed else 0
        if args.command in ("drift", "report"):
            for lane in lanes(args.lane):
                report_lane(lane, args.check)
            return 0
        update_lane(args.lane, args.revision, args.reviewed_revision, args.source, args.force_dirty)
        return 0
    except (Error, OSError) as exc:
        parser.error(str(exc))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
