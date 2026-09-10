from pathlib import Path

path = Path('/usr/local/lib/python3.12/dist-packages/vllm/v1/worker/utils.py')
text = path.read_text()
text = text.replace('import math\n', 'import math\nimport os\n', 1)
needle = '''    if init_snapshot.free_memory < requested_memory:\n        raise ValueError(\n'''
replacement = '''    if init_snapshot.free_memory < requested_memory and os.getenv(\n        "VLLM_SKIP_INIT_MEMORY_CHECK", "0"\n    ) not in {"1", "true", "True"}:\n        raise ValueError(\n'''
if text.count(needle) != 1:
    raise SystemExit(f'expected one request_memory guard, found {text.count(needle)}')
path.write_text(text.replace(needle, replacement, 1))
print('patched request_memory guard')
