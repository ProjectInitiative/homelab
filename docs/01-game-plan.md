# Production CA and Vault: A GitOps Game Plan

This document outlines the complete plan to deploy a production-ready, High-Availability (HA) `step-ca` and OpenBao installation, fully integrated with a GitOps workflow using Argo CD.

The core challenge is the "chicken-and-egg" problem: OpenBao needs a trusted CA for its own TLS certificates, but the CA needs a secure vault to store its root-of-trust secrets. We will solve this by performing a secure, one-time manual bootstrap of the CA's root keys.

## The Phased Approach

1.  **Phase 1: Prepare the HA Database:** Manually create a dedicated user and database in the existing PostgreSQL cluster for `step-ca`. We will create a temporary Kubernetes secret for these credentials.
2.  **Phase 2: The Root of Trust (Manual Bootstrap):** Generate the `step-ca` root and intermediate keys *locally*. These keys, along with their passwords, will be securely stored in Kubernetes secrets as a one-time action. This is the most critical step for disaster recovery.
3.  **Phase 3: Deploy `step-ca` via GitOps:** Update the `step-ca-values.yaml` to use the PostgreSQL database and the secrets created in the previous phases. Committing this file will trigger Argo CD to deploy a fully configured, HA-ready `step-ca`.
4.  **Phase 4: Deploy OpenBao:** With a trusted CA running, we will deploy OpenBao and use `cert-manager` to automatically issue it a TLS certificate from `step-ca`.
5.  **Phase 5: Connect OpenBao to Argo CD:** Configure the Argo CD Vault Plugin, migrate the temporary PostgreSQL secret into OpenBao, and update the Argo CD application to pull database credentials directly from the vault, completing the secure GitOps loop.
