# ArgoCD Pitfall: Manifest-based Applications and SharedResourceWarning

This document explains a common pitfall when working with manifest-based applications in ArgoCD with a multi-cluster setup, and how to avoid it.

## The Problem

When creating a new manifest-based application to be deployed across multiple clusters, it is possible to incorrectly structure the application in a way that causes ArgoCD to generate raw Kubernetes manifests directly from the overlay's `kustomize build`, instead of generating an ArgoCD `Application` resource.

## The Symptom

This incorrect structure leads to a `SharedResourceWarning` in ArgoCD for any cluster-scoped resources (like `ClusterRoleBinding`) or resources in shared namespaces (like `kube-system`). The warning indicates that the same resource is being managed by multiple ArgoCD applications.

Example warning:
```
SharedResourceWarning: ClusterRoleBinding/openbao-auth-delegator is part of applications argocd/bootstrap-dependencies and bootstrap-main-cluster-dependencies
```

## The Cause

The root cause of this issue is an incorrect structure of the application's kustomize files.

**Incorrect Structure:**
```
/bootstrap/base/my-app
├── my-app-crb.yaml
├── my-app-sa.yaml
└── kustomization.yaml  # Contains my-app-crb.yaml, my-app-sa.yaml
```
If the overlay's `kustomization.yaml` directly includes `../../bootstrap/base/my-app` in its `resources`, the `kustomize build` will generate the raw manifests for the `ClusterRoleBinding` and `ServiceAccount`.

## The Solution

The correct approach is to structure the application in a way that the overlay's `kustomize build` generates an ArgoCD `Application` resource, which then deploys the raw manifests.

**Correct Structure:**
```
/bootstrap/base/my-app
├── my-app-app.yaml       # The ArgoCD Application manifest
├── kustomization.yaml    # Contains only my-app-app.yaml
└── config/
    ├── my-app-crb.yaml
    ├── my-app-sa.yaml
    └── kustomization.yaml  # Contains my-app-crb.yaml, my-app-sa.yaml
```

In this structure:
1.  The `my-app-app.yaml` is the ArgoCD `Application` manifest. Its `source.path` points to the `config` directory.
2.  The `kustomization.yaml` in the root of the application directory (`/bootstrap/base/my-app`) only includes the `my-app-app.yaml`.
3.  The overlay's `kustomization.yaml` includes `../../bootstrap/base/my-app` in its `resources`.

With this correct structure, the `kustomize build` on the overlay will generate the `my-app-app` `Application` resource. ArgoCD will then deploy this application, which in turn will deploy the `ClusterRoleBinding` and `ServiceAccount` to the target cluster. This ensures that each cluster gets its own set of resources managed by its own ArgoCD application, avoiding the `SharedResourceWarning`.
