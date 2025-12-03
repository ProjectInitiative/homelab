#!/usr/bin/env python
import json
import subprocess
import os
import argparse

def main():
    """
    Imports CRDs from a JSON file.
    """
    parser = argparse.ArgumentParser(description="Import CRDs from a JSON file.")
    parser.add_argument(
        "crd_file",
        nargs="?",
        default="crd-imports.json",
        help="Path to the JSON file containing CRD URLs. Defaults to 'crd-imports.json' in the current directory.",
    )
    args = parser.parse_args()

    crd_imports_file = args.crd_file

    try:
        with open(crd_imports_file, 'r') as f:
            crd_urls = json.load(f)
    except FileNotFoundError:
        print(f"Error: '{crd_imports_file}' not found.")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{crd_imports_file}'.")
        return

    for url in crd_urls:
        print(f"Importing CRD from: {url}")
        command = f"export TMPDIR=/tmp; cdk8s import --language python {url}"
        
        # We need to run this in the cdk8s directory, which is the script's directory
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )

        if result.returncode == 0:
            print("Import successful.")
            print(result.stdout)
        else:
            # The user mentioned that it imports fine but fails on cleanup.
            # cdk8s import returns a non-zero exit code on cleanup failure.
            # We will check if the import was actually successful by looking at the output.
            if "error" in result.stderr.lower() and "eacces" not in result.stderr.lower():
                print("Import failed with an error:")
                print(result.stderr)
            else:
                print("Import likely succeeded, but cleanup may have failed.")
                print("Please check the 'imports' directory.")
                print("Stderr from cdk8s:")
                print(result.stderr)


if __name__ == "__main__":
    main()
