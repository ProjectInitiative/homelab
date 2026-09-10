# MiaAI Vision-Exp runtime integration

Upstream source: `https://github.com/MiaAI-Lab/DeepSeek-v4-Flash-DSpark-2x-DGX-Spark`

- Commit: `957890ac5e26ce149646719298169f80603a3e1f`
- Commit subject: `957890a Merge pull request #229 from palmfuture/fix/issue144-preflight-symlink`
- Base image: `ghcr.io/anemll/dspark-vllm-gx10:0.1.1`
- Base digest: `sha256:a83948492cf13df455170fb42885f5ef4db54fefe0feff0f841ecbff464ac9d8`
- Base vLLM: `0.25.2.dev0+g752a3a504.d20260714`
- Derivative: `registry.taildeab2.ts.net/dspark-vllm-gx10:0.1.1-vision-exp-957890a-r1`
- Derivative digest: `sha256:0d360416743f2cb2cd8059b3bf6966792c86cd55996ae0c0d0a87f1bd6e32270`

## Required patch tree

Copied exactly from the pinned upstream commit:

- `miaai-vision-exp/hotfix-dsv4-vision-exp.py`
- `miaai-vision-exp/vision_exp/__init__.py`
- `miaai-vision-exp/vision_exp/apply.py`
- `miaai-vision-exp/vision_exp/image_processor.py`
- `miaai-vision-exp/vision_exp/processor.py`
- `miaai-vision-exp/vision_exp/vision.py`

The dependency tree is complete: `apply.py` imports `image_processor.py`,
`processor.py`, and `vision.py`; those modules have no additional local modules
outside this tree.

## Ordered startup

The controlled Kubernetes startup now performs:

1. Copy the pinned checkpoint's `encoding/encoding_dsv4.py` into the vLLM
   tokenizer location.
2. Run `/opt/vision-exp-apply.sh`.
3. Verify the exact Anemll `model.py` and `dspark.py` source hashes.
4. Apply and verify the upstream Vision-Exp hotfix. This patches:
   - `nvidia/model.py`: ViT, Aligner, multimodal embedding path, and weight
     mappings.
   - `nvidia/dspark.py`: `bias_vl` to
     `e_score_correction_bias_vl` mapping.
   - `tokenizers/deepseek_v4_encoding.py`: Vision-Exp placeholder handling and
     user-message image validation.
5. Execute the unchanged `vllm serve` command.

Other MiaAI issue-specific performance/quality hotfixes remain disabled; they
are not required to resolve the missing `aligner` module and were not copied
into this derivative.

## Source hashes

Before patching, extracted from the digest-pinned base image:

```text
model.py:                a0cbb88b7a0ac5ba9419e07f8922bb84c861f41611596d719efdd86ce95a2e50
dspark.py:               efe33c32d37ed7f26d869d94626f1415906d31218ec0ee44d79bb2b815b8cf39
deepseek_v4_encoding.py: 582f735bf75ad5fbe2b4a8801d8280a65ff0e41175874249bd62433e78c487ff
```

After patching with the pinned Vision-Exp encoder:

```text
model.py:                dd3a109d12db2eef6d0893264be170c450a77b38a15369d621e09cca7ca86586
dspark.py:               60331f998ed37b64e53ccf024831633494820d47db2f1b5c14e1fedf43237635
deepseek_v4_encoding.py: 2fd01c0eef9466f1564bdaf1c004467eb5cfeac2b5562a3e4358d71fb713f3d2
```

## Offline verification

The no-model-load verification pod passed:

```text
Vision-Exp overlay verification: PASS
class DeepseekV4ForCausalLM
mapper prefixes: vision., aligner., image_start/end/newline/pad
mapper suffix: .ffn.gate.bias_vl
checkpoint tensor keys: 72633
aligner keys: 4
vision keys: 259
image keys: 4
bias_vl keys: 46
```

The 313 Vision-Exp-specific keys are explicitly covered by the upstream
prefix/suffix mappings. The remaining 72,320 text/runtime keys are delegated
to the stock DeepSeek loader; no Vision-Exp key is intentionally discarded.
A full meta-model instantiation was not possible in the CPU-only verification
pod because the Anemll model constructor unconditionally creates CUDA streams.

## Kubernetes parity

| Step | MiaAI default | Kubernetes | Status |
|---|---|---|---|
| Encoder source | selected pinned HF snapshot | same pinned local snapshot | equivalent |
| Vision patch | `python3 /opt/hotfix-dsv4-vision-exp.py` | `/opt/vision-exp-apply.sh` invoking same pinned script | equivalent, fail-closed |
| Vision dependency tree | `/opt/dspark-patches/vision_exp` | baked at same path | equivalent |
| Model/DSpark source guard | hotfix structural checks | exact SHA256 guard plus hotfix checks | stricter |
| vLLM executor | native MP | native MP | unchanged |
| TP / nodes | TP=2 / 2 nodes | TP=2 / 2 nodes | unchanged |
| model loading | lazy safetensors | lazy safetensors | unchanged |
| network/storage/memory settings | DSpark defaults | existing Kubernetes settings | unchanged |

A full TP=2 boot has not yet been run after the image integration. The
registry image is built and pushed, but cluster node containerd cannot resolve
the laptop-only Tailscale registry hostname; the prior HTTP NodePort is not
configured as an insecure registry. No model boot was started under that
condition.
