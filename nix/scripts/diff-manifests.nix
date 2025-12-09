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
  git fetch origin main
  git worktree add --force --detach "$WORKTREE_DIR" origin/main

  # 2. Setup Pulumi (once for both generations, if needed)
  echo "Setting up Pulumi for local environment..."
  nix run .#setup-pulumi

  # 3. Generate Main Manifests (using current tools against main's code)
  echo "Generating manifests for MAIN..."
  (
    cd "$WORKTREE_DIR/pulumi"
    
    # Create a temporary stack for comparison
    echo "Creating ephemeral stack 'diff-main'..."
    ${pkgs.pulumi}/bin/pulumi login --local
    ${pkgs.pulumi}/bin/pulumi stack select diff-main --create || true
    
    # Set the env var (for code that supports it)
    export PULUMI_MANIFEST_OUTPUT_DIR="$MANIFESTS_MAIN"
    export PULUMI_STACK="diff-main" # Ensure explicit stack usage for 'pulumi up'
    
    # Run generate-manifests from the main project root, but targeted at this worktree's config
    # The generate-manifests script does its own `cd pulumi` internally.
    # So we need to ensure it runs from the $WORKTREE_DIR to pick up main's `Pulumi.yaml`
    cd .. # Go back to worktree root
    nix run "$PROJECT_ROOT#generate-manifests"
    
    # Collect outputs:
    # 1. If code respected PULUMI_MANIFEST_OUTPUT_DIR, they are already in $MANIFESTS_MAIN.
    # 2. If code used default 'manifests' dir (legacy), move them.
    FULL_LEGACY_PATH="$WORKTREE_DIR/pulumi/manifests"
    
    if [ -d "$FULL_LEGACY_PATH" ] && [ -n "$(ls -A "$FULL_LEGACY_PATH")" ]; then
      echo "  Found manifests in legacy path ($FULL_LEGACY_PATH). Moving to collection dir..."
      mkdir -p "$MANIFESTS_MAIN"
      cp -r "$FULL_LEGACY_PATH"/* "$MANIFESTS_MAIN/"
    fi
    
    # Clean up the ephemeral stack
    echo "Removing ephemeral stack..."
    cd "$WORKTREE_DIR/pulumi" # Change back to pulumi dir to remove stack
    ${pkgs.pulumi}/bin/pulumi stack rm diff-main --yes --force || true
  )

  # 4. Generate Current Manifests
  echo "Generating manifests for CURRENT..."
  (
    # We need to be in the pulumi directory to select/create a stack
    cd pulumi
    
    echo "Creating ephemeral stack 'diff-current'..."
    ${pkgs.pulumi}/bin/pulumi login --local
    ${pkgs.pulumi}/bin/pulumi stack select diff-current --create || true
    
    export PULUMI_MANIFEST_OUTPUT_DIR="$MANIFESTS_CURRENT"
    export PULUMI_STACK="diff-current"
    
    # We can run the generate-manifests script from the project root.
    # It will cd into pulumi, but we want it to use our stack.
    # Since we set PULUMI_STACK env var, it should respect it if we modify generate-manifests to respect it?
    # Actually, generate-manifests just runs `pulumi up`.
    # `pulumi up` respects PULUMI_STACK.
    
    cd ..
    nix run .#generate-manifests
    
    # Clean up
    echo "Removing ephemeral stack..."
    cd pulumi
    ${pkgs.pulumi}/bin/pulumi stack rm diff-current --yes --force || true
  )

  # 5. Diff
  echo "Diffing manifests..."
  echo "----------------------------------------------------------------"
  diff -r -u "$MANIFESTS_MAIN" "$MANIFESTS_CURRENT" --color=auto || true
  echo "----------------------------------------------------------------"
  echo "Diff complete."
''