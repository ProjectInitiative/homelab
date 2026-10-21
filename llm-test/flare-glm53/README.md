# Flare GLM-5.3 Flash NVFP4/MXFP8 — staged cache preload

This is a staged, non-serving lane for NVIDIA Flare's GLM-5.3 Flash recipe.
It downloads the pinned Local Inference Lab checkpoint into the shared
`model-cache` PVC. It does not create GPU workloads or alter the active
TensorFold/LiteLLM route.

## Pins

- Flare source: `NVIDIA/flare-local-inference` at the reviewed source revision
  `5f37bd14062334f7687d168d58ea00567b9aa7fe` (verify the build commit before
  producing a runtime image).
- Checkpoint: `local-inference-lab/GLM-5.3-Flash-NVFP4-MXFP8-CSF-QAD`
  at `dec48abd33efa73c3bb7c95b74eee10cad34f9be`.
- Storage: 36 safetensors shards under `tensors/`, plus model metadata and
  tokenizer files; the Hugging Face model card says the shards target 5 GB
  each. The download Job verifies the indexed shard set and writes a receipt.

## Next phase (not activated here)

1. Build and digest-pin the upstream Flare serving image for Linux arm64.
2. Run `ignition export glm-5.3-flash --ranks 2` on two eligible DGX Sparks,
   with the Flare checkpoint as input and a deliberately chosen concurrency
   profile (start at 2, then qualify 4 and 6).
3. Publish the signed TP2 runtime package and deploy a test API separately.
4. Register the two Flare rank Deployments in `conductor-workloads` as a
   `ManagedWorkload` using `poolRef: dgx-spark`, `recoveryPolicy:
   RecreateTogether`, worker-first startup/head-first shutdown, and `/health`
   qualification. Start with `desiredState: Standby`; promote to `Resident`
   only after direct and routed qualification. Conductor, not an ad hoc
   restart script, will own pair recovery and redeployment.
5. Evaluate a pod-network/RDMA design before removing `hostNetwork` from the
   current TensorFold lanes. Flare's multi-host mode still requires reachable
   rank control/rendezvous and RoCE; its Dockerfile alone does not solve that
   networking boundary.

The active TensorFold v1.2 lane remains the rollback path until direct,
LiteLLM-routed, 512k-context and concurrency tests pass.
