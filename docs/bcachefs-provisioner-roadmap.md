## **Project: Bcachefs-Native K8s Local Provisioner**

### **Phase 1: Tooling & Image Preparation**

* [ ] **Create a Dockerfile:**
  * Base: `alpine` or `debian:slim`.
  * Action: Install `bcachefs-tools` and `bash`.
  * Logic: Include a `setup.sh` script to handle the subvolume creation logic.


* [ ] **Develop `setup.sh` Logic:**
  * Primary: Run `bcachefs subvolume create <PATH>`.
  * Secondary: Implement "Tagging" (e.g., `touch <PATH>/.retention_standard`).
  * Error Handling: Ensure the script exits gracefully if the directory already exists.


* [ ] **CI/CD Build:** Build and push the image to a local/private registry accessible by the K8s cluster.

### **Phase 2: Local-Path-Provisioner Configuration**

* [ ] **Modify `local-path-config` ConfigMap:**
  * Update `helperImage` to point to the new custom Bcachefs image.
  * Define `setupCommand` to point to the `/usr/local/bin/setup.sh` inside the image.


* [ ] **Verify RBAC/Permissions:** Ensure the provisioner’s ServiceAccount has permissions to launch the helper pod with `privileged: true` (necessary for filesystem ioctl calls).

### **Phase 3: Host-Side Automation (Retention)**

* [ ] **Develop Retention Script:**
  * Write a script to crawl `/mnt/pool/k8s-vols/`.
  * Detect subvolumes containing the `.retention_standard` (or similar) marker.
  * Execute `bcachefs subvolume snapshot` for backups and `bcachefs subvolume delete` for cleanup.


* [ ] **Schedule via Systemd/Cron:** Deploy the script on the host OS to run at desired intervals.

### **Phase 4: Validation & Testing**

* [ ] **Test PVC Creation:** Deploy a test Pod/PVC and verify the resulting directory on the host is a true subvolume (`bcachefs subvolume show <PATH>`).
* [ ] **Test Recursion Isolation:** Create a snapshot of the parent `/mnt/pool` and verify that the PVC subvolumes appear as empty directories (proving no infinite recursion).
