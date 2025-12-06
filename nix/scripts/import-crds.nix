{ pkgs }:
pkgs.writeShellScriptBin "import-crds" ''
  #!${pkgs.stdenv.shell}
  # Usage: import-crds <path-to-json-file>
  # Example: import-crds cdk8s/crd-imports.json
  
  if [ -z "$1" ]; then
    echo "Usage: import-crds <path-to-json-file>"
    exit 1
  fi

  JSON_FILE="$1"
  
  if [ ! -f "$JSON_FILE" ]; then
     echo "Error: File $JSON_FILE not found."
     exit 1
  fi

  echo "Reading CRDs from $JSON_FILE..."
  
  # Extract CRDs from JSON using Python
  CRD_ARGS=$(${pkgs.python3}/bin/python3 -c "import json, sys; print(' '.join(json.load(open('$JSON_FILE'))))")
  
  echo "Running crd2pulumi..."
  # Generate Python types for the CRDs
  # shellcheck disable=SC2086
  ${pkgs.crd2pulumi}/bin/crd2pulumi --pythonPath ./pulumi/crds $CRD_ARGS --force
''