#!/usr/bin/env bash
set -euo pipefail
MODEL_ROOT=${MODEL_ROOT:-/local-models/deepseek-v4-flash-vision-exp}
cp "$MODEL_ROOT/encoding/encoding_dsv4.py" /usr/local/lib/python3.12/dist-packages/vllm/tokenizers/deepseek_v4_encoding.py
bash /opt/vision-exp-apply.sh
export PYTHONPATH=/opt/dspark-patches${PYTHONPATH:+:$PYTHONPATH}
python3 - <<'PY'
import vllm
import vision_exp.apply as va
from vllm.models.deepseek_v4.nvidia.model import DeepseekV4ForCausalLM
print("vllm", vllm.__version__)
print("class", DeepseekV4ForCausalLM.__name__)
print("mapper_prefixes", sorted(va.VISION_MAPPER_PREFIXES))
print("mapper_suffixes", sorted(va.VISION_MAPPER_SUFFIXES))
PY
python3 - <<'PY'
from pathlib import Path
from safetensors import safe_open
root = Path("/local-models/deepseek-v4-flash-vision-exp")
keys = []
for path in sorted(root.rglob("*.safetensors")):
    with safe_open(str(path), framework="pt", device="cpu") as shard:
        keys.extend(shard.keys())
print("checkpoint_tensor_keys", len(keys))
for needle in ("aligner", "vision", "image", "bias_vl"):
    matches = [key for key in keys if needle in key]
    print(needle, len(matches), matches[:12])
PY
