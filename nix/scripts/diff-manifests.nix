{ pkgs }:
pkgs.writeShellScriptBin "diff-manifests" ''
  set -e
  
  # Paths
  PROJECT_ROOT=$(git rev-parse --show-toplevel)
  COMPARE_DIR="$PROJECT_ROOT/.direnv/compare"
  WORKTREE_DIR="$COMPARE_DIR/main"
  MANIFESTS_MAIN="$COMPARE_DIR/manifests-main"
  MANIFESTS_CURRENT="$COMPARE_DIR/manifests-current"

  # Cleanup function
  cleanup() {
    echo "Cleaning up..."
    if [ -d "$WORKTREE_DIR" ]; then
      git worktree remove --force "$WORKTREE_DIR" || true
    fi
  }
  trap cleanup EXIT

  echo "Preparing comparison environment..."
  rm -rf "$COMPARE_DIR"
  mkdir -p "$COMPARE_DIR"

  # 1. Checkout Main to Worktree
  echo "Checking out 'main' branch to $WORKTREE_DIR..."
  git worktree add --force --detach "$WORKTREE_DIR" main

  # 2. Setup Pulumi (once)
  echo "Setting up Pulumi..."
  nix run .#setup-pulumi

  # 3. Generate Main Manifests
  # We run the CURRENT generation code (nix run .#generate-manifests)
  # but we execute it inside the main worktree directory so it reads main's configs.
  echo "Generating manifests for MAIN..."
  export PULUMI_MANIFEST_OUTPUT_DIR="$MANIFESTS_MAIN"
  
  # We need to call the generate-manifests script from the current flake,
  # but ensure it runs inside the worktree.
  # We use a subshell to change directory without affecting the script.
  (
    cd "$WORKTREE_DIR"
    # We reference the flake in the original project root to use current tools
    nix run "$PROJECT_ROOT#generate-manifests"
  )

  # 4. Generate Current Manifests
  echo "Generating manifests for CURRENT..."
  export PULUMI_MANIFEST_OUTPUT_DIR="$MANIFESTS_CURRENT"
  nix run .#generate-manifests

  # 5. Diff
  echo "Diffing manifests..."
  echo "----------------------------------------------------------------"
  # Use 'diff' and allow exit code 1 (which means differences found)
  diff -r -u "$MANIFESTS_MAIN" "$MANIFESTS_CURRENT" --color=auto || true
  echo "----------------------------------------------------------------"
  echo "Diff complete."
''