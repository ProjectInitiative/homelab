# DGX Spark workload policy

## Scheduling model

The three `gpu=dgx-spark` nodes are one shared capability pool. Workloads must
select the capability labels, not hostnames. TensorFold keeps its two ranks on
different hosts using pod anti-affinity, but may use any eligible Spark.

Conductor owns residency and recovery. The large-model serving workload is the
highest Conductor priority (`0`), so when capacity is lost it can reclaim lower-
priority workloads from the surviving node and restore the LLM first. Lower-
priority workloads can be restored after the failed node returns.

This is deliberately different from Kubernetes `PriorityClass`: the pod class
(`llm-serving-critical`) protects scheduling once a pod is being placed, while
Conductor priority controls which managed workload should own scarce pool
capacity during coordinated recovery. Conductor must implement and verify that
reclamation policy before priority values are treated as operational guarantees.

## Audit findings (2026-10-23)

- TensorFold ranks request 96 GiB and limit 128 GiB each, and use
  `llm-serving-critical`.
- `cygnet-classifier-nv` requests 56 GiB and limits 64 GiB.
- `rkcls-served` requests 8 GiB and limits 32 GiB.
- `gcache-test` has 1 GiB requests and 8 GiB limits per member, but is not
  represented in this repository; ownership and cache behavior need GitOps
  coverage before changing its policy.
- JuiceFS node mounts, CSI, NVIDIA/RDMA, TPM, KubeVirt, and service load
  balancers are node infrastructure and must remain available on GPU nodes.
- Submariner route-agent runs on every node by design because it installs
  per-node routing state. Gateway/globalnet/metrics components are not
  GPU-dependent, but the upstream operator does not expose child resource
  controls through its Helm values.

## Changes in this revision

1. Replace TensorFold hostname affinity with the `gpu=dgx-spark` and
   `gpu-vendor=nvidia` capability selector plus required pod anti-affinity.
2. Set TensorFold's Conductor priority to `0`.
3. Remove the hard-coded DGX-node/Submariner placement policy.

Directly patching Submariner's generated child DaemonSets through an Argo Helm
source is invalid because it mixes Helm and Kustomize sources. No unsafe
post-render controller is introduced here.

## Follow-up required

- Implement Conductor priority-aware reclamation with fencing, bounded eviction,
  and recovery tests. A failed node must be fenced before destructive cleanup;
  a transient `NotReady` state must not trigger split-brain recovery.
- Give general workloads explicit lower Conductor priorities and Kubernetes
  priority classes, then verify that recovery can reclaim them safely.
- Bring `gcache-test` under GitOps and assign it an explicit lower priority and
  namespace quota.
- Add `LimitRange`/`ResourceQuota` for general-purpose namespaces after auditing
  legitimate peaks. These controls do not fully cover GB10 unified-memory use.
- Add host-level OOM, NVIDIA allocation-failure, and node reachability alerts.
