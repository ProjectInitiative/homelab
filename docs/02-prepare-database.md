# Phase 1: Prepare the HA Database

In this phase, we will connect to the existing PostgreSQL cluster and create a dedicated database and user for `step-ca`. We will then create a temporary Kubernetes secret to hold these credentials. This secret will be migrated to OpenBao in a later phase.

## Steps

1.  **Identify the Primary PostgreSQL Pod:**
    We need to connect to the primary pod to perform database operations. The correct namespace is `postgres-db`.

    ```bash
    kubectl get cluster main-postgres-cluster -n postgres-db -o jsonpath='{.status.currentPrimary}'
    ```

    The output of this command will be the name of the primary pod (e.g., `main-postgres-cluster-1`).

2.  **Connect to the Pod and Create the Database and User:**
    Replace `<primary-pod-name>` with the output from the previous command (`main-postgres-cluster-1`).

    ```bash
    kubectl exec -it -n postgres-db main-postgres-cluster-1 -- bash
    ```

    Once inside the pod, connect to PostgreSQL and create the user and database. **Use a strong, randomly generated password.**

    ```sql
    psql -U postgres

    -- Inside the psql shell:
    CREATE DATABASE stepca;
    CREATE USER stepca_user WITH PASSWORD 'YOUR_STRONG_PASSWORD';
    GRANT ALL PRIVILEGES ON DATABASE stepca TO stepca_user;
    \q
    ```

3.  **Create the Temporary Kubernetes Secret:**
    Replace `YOUR_STRONG_PASSWORD` with the password you created. This secret will be created in the `step-ca` namespace. The `dataSource` string will be used by `step-ca` to connect to PostgreSQL.

    ```bash
    kubectl create secret generic step-ca-db-datasource -n step-ca \
      --from-literal=datasource="postgres://stepca_user:YOUR_STRONG_PASSWORD@main-postgres-cluster.postgres.svc.cluster.local:5432/stepca?sslmode=disable"
    ```
