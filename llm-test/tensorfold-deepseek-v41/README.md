# DeepSeek-V4.1-Flash-1017 EXL3 / TensorFold TP2

Staged, **not activated** (`ManagedWorkload.spec.desiredState: Standby`). This is the Kubernetes adaptation of [MiaAI-Lab/DeepSeek-v4.1-Flash-1017-2x-DGX-Sparks](https://github.com/MiaAI-Lab/DeepSeek-v4.1-Flash-1017-2x-DGX-Sparks) at `31eea4608f8bb292a92e2f7a1db400e928620c78`.

## Pins

- Checkpoint: `Mia-AiLab/DeepSeek-V4.1-Flash-1017-EXL3-EAQ-v1-2.9-bpw` @ `45ee5d0fd106c94a3d77f721e09cbb2f50e5a16b`
- Engram source: `deepseek-ai/DeepSeek-V4.1-Flash-1017` @ `1bae0e1088993b9b82de08f59de5be5a34e42170`; only shards 47 and 48 are needed
- Published engine image: `ghcr.io/miaai-lab/deepseek-v4.1-flash-1017-2x-dgx-sparks-tensorfold@sha256:4ed15dceaf0a210052d5db89c74145794d8ee45f63a3436878ac3ec01cea38b5`
- API model: `DeepSeek-V4.1-Flash-1017`, port `8888`
- Recipe upstream commit: `31eea4608f8bb292a92e2f7a1db400e928620c78`

The checkpoint is approximately 196 GiB and the two Engram shards approximately 203 GB. The shared `model-cache` PVC is 3 TiB. The pull job is intentionally suspended in Git; it is a one-shot cache mutation and must be explicitly unsuspended.

## Files

- `05-deepseek-v41-download.yaml`: resumable cache preload for the checkpoint and Engram shards.
- `12-deepseek-v41.yaml`: standby TP2 head/worker Deployments and internal Service.
- `managed-workload.yaml`: Conductor registration, standby until deliberately promoted.
- `zig/Dockerfile` + `zig/patches/`: upstream reproducible image recipe; the staged deployment uses the pinned published image.

## Activation sequence

```sh
kubectl apply -f llm-test/tensorfold-deepseek-v41/05-deepseek-v41-download.yaml
kubectl -n llm-test patch job deepseek-v41-cache-pull-v1 --type=merge -p '{"spec":{"suspend":false}}'
kubectl -n llm-test logs -f job/deepseek-v41-cache-pull-v1
kubectl apply -f llm-test/tensorfold-deepseek-v41/12-deepseek-v41.yaml
kubectl apply -f llm-test/tensorfold-deepseek-v41/managed-workload.yaml
```

The first implementation stops after verified raw weights/Engram files. Rank-cache and kernel-kit preparation must be added and verified before changing the workload from `Standby` to `Resident`; do not route `dgx-spark` traffic to this lane until direct API qualification passes.
