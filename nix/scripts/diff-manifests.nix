{ pkgs, pythonEnv }:
pkgs.writeShellScriptBin "diff-manifests" ''
  set -e
  export PATH="${pythonEnv}/bin:${pkgs.nodejs_22}/bin:$PATH"
  ROOT=$(git rev-parse --show-toplevel)
  COMPARE="$ROOT/.direnv/compare"
  WORKTREE="$COMPARE/main"

  cleanup() { git worktree remove --force "$WORKTREE" 2>/dev/null || true; }
  trap cleanup EXIT

  rm -rf "$COMPARE"
  mkdir -p "$COMPARE/manifests-main" "$COMPARE/manifests-current"

  echo "Checking out 'main' branch to $WORKTREE..."
  git fetch origin main
  git worktree add --force --detach "$WORKTREE" origin/main

  echo "Generating manifests for MAIN..."
  cd "$WORKTREE/generator"
  MANIFEST_OUTPUT_DIR="$COMPARE/manifests-main" ${pythonEnv}/bin/python main.py

  echo "Generating manifests for CURRENT..."
  cd "$ROOT/generator"
  MANIFEST_OUTPUT_DIR="$COMPARE/manifests-current" ${pythonEnv}/bin/python main.py

  echo ""
  echo "============================================"
  echo "# Generated Manifests"
  echo "============================================"
  ${pkgs.dyff}/bin/dyff between -b --ignore-order-changes \
    "$COMPARE/manifests-main/" "$COMPARE/manifests-current/"

  echo ""
  echo "============================================"
  echo "# Static Config Changes"
  echo "============================================"
  git -C "$ROOT" diff "$WORKTREE" HEAD -- \
    'bootstrap/' 'apps/' 'argocd-deployment/' 'parent-apps/' \
    ':!.direnv' 2>/dev/null || true
  echo "Diff complete."
''
