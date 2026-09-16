#!/usr/bin/env python3
"""Create a complete, inactive local cooperative-MoE candidate bundle."""

import argparse
import hashlib
from pathlib import Path, PurePosixPath
import shutil

STOCK_SHA256 = "ccdc69bfa04bff4870c3e555736a990fde6448ddb329441c4e0a27d6fc41078d"
BINARY_SHA256 = "16191d208101a3a04b021f8a2d0da360c5ebb710c0145b2e312052a02ce40305"
UPSTREAM_BINARY_SHA256 = "a09a589cbdcecb5372991c7b091d732236d58bc5f5aea14ab91e38e426f08d78"
PRISTINE_RUNTIME_SHA256 = "9f1d10ffc39ac4433828a000c4932a4a773b00acadd80b46c7568f494a77b2fb"
CANDIDATE_RUNTIME_SHA256 = "2d33c5cd57c447b4d6545abfb59356ca7ee9cefe8aa2e4fe2c2023fe09bf35de"
CUDA_TEST_SHA256 = "249934dddcded4977524d139e78f6ea9fbdc40cd147eb304a2ae5c01e78f0f00"
OVERLAY_TEST_SHA256 = "faecaeaf16b6142f020704cd3d003b0cc55611b2ad28886b4976d97322bd988b"
RUNTIME_DIRECTORY = "/root/.cache/vllm/dsv41-cooperative-moe/f083d7e-local-16191d2"


def checked(path: Path, digest: str) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"expected a regular non-symlink input file: {path}")
    data = path.read_bytes()
    actual = hashlib.sha256(data).hexdigest()
    if actual != digest:
        raise ValueError(f"hash mismatch for {path}: {actual} != {digest}")
    return data


def write_checked(path: Path, data: bytes, digest: str) -> None:
    actual = hashlib.sha256(data).hexdigest()
    if actual != digest:
        raise ValueError(f"generated hash mismatch for {path.name}: {actual} != {digest}")
    with path.open("xb") as handle:
        handle.write(data)
    path.chmod(0o444)


def make_bundle(stock: Path, artifacts: Path, output_directory: Path) -> None:
    """Exclusively create the five-file bundle without mutating any input."""
    stock_bytes = checked(stock, STOCK_SHA256)
    binary = checked(artifacts / "cooperative_moe.so", BINARY_SHA256)
    pristine_runtime = checked(artifacts / "runtime.py", PRISTINE_RUNTIME_SHA256)
    cuda_test = checked(artifacts / "test_cuda_integration.py", CUDA_TEST_SHA256)
    overlay_test = checked(artifacts / "test_exl3_overlay.py", OVERLAY_TEST_SHA256)

    old_pin = UPSTREAM_BINARY_SHA256.encode()
    new_pin = BINARY_SHA256.encode()
    if pristine_runtime.count(old_pin) != 1:
        raise ValueError("pristine runtime must contain exactly one upstream binary pin")
    candidate_runtime = pristine_runtime.replace(old_pin, new_pin)

    runtime_root = PurePosixPath(RUNTIME_DIRECTORY)
    footer = (
        "\n# Explicit unqualified local cooperative-MoE candidate; unsupported calls stay stock.\n"
        "import runpy as _coop_runpy\nimport sys as _coop_sys\n"
        f'_coop_setup = _coop_runpy.run_path({str(runtime_root / "runtime.py")!r})\n'
        f'_coop_setup["install"](_coop_sys.modules[__name__], library_root={str(runtime_root)!r}, enabled=True)\n'
    ).encode()
    overlay = stock_bytes + footer

    output_directory = output_directory.absolute()
    parent = output_directory.parent
    if output_directory.exists() or output_directory.is_symlink():
        raise FileExistsError(f"refusing existing output directory: {output_directory}")
    if parent.is_symlink() or not parent.is_dir():
        raise ValueError(f"output parent must be an existing non-symlink directory: {parent}")

    output_directory.mkdir(mode=0o700)
    try:
        write_checked(output_directory / "cooperative_moe.so", binary, BINARY_SHA256)
        write_checked(output_directory / "runtime.py", candidate_runtime, CANDIDATE_RUNTIME_SHA256)
        write_checked(output_directory / "exl3-cooperative.py", overlay, "b68bf2405d8d427407fcc18f728943cda964376a4c25637f5e9f5d791a3a6aac")
        write_checked(output_directory / "test_cuda_integration.py", cuda_test, CUDA_TEST_SHA256)
        write_checked(output_directory / "test_exl3_overlay.py", overlay_test, OVERLAY_TEST_SHA256)
    except Exception:
        shutil.rmtree(output_directory)
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stock", type=Path, required=True)
    parser.add_argument(
        "--artifacts",
        type=Path,
        required=True,
        help="input directory containing the binary, pristine runtime.py, and two test files",
    )
    parser.add_argument(
        "--output-directory",
        type=Path,
        required=True,
        help="new directory to create exclusively; it must not already exist",
    )
    args = parser.parse_args()
    make_bundle(args.stock, args.artifacts, args.output_directory)
    print(f"wrote inactive five-file candidate bundle: {args.output_directory}")
