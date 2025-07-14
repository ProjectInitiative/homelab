# Enabling Argo CD's "Applications in any Namespace" Feature

To solve the problem of application name collisions in a multi-cluster setup, we enabled the **"Applications in any namespace"** feature in Argo CD. This is the standard, most scalable way to manage multiple clusters or tenants from a single Argo CD instance.

Instead of renaming applications with a suffix (e.g., `openbao-main-cluster`), this feature changes how Argo CD identifies an application. The unique ID becomes a combination of its namespace and its name (e.g., `argocd-mc/openbao`). This allows you to use the same application name across different clusters without conflict.

**Official Documentation Link:**

  * [Argo CD Documentation: Applications in any namespace](https://argo-cd.readthedocs.io/en/latest/operator-manual/app-any-namespace/)

-----

## Summary of Manual Steps

Here are the four manual configuration steps we performed to enable and use this feature.

### 1\. Allow Argo CD to Watch New Namespaces

First, you must tell the Argo CD controller that it's allowed to find and manage `Application` resources in namespaces other than the default `argocd` namespace.

  * **Action:** Edit the `argocd-cmd-params-cm` ConfigMap in the `argocd` namespace.

  * **Command:** `kubectl edit configmap argocd-cmd-params-cm -n argocd`

  * **Change:** Add the `application.namespaces` key with a comma-separated list of the namespaces you want to use for your child applications.

    ```yaml
    data:
      application.namespaces: argocd-cc, argocd-mc
    ```

  * **Restart Pods:** After saving the ConfigMap, restart the controller and server pods to apply the change.

    ```bash
    kubectl rollout restart statefulset argocd-application-controller -n argocd
    kubectl rollout restart deployment argocd-repo-server -n argocd
    ```

### 2\. Permit Your AppProject to Use the New Namespaces

Next, you must update your `AppProject` to explicitly allow it to deploy applications that originate from these new namespaces.

  * **Action:** Edit your `AppProject` manifest (e.g., `mc-bootstrap`).

  * **Change:** Add the `sourceNamespaces` field, listing the namespaces you enabled in Step 1.

    ```yaml
    apiVersion: argoproj.io/v1alpha1
    kind: AppProject
    metadata:
      name: mc-bootstrap
      namespace: argocd
    spec:
      # ... other project settings ...
      sourceNamespaces:
      - argocd-cc
      - argocd-mc
    ```

### 3\. Grant the UI/API Access to See the Apps

By default, the Argo CD server (which powers the UI) can only see applications in the `argocd` namespace. You need to grant it cluster-wide permissions to see the applications in your new namespaces.

  * **Action:** Apply the pre-made RBAC manifests provided by the Argo CD project.
  * **Command:**
    ```bash
    # Clone the repo if you don't have it
    git clone https://github.com/argoproj/argo-cd.git

    # Apply the ClusterRole and ClusterRoleBinding
    kubectl apply -k argo-cd/examples/k8s-rbac/argocd-server-applications/
    ```
    This step does not require any edits to the files.

### 4\. Update Kustomize Overlays to Set the Namespace

Finally, instead of patching the `metadata.name` of each application, you use a single, efficient patch in each overlay to set the correct `metadata.namespace`.

  * **Action:** In each cluster's overlay (`overlays/main-cluster`, `overlays/control-cluster`, etc.), use a patch to set the namespace for all child applications.

  * **Example Patch for `main-cluster`:**

    ```yaml
    # In overlays/main-cluster/kustomization.yaml
    patches:
      # ... your destination patch ...

      # Add this patch to set the source namespace for all child apps
      - patch: |-
          - op: add
            path: /metadata/namespace
            value: argocd-mc # <-- All apps for this cluster go in argocd-mc
        target:
          kind: Application
    ```

This approach provides a clean, scalable, and maintainable way to manage multi-cluster deployments without naming conflicts.
