# 🐳 Local Docker Registry in k3s Backed by Garage S3

This guide explains how to set up a **private Docker registry inside your k3s cluster**, backed by your **Garage S3 storage**.  
You can then push locally built images directly into your cluster for fast testing, without waiting for CI/CD builds.

---

## 🧭 Overview

You’ll deploy:

- A `registry:2` container inside your k3s cluster  
- Config stored in a Kubernetes `ConfigMap`  
- S3-compatible backend using your **Garage** cluster  
- Accessible at `local-registry.registry.svc.cluster.local:5000` inside the cluster  
- Optional local access via `kubectl port-forward`

---

## ⚙️ 1. Gather Garage S3 Information

You’ll need the following details from your Garage S3 setup:

| Setting | Example |
|----------|----------|
| Access key | `GKxxxx` |
| Secret key | `yyyyy` |
| Bucket name | `docker` |
| Endpoint URL | `http://garage-s3.garage.svc.cluster.local:3900` |
| Secure | `false` |

> 💡 Use `kubectl get svc -A | grep garage` to find your S3 service endpoint.

---

## 🪶 2. Create the Docker Registry Configuration

Save the following as **`config.yml`**:

```yaml
version: 0.1
log:
  level: info
http:
  addr: :5000
  secret: localdevsecret
  headers:
    X-Content-Type-Options: [nosniff]
storage:
  s3:
    accesskey: GKxxxx
    secretkey: yyyyy
    region: garage
    regionendpoint: http://garage-s3.garage.svc.cluster.local:3900
    bucket: docker
    secure: false
    v4auth: true
    rootdirectory: /
```

Replace the access key, secret key, bucket, and endpoint values with your own.

Create the configmap in your cluster:

```bash
kubectl create namespace registry
kubectl create configmap registry-config --from-file=config.yml -n registry
```

---

## 🚀 3. Deploy the Registry to k3s

Save the following as **`local-registry.yaml`**:

```yaml
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: local-registry
  namespace: registry
spec:
  replicas: 1
  selector:
    matchLabels:
      app: local-registry
  template:
    metadata:
      labels:
        app: local-registry
    spec:
      containers:
      - name: registry
        image: registry:2
        ports:
        - containerPort: 5000
        volumeMounts:
        - name: config
          mountPath: /etc/docker/registry/
        resources:
          requests:
            cpu: 50m
            memory: 128Mi
          limits:
            cpu: 200m
            memory: 512Mi
      volumes:
      - name: config
        configMap:
          name: registry-config
---
apiVersion: v1
kind: Service
metadata:
  name: local-registry
  namespace: registry
spec:
  selector:
    app: local-registry
  ports:
  - port: 5000
    targetPort: 5000
    protocol: TCP
    name: http
  type: ClusterIP
```

Apply it:

```bash
kubectl apply -f local-registry.yaml
```

---

## 🌐 4. Accessing the Registry

### Option A — From Your Local Machine

Forward the registry port:

```bash
kubectl port-forward -n registry svc/local-registry 5000:5000
```

Now push to it from your local Docker:

```bash
docker tag myapp:dev localhost:5000/myapp:dev
docker push localhost:5000/myapp:dev
```

### Option B — From Inside the Cluster

Use the in-cluster DNS name:

```
local-registry.registry.svc.cluster.local:5000
```

Your Kubernetes manifests can reference this directly:

```yaml
image: local-registry.registry.svc.cluster.local:5000/myapp:dev
imagePullPolicy: Always
```

---

## ⚠️ 5. Mark the Registry as Insecure (No TLS)

Because this registry is HTTP-only, you must mark it as insecure.

### On Your Local Machine

Edit `/etc/docker/daemon.json`:

```json
{
  "insecure-registries": ["localhost:5000"]
}
```

Then restart Docker:

```bash
sudo systemctl restart docker
```

### On k3s Nodes (Optional)

If your workloads pull images directly (not preloaded), configure k3s:

```bash
sudo vi /etc/rancher/k3s/registries.yaml
```

Add:

```yaml
mirrors:
  "local-registry.registry.svc.cluster.local:5000":
    endpoint:
      - "http://local-registry.registry.svc.cluster.local:5000"
configs:
  "local-registry.registry.svc.cluster.local:5000":
    tls:
      insecure_skip_verify: true
```

Then restart k3s:

```bash
sudo systemctl restart k3s
```

---

## 🧩 6. Deploy Your App Using the Local Registry

Update your Kubernetes deployment manifest:

```yaml
containers:
- name: myapp
  image: local-registry.registry.svc.cluster.local:5000/myapp:dev
  imagePullPolicy: Always
```

Apply as usual:

```bash
kubectl apply -f myapp-deployment.yaml
```

---

## 🧹 7. Optional Cleanup

To remove everything later:

```bash
kubectl delete namespace registry
```

---

## ✅ Summary

| Step | Description |
|------|--------------|
| 1 | Gather Garage S3 credentials |
| 2 | Create `config.yml` with S3 backend settings |
| 3 | Deploy registry with configmap and service |
| 4 | Push locally via port-forward or access in-cluster |
| 5 | Mark registry as insecure (no TLS) |
| 6 | Deploy workloads referencing your local registry |

---
