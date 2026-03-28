---
name: kubecrafter
description: Writes production-ready Kubernetes manifests and Helm chart patterns including Deployments, Services, Ingress, HPA, resource limits, security contexts, liveness/readiness probes, and Pod Security Standards. Use when a user needs help with k8s configs, Helm values, cluster autoscaling, or hardening workloads.
---

# KubeCrafter

## Overview

Produces complete, hardened Kubernetes manifests and Helm chart structures following Pod Security Standards (Restricted profile), with proper resource requests/limits, health probes, security contexts, and HPA configurations. Every manifest is `kubectl apply` ready.

## Workflow

### 1. Gather Requirements

Before generating manifests, confirm: container image/tag (never `latest`), replica bounds, CPU/memory baseline, exposed ports, config/secrets, ingress hostname + TLS, namespace, and RBAC constraints.

### 2. Deployment Manifest

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
  namespace: production
  labels:
    app.kubernetes.io/name: my-app
    app.kubernetes.io/version: "1.4.2"
spec:
  replicas: 3
  selector:
    matchLabels:
      app.kubernetes.io/name: my-app
  strategy:
    type: RollingUpdate
    rollingUpdate: { maxSurge: 1, maxUnavailable: 0 }
  template:
    metadata:
      labels:
        app.kubernetes.io/name: my-app
    spec:
      automountServiceAccountToken: false
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
        seccompProfile:
          type: RuntimeDefault
      containers:
        - name: my-app
          image: my-org/my-app:1.4.2
          imagePullPolicy: IfNotPresent
          ports: [{ name: http, containerPort: 8080 }]
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities: { drop: ["ALL"] }
          resources:
            requests: { cpu: "100m", memory: "128Mi" }
            limits:   { cpu: "500m", memory: "256Mi" }
          livenessProbe:
            httpGet: { path: /healthz, port: http }
            initialDelaySeconds: 10
            periodSeconds: 15
          readinessProbe:
            httpGet: { path: /readyz, port: http }
            initialDelaySeconds: 5
            periodSeconds: 10
          volumeMounts:
            - { name: tmp, mountPath: /tmp }
      volumes:
        - { name: tmp, emptyDir: {} }
      topologySpreadConstraints:
        - { maxSkew: 1, topologyKey: kubernetes.io/hostname, whenUnsatisfiable: DoNotSchedule,
            labelSelector: { matchLabels: { app.kubernetes.io/name: my-app } } }
```

### 3. Service, Ingress, and HPA

Service: `type: ClusterIP`; expose via Ingress with `cert-manager.io/cluster-issuer: letsencrypt-prod` and `nginx.ingress.kubernetes.io/ssl-redirect: "true"`.

HPA (autoscaling/v2): target `averageUtilization: 70` for CPU, `80` for memory. Set `scaleDown.stabilizationWindowSeconds: 300` to prevent thrashing.

### 4. StatefulSet for Stateful Workloads

Use `StatefulSet` instead of `Deployment` when pods need stable network identity or persistent storage:

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata: { name: my-db, namespace: production }
spec:
  serviceName: my-db
  replicas: 3
  selector: { matchLabels: { app.kubernetes.io/name: my-db } }
  template:
    metadata: { labels: { app.kubernetes.io/name: my-db } }
    spec:
      containers:
        - name: my-db
          image: postgres:16
          volumeMounts: [{ name: data, mountPath: /var/lib/postgresql/data }]
  volumeClaimTemplates:
    - metadata: { name: data }
      spec: { accessModes: [ReadWriteOnce], storageClassName: fast-ssd,
              resources: { requests: { storage: 20Gi } } }
```

Each pod gets its own PVC (`data-my-db-0`, `data-my-db-1`, …). PVCs persist after StatefulSet deletion — clean up manually.

### 5. Helm Chart Structure

Standard layout: `Chart.yaml`, `values.yaml`, `values-production.yaml`, `templates/` containing `_helpers.tpl`, `deployment.yaml`, `service.yaml`, `ingress.yaml`, `hpa.yaml`, `serviceaccount.yaml`. Override image tag at deploy time: `helm upgrade --install my-app ./charts/my-app --set image.tag=$SHA`.

### 6. Pod Security Standards

```yaml
metadata:
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/warn: restricted
```

Restricted profile requires: `runAsNonRoot: true`, `readOnlyRootFilesystem: true`, `allowPrivilegeEscalation: false`, `capabilities.drop: [ALL]`, `seccompProfile.type: RuntimeDefault`.

## Output Format

Deliver: YAML manifests in named files, Helm values file if chart-based, `kubectl apply` or `helm upgrade --install` command, and a checklist of replaceable values (image tags, hostnames, secrets).

## Edge Cases

**`readOnlyRootFilesystem: true` writable path discovery:** Enable in staging first. Check logs for `Read-only file system` errors. For deeper discovery: `kubectl exec <pod> -- strace -e trace=file <app-cmd>` to capture all filesystem writes, then add `emptyDir` volumes for each identified path.

**Resource limits causing OOMKilled:** Increase `limits.memory` to 2× the p99 observed `container_memory_working_set_bytes`. Set `requests` equal to p50 usage. Never remove limits entirely.

**HPA + ArgoCD/Flux `replicas` conflict:** Remove `replicas` from the Deployment manifest (let HPA own it), or configure `ignoreDifferences` in ArgoCD to avoid sync overwriting HPA-managed replica counts:
```yaml
# argocd Application spec
ignoreDifferences:
  - group: apps
    kind: Deployment
    jsonPointers:
      - /spec/replicas
  - group: apps
    kind: StatefulSet
    jsonPointers:
      - /spec/replicas
```
Add additional `jsonPointers` for any other fields ArgoCD overwrites (e.g., `/spec/template/metadata/annotations` for injected sidecars).
