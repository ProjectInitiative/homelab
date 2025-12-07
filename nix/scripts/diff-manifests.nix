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
            echo "Generating manifests for MAIN..."
            
            # We use a subshell to change directory without affecting the script.
            (
              cd "$WORKTREE_DIR"
              
              # Create a temporary stack for comparison to avoid locking/dirtying the 'dev' stack
              # if the main branch uses a different state structure.
              # We assume the user has credentials configured.
              echo "Creating ephemeral stack 'diff-main'..."
              ${pkgs.pulumi}/bin/pulumi login --local
              ${pkgs.pulumi}/bin/pulumi stack select diff-main --create || true
              
              # Set the env var (for code that supports it)
              export PULUMI_MANIFEST_OUTPUT_DIR="$MANIFESTS_MAIN"
              
              # We reference the flake in the original project root to use current tools
              # Note: We rely on the tools to respect PULUMI_MANIFEST_OUTPUT_DIR, 
              # OR the code to output to 'manifests'.
              # We suppress the "nix run" output slightly to reduce noise, but keep pulumi output
              nix run "$PROJECT_ROOT#generate-manifests"
              
              # Collect outputs:
              # 1. If code respected PULUMI_MANIFEST_OUTPUT_DIR, they are already in $MANIFESTS_MAIN.
              # 2. If code used default 'manifests' dir (legacy), move them.
              LEGACY_OUTPUT_DIR="manifests" # Relative to where pulumi runs (inside pulumi dir usually, but generate-manifests cd's to pulumi)
              # The generate-manifests script cd's into 'pulumi'. 
              # So if legacy code writes to 'manifests', it ends up in '$WORKTREE_DIR/pulumi/manifests'.
              
              FULL_LEGACY_PATH="$WORKTREE_DIR/pulumi/manifests"
              
              if [ -d "$FULL_LEGACY_PATH" ] && [ -n "$(ls -A "$FULL_LEGACY_PATH")" ]; then
                echo "  Found manifests in legacy path ($FULL_LEGACY_PATH). Moving to collection dir..."
                mkdir -p "$MANIFESTS_MAIN"
                cp -r "$FULL_LEGACY_PATH"/* "$MANIFESTS_MAIN/"
              fi
              
              # Clean up the stack
              echo "Removing ephemeral stack..."
              ${pkgs.pulumi}/bin/pulumi stack rm diff-main --yes --force || true
            )
  
            # 4. Generate Current Manifests  echo "Generating manifests for CURRENT..."
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