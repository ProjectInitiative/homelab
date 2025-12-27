# Nix Docker Image Building: Mutability vs. Store Paths

## The Problem
When building Docker images with Nix (`dockerTools.buildImage`), you often use `copyToRoot` to add packages and configuration files. These files reside in the Nix Store (`/nix/store/...`), which is **read-only and immutable**.

If you include a directory in `copyToRoot` (e.g., via `buildEnv` or `runCommand`), that directory in the final image is often a symlink to the read-only store path.

If you then try to modify that directory (e.g., `chown`, `chmod`, or writing files) inside the `runAsRoot` script, the build will fail. This is because `runAsRoot` runs inside a VM that mounts the Nix Store as a read-only filesystem (via `virtiofsd`). Attempting to modify permissions on a read-only mount causes "Input/output error" or "Operation not permitted".

## The Solution
To create a directory that you can modify (e.g., a user's home directory like `/home/nix`):

1.  **Do NOT create it in `copyToRoot`**: Ensure the directory does not exist in the package set you are copying into the image.
2.  **Create it in `runAsRoot`**: Use the `runAsRoot` script to `mkdir`, `chown`, and `chmod` the directory.

When `runAsRoot` executes, it runs in a mutable overlay on top of the base image. Directories created here are standard directories in that overlay, not symlinks to the Nix Store, so you have full permission to modify them.

## Example (Correct Pattern)

```nix
copyToRoot = pkgs.buildEnv {
  # ... packages ...
  # Do NOT include /home/user here
};

runAsRoot = ''
  # Create the directory purely in the mutable layer
  mkdir -p /home/user
  chown -R 1000:1000 /home/user
'';
```
