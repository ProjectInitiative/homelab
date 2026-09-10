#!/usr/bin/env bash
set -euo pipefail

MODEL=/usr/local/lib/python3.12/dist-packages/vllm/models/deepseek_v4/nvidia/model.py
DSPARK=/usr/local/lib/python3.12/dist-packages/vllm/models/deepseek_v4/nvidia/dspark.py
ENCODING=/usr/local/lib/python3.12/dist-packages/vllm/tokenizers/deepseek_v4_encoding.py
PATCH=/opt/vision-exp-hotfix.py
PATCHES=/opt/dspark-patches/vision_exp

# These hashes identify the exact Anemll 0.1.1 source this overlay targets.
EXPECTED_MODEL=a0cbb88b7a0ac5ba9419e07f8922bb84c861f41611596d719efdd86ce95a2e50
EXPECTED_DSPARK=efe33c32d37ed7f26d869d94626f1415906d31218ec0ee44d79bb2b815b8cf39
for pair in "$EXPECTED_MODEL  $MODEL" "$EXPECTED_DSPARK  $DSPARK"; do
  set -- $pair
  actual=$(sha256sum "$2" | awk '{print $1}')
  [ "$actual" = "$1" ] || {
    echo "FATAL: Anemll source drift: $2 has $actual, expected $1" >&2
    exit 1
  }
done
[ -f "$ENCODING" ] || { echo "FATAL: Vision-Exp encoder is not installed: $ENCODING" >&2; exit 1; }
[ -f "$PATCH" ] && [ -f "$PATCHES/apply.py" ] && [ -f "$PATCHES/vision.py" ] || {
  echo "FATAL: incomplete MiaAI Vision-Exp dependency tree" >&2
  exit 1
}

python3 "$PATCH" "$PATCHES" "$MODEL" "$ENCODING" "$DSPARK"
python3 "$PATCH" --status
python3 - <<'PY'
from pathlib import Path
import ast
model = Path('/usr/local/lib/python3.12/dist-packages/vllm/models/deepseek_v4/nvidia/model.py').read_text()
encoding = Path('/usr/local/lib/python3.12/dist-packages/vllm/tokenizers/deepseek_v4_encoding.py').read_text()
ds = Path('/usr/local/lib/python3.12/dist-packages/vllm/models/deepseek_v4/nvidia/dspark.py').read_text()
assert '# [vision-exp-hotfix] native DeepSeek-V4-Flash-Vision-Exp image tower' in model
assert '# [vision-exp-hotfix] allow vLLM-inserted image placeholders' in encoding
assert '# [vision-exp-hotfix] remap ffn.gate.bias_vl' in ds
ast.parse(model); ast.parse(encoding); ast.parse(ds)
print('Vision-Exp overlay verification: PASS')
PY
